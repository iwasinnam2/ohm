//! at-utility Rust edge gateway.
//!
//! Maintains Redis RESP cache lookups and reverse-proxies to the Python
//! control-plane (or directly to provider base URLs) with connection reuse.
//! Mid-stream failover: if primary upstream errors before first byte, retry
//! fallback base URL on a pre-warmed path.
//!
//! Redis split (Phase 4): AT_RS_REDIS = GET (replica); AT_RS_REDIS_WRITE = SET
//! (leader). Cache keys match Python `cache_key_for_request` (docs/REDIS_MESH.md).

mod resp;

use std::convert::Infallible;
use std::env;
use std::net::SocketAddr;
use std::sync::Arc;

use anyhow::Result;
use bytes::Bytes;
use http_body_util::{BodyExt, Full};
use hyper::body::Incoming;
use hyper::server::conn::http1;
use hyper::service::service_fn;
use hyper::{Method, Request, Response, StatusCode, Uri};
use hyper_util::rt::TokioIo;
use sha2::{Digest, Sha256};
use tokio::net::TcpListener;
use tokio::sync::Mutex;
use tracing::{info, warn};

use crate::resp::RespClient;

#[derive(Clone)]
struct Config {
    listen: SocketAddr,
    redis_addr: String,
    redis_write_addr: String,
    primary_upstream: String,
    fallback_upstream: String,
    cache_ttl: u64,
    api_keys: Vec<String>,
}

impl Config {
    fn from_env() -> Self {
        let listen: SocketAddr = env::var("AT_RS_LISTEN")
            .unwrap_or_else(|_| "0.0.0.0:8081".into())
            .parse()
            .expect("AT_RS_LISTEN");
        let redis_addr = env::var("AT_RS_REDIS").unwrap_or_else(|_| "127.0.0.1:6379".into());
        let redis_write_addr =
            env::var("AT_RS_REDIS_WRITE").unwrap_or_else(|_| redis_addr.clone());
        Self {
            listen,
            redis_addr,
            redis_write_addr,
            primary_upstream: env::var("AT_RS_PRIMARY")
                .unwrap_or_else(|_| "http://127.0.0.1:8080".into()),
            fallback_upstream: env::var("AT_RS_FALLBACK")
                .unwrap_or_else(|_| "http://127.0.0.1:8080".into()),
            cache_ttl: env::var("AT_RS_CACHE_TTL")
                .ok()
                .and_then(|s| s.parse().ok())
                .unwrap_or(3600),
            api_keys: env::var("AT_API_KEYS")
                .unwrap_or_else(|_| "sk-at-dev".into())
                .split(',')
                .map(|s| s.trim().to_string())
                .filter(|s| !s.is_empty())
                .collect(),
        }
    }
}

struct App {
    cfg: Config,
    redis_read: Mutex<Option<RespClient>>,
    redis_write: Mutex<Option<RespClient>>,
    http: hyper_util::client::legacy::Client<
        hyper_util::client::legacy::connect::HttpConnector,
        Full<Bytes>,
    >,
}

fn unauthorized() -> Response<Full<Bytes>> {
    Response::builder()
        .status(StatusCode::UNAUTHORIZED)
        .header("content-type", "application/json")
        .body(Full::new(Bytes::from(
            "{\"error\":{\"message\":\"Invalid API key\",\"type\":\"invalid_request_error\",\"code\":\"unauthorized\"}}",
        )))
        .unwrap()
}

fn extract_bearer(req: &Request<Incoming>) -> Option<String> {
    req.headers()
        .get(hyper::header::AUTHORIZATION)
        .and_then(|v| v.to_str().ok())
        .and_then(|v| {
            let mut parts = v.splitn(2, ' ');
            match (parts.next(), parts.next()) {
                (Some(scheme), Some(token)) if scheme.eq_ignore_ascii_case("bearer") => {
                    Some(token.trim().to_string())
                }
                _ => None,
            }
        })
}

fn sha256_hex(data: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(data);
    hex::encode(hasher.finalize())
}

/// Canonical JSON matching Python `json.dumps(..., sort_keys=True, separators=(",", ":"))`.
fn canonical_json(value: &serde_json::Value) -> String {
    match value {
        serde_json::Value::Null => "null".to_string(),
        serde_json::Value::Bool(b) => {
            if *b {
                "true".to_string()
            } else {
                "false".to_string()
            }
        }
        serde_json::Value::Number(n) => n.to_string(),
        serde_json::Value::String(s) => serde_json::to_string(s).unwrap_or_else(|_| "\"\"".into()),
        serde_json::Value::Array(arr) => {
            let parts: Vec<String> = arr.iter().map(canonical_json).collect();
            format!("[{}]", parts.join(","))
        }
        serde_json::Value::Object(map) => {
            let mut keys: Vec<&String> = map.keys().collect();
            keys.sort();
            let parts: Vec<String> = keys
                .into_iter()
                .map(|k| {
                    let key_json = serde_json::to_string(k).unwrap_or_else(|_| "\"\"".into());
                    format!("{}:{}", key_json, canonical_json(&map[k]))
                })
                .collect();
            format!("{{{}}}", parts.join(","))
        }
    }
}

/// Match Python `cache_key_for_request` (docs/REDIS_MESH.md).
fn cache_key_structured(tenant: &str, body: &serde_json::Value) -> String {
    let model = body.get("model").cloned().unwrap_or(serde_json::Value::Null);
    let messages = body
        .get("messages")
        .cloned()
        .unwrap_or_else(|| serde_json::json!([]));
    let mut extras = serde_json::Map::new();
    extras.insert(
        "fetch_web_context".into(),
        body.get("fetch_web_context")
            .cloned()
            .unwrap_or(serde_json::Value::Bool(false)),
    );
    extras.insert(
        "web_query".into(),
        body.get("web_query")
            .cloned()
            .unwrap_or(serde_json::Value::Null),
    );
    extras.insert(
        "web_urls".into(),
        body.get("web_urls")
            .cloned()
            .unwrap_or_else(|| serde_json::json!([])),
    );
    extras.insert(
        "web_purpose".into(),
        body.get("web_purpose")
            .cloned()
            .unwrap_or(serde_json::Value::Null),
    );
    extras.insert(
        "web_format".into(),
        body.get("web_format")
            .cloned()
            .unwrap_or(serde_json::Value::Null),
    );
    extras.insert(
        "temperature".into(),
        body.get("temperature")
            .cloned()
            .unwrap_or(serde_json::Value::Null),
    );
    extras.insert(
        "max_tokens".into(),
        body.get("max_tokens")
            .cloned()
            .unwrap_or(serde_json::Value::Null),
    );
    extras.insert(
        "cache_control".into(),
        body.get("cache_control")
            .cloned()
            .unwrap_or(serde_json::Value::Null),
    );
    let payload = serde_json::json!({
        "model": model,
        "messages": messages,
        "extras": serde_json::Value::Object(extras),
    });
    let digest = sha256_hex(canonical_json(&payload).as_bytes());
    format!("at:{tenant}:cache:{digest}")
}

async fn ensure_client(slot: &Mutex<Option<RespClient>>, addr: &str) -> bool {
    let mut guard = slot.lock().await;
    if guard.is_none() {
        match RespClient::connect(addr).await {
            Ok(c) => *guard = Some(c),
            Err(e) => {
                warn!("redis connect {addr} failed: {e}");
                return false;
            }
        }
    }
    true
}

async fn authorize(app: &App, token: &str) -> bool {
    if token.is_empty() {
        return false;
    }
    if app.cfg.api_keys.iter().any(|k| k == token) {
        return true;
    }
    let idx = format!("at:global:apikey:{}", sha256_hex(token.as_bytes()));
    if ensure_client(&app.redis_read, &app.cfg.redis_addr).await {
        let mut guard = app.redis_read.lock().await;
        if let Some(client) = guard.as_mut() {
            if let Ok(Some(_)) = client.get(&idx).await {
                return true;
            }
        }
    }
    false
}

async fn resolve_tenant(app: &App, token: &str) -> String {
    let suffix = &token[token.len().saturating_sub(8)..];
    if app.cfg.api_keys.iter().any(|k| k == token) {
        return format!("tenant_bootstrap_{suffix}");
    }
    let idx = format!("at:global:apikey:{}", sha256_hex(token.as_bytes()));
    if ensure_client(&app.redis_read, &app.cfg.redis_addr).await {
        let mut guard = app.redis_read.lock().await;
        if let Some(client) = guard.as_mut() {
            if let Ok(Some(tid)) = client.get(&idx).await {
                return tid;
            }
        }
    }
    format!("tenant_{suffix}")
}

async fn proxy_once(
    app: &App,
    upstream_base: &str,
    req_method: Method,
    path_and_query: &str,
    headers: hyper::HeaderMap,
    body: Bytes,
) -> Result<Response<Incoming>> {
    let uri: Uri = format!(
        "{}{}",
        upstream_base.trim_end_matches('/'),
        path_and_query
    )
    .parse()?;
    let mut builder = Request::builder().method(req_method).uri(uri);
    for (k, v) in headers.iter() {
        // hop-by-hop
        if k == hyper::header::HOST {
            continue;
        }
        builder = builder.header(k, v);
    }
    let upstream_req = builder.body(Full::new(body))?;
    let res = app.http.request(upstream_req).await?;
    Ok(res)
}

async fn handle(app: Arc<App>, req: Request<Incoming>) -> Result<Response<Full<Bytes>>, Infallible> {
    let cfg = &app.cfg;
    if req.uri().path() == "/health" {
        return Ok(Response::new(Full::new(Bytes::from(
            "{\"ok\":true,\"service\":\"ohm\",\"plane\":\"rust\"}",
        ))));
    }

    let Some(token) = extract_bearer(&req) else {
        return Ok(unauthorized());
    };
    if !authorize(&app, &token).await {
        return Ok(unauthorized());
    }

    let method = req.method().clone();
    let path_q = req
        .uri()
        .path_and_query()
        .map(|p| p.as_str().to_string())
        .unwrap_or_else(|| req.uri().path().to_string());
    let headers = req.headers().clone();
    let body = match req.collect().await {
        Ok(c) => c.to_bytes(),
        Err(e) => {
            warn!("body read error: {e}");
            return Ok(Response::builder()
                .status(500)
                .body(Full::new(Bytes::from("body error")))
                .unwrap());
        }
    };

    let tenant = resolve_tenant(&app, &token).await;

    // Cache only non-stream chat completions that do not request web enrichment.
    let is_chat = path_q.starts_with("/v1/chat/completions") && method == Method::POST;
    let body_json = serde_json::from_slice::<serde_json::Value>(&body).ok();
    let wants_stream = body_json
        .as_ref()
        .and_then(|v| v.get("stream").and_then(|s| s.as_bool()))
        .unwrap_or(false);
    let wants_web = body_json
        .as_ref()
        .and_then(|v| v.get("fetch_web_context").and_then(|s| s.as_bool()))
        .unwrap_or(false);

    if is_chat && !wants_stream && !wants_web {
        let key = match body_json.as_ref() {
            Some(v) => cache_key_structured(&tenant, v),
            None => {
                let digest = sha256_hex(&body);
                format!("at:{tenant}:cache:{digest}")
            }
        };
        {
            if ensure_client(&app.redis_read, &cfg.redis_addr).await {
                let mut guard = app.redis_read.lock().await;
                if let Some(client) = guard.as_mut() {
                    if let Ok(Some(cached)) = client.get(&key).await {
                        info!("cache HIT {key}");
                        return Ok(Response::builder()
                            .status(200)
                            .header("content-type", "application/json")
                            .header("x-at-cache", "HIT")
                            .header("x-at-plane", "rust")
                            .body(Full::new(Bytes::from(cached)))
                            .unwrap());
                    }
                }
            }
        }

        // Miss: primary then failover
        let result = match proxy_once(
            &app,
            &cfg.primary_upstream,
            method.clone(),
            &path_q,
            headers.clone(),
            body.clone(),
        )
        .await
        {
            Ok(r) if r.status().is_success() => Ok(r),
            Ok(r) => {
                warn!("primary status {}; trying fallback", r.status());
                proxy_once(
                    &app,
                    &cfg.fallback_upstream,
                    method.clone(),
                    &path_q,
                    headers.clone(),
                    body.clone(),
                )
                .await
            }
            Err(e) => {
                warn!("primary error {e}; trying fallback");
                proxy_once(
                    &app,
                    &cfg.fallback_upstream,
                    method,
                    &path_q,
                    headers,
                    body.clone(),
                )
                .await
            }
        };

        match result {
            Ok(res) => {
                let status = res.status();
                let headers_out = res.headers().clone();
                let bytes = match res.collect().await {
                    Ok(c) => c.to_bytes(),
                    Err(_) => Bytes::new(),
                };
                if status.is_success() {
                    // Prefer Python's write when proxying through control-plane; still
                    // SET on write URL so pure-Rust edges never write a replica.
                    if ensure_client(&app.redis_write, &cfg.redis_write_addr).await {
                        let mut guard = app.redis_write.lock().await;
                        if let Some(client) = guard.as_mut() {
                            let _ = client
                                .set_ex(
                                    &key,
                                    std::str::from_utf8(&bytes).unwrap_or(""),
                                    cfg.cache_ttl,
                                )
                                .await;
                        }
                    }
                }
                let mut builder = Response::builder().status(status);
                for (k, v) in headers_out.iter() {
                    if k == hyper::header::TRANSFER_ENCODING {
                        continue;
                    }
                    builder = builder.header(k, v);
                }
                builder = builder.header("x-at-cache", "MISS").header("x-at-plane", "rust");
                Ok(builder.body(Full::new(bytes)).unwrap())
            }
            Err(e) => Ok(Response::builder()
                .status(502)
                .body(Full::new(Bytes::from(format!("{{\"error\":\"{e}\"}}"))))
                .unwrap()),
        }
    } else {
        // Pass-through (including SSE streams) with failover on connect error
        let result = match proxy_once(
            &app,
            &cfg.primary_upstream,
            method.clone(),
            &path_q,
            headers.clone(),
            body.clone(),
        )
        .await
        {
            Ok(r) => Ok(r),
            Err(e) => {
                warn!("stream/primary fail {e}; fallback");
                proxy_once(&app, &cfg.fallback_upstream, method, &path_q, headers, body).await
            }
        };
        match result {
            Ok(res) => {
                let status = res.status();
                let headers_out = res.headers().clone();
                let bytes = res.collect().await.map(|c| c.to_bytes()).unwrap_or_default();
                let mut builder = Response::builder().status(status);
                for (k, v) in headers_out.iter() {
                    if k == hyper::header::TRANSFER_ENCODING {
                        continue;
                    }
                    builder = builder.header(k, v);
                }
                Ok(builder
                    .header("x-at-plane", "rust")
                    .body(Full::new(bytes))
                    .unwrap())
            }
            Err(e) => Ok(Response::builder()
                .status(502)
                .body(Full::new(Bytes::from(format!("{{\"error\":\"{e}\"}}"))))
                .unwrap()),
        }
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(env::var("RUST_LOG").unwrap_or_else(|_| "info".into()))
        .init();

    let cfg = Config::from_env();
    let listener = TcpListener::bind(cfg.listen).await?;
    info!(
        "at-gateway-rs listening on {} redis_get={} redis_set={}",
        cfg.listen, cfg.redis_addr, cfg.redis_write_addr
    );

    let https = hyper_util::client::legacy::connect::HttpConnector::new();
    let client = hyper_util::client::legacy::Client::builder(hyper_util::rt::TokioExecutor::new())
        .build::<_, Full<Bytes>>(https);

    let app = Arc::new(App {
        cfg,
        redis_read: Mutex::new(None),
        redis_write: Mutex::new(None),
        http: client,
    });

    loop {
        let (stream, addr) = listener.accept().await?;
        let app = app.clone();
        tokio::spawn(async move {
            let io = TokioIo::new(stream);
            let svc = service_fn(move |req| handle(app.clone(), req));
            if let Err(e) = http1::Builder::new().serve_connection(io, svc).await {
                warn!("conn from {addr} error: {e}");
            }
        });
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn structured_key_matches_python_shape() {
        let body = serde_json::json!({
            "model": "mock",
            "messages": [{"role": "user", "content": "hi"}],
        });
        // sk-at-dev last 8 → k-at-dev (matches Python tenant_bootstrap_{key[-8:]})
        let key = cache_key_structured("tenant_bootstrap_k-at-dev", &body);
        assert!(key.starts_with("at:tenant_bootstrap_k-at-dev:cache:"));
        assert_eq!(key.len(), "at:tenant_bootstrap_k-at-dev:cache:".len() + 64);
    }

    #[test]
    fn canonical_json_sorts_keys() {
        let v = serde_json::json!({"b": 1, "a": 2});
        assert_eq!(canonical_json(&v), r#"{"a":2,"b":1}"#);
    }
}

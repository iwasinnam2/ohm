//! at-utility Rust edge gateway.
//!
//! Maintains Redis RESP cache lookups and reverse-proxies to the Python
//! control-plane (or directly to provider base URLs) with connection reuse.
//! Mid-stream failover: if primary upstream errors before first byte, retry
//! fallback base URL on a pre-warmed path.

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
        Self {
            listen,
            redis_addr: env::var("AT_RS_REDIS").unwrap_or_else(|_| "127.0.0.1:6379".into()),
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
    redis: Mutex<Option<RespClient>>,
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

fn cache_key(tenant: &str, body: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(body);
    let digest = hex::encode(hasher.finalize());
    format!("at:{tenant}:cache:{digest}")
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
    if !cfg.api_keys.iter().any(|k| k == &token) {
        return Ok(unauthorized());
    }
    let tenant = format!(
        "tenant_{}",
        &token[token.len().saturating_sub(8)..]
    );

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

    // Cache only non-stream chat completions that do not request web enrichment.
    // fetch_web_context is injected in Python after the raw body hash — edge-caching
    // those requests would skip re-fetch and serve stale augmented completions.
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
        let key = cache_key(&tenant, &body);
        {
            let mut guard = app.redis.lock().await;
            if guard.is_none() {
                match RespClient::connect(&cfg.redis_addr).await {
                    Ok(c) => *guard = Some(c),
                    Err(e) => warn!("redis connect failed: {e}"),
                }
            }
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
                    let mut guard = app.redis.lock().await;
                    if let Some(client) = guard.as_mut() {
                        let _ = client
                            .set_ex(&key, std::str::from_utf8(&bytes).unwrap_or(""), cfg.cache_ttl)
                            .await;
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
    info!("at-gateway-rs listening on {}", cfg.listen);

    let https = hyper_util::client::legacy::connect::HttpConnector::new();
    let client = hyper_util::client::legacy::Client::builder(hyper_util::rt::TokioExecutor::new())
        .build::<_, Full<Bytes>>(https);

    let app = Arc::new(App {
        cfg,
        redis: Mutex::new(None),
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

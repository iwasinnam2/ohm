//! at-utility Rust edge gateway.
//!
//! Maintains Redis RESP cache lookups and reverse-proxies to the Python
//! control-plane (or directly to provider base URLs) with connection reuse.
//! Failover is pre-commit only: if the primary upstream fails on connect (or,
//! for cacheable requests, returns a non-success status), the fallback base
//! URL is retried. Mid-stream handoff after first byte is NOT supported.
//!
//! Cache HITs are only served after Python accepts them via
//! `/internal/edge-hit` (metering + tenant enforcement). Without the shared
//! secret the edge full-proxies so the control plane bills the hit itself.
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
use http_body_util::combinators::BoxBody;
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
    /// Admin keys are not tenant keys and are absent from the Redis key index,
    /// so without this the edge would deny every /v1/admin/* call with a 401
    /// before Python's admin_dep ever saw it. Recognised here only to defer:
    /// authorization stays with Python.
    admin_api_keys: Vec<String>,
    /// Shared secret for /internal/edge-hit. Empty disables edge HIT serving.
    edge_secret: String,
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
            admin_api_keys: env::var("AT_ADMIN_API_KEYS")
                .unwrap_or_default()
                .split(',')
                .map(|s| s.trim().to_string())
                .filter(|s| !s.is_empty())
                .collect(),
            edge_secret: env::var("AT_RS_EDGE_SECRET").unwrap_or_default(),
        }
    }
}

/// Response body: either a buffered chunk or a streamed upstream body.
type ProxyBody = BoxBody<Bytes, hyper::Error>;

fn full_body(data: impl Into<Bytes>) -> ProxyBody {
    Full::new(data.into()).map_err(|never| match never {}).boxed()
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

fn unauthorized() -> Response<ProxyBody> {
    Response::builder()
        .status(StatusCode::UNAUTHORIZED)
        .header("content-type", "application/json")
        .body(full_body(
            "{\"error\":{\"message\":\"Invalid API key\",\"type\":\"invalid_request_error\",\"code\":\"unauthorized\"}}",
        ))
        .unwrap()
}

/// Browser Shell / org console call api.withohm.dev from withohm.dev — need CORS.
fn allowed_cors_origin(origin: Option<&str>) -> Option<&str> {
    let origin = origin?;
    const ALLOWED: &[&str] = &[
        "https://www.withohm.dev",
        "https://withohm.dev",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ];
    if ALLOWED.contains(&origin) {
        return Some(origin);
    }
    // Amplify preview deploys of the marketing site
    if origin.starts_with("https://") && origin.ends_with(".amplifyapp.com") {
        return Some(origin);
    }
    None
}

fn cors_preflight(origin: Option<&str>) -> Response<ProxyBody> {
    let mut builder = Response::builder().status(StatusCode::NO_CONTENT);
    if let Some(o) = allowed_cors_origin(origin) {
        builder = builder
            .header("access-control-allow-origin", o)
            .header(
                "access-control-allow-methods",
                "GET, POST, PUT, PATCH, DELETE, OPTIONS",
            )
            .header(
                "access-control-allow-headers",
                "authorization, content-type, x-ohm-upstream-key, x-ohm-session, x-ohm-path, x-ohm-cost-center",
            )
            .header("access-control-max-age", "86400")
            .header("access-control-allow-credentials", "true")
            .header("vary", "Origin");
    }
    builder.body(full_body("")).unwrap()
}

fn with_cors(mut res: Response<ProxyBody>, origin: Option<&str>) -> Response<ProxyBody> {
    if let Some(o) = allowed_cors_origin(origin) {
        let headers = res.headers_mut();
        headers.insert(
            hyper::header::HeaderName::from_static("access-control-allow-origin"),
            o.parse().unwrap(),
        );
        headers.insert(
            hyper::header::HeaderName::from_static("access-control-allow-credentials"),
            "true".parse().unwrap(),
        );
        headers.insert(
            hyper::header::HeaderName::from_static("access-control-expose-headers"),
            "x-at-cache, x-at-billed-usd, x-at-plane, x-ohm-cost-center, x-ohm-path, x-ohm-spend-cap, x-ohm-spend-cap-usd"
                .parse()
                .unwrap(),
        );
        headers.insert(hyper::header::VARY, "Origin".parse().unwrap());
    }
    res
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

/// Key-v2 content normalization matching Python `cache.normalize_content`:
/// CRLF/CR -> LF, then trim outer whitespace. Interior whitespace untouched.
fn normalize_content(text: &str) -> String {
    text.replace("\r\n", "\n").replace('\r', "\n").trim().to_string()
}

fn normalized_messages(messages: serde_json::Value) -> serde_json::Value {
    match messages {
        serde_json::Value::Array(items) => serde_json::Value::Array(
            items
                .into_iter()
                .map(|mut msg| {
                    if let Some(obj) = msg.as_object_mut() {
                        if let Some(serde_json::Value::String(content)) = obj.get("content") {
                            let normalized = normalize_content(content);
                            if normalized != *content {
                                obj.insert(
                                    "content".into(),
                                    serde_json::Value::String(normalized),
                                );
                            }
                        }
                    }
                    msg
                })
                .collect(),
        ),
        other => other,
    }
}

/// Match Python `cache_key_for_request` (docs/REDIS_MESH.md) — key namespace
/// v2 with normalized message content. Must stay byte-identical to Python or
/// edge HITs silently vanish (parity: tests/test_units.py, tests below).
fn cache_key_structured(tenant: &str, body: &serde_json::Value) -> String {
    let model = body.get("model").cloned().unwrap_or(serde_json::Value::Null);
    let messages = normalized_messages(
        body.get("messages")
            .cloned()
            .unwrap_or_else(|| serde_json::json!([])),
    );
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
    format!("at:{tenant}:cache:v2:{digest}")
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

#[derive(PartialEq)]
enum EdgeAuth {
    /// Bootstrap key or Redis-confirmed tenant key: edge may serve cache HITs.
    Allowed,
    /// Redis reachable and the key is definitively absent: reject at the edge.
    Denied,
    /// Redis unreachable/unconfigured: proxy to Python, which authenticates
    /// every request itself. The edge must NEVER deny on its own outage —
    /// that turns a degraded cache tier into a total API outage for every
    /// issued key (bootstrap keys skip Redis and mask it in CI).
    Unverified,
}

async fn authorize(app: &App, token: &str) -> EdgeAuth {
    if token.is_empty() {
        return EdgeAuth::Denied;
    }
    if app.cfg.api_keys.iter().any(|k| k == token) {
        return EdgeAuth::Allowed;
    }
    // Admin keys: do not deny, do not vouch. Unverified full-proxies to Python,
    // whose admin_dep is the only thing that knows what an admin key may do —
    // and it keeps the key out of the edge cache path, which is tenant-scoped.
    if app.cfg.admin_api_keys.iter().any(|k| k == token) {
        return EdgeAuth::Unverified;
    }
    let idx = format!("at:global:apikey:{}", sha256_hex(token.as_bytes()));
    if ensure_client(&app.redis_read, &app.cfg.redis_addr).await {
        let mut guard = app.redis_read.lock().await;
        if let Some(client) = guard.as_mut() {
            match client.get(&idx).await {
                Ok(Some(_)) => return EdgeAuth::Allowed,
                Ok(None) => return EdgeAuth::Denied,
                Err(e) => {
                    warn!("redis GET apikey failed: {e}; passing through to Python auth");
                    *guard = None;
                    return EdgeAuth::Unverified;
                }
            }
        }
    }
    EdgeAuth::Unverified
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

/// Ask the Python control plane to meter + enforce a cache HIT.
///
/// Returns `Some((status, body))` when Python answered: 2xx means "serve the
/// cached body"; 4xx (401/402/403/429) is a tenant denial to relay verbatim.
/// Returns `None` when the gate is unreachable or 5xx (including 503 when
/// metering is unconfigured) — the caller must fall back to a full proxy.
async fn edge_hit_gate(
    app: &App,
    token: &str,
    total_tokens: i64,
) -> Option<(StatusCode, Bytes)> {
    let cfg = &app.cfg;
    let uri: Uri = format!(
        "{}/internal/edge-hit",
        cfg.primary_upstream.trim_end_matches('/')
    )
    .parse()
    .ok()?;
    let payload = serde_json::json!({ "total_tokens": total_tokens }).to_string();
    let req = Request::builder()
        .method(Method::POST)
        .uri(uri)
        .header(hyper::header::AUTHORIZATION, format!("Bearer {token}"))
        .header("x-ohm-edge-secret", cfg.edge_secret.as_str())
        .header(hyper::header::CONTENT_TYPE, "application/json")
        .body(Full::new(Bytes::from(payload)))
        .ok()?;
    let res = app.http.request(req).await.ok()?;
    let status = res.status();
    if status.is_server_error() {
        return None;
    }
    let bytes = res.collect().await.ok()?.to_bytes();
    Some((status, bytes))
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

async fn handle(app: Arc<App>, req: Request<Incoming>) -> Result<Response<ProxyBody>, Infallible> {
    let origin = req
        .headers()
        .get(hyper::header::ORIGIN)
        .and_then(|v| v.to_str().ok())
        .map(|s| s.to_string());
    if req.method() == Method::OPTIONS {
        return Ok(cors_preflight(origin.as_deref()));
    }
    let res = handle_inner(app, req).await?;
    Ok(with_cors(res, origin.as_deref()))
}

async fn handle_inner(
    app: Arc<App>,
    req: Request<Incoming>,
) -> Result<Response<ProxyBody>, Infallible> {
    let cfg = &app.cfg;
    let path_only = req.uri().path();
    // Liveness is answered at the edge; readiness is proxied without auth so
    // load balancers can probe Redis/provider state on Python.
    if path_only == "/health" {
        return Ok(Response::new(full_body(
            "{\"ok\":true,\"service\":\"ohm\",\"plane\":\"rust\"}",
        )));
    }

    let method = req.method().clone();
    let path_q = req
        .uri()
        .path_and_query()
        .map(|p| p.as_str().to_string())
        .unwrap_or_else(|| req.uri().path().to_string());

    // Stripe webhooks have no Bearer key — signature is verified by Python.
    let is_stripe_webhook =
        path_q.starts_with("/v1/billing/webhook") && method == Method::POST;
    let is_ready = path_only == "/ready" && method == Method::GET;
    // Self-serve checkout mints the tenant key, so callers cannot have one yet.
    // Python applies its own per-IP token bucket on this route.
    let is_public_checkout = path_only == "/v1/billing/checkout" && method == Method::POST;
    // Savings receipts / aggregate stats are unauthenticated by design —
    // Python applies its own per-IP token bucket on these routes.
    let is_public_read = path_only.starts_with("/v1/public/") && method == Method::GET;
    // Slack slash commands carry a Slack signature, not a Bearer key; Python
    // verifies the signature. Without this the edge would 401 them like it did
    // /v1/admin/* before AT_ADMIN_API_KEYS was wired in.
    let is_slack_command =
        path_only.starts_with("/v1/slack/") && method == Method::POST;
    let is_passthrough =
        is_stripe_webhook || is_ready || is_public_checkout || is_public_read || is_slack_command;
    let mut edge_verified = false;
    let token = if is_passthrough {
        None
    } else {
        let Some(token) = extract_bearer(&req) else {
            return Ok(unauthorized());
        };
        match authorize(&app, &token).await {
            EdgeAuth::Denied => return Ok(unauthorized()),
            EdgeAuth::Allowed => edge_verified = true,
            // Unverified: full-proxy; Python re-authenticates every request.
            EdgeAuth::Unverified => {}
        }
        Some(token)
    };

    let headers = req.headers().clone();
    let body = match req.collect().await {
        Ok(c) => c.to_bytes(),
        Err(e) => {
            warn!("body read error: {e}");
            return Ok(Response::builder()
                .status(500)
                .body(full_body("body error"))
                .unwrap());
        }
    };

    if is_passthrough {
        let label = if is_ready {
            "ready"
        } else if is_public_checkout {
            "public checkout"
        } else if is_public_read {
            "public read"
        } else if is_slack_command {
            "slack command"
        } else {
            "stripe webhook"
        };
        let proxied = match proxy_once(
            &app,
            &cfg.primary_upstream,
            method,
            &path_q,
            headers,
            body,
        )
        .await
        {
            Ok(r) => r,
            Err(e) => {
                warn!("{label} proxy error: {e}");
                return Ok(Response::builder()
                    .status(502)
                    .body(full_body("upstream error"))
                    .unwrap());
            }
        };
        let status = proxied.status();
        let out_headers = proxied.headers().clone();
        let bytes = match proxied.collect().await {
            Ok(c) => c.to_bytes(),
            Err(e) => {
                warn!("{label} body error: {e}");
                return Ok(Response::builder()
                    .status(502)
                    .body(full_body("upstream body error"))
                    .unwrap());
            }
        };
        let mut builder = Response::builder().status(status);
        for (k, v) in out_headers.iter() {
            if k == hyper::header::TRANSFER_ENCODING || k == hyper::header::CONTENT_LENGTH {
                continue;
            }
            builder = builder.header(k, v);
        }
        builder = builder.header("x-at-plane", "rust");
        return Ok(builder.body(full_body(bytes)).unwrap());
    }

    let token = token.expect("authorized token");

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

    // Edge cache serving requires verified identity (Redis-confirmed key);
    // unverified requests full-proxy so Python owns both auth and caching.
    if edge_verified && is_chat && !wants_stream && !wants_web {
        let key = match body_json.as_ref() {
            Some(v) => cache_key_structured(&tenant, v),
            None => {
                let digest = sha256_hex(&body);
                format!("at:{tenant}:cache:v2:{digest}")
            }
        };
        let cached: Option<String> = if ensure_client(&app.redis_read, &cfg.redis_addr).await {
            let mut guard = app.redis_read.lock().await;
            match guard.as_mut() {
                Some(client) => client.get(&key).await.ok().flatten(),
                None => None,
            }
        } else {
            None
        };
        if let Some(cached) = cached {
            // Metering + tenant enforcement live in Python: a HIT is only
            // served after /internal/edge-hit accepts it. Without the shared
            // secret, or when the gate is unreachable, fall through to a full
            // proxy so the control plane bills the hit itself.
            if !cfg.edge_secret.is_empty() {
                let total_tokens = serde_json::from_str::<serde_json::Value>(&cached)
                    .ok()
                    .and_then(|v| {
                        v.get("usage")
                            .and_then(|u| u.get("total_tokens"))
                            .and_then(|t| t.as_i64())
                    })
                    .unwrap_or(0);
                match edge_hit_gate(&app, &token, total_tokens).await {
                    Some((status, gate_body)) if status.is_success() => {
                        info!("cache HIT {key} (metered)");
                        let billed = serde_json::from_slice::<serde_json::Value>(&gate_body)
                            .ok()
                            .and_then(|v| v.get("billed_usd").and_then(|b| b.as_f64()))
                            .unwrap_or(0.0);
                        return Ok(Response::builder()
                            .status(200)
                            .header("content-type", "application/json")
                            .header("x-at-cache", "HIT")
                            .header("x-at-plane", "rust")
                            .header("x-at-billed-usd", format!("{billed:.6}"))
                            .body(full_body(cached))
                            .unwrap());
                    }
                    Some((status, gate_body)) => {
                        // Tenant denied (401/402/403/429) — relay verbatim so
                        // suspended/capped tenants are never served from cache.
                        warn!("cache HIT denied by control plane: {status}");
                        return Ok(Response::builder()
                            .status(status)
                            .header("content-type", "application/json")
                            .header("x-at-plane", "rust")
                            .body(full_body(gate_body))
                            .unwrap());
                    }
                    None => {
                        warn!("edge-hit gate unreachable; full-proxying {key}");
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
                // Python already labels its own cache result (e.g. HIT when the
                // edge fell through) — only stamp MISS when it did not.
                if !headers_out.contains_key("x-at-cache") {
                    builder = builder.header("x-at-cache", "MISS");
                }
                builder = builder.header("x-at-plane", "rust");
                Ok(builder.body(full_body(bytes)).unwrap())
            }
            Err(e) => Ok(Response::builder()
                .status(502)
                .body(full_body(format!("{{\"error\":\"{e}\"}}")))
                .unwrap()),
        }
    } else {
        // Pass-through with failover on connect error. Bodies (including SSE
        // streams) are forwarded chunk-by-chunk — never buffered at the edge.
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
                let (parts, upstream_body) = res.into_parts();
                let mut builder = Response::builder().status(parts.status);
                for (k, v) in parts.headers.iter() {
                    if k == hyper::header::TRANSFER_ENCODING
                        || k == hyper::header::CONTENT_LENGTH
                    {
                        continue;
                    }
                    builder = builder.header(k, v);
                }
                Ok(builder
                    .header("x-at-plane", "rust")
                    .body(upstream_body.boxed())
                    .unwrap())
            }
            Err(e) => Ok(Response::builder()
                .status(502)
                .body(full_body(format!("{{\"error\":\"{e}\"}}")))
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
        assert!(key.starts_with("at:tenant_bootstrap_k-at-dev:cache:v2:"));
        assert_eq!(
            key.len(),
            "at:tenant_bootstrap_k-at-dev:cache:v2:".len() + 64
        );
    }

    #[test]
    fn cache_key_v2_parity_with_python() {
        // Pinned against Python cache_key_for_request for the same fixture
        // (tests/test_units.py::test_cache_key_v2_parity). If this drifts,
        // edge HITs silently vanish.
        let body = serde_json::json!({
            "model": "mock",
            "messages": [{"role": "user", "content": "  hello\r\nworld  "}],
        });
        assert_eq!(
            cache_key_structured("parity", &body),
            "at:parity:cache:v2:ea9e2e59350222baec8ed5fc7f85078ea788c48526f389bb6264ef251052db4d"
        );
    }

    #[test]
    fn normalize_content_strips_outer_noise_only() {
        assert_eq!(normalize_content("  a\r\nb  "), "a\nb");
        // Interior whitespace (code indentation) is significant and kept.
        assert_eq!(normalize_content("def f():\n    pass"), "def f():\n    pass");
    }

    #[test]
    fn canonical_json_sorts_keys() {
        let v = serde_json::json!({"b": 1, "a": 2});
        assert_eq!(canonical_json(&v), r#"{"a":2,"b":1}"#);
    }
}

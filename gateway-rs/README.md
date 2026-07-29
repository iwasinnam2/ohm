# at-gateway-rs
#
# Env:
#   AT_RS_LISTEN=0.0.0.0:8081
#   AT_RS_REDIS=127.0.0.1:6379
#   AT_RS_PRIMARY=http://127.0.0.1:8080
#   AT_RS_FALLBACK=http://127.0.0.1:8080
#   AT_API_KEYS=sk-at-dev
#
# Speaks raw RESP to Redis (see src/resp.rs). Proxies OpenAI-compatible traffic
# with primary→fallback failover for zero-downtime model/upstream switching.
#
# Edge chat cache (body-hash) is skipped when fetch_web_context=true so Python
# can inject live context before its post-augmentation cache key.

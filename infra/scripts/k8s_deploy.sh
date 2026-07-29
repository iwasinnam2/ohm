#!/usr/bin/env bash
# Deploy Ohm edge workloads to the leader cluster and print the NLB hostname.
# Prerequisites: kubectl context set; images in ECR; ACM cert issued.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
NS="${AT_K8S_NAMESPACE:-at-utility}"
MANIFEST="${ROOT}/infra/k8s/manifests.yaml"
ACM_ARN="${ACM_CERTIFICATE_ARN:-}"

if [[ -n "$ACM_ARN" ]]; then
  echo "Patching NLB TLS annotation with ACM_CERTIFICATE_ARN"
  tmp="$(mktemp)"
  # shellcheck disable=SC2016
  sed "s|ACM_CERTIFICATE_ARN_PLACEHOLDER|${ACM_ARN}|g" "$MANIFEST" >"$tmp"
  MANIFEST="$tmp"
fi

kubectl get ns "$NS" >/dev/null 2>&1 || kubectl create namespace "$NS"

if [[ -n "${AT_RUNTIME_SECRET_NAME:-}" ]]; then
  echo "Ensure k8s secret exists (skip if already applied): $AT_RUNTIME_SECRET_NAME"
fi

kubectl apply -f "$MANIFEST"
kubectl -n "$NS" rollout status deploy/gateway-rs --timeout=180s
kubectl -n "$NS" rollout status deploy/gateway --timeout=180s

echo "Waiting for NLB hostname…"
for _ in $(seq 1 60); do
  host="$(kubectl -n "$NS" get svc gateway-rs -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || true)"
  if [[ -n "$host" ]]; then
    echo "NLB_HOSTNAME=$host"
    echo "Next: infra/runbooks/API_CUTOVER.md (Phase 1)"
    exit 0
  fi
  sleep 5
done

echo "NLB hostname not ready yet — re-check: kubectl -n $NS get svc gateway-rs" >&2
exit 1

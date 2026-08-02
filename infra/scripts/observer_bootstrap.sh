#!/usr/bin/env bash
# One-time (idempotent) cluster bootstrap for the Observer reflex layer.
# Requires cluster-admin kubectl context on the leader EKS cluster and a
# prior `terraform apply` (pod identity addon + autoscaler IAM + ASG tags).
#
#   aws eks update-kubeconfig --region us-east-1 --name at-utility-eks
#   bash infra/scripts/observer_bootstrap.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

# metrics-server: HPAs read CPU utilization through it. Pinned release so
# bootstrap is reproducible; bump deliberately.
METRICS_SERVER_VERSION="v0.7.2"
echo "Installing metrics-server ${METRICS_SERVER_VERSION}…"
kubectl apply -f "https://github.com/kubernetes-sigs/metrics-server/releases/download/${METRICS_SERVER_VERSION}/components.yaml"

echo "Installing cluster-autoscaler…"
kubectl apply -f "${ROOT}/infra/k8s/autoscaler.yaml"

kubectl -n kube-system rollout status deploy/metrics-server --timeout=120s
kubectl -n kube-system rollout status deploy/cluster-autoscaler --timeout=120s

echo "Applying workload manifests (HPAs)…"
MANIFEST="${ROOT}/infra/k8s/manifests.yaml"
if [[ -n "${ACM_CERTIFICATE_ARN:-}" ]]; then
  # Same placeholder handling as k8s_deploy.sh — never apply the raw
  # placeholder over the live NLB TLS annotation.
  tmp="$(mktemp)"
  sed "s|ACM_CERTIFICATE_ARN_PLACEHOLDER|${ACM_CERTIFICATE_ARN}|g" "$MANIFEST" >"$tmp"
  MANIFEST="$tmp"
else
  echo "ACM_CERTIFICATE_ARN unset — applying HPAs and CronJob only (svc untouched)."
  kubectl apply -f "${ROOT}/infra/k8s/manifests.yaml" --dry-run=client -o yaml >/dev/null # validate
  kubectl -n at-utility apply -f <(python3 - "$MANIFEST" <<'PY'
import sys, yaml
docs = [d for d in yaml.safe_load_all(open(sys.argv[1])) if d]
keep = {"HorizontalPodAutoscaler", "CronJob", "Role", "RoleBinding"}
print(yaml.safe_dump_all([d for d in docs if d.get("kind") in keep]))
PY
  )
  echo "Run infra/scripts/k8s_deploy.sh with ACM_CERTIFICATE_ARN for the full apply."
  MANIFEST=""
fi
if [[ -n "$MANIFEST" ]]; then
  kubectl apply -f "$MANIFEST"
fi

echo
echo "Verify:"
echo "  kubectl -n at-utility get hpa            # targets should show % not <unknown>"
echo "  kubectl top pods -n at-utility           # metrics-server live"
echo "  kubectl -n kube-system logs deploy/cluster-autoscaler | tail -5"

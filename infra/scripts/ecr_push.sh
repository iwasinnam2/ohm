# Build and push immutable version tags to ECR (Section C).
# Usage: ./infra/scripts/ecr_push.sh 0.1.0

set -euo pipefail

TAG="${1:?usage: ecr_push.sh <version>}"
REGION="${AWS_REGION:-us-east-1}"
ACCOUNT_ID="${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text)}"
PREFIX="${ECR_PREFIX:-at-utility}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

login() {
  aws ecr get-login-password --region "$REGION" \
    | docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"
}

push_one() {
  local name="$1"
  local dockerfile="$2"
  local context="$3"
  local repo="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${PREFIX}/${name}:${TAG}"
  echo "Building $repo"
  docker build -f "$dockerfile" -t "$repo" "$context"
  docker push "$repo"
}

login
push_one "gateway" "${ROOT}/Dockerfile" "${ROOT}"
push_one "gateway-rs" "${ROOT}/gateway-rs/Dockerfile" "${ROOT}/gateway-rs"
push_one "ingest-worker" "${ROOT}/workers/Dockerfile" "${ROOT}"

echo "Pushed ${PREFIX}/*:${TAG} — use this tag in k8s manifests (never latest)."

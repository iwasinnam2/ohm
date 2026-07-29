# Bootstrap AWS account pieces for Section C (run once per account).
# Requires: aws CLI authenticated, permissions for S3 + DynamoDB.

set -euo pipefail

ACCOUNT_ID="${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text)}"
REGION="${AWS_REGION:-us-east-1}"
BUCKET="${TF_STATE_BUCKET:-at-utility-tfstate}"
TABLE="${TF_LOCK_TABLE:-at-utility-tf-locks}"

echo "Account=$ACCOUNT_ID Region=$REGION Bucket=$BUCKET Table=$TABLE"

if ! aws s3api head-bucket --bucket "$BUCKET" 2>/dev/null; then
  if [ "$REGION" = "us-east-1" ]; then
    aws s3api create-bucket --bucket "$BUCKET" --region "$REGION"
  else
    aws s3api create-bucket --bucket "$BUCKET" --region "$REGION" \
      --create-bucket-configuration LocationConstraint="$REGION"
  fi
  aws s3api put-bucket-versioning --bucket "$BUCKET" \
    --versioning-configuration Status=Enabled
  aws s3api put-bucket-encryption --bucket "$BUCKET" \
    --server-side-encryption-configuration \
    '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
  aws s3api put-public-access-block --bucket "$BUCKET" \
    --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
fi

aws dynamodb describe-table --table-name "$TABLE" --region "$REGION" >/dev/null 2>&1 || \
  aws dynamodb create-table \
    --table-name "$TABLE" \
    --attribute-definitions AttributeName=LockID,AttributeType=S \
    --key-schema AttributeName=LockID,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region "$REGION"

echo "Enable billing alarms in AWS Budgets console (OpenAI spend is separate)."
echo "Done. Copy backend.hcl.example -> backend.hcl and terraform init -backend-config=backend.hcl"

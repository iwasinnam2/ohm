# CI/CD identity — GitHub Actions deploys with no long-lived AWS keys.
# The workflow (.github/workflows/deploy.yml) assumes ohm-github-deployer via
# OIDC, pushes SHA-tagged images to ECR, and rolls the at-utility deployments.
# Local machines are only needed for intentional ops (see docs/OPERATIONS.md).

variable "github_repo" {
  type        = string
  default     = "iwasinnam2/ohm"
  description = "GitHub repo (owner/name) allowed to assume the deployer role"
}

resource "aws_iam_openid_connect_provider" "github" {
  provider = aws.leader
  url      = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
  # AWS validates GitHub's cert against trusted roots; thumbprints are
  # required by the API but effectively ignored for this provider.
  thumbprint_list = [
    "6938fd4d98bab03faadb97b34396831e3780aea1",
    "1c58a3a8518e8759bf075b76b750d4f2df264fcd",
  ]
  tags = { Project = var.project }
}

data "aws_iam_policy_document" "github_trust" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }
    # master only — PRs and forks cannot assume the role.
    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_repo}:ref:refs/heads/master"]
    }
  }
}

resource "aws_iam_role" "github_deployer" {
  provider           = aws.leader
  name               = "ohm-github-deployer"
  assume_role_policy = data.aws_iam_policy_document.github_trust.json
  tags               = { Project = var.project }
}

data "aws_iam_policy_document" "github_deployer" {
  statement {
    sid       = "EcrAuth"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }

  statement {
    sid = "EcrPushPull"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:BatchGetImage",
      "ecr:GetDownloadUrlForLayer",
      "ecr:InitiateLayerUpload",
      "ecr:UploadLayerPart",
      "ecr:CompleteLayerUpload",
      "ecr:PutImage",
      "ecr:DescribeImages",
    ]
    resources = [
      aws_ecr_repository.gateway.arn,
      aws_ecr_repository.gateway_rs.arn,
      aws_ecr_repository.ingest_worker.arn,
    ]
  }

  statement {
    sid       = "EksDescribe"
    actions   = ["eks:DescribeCluster"]
    resources = [aws_eks_cluster.leader[0].arn]
  }
}

resource "aws_iam_role_policy" "github_deployer" {
  provider = aws.leader
  name     = "ohm-github-deployer"
  role     = aws_iam_role.github_deployer.id
  policy   = data.aws_iam_policy_document.github_deployer.json
}

# Maps the role into Kubernetes as group "ohm-deployers"; the namespace-scoped
# Role/RoleBinding in infra/k8s/manifests.yaml grants rollout rights only.
resource "aws_eks_access_entry" "github_deployer" {
  count             = var.enable_eks ? 1 : 0
  provider          = aws.leader
  cluster_name      = aws_eks_cluster.leader[0].name
  principal_arn     = aws_iam_role.github_deployer.arn
  kubernetes_groups = ["ohm-deployers"]
  type              = "STANDARD"
  tags              = { Project = var.project }
}

output "github_deployer_role_arn" {
  value = aws_iam_role.github_deployer.arn
}

# Observer reflex layer — cluster-autoscaler wiring (leader EKS).
#
# IAM via EKS Pod Identity (no OIDC thumbprint plumbing): the
# eks-pod-identity-agent addon plus an association maps the kube-system
# cluster-autoscaler ServiceAccount to an IAM role scoped to this cluster's
# ASGs. The workload itself is infra/k8s/autoscaler.yaml, applied once by
# infra/scripts/observer_bootstrap.sh.

resource "aws_eks_addon" "pod_identity" {
  count        = var.enable_eks ? 1 : 0
  provider     = aws.leader
  cluster_name = aws_eks_cluster.leader[0].name
  addon_name   = "eks-pod-identity-agent"
}

# Cluster-autoscaler auto-discovery reads these tags off the ASG. EKS managed
# node-group tags do not propagate to the ASG, so tag it directly.
resource "aws_autoscaling_group_tag" "ca_enabled" {
  count    = var.enable_eks ? 1 : 0
  provider = aws.leader

  autoscaling_group_name = aws_eks_node_group.leader[0].resources[0].autoscaling_groups[0].name

  tag {
    key                 = "k8s.io/cluster-autoscaler/enabled"
    value               = "true"
    propagate_at_launch = false
  }
}

resource "aws_autoscaling_group_tag" "ca_owned" {
  count    = var.enable_eks ? 1 : 0
  provider = aws.leader

  autoscaling_group_name = aws_eks_node_group.leader[0].resources[0].autoscaling_groups[0].name

  tag {
    key                 = "k8s.io/cluster-autoscaler/${local.name_prefix}-eks"
    value               = "owned"
    propagate_at_launch = false
  }
}

resource "aws_iam_role" "cluster_autoscaler" {
  count    = var.enable_eks ? 1 : 0
  provider = aws.leader
  name     = "${local.name_prefix}-cluster-autoscaler"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "pods.eks.amazonaws.com" }
      Action    = ["sts:AssumeRole", "sts:TagSession"]
    }]
  })

  tags = { Project = var.project }
}

resource "aws_iam_role_policy" "cluster_autoscaler" {
  count    = var.enable_eks ? 1 : 0
  provider = aws.leader
  name     = "cluster-autoscaler"
  role     = aws_iam_role.cluster_autoscaler[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        # Read-only discovery across ASGs/instances.
        Effect = "Allow"
        Action = [
          "autoscaling:DescribeAutoScalingGroups",
          "autoscaling:DescribeAutoScalingInstances",
          "autoscaling:DescribeLaunchConfigurations",
          "autoscaling:DescribeScalingActivities",
          "autoscaling:DescribeTags",
          "ec2:DescribeImages",
          "ec2:DescribeInstanceTypes",
          "ec2:DescribeLaunchTemplateVersions",
          "ec2:GetInstanceTypesFromInstanceRequirements",
          "eks:DescribeNodegroup",
        ]
        Resource = "*"
      },
      {
        # Mutations only on ASGs tagged for this cluster.
        Effect = "Allow"
        Action = [
          "autoscaling:SetDesiredCapacity",
          "autoscaling:TerminateInstanceInAutoScalingGroup",
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "autoscaling:ResourceTag/k8s.io/cluster-autoscaler/${local.name_prefix}-eks" = "owned"
          }
        }
      },
    ]
  })
}

resource "aws_eks_pod_identity_association" "cluster_autoscaler" {
  count           = var.enable_eks ? 1 : 0
  provider        = aws.leader
  cluster_name    = aws_eks_cluster.leader[0].name
  namespace       = "kube-system"
  service_account = "cluster-autoscaler"
  role_arn        = aws_iam_role.cluster_autoscaler[0].arn

  depends_on = [aws_eks_addon.pod_identity]
}

# Leader-region EKS for single-region public API (Section C / API_CUTOVER Phase 1).
# Keep enable_edges=false until api.withohm.dev miss/hit is green.

variable "enable_eks" {
  type        = bool
  default     = true
  description = "Provision EKS control plane + managed node group in the leader VPC"
}

variable "eks_node_instance_types" {
  type    = list(string)
  default = ["t3.medium"]
}

variable "eks_desired_nodes" {
  type    = number
  default = 2
}

data "aws_eks_cluster_auth" "leader" {
  count    = var.enable_eks ? 1 : 0
  provider = aws.leader
  name     = aws_eks_cluster.leader[0].name
}

resource "aws_iam_role" "eks_cluster" {
  count    = var.enable_eks ? 1 : 0
  provider = aws.leader
  name     = "${local.name_prefix}-eks-cluster"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "eks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  count      = var.enable_eks ? 1 : 0
  provider   = aws.leader
  role       = aws_iam_role.eks_cluster[0].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
}

resource "aws_iam_role" "eks_node" {
  count    = var.enable_eks ? 1 : 0
  provider = aws.leader
  name     = "${local.name_prefix}-eks-node"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "eks_worker" {
  count      = var.enable_eks ? 1 : 0
  provider   = aws.leader
  role       = aws_iam_role.eks_node[0].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
}

resource "aws_iam_role_policy_attachment" "eks_cni" {
  count      = var.enable_eks ? 1 : 0
  provider   = aws.leader
  role       = aws_iam_role.eks_node[0].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
}

resource "aws_iam_role_policy_attachment" "eks_ecr" {
  count      = var.enable_eks ? 1 : 0
  provider   = aws.leader
  role       = aws_iam_role.eks_node[0].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

resource "aws_security_group" "eks_cluster" {
  count       = var.enable_eks ? 1 : 0
  provider    = aws.leader
  name        = "${local.name_prefix}-eks-cluster"
  description = "EKS control plane"
  vpc_id      = aws_vpc.leader.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${local.name_prefix}-eks-cluster-sg" }
}

resource "aws_eks_cluster" "leader" {
  count     = var.enable_eks ? 1 : 0
  provider  = aws.leader
  name      = "${local.name_prefix}-eks"
  role_arn  = aws_iam_role.eks_cluster[0].arn
  version   = "1.31"

  vpc_config {
    subnet_ids              = concat(aws_subnet.private[*].id, aws_subnet.public[*].id)
    endpoint_private_access = true
    endpoint_public_access  = true
    security_group_ids      = [aws_security_group.eks_cluster[0].id]
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy,
  ]

  tags = { Project = var.project }
}

resource "aws_eks_node_group" "leader" {
  count           = var.enable_eks ? 1 : 0
  provider        = aws.leader
  cluster_name    = aws_eks_cluster.leader[0].name
  node_group_name = "${local.name_prefix}-ng"
  node_role_arn   = aws_iam_role.eks_node[0].arn
  subnet_ids      = aws_subnet.private[*].id
  instance_types  = var.eks_node_instance_types

  scaling_config {
    desired_size = var.eks_desired_nodes
    max_size     = max(var.eks_desired_nodes + 1, 3)
    min_size     = 1
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_worker,
    aws_iam_role_policy_attachment.eks_cni,
    aws_iam_role_policy_attachment.eks_ecr,
  ]

  tags = { Project = var.project }
}

# Broader: allow Redis from entire VPC (EKS pods use CNI ENIs in VPC CIDR)
resource "aws_security_group_rule" "redis_from_vpc" {
  count             = var.enable_eks ? 1 : 0
  provider          = aws.leader
  type              = "ingress"
  from_port         = 6379
  to_port           = 6379
  protocol          = "tcp"
  security_group_id = aws_security_group.redis.id
  cidr_blocks       = [aws_vpc.leader.cidr_block]
  description       = "Redis from leader VPC (EKS pods)"
}

output "eks_cluster_name" {
  value = try(aws_eks_cluster.leader[0].name, null)
}

output "eks_cluster_endpoint" {
  value = try(aws_eks_cluster.leader[0].endpoint, null)
}

output "eks_update_kubeconfig" {
  value = var.enable_eks ? "aws eks update-kubeconfig --region ${var.leader_region} --name ${aws_eks_cluster.leader[0].name}" : null
}

# Regional edge — Global Datastore secondary + RL Redis + optional EKS (Section D).

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

variable "project" {
  type = string
}

variable "region" {
  type = string
}

variable "leader_primary_endpoint" {
  type = string
}

variable "leader_vpc_id" {
  type = string
}

variable "leader_vpc_cidr" {
  type = string
}

variable "leader_route_table_ids" {
  type        = list(string)
  description = "Leader private (+ public) route tables that need a return path to this edge"
  default     = []
}

variable "global_replication_group_id" {
  type        = string
  default     = ""
  description = "ElastiCache Global Datastore id from leader"
}

variable "attach_global_datastore" {
  type        = bool
  default     = false
  description = "Create secondary RG attached to Global Datastore (known at plan time)"
}

variable "vpc_cidr" {
  type    = string
  default = "10.30.0.0/16"
}

variable "gateway_image" {
  type    = string
  default = ""
}

variable "gateway_rs_image" {
  type    = string
  default = ""
}

variable "replica_node_type" {
  type    = string
  default = "cache.t4g.micro"
}

variable "create_resources" {
  type        = bool
  default     = false
  description = "Set true when AWS credentials + peering are ready for this region"
}

variable "enable_eks" {
  type        = bool
  default     = true
  description = "Provision EKS + node group in this edge for gateway NLBs"
}

variable "eks_node_instance_types" {
  type    = list(string)
  default = ["t3.medium"]
}

variable "eks_desired_nodes" {
  type    = number
  default = 2
}

variable "domain_name" {
  type    = string
  default = "api.withohm.dev"
}

variable "leader_region" {
  type    = string
  default = "us-east-1"
}

data "aws_caller_identity" "current" {
  count = var.create_resources ? 1 : 0
}

data "aws_availability_zones" "available" {
  count = var.create_resources ? 1 : 0
  state = "available"
}

locals {
  azs          = var.create_resources ? slice(data.aws_availability_zones.available[0].names, 0, 2) : []
  has_global   = var.create_resources && var.attach_global_datastore
  replica_host = local.has_global ? aws_elasticache_replication_group.cache_secondary[0].primary_endpoint_address : ""
  rl_host      = var.create_resources ? aws_elasticache_cluster.rl[0].cache_nodes[0].address : ""
  name_prefix  = "${var.project}-${replace(var.region, "-", "")}"
}

resource "aws_vpc" "edge" {
  count                = var.create_resources ? 1 : 0
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = {
    Name    = "${var.project}-edge-${var.region}"
    Project = var.project
    Region  = var.region
  }
}

resource "aws_internet_gateway" "edge" {
  count  = var.create_resources ? 1 : 0
  vpc_id = aws_vpc.edge[0].id
  tags   = { Name = "${var.project}-edge-igw-${var.region}" }
}

resource "aws_subnet" "public" {
  count                   = var.create_resources ? length(local.azs) : 0
  vpc_id                  = aws_vpc.edge[0].id
  cidr_block              = cidrsubnet(var.vpc_cidr, 4, count.index + 8)
  availability_zone       = local.azs[count.index]
  map_public_ip_on_launch = true
  tags                    = { Name = "${var.project}-edge-public-${count.index}" }
}

resource "aws_subnet" "private" {
  count             = var.create_resources ? length(local.azs) : 0
  vpc_id            = aws_vpc.edge[0].id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, count.index)
  availability_zone = local.azs[count.index]
  tags              = { Name = "${var.project}-edge-private-${count.index}" }
}

resource "aws_eip" "nat" {
  count  = var.create_resources ? 1 : 0
  domain = "vpc"
  tags   = { Name = "${var.project}-edge-nat-${var.region}" }
}

resource "aws_nat_gateway" "edge" {
  count         = var.create_resources ? 1 : 0
  allocation_id = aws_eip.nat[0].id
  subnet_id     = aws_subnet.public[0].id
  tags          = { Name = "${var.project}-edge-nat-${var.region}" }
  depends_on    = [aws_internet_gateway.edge]
}

resource "aws_route_table" "public" {
  count  = var.create_resources ? 1 : 0
  vpc_id = aws_vpc.edge[0].id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.edge[0].id
  }
  tags = { Name = "${var.project}-edge-public-rt-${var.region}" }
}

resource "aws_route_table_association" "public" {
  count          = var.create_resources ? length(aws_subnet.public) : 0
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public[0].id
}

resource "aws_route_table" "private" {
  count  = var.create_resources ? 1 : 0
  vpc_id = aws_vpc.edge[0].id
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.edge[0].id
  }
  tags = { Name = "${var.project}-edge-private-rt-${var.region}" }
}

resource "aws_route_table_association" "private" {
  count          = var.create_resources ? length(aws_subnet.private) : 0
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[0].id
}

# Cross-region peering requester (accepted in leader)
resource "aws_vpc_peering_connection" "to_leader" {
  count         = var.create_resources ? 1 : 0
  vpc_id        = aws_vpc.edge[0].id
  peer_vpc_id   = var.leader_vpc_id
  peer_owner_id = data.aws_caller_identity.current[0].account_id
  peer_region   = var.leader_region
  auto_accept   = false
  tags = {
    Name    = "${var.project}-peer-to-leader"
    Project = var.project
  }
}

resource "aws_route" "to_leader" {
  count                     = var.create_resources ? 1 : 0
  route_table_id            = aws_route_table.private[0].id
  destination_cidr_block    = var.leader_vpc_cidr
  vpc_peering_connection_id = aws_vpc_peering_connection.to_leader[0].id
}

resource "aws_security_group" "redis" {
  count       = var.create_resources ? 1 : 0
  name        = "${var.project}-edge-redis-${var.region}"
  description = "Edge Global Datastore secondary + local RL Redis"
  vpc_id      = aws_vpc.edge[0].id

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_elasticache_subnet_group" "edge" {
  count      = var.create_resources ? 1 : 0
  name       = "${var.project}-edge-${var.region}"
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_elasticache_cluster" "rl" {
  count                = var.create_resources ? 1 : 0
  cluster_id           = "${var.project}-rl-${replace(var.region, "-", "")}"
  engine               = "redis"
  engine_version       = "7.1"
  node_type            = var.replica_node_type
  num_cache_nodes      = 1
  port                 = 6379
  subnet_group_name    = aws_elasticache_subnet_group.edge[0].name
  security_group_ids   = [aws_security_group.redis[0].id]
  parameter_group_name = "default.redis7"
  tags = {
    Role   = "regional-rate-limit"
    Region = var.region
  }
}

resource "aws_elasticache_replication_group" "cache_secondary" {
  count                       = local.has_global ? 1 : 0
  replication_group_id        = "${var.project}-cache-${replace(var.region, "-", "")}"
  description                 = "${var.project} prompt-cache secondary ${var.region}"
  global_replication_group_id = var.global_replication_group_id
  num_cache_clusters          = 2
  automatic_failover_enabled  = true
  multi_az_enabled            = true
  port                        = 6379
  subnet_group_name           = aws_elasticache_subnet_group.edge[0].name
  security_group_ids          = [aws_security_group.redis[0].id]
  tags = {
    Role   = "redis-cache-secondary"
    Region = var.region
  }
}

# --- ACM (regional) for NLB TLS ---
resource "aws_acm_certificate" "api" {
  count             = var.create_resources ? 1 : 0
  domain_name       = var.domain_name
  validation_method = "DNS"
  lifecycle {
    create_before_destroy = true
  }
  tags = { Project = var.project, Region = var.region }
}

# --- EKS ---
resource "aws_iam_role" "eks_cluster" {
  count = var.create_resources && var.enable_eks ? 1 : 0
  name  = "${local.name_prefix}-eks-cluster"

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
  count      = var.create_resources && var.enable_eks ? 1 : 0
  role       = aws_iam_role.eks_cluster[0].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
}

resource "aws_iam_role" "eks_node" {
  count = var.create_resources && var.enable_eks ? 1 : 0
  name  = "${local.name_prefix}-eks-node"

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
  count      = var.create_resources && var.enable_eks ? 1 : 0
  role       = aws_iam_role.eks_node[0].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
}

resource "aws_iam_role_policy_attachment" "eks_cni" {
  count      = var.create_resources && var.enable_eks ? 1 : 0
  role       = aws_iam_role.eks_node[0].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
}

resource "aws_iam_role_policy_attachment" "eks_ecr" {
  count      = var.create_resources && var.enable_eks ? 1 : 0
  role       = aws_iam_role.eks_node[0].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

resource "aws_security_group" "eks_cluster" {
  count       = var.create_resources && var.enable_eks ? 1 : 0
  name        = "${local.name_prefix}-eks-cluster"
  description = "EKS control plane"
  vpc_id      = aws_vpc.edge[0].id
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = { Name = "${local.name_prefix}-eks-cluster-sg" }
}

resource "aws_eks_cluster" "edge" {
  count     = var.create_resources && var.enable_eks ? 1 : 0
  name      = "${local.name_prefix}-eks"
  role_arn  = aws_iam_role.eks_cluster[0].arn
  version   = "1.31"

  vpc_config {
    subnet_ids              = concat(aws_subnet.private[*].id, aws_subnet.public[*].id)
    endpoint_private_access = true
    endpoint_public_access  = true
    security_group_ids      = [aws_security_group.eks_cluster[0].id]
  }

  depends_on = [aws_iam_role_policy_attachment.eks_cluster_policy]
  tags       = { Project = var.project, Region = var.region }
}

resource "aws_eks_node_group" "edge" {
  count           = var.create_resources && var.enable_eks ? 1 : 0
  cluster_name    = aws_eks_cluster.edge[0].name
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
  tags = { Project = var.project, Region = var.region }
}

output "vpc_id" {
  value = var.create_resources ? aws_vpc.edge[0].id : null
}

output "vpc_cidr" {
  value = var.vpc_cidr
}

output "private_route_table_id" {
  value = var.create_resources ? aws_route_table.private[0].id : null
}

output "edge_env" {
  value = {
    region            = var.region
    AT_REGION         = var.region
    REDIS_URL         = local.has_global ? "rediss://${local.replica_host}:6379/0" : "<pending-global-datastore-secondary>"
    REDIS_WRITE_URL   = "rediss://${var.leader_primary_endpoint}:6379/0"
    REDIS_RL_URL      = var.create_resources ? "redis://${local.rl_host}:6379/0" : "<rl-endpoint>"
    AT_RS_REDIS       = local.has_global ? "${local.replica_host}:6379" : "<pending-global-datastore-secondary>"
    AT_RS_REDIS_WRITE = "${var.leader_primary_endpoint}:6379"
    gateway_image     = var.gateway_image
    gateway_rs_image  = var.gateway_rs_image
    consistency_note  = "Async replica lag OK for prompt cache; billing uses leader ledger writes"
    lag_budget_ms     = 1000
    global_datastore  = local.has_global
    eks_cluster_name  = var.create_resources && var.enable_eks ? aws_eks_cluster.edge[0].name : null
    acm_certificate_arn = var.create_resources ? aws_acm_certificate.api[0].arn : null
    acm_validation = var.create_resources ? {
      for dvo in aws_acm_certificate.api[0].domain_validation_options : dvo.domain_name => {
        name  = dvo.resource_record_name
        type  = dvo.resource_record_type
        value = dvo.resource_record_value
      }
    } : null
  }
}

output "cache_secondary_primary_endpoint" {
  value = local.has_global ? aws_elasticache_replication_group.cache_secondary[0].primary_endpoint_address : null
}

output "eks_cluster_name" {
  value = var.create_resources && var.enable_eks ? aws_eks_cluster.edge[0].name : null
}

output "acm_certificate_arn" {
  value = var.create_resources ? aws_acm_certificate.api[0].arn : null
}

output "peering_connection_id" {
  value = var.create_resources ? aws_vpc_peering_connection.to_leader[0].id : null
}

output "eks_update_kubeconfig" {
  value = var.create_resources && var.enable_eks ? "aws eks update-kubeconfig --region ${var.region} --name ${aws_eks_cluster.edge[0].name}" : null
}

# Regional edge — Global Datastore secondary + local RL Redis (Section D).

variable "project" {
  type = string
}

variable "region" {
  type = string
}

variable "leader_primary_endpoint" {
  type = string
}

variable "global_replication_group_id" {
  type        = string
  default     = ""
  description = "ElastiCache Global Datastore id from leader (empty until enable_edges)"
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

provider "aws" {
  region = var.region
}

data "aws_availability_zones" "available" {
  count = var.create_resources ? 1 : 0
  state = "available"
}

locals {
  azs          = var.create_resources ? slice(data.aws_availability_zones.available[0].names, 0, 2) : []
  has_global   = var.create_resources && var.global_replication_group_id != ""
  replica_host = local.has_global ? aws_elasticache_replication_group.cache_secondary[0].primary_endpoint_address : ""
  rl_host      = var.create_resources ? aws_elasticache_cluster.rl[0].cache_nodes[0].address : ""
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

resource "aws_subnet" "private" {
  count             = var.create_resources ? length(local.azs) : 0
  vpc_id            = aws_vpc.edge[0].id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, count.index)
  availability_zone = local.azs[count.index]
  tags              = { Name = "${var.project}-edge-private-${count.index}" }
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

# Local writable Redis for regional token-bucket allotments (not the read replica).
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

# Cross-region read replica via Global Datastore (engine/auth inherit from primary).
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

output "edge_env" {
  value = {
    region              = var.region
    AT_REGION           = var.region
    REDIS_URL           = local.has_global ? "rediss://${local.replica_host}:6379/0" : "<pending-global-datastore-secondary>"
    REDIS_WRITE_URL     = "rediss://${var.leader_primary_endpoint}:6379/0"
    REDIS_RL_URL        = var.create_resources ? "redis://${local.rl_host}:6379/0" : "<rl-endpoint>"
    AT_RS_REDIS         = local.has_global ? "${local.replica_host}:6379" : "<pending-global-datastore-secondary>"
    AT_RS_REDIS_WRITE   = "${var.leader_primary_endpoint}:6379"
    gateway_image       = var.gateway_image
    gateway_rs_image    = var.gateway_rs_image
    consistency_note    = "Async replica lag OK for prompt cache; billing uses leader ledger writes"
    lag_budget_ms       = 1000
    global_datastore    = local.has_global
  }
}

output "edge_notes" {
  value = <<-EOT
    Deploy in ${var.region}:
      1. enable_edges creates Global Datastore secondary + RL cluster when global_replication_group_id is set
      2. Set REDIS_URL=secondary (GET), REDIS_WRITE_URL=leader (SET), REDIS_RL_URL=local RL
      3. Set AT_RS_REDIS=secondary, AT_RS_REDIS_WRITE=leader
      4. Deploy gateway + gateway-rs; NLB in front of Rust :8081
      5. Register NLB with Global Accelerator (Section E)
      6. Run quota-allotment CronJob against REDIS_WRITE_URL / REDIS_RL_URL
  EOT
}

output "cache_secondary_primary_endpoint" {
  value = local.has_global ? aws_elasticache_replication_group.cache_secondary[0].primary_endpoint_address : null
}

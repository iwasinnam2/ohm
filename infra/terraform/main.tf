# Leader region (Section C) — VPC, ElastiCache, Secrets, ECR refs, GA skeleton.
# Apply after creating the S3/DynamoDB state backend (see infra/README.md).

terraform {
  required_version = ">= 1.5.0"

  # Remote state: values come from backend.hcl via terraform init -backend-config=
  backend "s3" {}

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

variable "project" {
  type    = string
  default = "at-utility"
}

variable "leader_region" {
  type    = string
  default = "us-east-1"
}

variable "edge_regions" {
  type    = list(string)
  default = ["us-west-2", "eu-west-2", "ap-northeast-1"]
}

variable "anycast_enabled" {
  type        = bool
  default     = false
  description = "Set true in Section E to provision Global Accelerator"
}

variable "enable_edges" {
  type        = bool
  default     = false
  description = "Section D: provision edge regional VPC + RL Redis (us-west-2, eu-west-2, ap-northeast-1)"
}

variable "redis_node_type" {
  type        = string
  default     = "cache.r6g.large"
  description = "Leader Redis node type; Global Datastore requires large+ (not t-family)"
}

variable "redis_snapshot_retention_days" {
  type        = number
  default     = 7
  description = "Daily Redis snapshot retention — this RG is the only datastore, keep backups on"
}

variable "ga_nlb_endpoint_arns" {
  type        = map(string)
  default     = {}
  description = "Map of AWS region => NLB ARN for GA endpoint groups (one group per region)"
}

variable "domain_name" {
  type        = string
  default     = "api.withohm.dev"
  description = "Public API hostname (TLS via ACM in leader region for NLB/ALB)"
}

variable "vpc_cidr" {
  type    = string
  default = "10.20.0.0/16"
}

variable "image_tag" {
  type        = string
  default     = "0.1.0"
  description = "Immutable image tag (never latest) for rollbacks"
}

variable "openai_api_key" {
  type      = string
  sensitive = true
  default   = ""
}

variable "at_api_keys" {
  type      = string
  sensitive = true
  default   = ""
}

provider "aws" {
  region = var.leader_region
  alias  = "leader"
}

data "aws_availability_zones" "available" {
  provider = aws.leader
  state    = "available"
}

locals {
  azs         = slice(data.aws_availability_zones.available.names, 0, 2)
  name_prefix = var.project
}

# --- Networking ---
resource "aws_vpc" "leader" {
  provider             = aws.leader
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = {
    Name    = "${local.name_prefix}-leader"
    Project = var.project
  }
}

resource "aws_internet_gateway" "leader" {
  provider = aws.leader
  vpc_id   = aws_vpc.leader.id
  tags     = { Name = "${local.name_prefix}-igw" }
}

resource "aws_subnet" "public" {
  provider                = aws.leader
  count                   = length(local.azs)
  vpc_id                  = aws_vpc.leader.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 4, count.index)
  availability_zone       = local.azs[count.index]
  map_public_ip_on_launch = true
  tags = {
    Name = "${local.name_prefix}-public-${local.azs[count.index]}"
    Tier = "public"
  }
}

resource "aws_subnet" "private" {
  provider          = aws.leader
  count             = length(local.azs)
  vpc_id            = aws_vpc.leader.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, count.index + 8)
  availability_zone = local.azs[count.index]
  tags = {
    Name = "${local.name_prefix}-private-${local.azs[count.index]}"
    Tier = "private"
  }
}

resource "aws_eip" "nat" {
  provider = aws.leader
  domain   = "vpc"
  tags     = { Name = "${local.name_prefix}-nat-eip" }
}

resource "aws_nat_gateway" "leader" {
  provider      = aws.leader
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public[0].id
  tags          = { Name = "${local.name_prefix}-nat" }
  depends_on    = [aws_internet_gateway.leader]
}

resource "aws_route_table" "public" {
  provider = aws.leader
  vpc_id   = aws_vpc.leader.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.leader.id
  }
  tags = { Name = "${local.name_prefix}-public-rt" }
}

resource "aws_route_table_association" "public" {
  provider       = aws.leader
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table" "private" {
  provider = aws.leader
  vpc_id   = aws_vpc.leader.id
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.leader.id
  }
  tags = { Name = "${local.name_prefix}-private-rt" }
}

resource "aws_route_table_association" "private" {
  provider       = aws.leader
  count          = length(aws_subnet.private)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

# --- Security groups ---
resource "aws_security_group" "redis" {
  provider    = aws.leader
  name        = "${local.name_prefix}-redis"
  description = "ElastiCache Redis"
  vpc_id      = aws_vpc.leader.id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.gateway.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${local.name_prefix}-redis-sg" }
}

resource "aws_security_group" "gateway" {
  provider    = aws.leader
  name        = "${local.name_prefix}-gateway"
  description = "Gateway and Rust edge pods / tasks"
  vpc_id      = aws_vpc.leader.id

  ingress {
    description = "HTTP from NLB / cluster"
    from_port   = 8080
    to_port     = 8081
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "NLB health / TLS target"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${local.name_prefix}-gateway-sg" }
}

# --- ElastiCache subnet group + Redis leader ---
resource "aws_elasticache_subnet_group" "leader" {
  provider   = aws.leader
  name       = "${local.name_prefix}-redis"
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_elasticache_replication_group" "leader" {
  provider                   = aws.leader
  replication_group_id       = "${var.project}-redis-leader"
  description                = "at-utility Redis replication leader (cache writes + quota grants)"
  engine                     = "redis"
  engine_version             = "7.1"
  node_type                  = var.redis_node_type
  num_cache_clusters         = 2
  automatic_failover_enabled = true
  multi_az_enabled           = true
  port                       = 6379
  apply_immediately          = true
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  # Must not overlap the maintenance window (sun:03:00-sun:04:00).
  snapshot_retention_limit   = var.redis_snapshot_retention_days
  snapshot_window            = "05:00-07:00"
  subnet_group_name          = aws_elasticache_subnet_group.leader.name
  security_group_ids         = [aws_security_group.redis.id]
  tags = {
    Project = var.project
    Role    = "redis-leader"
  }
}

# Phase 3 — ElastiCache Global Datastore (secondaries created in edge modules)
resource "aws_elasticache_global_replication_group" "ohm" {
  count                                = var.enable_edges ? 1 : 0
  provider                             = aws.leader
  global_replication_group_id_suffix   = "ohm"
  primary_replication_group_id         = aws_elasticache_replication_group.leader.id
  global_replication_group_description = "${var.project} prompt-cache global datastore"
}

output "redis_global_replication_group_id" {
  value = try(aws_elasticache_global_replication_group.ohm[0].global_replication_group_id, null)
}

# --- Secrets Manager ---
resource "aws_secretsmanager_secret" "runtime" {
  provider = aws.leader
  name     = "${local.name_prefix}/runtime"
  tags     = { Project = var.project }
}

resource "aws_secretsmanager_secret_version" "runtime" {
  provider  = aws.leader
  secret_id = aws_secretsmanager_secret.runtime.id
  secret_string = jsonencode({
    OPENAI_API_KEY     = var.openai_api_key
    AT_API_KEYS        = var.at_api_keys
    # Phase 2: GET on same-region reader; SET/RL/tenants on primary
    REDIS_URL          = "rediss://${aws_elasticache_replication_group.leader.reader_endpoint_address}:6379/0"
    REDIS_WRITE_URL    = "rediss://${aws_elasticache_replication_group.leader.primary_endpoint_address}:6379/0"
    REDIS_RL_URL       = "rediss://${aws_elasticache_replication_group.leader.primary_endpoint_address}:6379/0"
    AT_RS_REDIS        = "${aws_elasticache_replication_group.leader.reader_endpoint_address}:6379"
    AT_RS_REDIS_WRITE  = "${aws_elasticache_replication_group.leader.primary_endpoint_address}:6379"
  })
}

# --- ECR repositories (immutable tags by policy) ---
resource "aws_ecr_repository" "gateway" {
  provider             = aws.leader
  name                 = "${var.project}/gateway"
  image_tag_mutability = "IMMUTABLE"
  image_scanning_configuration { scan_on_push = true }
}

resource "aws_ecr_repository" "gateway_rs" {
  provider             = aws.leader
  name                 = "${var.project}/gateway-rs"
  image_tag_mutability = "IMMUTABLE"
  image_scanning_configuration { scan_on_push = true }
}

resource "aws_ecr_repository" "ingest_worker" {
  provider             = aws.leader
  name                 = "${var.project}/ingest-worker"
  image_tag_mutability = "IMMUTABLE"
  image_scanning_configuration { scan_on_push = true }
}

# --- ACM (DNS validation; attach certificate ARN to NLB listener in k8s/Ingress) ---
resource "aws_acm_certificate" "api" {
  provider          = aws.leader
  domain_name       = var.domain_name
  validation_method = "DNS"
  lifecycle {
    create_before_destroy = true
  }
  tags = { Project = var.project }
}

# --- Optional Global Accelerator (Section E) ---
resource "aws_globalaccelerator_accelerator" "api" {
  count           = var.anycast_enabled ? 1 : 0
  provider        = aws.leader
  name            = "${var.project}-anycast"
  ip_address_type = "IPV4"
  enabled         = true
  attributes {
    flow_logs_enabled = false
  }
}

resource "aws_globalaccelerator_listener" "https" {
  count           = var.anycast_enabled ? 1 : 0
  provider        = aws.leader
  accelerator_arn = aws_globalaccelerator_accelerator.api[0].id
  protocol        = "TCP"
  port_range {
    from_port = 443
    to_port   = 443
  }
}

resource "aws_globalaccelerator_endpoint_group" "https" {
  for_each     = var.anycast_enabled ? var.ga_nlb_endpoint_arns : {}
  provider     = aws.leader
  listener_arn = aws_globalaccelerator_listener.https[0].id

  # Must match the NLB's region
  endpoint_group_region = each.key

  health_check_protocol = "TCP"
  health_check_port     = 443
  threshold_count       = 3

  endpoint_configuration {
    endpoint_id = each.value
    weight      = 128
  }
}

output "redis_leader_primary_endpoint" {
  value = aws_elasticache_replication_group.leader.primary_endpoint_address
}

output "redis_leader_reader_endpoint" {
  value = aws_elasticache_replication_group.leader.reader_endpoint_address
}

# Phase 0–2 single-region wiring helper (before Global Datastore edges)
output "leader_redis_env" {
  value = {
    REDIS_URL         = "rediss://${aws_elasticache_replication_group.leader.reader_endpoint_address}:6379/0"
    REDIS_WRITE_URL   = "rediss://${aws_elasticache_replication_group.leader.primary_endpoint_address}:6379/0"
    REDIS_RL_URL      = "rediss://${aws_elasticache_replication_group.leader.primary_endpoint_address}:6379/0"
    AT_RS_REDIS       = "${aws_elasticache_replication_group.leader.reader_endpoint_address}:6379"
    AT_RS_REDIS_WRITE = "${aws_elasticache_replication_group.leader.primary_endpoint_address}:6379"
    note              = "Phase 2 same-region reader; Phase 0 may point all three at primary if reader lag is a concern during cutover"
  }
}

output "vpc_id" {
  value = aws_vpc.leader.id
}

output "private_subnet_ids" {
  value = aws_subnet.private[*].id
}

output "public_subnet_ids" {
  value = aws_subnet.public[*].id
}

output "gateway_security_group_id" {
  value = aws_security_group.gateway.id
}

output "ecr_repositories" {
  value = {
    gateway       = aws_ecr_repository.gateway.repository_url
    gateway_rs    = aws_ecr_repository.gateway_rs.repository_url
    ingest_worker = aws_ecr_repository.ingest_worker.repository_url
  }
}

output "secrets_arn" {
  value = aws_secretsmanager_secret.runtime.arn
}

output "acm_certificate_arn" {
  value = aws_acm_certificate.api.arn
}

output "acm_validation_records" {
  value = {
    for dvo in aws_acm_certificate.api.domain_validation_options : dvo.domain_name => {
      name  = dvo.resource_record_name
      type  = dvo.resource_record_type
      value = dvo.resource_record_value
    }
  }
}

output "global_accelerator" {
  value = var.anycast_enabled ? {
    arn             = aws_globalaccelerator_accelerator.api[0].id
    dns             = aws_globalaccelerator_accelerator.api[0].dns_name
    ips             = aws_globalaccelerator_accelerator.api[0].ip_sets
    listen          = aws_globalaccelerator_listener.https[0].id
    endpoint_groups = { for k, g in aws_globalaccelerator_endpoint_group.https : k => g.id }
  } : null
}

output "topology" {
  value = {
    leader_region = var.leader_region
    edge_regions  = var.edge_regions
    edges_enabled = var.enable_edges
    pattern       = "single-leader multi-replica active-passive"
    rate_limits   = "regional token-bucket allotments refreshed from leader"
    anycast       = var.anycast_enabled ? "aws-global-accelerator" : "disabled-until-section-e"
    domain        = var.domain_name
    image_tag     = var.image_tag
  }
}

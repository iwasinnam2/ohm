# Section D — edge regions (Global Datastore secondaries + EKS).
# us-west-2 + eu-west-2 (≥2 for Anycast). Add ap-northeast-1 later if needed.

provider "aws" {
  alias  = "us_west_2"
  region = "us-west-2"
}

provider "aws" {
  alias  = "eu_west_2"
  region = "eu-west-2"
}

module "edge_us_west_2" {
  source = "./modules/edge"
  count  = var.enable_edges ? 1 : 0
  providers = {
    aws = aws.us_west_2
  }

  project                     = var.project
  region                      = "us-west-2"
  vpc_cidr                    = "10.31.0.0/16"
  leader_primary_endpoint     = aws_elasticache_replication_group.leader.primary_endpoint_address
  leader_vpc_id               = aws_vpc.leader.id
  leader_vpc_cidr             = aws_vpc.leader.cidr_block
  leader_region               = var.leader_region
  global_replication_group_id = try(aws_elasticache_global_replication_group.ohm[0].global_replication_group_id, "")
  attach_global_datastore     = true
  gateway_image               = "${aws_ecr_repository.gateway.repository_url}:${var.image_tag}"
  gateway_rs_image            = "${aws_ecr_repository.gateway_rs.repository_url}:${var.image_tag}"
  create_resources            = true
  enable_eks                  = true
  domain_name                 = var.domain_name
}

module "edge_eu_west_2" {
  source = "./modules/edge"
  count  = var.enable_edges ? 1 : 0
  providers = {
    aws = aws.eu_west_2
  }

  project                     = var.project
  region                      = "eu-west-2"
  vpc_cidr                    = "10.32.0.0/16"
  leader_primary_endpoint     = aws_elasticache_replication_group.leader.primary_endpoint_address
  leader_vpc_id               = aws_vpc.leader.id
  leader_vpc_cidr             = aws_vpc.leader.cidr_block
  leader_region               = var.leader_region
  global_replication_group_id = try(aws_elasticache_global_replication_group.ohm[0].global_replication_group_id, "")
  attach_global_datastore     = true
  gateway_image               = "${aws_ecr_repository.gateway.repository_url}:${var.image_tag}"
  gateway_rs_image            = "${aws_ecr_repository.gateway_rs.repository_url}:${var.image_tag}"
  create_resources            = true
  enable_eks                  = true
  domain_name                 = var.domain_name
}

locals {
  edge_modules = var.enable_edges ? {
    "us-west-2" = module.edge_us_west_2[0]
    "eu-west-2" = module.edge_eu_west_2[0]
  } : {}
  edge_cidrs = {
    "us-west-2" = "10.31.0.0/16"
    "eu-west-2" = "10.32.0.0/16"
  }
}

resource "aws_vpc_peering_connection_accepter" "edge" {
  for_each                  = local.edge_modules
  provider                  = aws.leader
  vpc_peering_connection_id = each.value.peering_connection_id
  auto_accept               = true
  tags = {
    Name    = "${var.project}-peer-accept-${each.key}"
    Project = var.project
  }
}

resource "aws_route" "leader_to_edge_private" {
  for_each                  = local.edge_modules
  provider                  = aws.leader
  route_table_id            = aws_route_table.private.id
  destination_cidr_block    = local.edge_cidrs[each.key]
  vpc_peering_connection_id = each.value.peering_connection_id
  depends_on                = [aws_vpc_peering_connection_accepter.edge]
}

resource "aws_route" "leader_to_edge_public" {
  for_each                  = local.edge_modules
  provider                  = aws.leader
  route_table_id            = aws_route_table.public.id
  destination_cidr_block    = local.edge_cidrs[each.key]
  vpc_peering_connection_id = each.value.peering_connection_id
  depends_on                = [aws_vpc_peering_connection_accepter.edge]
}

resource "aws_security_group_rule" "redis_from_edge" {
  for_each          = local.edge_modules
  provider          = aws.leader
  type              = "ingress"
  from_port         = 6379
  to_port           = 6379
  protocol          = "tcp"
  security_group_id = aws_security_group.redis.id
  cidr_blocks       = [local.edge_cidrs[each.key]]
  description       = "Redis from edge ${each.key}"
}

output "edge_wiring" {
  value = {
    for k, m in local.edge_modules : k => m.edge_env
  }
}

output "edge_eks_kubeconfig" {
  value = {
    for k, m in local.edge_modules : k => m.eks_update_kubeconfig
  }
}

output "edge_acm_validation" {
  value = {
    for k, m in local.edge_modules : k => try(m.edge_env.acm_validation, null)
  }
}

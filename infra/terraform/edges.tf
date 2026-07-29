# Instantiate edge region modules (Section D). Flip enable_edges=true in tfvars when ready.

module "edge_us_west_2" {
  source                      = "./modules/edge"
  project                     = var.project
  region                      = "us-west-2"
  leader_primary_endpoint     = aws_elasticache_replication_group.leader.primary_endpoint_address
  global_replication_group_id = try(aws_elasticache_global_replication_group.ohm[0].global_replication_group_id, "")
  vpc_cidr                    = "10.31.0.0/16"
  gateway_image               = "${aws_ecr_repository.gateway.repository_url}:${var.image_tag}"
  gateway_rs_image            = "${aws_ecr_repository.gateway_rs.repository_url}:${var.image_tag}"
  create_resources            = var.enable_edges
}

module "edge_eu_west_2" {
  source                      = "./modules/edge"
  project                     = var.project
  region                      = "eu-west-2"
  leader_primary_endpoint     = aws_elasticache_replication_group.leader.primary_endpoint_address
  global_replication_group_id = try(aws_elasticache_global_replication_group.ohm[0].global_replication_group_id, "")
  vpc_cidr                    = "10.32.0.0/16"
  gateway_image               = "${aws_ecr_repository.gateway.repository_url}:${var.image_tag}"
  gateway_rs_image            = "${aws_ecr_repository.gateway_rs.repository_url}:${var.image_tag}"
  create_resources            = var.enable_edges
}

module "edge_ap_northeast_1" {
  source                      = "./modules/edge"
  project                     = var.project
  region                      = "ap-northeast-1"
  leader_primary_endpoint     = aws_elasticache_replication_group.leader.primary_endpoint_address
  global_replication_group_id = try(aws_elasticache_global_replication_group.ohm[0].global_replication_group_id, "")
  vpc_cidr                    = "10.33.0.0/16"
  gateway_image               = "${aws_ecr_repository.gateway.repository_url}:${var.image_tag}"
  gateway_rs_image            = "${aws_ecr_repository.gateway_rs.repository_url}:${var.image_tag}"
  create_resources            = var.enable_edges
}

output "edge_wiring" {
  value = {
    us-west-2      = module.edge_us_west_2.edge_env
    eu-west-2      = module.edge_eu_west_2.edge_env
    ap-northeast-1 = module.edge_ap_northeast_1.edge_env
  }
}

# Always-on uptime alerting — runs entirely in AWS, no local machine involved.
# Route53 health checks probe the public endpoints from AWS's checker fleet;
# CloudWatch alarms (Route53 metrics live in us-east-1) email the SNS topic.
# NOTE: the email subscription must be confirmed once from the admin mailbox.

variable "alert_email" {
  type        = string
  default     = "admin@withohm.dev"
  description = "Email address that receives uptime alerts"
}

resource "aws_sns_topic" "ohm_alerts" {
  provider = aws.leader
  name     = "ohm-alerts"
  tags     = { Project = var.project }
}

resource "aws_sns_topic_subscription" "ohm_alerts_email" {
  provider  = aws.leader
  topic_arn = aws_sns_topic.ohm_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# var.domain_name is already the API host (api.withohm.dev).
locals {
  api_fqdn = var.domain_name
  www_fqdn = replace(var.domain_name, "api.", "www.")
}

resource "aws_route53_health_check" "api" {
  provider          = aws.leader
  type              = "HTTPS"
  fqdn              = local.api_fqdn
  port              = 443
  resource_path     = "/health"
  request_interval  = 30
  failure_threshold = 3
  measure_latency   = true
  tags              = { Name = "ohm-api-health", Project = var.project }
}

resource "aws_route53_health_check" "www" {
  provider          = aws.leader
  type              = "HTTPS"
  fqdn              = local.www_fqdn
  port              = 443
  resource_path     = "/"
  request_interval  = 30
  failure_threshold = 3
  measure_latency   = true
  tags              = { Name = "ohm-www-health", Project = var.project }
}

resource "aws_cloudwatch_metric_alarm" "api_down" {
  provider            = aws.leader
  alarm_name          = "ohm-api-down"
  alarm_description   = "${local.api_fqdn}/health failing from Route53 checkers"
  namespace           = "AWS/Route53"
  metric_name         = "HealthCheckStatus"
  dimensions          = { HealthCheckId = aws_route53_health_check.api.id }
  statistic           = "Minimum"
  period              = 60
  evaluation_periods  = 3
  threshold           = 1
  comparison_operator = "LessThanThreshold"
  treat_missing_data  = "breaching"
  alarm_actions       = [aws_sns_topic.ohm_alerts.arn]
  ok_actions          = [aws_sns_topic.ohm_alerts.arn]
  tags                = { Project = var.project }
}

resource "aws_cloudwatch_metric_alarm" "www_down" {
  provider            = aws.leader
  alarm_name          = "ohm-www-down"
  alarm_description   = "${local.www_fqdn} homepage failing from Route53 checkers"
  namespace           = "AWS/Route53"
  metric_name         = "HealthCheckStatus"
  dimensions          = { HealthCheckId = aws_route53_health_check.www.id }
  statistic           = "Minimum"
  period              = 60
  evaluation_periods  = 3
  threshold           = 1
  comparison_operator = "LessThanThreshold"
  treat_missing_data  = "breaching"
  alarm_actions       = [aws_sns_topic.ohm_alerts.arn]
  ok_actions          = [aws_sns_topic.ohm_alerts.arn]
  tags                = { Project = var.project }
}

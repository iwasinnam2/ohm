# Observer watchdog sink: SNS -> Slack via AWS Chatbot.
#
# One-time manual prerequisite (cannot be terraformed): authorize the Slack
# workspace in the AWS console — Chatbot (Amazon Q Developer in chat apps)
# -> Configure new client -> Slack -> allow. Then copy the workspace ID and
# the target channel ID into terraform.tfvars and set
# enable_slack_alerts = true.
#
# Routes both the uptime topic (ohm-alerts, alerts.tf) and the budget topic
# (created manually per infra/runbooks/BUDGETS.md) into the channel, so
# api/www-down alarms and spend alerts land where you actually look.

variable "enable_slack_alerts" {
  type        = bool
  default     = false
  description = "Route SNS alert topics into Slack via AWS Chatbot"
}

variable "slack_workspace_id" {
  type        = string
  default     = ""
  description = "Slack workspace ID from the Chatbot console authorization (T...)"
}

variable "slack_channel_id" {
  type        = string
  default     = ""
  description = "Slack channel ID to receive alerts (C...)"
}

variable "budget_alerts_topic_arn" {
  type        = string
  default     = "arn:aws:sns:us-east-1:594161136574:withohm-budget-alerts"
  description = "Existing budget alert topic (infra/runbooks/BUDGETS.md)"
}

resource "aws_iam_role" "chatbot" {
  count    = var.enable_slack_alerts ? 1 : 0
  provider = aws.leader
  name     = "${local.name_prefix}-chatbot"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "chatbot.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = { Project = var.project }
}

# Read-only: Chatbot only needs to render alarm context in the channel.
resource "aws_iam_role_policy" "chatbot_readonly" {
  count    = var.enable_slack_alerts ? 1 : 0
  provider = aws.leader
  name     = "chatbot-notifications"
  role     = aws_iam_role.chatbot[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "cloudwatch:Describe*",
        "cloudwatch:Get*",
        "cloudwatch:List*",
      ]
      Resource = "*"
    }]
  })
}

resource "aws_chatbot_slack_channel_configuration" "ohm_alerts" {
  count              = var.enable_slack_alerts ? 1 : 0
  provider           = aws.leader
  configuration_name = "${local.name_prefix}-alerts"
  iam_role_arn       = aws_iam_role.chatbot[0].arn
  slack_team_id      = var.slack_workspace_id
  slack_channel_id   = var.slack_channel_id
  sns_topic_arns = [
    aws_sns_topic.ohm_alerts.arn,
    var.budget_alerts_topic_arn,
  ]
  logging_level = "ERROR"

  tags = { Project = var.project }
}

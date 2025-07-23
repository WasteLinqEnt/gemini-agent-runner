output "ecr_repository_url" {
  description = "The URL of the ECR repository."
  value       = aws_ecr_repository.app.repository_url
}

output "api_gateway_endpoint" {
  description = "The endpoint URL for the API Gateway."
  value       = aws_apigatewayv2_api.http_api.api_endpoint
}

output "github_actions_role_arn" {
  description = "The ARN of the IAM role for GitHub Actions."
  value       = aws_iam_role.github_actions.arn
}

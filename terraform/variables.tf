variable "aws_region" {
  description = "The AWS region to deploy resources in."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "The name of the project, used for naming resources."
  type        = string
  default     = "gemini-agent-runner"
}

variable "ecr_image_uri" {
  description = "The URI of the Docker image in ECR."
  type        = string
}

variable "github_repo" {
  description = "The GitHub repository (e.g., 'my-org/my-repo') for OIDC integration."
  type        = string
}

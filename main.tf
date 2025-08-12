terraform {
  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
  }
}

provider "github" {
  token = var.github_token
  owner = "calebndavidson-del"
}

resource "aws_s3_bucket" "lambda_deployment" {
  bucket = "cloud-trading-bot-lambda-deployment-m6x4p8e"
  # Do NOT set force_destroy or try to set settings that would change the existing bucket unless you intend to
  # Only specify arguments that match how the bucket is already configured, or leave blank/minimal
}
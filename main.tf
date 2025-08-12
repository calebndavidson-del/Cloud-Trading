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

resource "github_repository" "example" {
  name        = "tf-example-repo"
  description = "Created by Terraform!"
  visibility  = "private"
}
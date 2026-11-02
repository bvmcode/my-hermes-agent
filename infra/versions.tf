terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.0"
    }
  }

  # bucket, key, and region come from backend.hcl. Backend blocks cannot
  # reference variables. region there is the bucket's region.
  backend "s3" {
    encrypt = true
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project   = "hermes-agent"
      ManagedBy = "terraform"
    }
  }
}

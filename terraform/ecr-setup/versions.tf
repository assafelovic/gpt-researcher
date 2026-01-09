terraform {
  required_version = ">= 1.0.0"
  backend "s3" {
    bucket         = "gg-ai-terraform-states"
    key            = "production/gpt-researcher/ecr.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-state-locks"
    encrypt        = true
  }
}

provider "aws" {
  region  = "us-east-1"
  profile = "908027381725_AdministratorAccess"
}

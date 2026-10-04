terraform {
  backend "s3" {
    bucket       = "tfstate-selfheal-14724"
    key          = "aws-vpc-selfheal/terraform.tfstate"
    region       = "us-east-1"
    use_lockfile = true
    encrypt      = true
  }
}
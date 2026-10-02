variable "aws_region" {
  description = "AWS region to build in"
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "CIDR range for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR range for the public subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "private_subnet_cidr" {
  description = "CIDR range for the private subnet"
  type        = string
  default     = "10.0.2.0/24"
}

variable "my_ip" {
  description = "My public IP in CIDR form, for SSH and HTTP access"
  type        = string

  validation {
    condition     = var.my_ip != "0.0.0.0/0"
    error_message = "Do not open SSH to the whole internet. Use your own IP with /32."
  }
}

variable "public_key_path" {
  description = "Path to the public SSH key to upload"
  type        = string
  default     = "~/.ssh/tf-key.pub"
}

variable "instance_type" {
  description = "EC2 instance size"
  type        = string
  default     = "t3.micro"
}
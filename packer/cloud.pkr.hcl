packer {
  required_plugins {
    amazon = {
      version = ">= 1.2.0"
      source  = "github.com/hashicorp/amazon"
    }
  }
}

// Common variables
variable "postgres_password" {
  type    = string
  default = "your_password_here"
}

// AWS-specific variables
variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "aws_source_ami" {
  type    = string
  default = "ami-0c7217cdde317cfec" // Ubuntu 24.04 LTS
}

variable "aws_instance_type" {
  type    = string
  default = "t2.micro"
}

variable "aws_ami_users" {
  type        = list(string)
  description = "List of AWS account IDs that can access the AMI"
  default     = []
}


// AWS source definition
source "amazon-ebs" "ubuntu" {
  region          = var.aws_region
  ami_name        = "csye6225-${formatdate("YYYY-MM-DD-hh-mm-ss", timestamp())}"
  instance_type   = var.aws_instance_type
  source_ami      = var.aws_source_ami
  ssh_username    = "ubuntu"
  ami_users       = var.aws_ami_users
  ami_description = "Ubuntu AMI for CSYE 6225"

  tags = {
    Name = "csye6225-ami"
  }
}


// Common build configuration
build {
  name = "build-csye6225-image"

  sources = [
    "source.amazon-ebs.ubuntu"
  ]

  provisioner "file" {
    source      = "${path.root}/../webapp.zip"
    destination = "/tmp/webapp.zip"
    timeout     = "5m"
  }

  provisioner "file" {
    source      = "${path.root}/../systemd/webapp.service"
    destination = "/tmp/webapp.service"
    timeout     = "5m"
  }

  provisioner "shell" {
    script  = "setup.sh"
    timeout = "10m"
    environment_vars = [
      "POSTGRES_PASSWORD=${var.postgres_password}",
      "DATABASE_URL=postgresql+psycopg2://postgres:${var.postgres_password}@localhost:5432/healthcheck_db",
      "TEST_DATABASE_URL=postgresql+psycopg2://postgres:${var.postgres_password}@localhost:5432/test_healthcheck_db"
    ]
  }

  error-cleanup-provisioner "shell" {
    inline = ["echo 'Cleaning up after error'"]
  }
}

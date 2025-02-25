packer {
  required_plugins {
    amazon = {
      version = ">= 1.2.0"
      source  = "github.com/hashicorp/amazon"
    }
  }
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "source_ami" {
  type    = string
  default = "ami-0c7217cdde317cfec" # Ubuntu 24.04 LTS
}

variable "instance_type" {
  type    = string
  default = "t2.micro"
}

variable "postgres_password" {
  type    = string
  default = "your_password_here"
}

source "amazon-ebs" "ubuntu" {
  region          = var.aws_region
  ami_name        = "csye6225-${formatdate("YYYY-MM-DD-hh-mm-ss", timestamp())}"
  instance_type   = var.instance_type
  source_ami      = var.source_ami
  ssh_username    = "ubuntu"
  ami_description = "Ubuntu AMI for CSYE 6225"

  tags = {
    Name = "csye6225-ami"
  }
}

build {
  sources = ["source.amazon-ebs.ubuntu"]

  provisioner "file" {
    source      = "${path.root}/../webapp.zip"
    destination = "/tmp/webapp.zip"
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

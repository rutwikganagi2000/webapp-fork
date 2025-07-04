#!/bin/bash
set -e

# Create .env file
echo "Creating .env file..."
cat > /tmp/.env << EOF
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
DATABASE_URL=${DATABASE_URL}
TEST_DATABASE_URL=${TEST_DATABASE_URL}
EOF

# Update system packages
echo "Updating package lists and upgrading packages..."
sudo add-apt-repository universe  # Enable universe repository
sudo apt update
sudo apt upgrade -y

# Install dependencies
echo "Installing dependencies..."
sudo apt install -y curl ca-certificates python3 python3-pip python3-venv unzip jq

# Install AWS CLI
echo "Installing AWS CLI..."
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip"
unzip /tmp/awscliv2.zip -d /tmp
sudo /tmp/aws/install
rm -rf /tmp/awscliv2.zip /tmp/aws

# Verify AWS CLI installation
aws --version

# Install amazon-cloudwatch-agent
echo "Installing amazon-cloudwatch-agent..."
sudo curl -s https://s3.amazonaws.com/amazoncloudwatch-agent/debian/amd64/latest/amazon-cloudwatch-agent.deb -o /tmp/amazon-cloudwatch-agent.deb
sudo dpkg -i -E /tmp/amazon-cloudwatch-agent.deb
sudo rm /tmp/amazon-cloudwatch-agent.deb

# Configure CloudWatch Agent
echo "Configuring CloudWatch Agent..."
sudo mkdir -p /opt/aws/amazon-cloudwatch-agent/etc
sudo chown ubuntu:ubuntu /opt/aws/amazon-cloudwatch-agent/etc
cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << EOF
{
  "agent": {
    "metrics_collection_interval": 10,
    "logfile": "/var/log/amazon-cloudwatch-agent.log"
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/webapp/webapp.log",
            "log_group_name": "csye6225-webapp-logs",
            "log_stream_name": "webapp-log-stream"
          }
        ]
      }
    }
  },
  "metrics": {
    "metrics_collected": {
      "statsd": {
        "service_address": ":8125",
        "metrics_collection_interval": 15,
        "metrics_aggregation_interval": 300
      }
    }
  }
}
EOF

# Start CloudWatch Agent
echo "Starting CloudWatch Agent..."
sudo systemctl start amazon-cloudwatch-agent
sudo systemctl enable amazon-cloudwatch-agent

# Create application group
echo "Creating application group..."
sudo groupadd --system csye6225 || true

# Create application user with nologin shell
echo "Creating application user..."
sudo useradd --system --gid csye6225 --shell /usr/sbin/nologin csye6225 || true

# Create log directory for application
echo "Creating log directory for application..."
sudo mkdir -p /var/log/webapp
sudo chown csye6225:csye6225 /var/log/webapp
sudo chmod -R 755 /var/log/webapp

# Create application directory
echo "Creating application directory..."
sudo mkdir -p /opt/csye6225/webapp
sudo chown csye6225:csye6225 /opt/csye6225

# Unzip application files directly to the target directory
echo "Unzipping application..."
cd /tmp
sudo unzip -o webapp.zip -d /opt/csye6225/webapp

# Copy .env file
echo "Copying .env file..."
sudo cp /tmp/.env /opt/csye6225/webapp/.env

# Set correct permissions
echo "Setting permissions..."
sudo chown -R csye6225:csye6225 /opt/csye6225
sudo chmod -R 755 /opt/csye6225

# Setup Python environment
echo "Setting up Python environment..."
cd /opt/csye6225/webapp
sudo -u csye6225 python3 -m venv venv
sudo -u csye6225 /opt/csye6225/webapp/venv/bin/pip3 install -r /opt/csye6225/webapp/requirements.txt

# Copy systemd service file
echo "Copying systemd service file..."
sudo cp /tmp/webapp.service /etc/systemd/system/webapp.service

# Reload systemd and enable services
echo "Enabling services..."
sudo systemctl daemon-reload
sudo systemctl enable webapp

echo "Setup completed successfully!"

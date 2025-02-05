#!/bin/bash

# Exit on any error
set -e

# Load environment variables
source /tmp/.env

# Update package lists and upgrade packages
echo "Updating package lists and upgrading packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install required packages
echo "Installing required packages..."
sudo apt-get install postgresql postgresql-contrib python3 python3-pip python3-venv unzip -y

# Start PostgreSQL service
echo "Starting PostgreSQL service..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Configure PostgreSQL authentication
echo "Configuring PostgreSQL..."
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD '${POSTGRES_PASSWORD}';"

# Create database and user
echo "Creating database and user..."
sudo -u postgres psql <<EOF
CREATE DATABASE healthcheck_db;
GRANT ALL PRIVILEGES ON DATABASE healthcheck_db TO postgres;
CREATE DATABASE test_healthcheck_db;
GRANT ALL PRIVILEGES ON DATABASE test_healthcheck_db TO postgres;
EOF

# Create application group
echo "Creating application group..."
sudo groupadd --system webapp || true

# Create application user
echo "Creating application user..."
sudo useradd --system --gid webapp --shell /bin/bash webapp || true

# Create application directory
echo "Creating application directory..."
sudo mkdir -p /opt/csye6225
sudo chown webapp:webapp /opt/csye6225

# Deploy application from tmp folder
echo "Deploying application..."
sudo unzip /tmp/Rutwik_Ganagi_002305290_02.zip -d /opt/csye6225/

# Copy .env file from /tmp to application directory
echo "Copying environment file..."
cp /tmp/.env /opt/csye6225/Rutwik_Ganagi_002305290_02/webapp/.env

# Set correct permissions
echo "Setting permissions..."
sudo chown -R webapp:webapp /opt/csye6225
sudo chmod -R 755 /opt/csye6225

# Setup Python virtual environment and install dependencies
echo "Setting up Python environment..."
cd /opt/csye6225/Rutwik_Ganagi_002305290_02/webapp
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt

# Verify PostgreSQL is running and accepting connections
echo "Verifying PostgreSQL connection..."
pg_isready -h localhost -p 5432

echo "Setup completed successfully!"
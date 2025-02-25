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
sudo apt update
sudo apt upgrade -y

# Install dependencies
echo "Installing dependencies..."
sudo apt install -y curl ca-certificates python3 python3-pip python3-venv unzip

# Add PostgreSQL repository and key
echo "Adding PostgreSQL repository..."
sudo install -d /usr/share/postgresql-common/pgdg
sudo curl -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc --fail https://www.postgresql.org/media/keys/ACCC4CF8.asc
sudo sh -c 'echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'

# Update and install PostgreSQL
echo "Installing PostgreSQL..."
sudo apt update
sudo apt install -y postgresql postgresql-contrib

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

# Unzip application files
echo "Unzipping application..."
cd /tmp
unzip webapp.zip

# Deploy application from tmp folder
echo "Deploying application..."
sudo mv /tmp/webapp /opt/csye6225/webapp

# Copy .env file
echo "Copying .env file..."
sudo cp /tmp/.env /opt/csye6225/webapp/.env

# Set correct permissions
echo "Setting permissions..."
sudo chown -R webapp:webapp /opt/csye6225
sudo chmod -R 755 /opt/csye6225

# Setup Python environment
echo "Setting up Python environment..."
cd /opt/csye6225/webapp
sudo -u webapp python3 -m venv venv
sudo -u webapp /opt/csye6225/webapp/venv/bin/pip3 install -r requirements.txt

# Create systemd service
echo "Creating systemd service..."
sudo tee /etc/systemd/system/webapp.service << EOF
[Unit]
Description=CSYE 6225 Web Application
After=network.target postgresql.service

[Service]
User=webapp
WorkingDirectory=/opt/csye6225/webapp
Environment="PATH=/opt/csye6225/webapp/venv/bin"
ExecStart=/opt/csye6225/webapp/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8080

[Install]
WantedBy=multi-user.target
EOF

# Enable services
echo "Enabling services..."
sudo systemctl enable postgresql
sudo systemctl enable webapp

# Verify PostgreSQL connection
echo "Verifying PostgreSQL connection..."
pg_isready -h localhost -p 5432

echo "Setup completed successfully!"

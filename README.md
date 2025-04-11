# Health Check API Application

## Prerequisites

### System Requirements
- Python 3.8 or higher
- PostgreSQL 14.0 or higher

### Python Dependencies
- fastapi
- sqlalchemy
- uvicorn
- psycopg2-binary
- python-dotenv


### Database Setup
- PostgreSQL server installed and running
- Database user with permissions to create databases and tables
- Environment variables configured


## Installation Steps

1. Install Python dependencies:
pip3 install -r requirements.txt

2. Configure PostgreSQL:
   - Create a new database
   - Set up database credentials
   - Update .env file with database connection details

3. Run the application:
uvicorn app.main:app --host 0.0.0.0 --port 8080


## Notes
- The application will automatically create required database tables on startup through SQLAlchemy ORM
- No manual database schema setup is required
- The health check endpoint is available at `/healthz`

## Testing
Run the following command for API testing:
pytest tests/ -v

## Deployment
For deploying the application on Ubuntu server, follow the below steps:
1) Transfer the files to the server(Replace the ipv4):
   scp -i ~/.ssh/do Rutwik_Ganagi_002305290_02.zip .env setup.sh root@206.81.5.175:/tmp
2) Make the script executable:
   chmod +x /tmp/setup.sh   
3) Run the script:
   sudo /tmp/setup.sh

## Running the application on Ubuntu Server
Follow the below commands:
1) cd /opt/csye6225/Rutwik_Ganagi_002305290_02/webapp
2) source venv/bin/activate
3) uvicorn app.main:app --host 0.0.0.0 --port 8080

## Continuous Integration (CI)
The project uses GitHub Actions for CI/CD pipeline:

### CI Workflow
- Automatically runs on pull requests to main branch
- Executes test suite against PostgreSQL database

### Branch Protection
- Enabled on main branch
- Requires CI checks to pass before merging
- Prevents direct pushes to main

## GitHub Actions Workflows

### Packer Validation Workflow
- Runs on pull requests to the `main` branch.
- Validates Packer template formatting and configuration.
- Prevents merging if validation fails.

### Packer Build Workflow
- Triggered when pull requests are merged to `main`.
- Runs integration tests with PostgreSQL.
- Builds application artifact on the GitHub Actions runner.
- Creates custom machine images for AWS.
- Configures the application with a non-login user (`csye6225`).
- Sets up `systemd` service for automatic application startup.

### Custom Image Features
- Pre-installed application dependencies.
- `systemd` service for automatic startup.
- PostgreSQL database running locally.
- Non-login user for security.

## File Upload API (`file.py`)

## Overview

The `file.py` module provides endpoints for uploading, getting and deleting files in an S3 bucket. It leverages FastAPI for API handling, the AWS SDK (Boto3) for S3 interactions, and SQLAlchemy for managing metadata storage in a PostgreSQL database.

## Functionality

- **File Upload:** Uploads files to an S3 bucket and stores metadata (filename, URL, upload timestamp) in the database.
- **File Get:** Returns the path to the file in the S3 bucket. 
- **File Deletion:** Deletes files from S3 and removes the corresponding metadata from the database.

## CloudWatch Integration

### Overview
The application integrates with AWS CloudWatch for logging and metrics collection.

### Logging
- Application logs are sent to CloudWatch using the **CloudWatch Agent**.
- Logs are stored in a log group named **csye6225-webapp-logs**.

### Metrics
- Custom metrics are collected using **StatsD** and sent to CloudWatch.
- Metrics include:
  - **API call counts**
  - **API call processing times**
  - **Database query times**
  - **S3 operation times**

## **Continuous Deployment (CD)**

The Continuous Deployment (CD) pipeline ensures that any code merged into the `main` branch is automatically deployed to AWS infrastructure. 

### Key Steps:
- **Build Custom AMI**:  
  Application code and dependencies are bundled into a custom AMI using **Packer**, with pre-installed dependencies and system services for easy deployment.

- **Update Launch Template**:  
  The new AMI ID is added to the latest version of the EC2 launch template, ensuring that new instances in the ASG use the updated AMI.

- **Instance Refresh**:  
  The ASG triggers an **instance refresh**, replacing old instances with new ones using the updated launch template. The refresh ensures zero-downtime.

- **Monitor Deployment**:  
  The workflow monitors the instance refresh process, logging any failures and ensuring a successful deployment.
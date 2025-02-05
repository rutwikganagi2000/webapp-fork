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


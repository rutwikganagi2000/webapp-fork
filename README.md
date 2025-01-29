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


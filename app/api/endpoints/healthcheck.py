from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from fastapi import Depends
from app.database import get_db
from app.models import HealthCheck
import logging
import time
from statsd import StatsClient
import os
import traceback

# Initialize StatsD client
statsd_client = StatsClient(host='localhost', port=8125)

router = APIRouter()

# Determine log file path based on environment
hostname = os.uname().nodename
if os.getenv('GITHUB_ACTIONS') == 'true' or hostname.endswith('.local'):
    log_file_path = 'webapp_local.log'
else:
    log_file_path = '/var/log/webapp/webapp.log'

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    filename=log_file_path, level=logging.INFO
)

@router.get("/healthz")
async def health_checks(request: Request, db: Session = Depends(get_db)):
    """
    Health Check Endpoint
    """
    try:
        start_time = time.time()
        
        # Check for payload in request body or query parameters
        if await request.body() or request.query_params:
            logging.error(f"Invalid request to health check endpoint. Request ID: {request.client.host}")
            return Response(
                status_code=status.HTTP_400_BAD_REQUEST,
                headers={"Cache-Control": "no-cache, no-store, must-revalidate", 
                        "Pragma": "no-cache",
                        "X-Content-Type-Options": "nosniff"}
            )

        # Measure database query time
        db_start_time = time.time()
        new_check = HealthCheck()
        db.add(new_check)
        db.commit()
        db_end_time = time.time()
        db_healthcheck_time = (db_end_time - db_start_time) * 1000  # Convert to milliseconds
        statsd_client.timing('db.healthcheck.time', db_healthcheck_time)

        end_time = time.time()
        processing_time = (end_time - start_time) * 1000  # Convert to milliseconds

        # Log the request
        logging.info(f"Health check successful. Request ID: {request.client.host}")

        # Send metrics to StatsD
        statsd_client.incr('healthcheck.count')
        statsd_client.timing('healthcheck.time', processing_time)

        return Response(
            status_code=status.HTTP_200_OK,
            headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "X-Content-Type-Options": "nosniff"}
        )
    except Exception as e:
        db.rollback()
        error_message = f"Failed to perform health check. Request ID: {request.client.host}. Error: {e}\n{traceback.format_exc()}"
        logging.error(error_message)
        return Response(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "X-Content-Type-Options": "nosniff"}
        )

@router.api_route("/healthz", methods=["POST", "PUT", "DELETE", "PATCH"])
async def method_not_allowed(request: Request):
    """Handle unsupported HTTP methods"""
    logging.info(f"Unsupported HTTP method attempted for /healthz. Request ID: {request.client.host}")
    return Response(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "X-Content-Type-Options": "nosniff"}
    )

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def catch_all(path: str, request: Request):
    """Handle all undefined routes"""
    logging.info(f"Undefined route accessed: {path}. Request ID: {request.client.host}")
    return Response(
        status_code=status.HTTP_404_NOT_FOUND,
        headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "X-Content-Type-Options": "nosniff"}
    )
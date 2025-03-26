from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session
from fastapi import Depends
from app.database import get_db
from app.models import FileMetadata
from botocore.exceptions import ClientError
import boto3
import uuid
from datetime import datetime
import os
import logging
import time
from statsd import StatsClient
import traceback

# Load bucket name from environment variables
bucket_name = os.getenv("S3_BUCKET_NAME", "my-default-bucket")

# Initialize S3 client using IAM role
s3 = boto3.client('s3')

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

@router.post("/v1/file", status_code=status.HTTP_201_CREATED)
async def create_file(profilePic: UploadFile = File(...), db: Session = Depends(get_db), request: Request = Request):
    """
    Upload a file to S3 and store metadata in the database.
    """
    try:
        start_time = time.time()
        
        # Generate a unique filename for S3
        filename = f"{uuid.uuid4()}_{profilePic.filename}"  # Include the actual file name

        # Reset the file cursor to the beginning
        await profilePic.seek(0)

        # Measure S3 upload time
        s3_start_time = time.time()
        s3.upload_fileobj(profilePic.file, bucket_name, filename)
        s3_end_time = time.time()
        s3_processing_time = (s3_end_time - s3_start_time) * 1000  # Convert to milliseconds
        statsd_client.timing('s3.upload.time', s3_processing_time)

        # Generate S3 URL for the file
        url = f"https://{bucket_name}.s3.amazonaws.com/{filename}"

        # Measure database query time
        db_start_time = time.time()
        new_file = FileMetadata(file_name=filename, url=url, upload_date=datetime.utcnow())
        db.add(new_file)
        db.commit()
        db.refresh(new_file)
        db_end_time = time.time()
        db_insert_time = (db_end_time - db_start_time) * 1000  # Convert to milliseconds
        statsd_client.timing('db.insert.time', db_insert_time)

        end_time = time.time()
        processing_time = (end_time - start_time) * 1000  # Convert to milliseconds

        # Log the request with filename
        logging.info(f"File uploaded successfully: {filename}. Request ID: {request.client.host}")

        # Send metrics to StatsD
        statsd_client.incr('file.upload.count')
        statsd_client.timing('file.upload.time', processing_time)

        return {
            "file_name": new_file.file_name,
            "id": str(new_file.id),
            "url": new_file.url,
            "upload_date": new_file.upload_date.strftime("%Y-%m-%d")
        }
    except ClientError as e:
        db.rollback()
        error_message = f"Failed to upload file: {e}\n{traceback.format_exc()}"
        logging.error(error_message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to upload file: {e}")
    except Exception as e:
        # Delete the file from S3 if database operation fails
        try:
            s3.delete_object(Bucket=bucket_name, Key=filename)
        except ClientError as e:
            logging.error(f"Failed to delete file from S3: {e}")

        db.rollback()
        error_message = f"Failed to process request: {e}\n{traceback.format_exc()}"
        logging.error(error_message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to process request: {e}")

@router.get("/v1/file", status_code=status.HTTP_400_BAD_REQUEST)
async def get_file_not_allowed(request: Request):
    """Handle GET request with 400 Bad Request"""
    logging.info(f"GET request not allowed for /v1/file. Request ID: {request.client.host}")
    return Response(
        status_code=status.HTTP_400_BAD_REQUEST,
        headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                 "Pragma": "no-cache",
                 "X-Content-Type-Options": "nosniff"}
    )

@router.delete("/v1/file", status_code=status.HTTP_400_BAD_REQUEST)
async def delete_file_not_allowed(request: Request):
    """Handle DELETE request with 400 Bad Request"""
    logging.info(f"DELETE request not allowed for /v1/file. Request ID: {request.client.host}")
    return Response(
        status_code=status.HTTP_400_BAD_REQUEST,
        headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                 "Pragma": "no-cache",
                 "X-Content-Type-Options": "nosniff"}
    )

@router.api_route("/v1/file", methods=["PUT", "PATCH", "OPTIONS", "HEAD"])
async def method_not_allowed(request: Request):
    """Handle unsupported HTTP methods"""
    logging.info(f"Unsupported HTTP method attempted for /v1/file. Request ID: {request.client.host}")
    return Response(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                 "Pragma": "no-cache",
                 "X-Content-Type-Options": "nosniff"}
    )

@router.get("/v1/file/{id}", status_code=status.HTTP_200_OK)
async def get_file(id: str, db: Session = Depends(get_db), request: Request = Request):
    """
    Retrieve a file's metadata by ID.
    """
    try:
        start_time = time.time()
        
        # Measure database query time
        db_start_time = time.time()
        file_metadata = db.query(FileMetadata).filter(FileMetadata.id == id).first()
        db_end_time = time.time()
        db_select_time = (db_end_time - db_start_time) * 1000  # Convert to milliseconds
        statsd_client.timing('db.select.time', db_select_time)

        if not file_metadata:
            logging.error(f"File not found with ID: {id}. Request ID: {request.client.host}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

        end_time = time.time()
        processing_time = (end_time - start_time) * 1000  # Convert to milliseconds

        # Log the request with filename
        logging.info(f"File metadata retrieved successfully: {file_metadata.file_name}. Request ID: {request.client.host}")

        # Send metrics to StatsD
        statsd_client.incr('file.get.count')
        statsd_client.timing('file.get.time', processing_time)

        return {
            "file_name": file_metadata.file_name,
            "id": str(file_metadata.id),
            "url": file_metadata.url,
            "upload_date": file_metadata.upload_date.strftime("%Y-%m-%d")
        }
    except Exception as e:
        error_message = f"Failed to retrieve file metadata: {e}\n{traceback.format_exc()}"
        logging.error(error_message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

@router.delete("/v1/file/{id}")
async def delete_file(id: str, db: Session = Depends(get_db), request: Request = Request):
    """
    Delete a file from S3 and remove its metadata from the database.
    """
    try:
        start_time = time.time()
        
        # Find file metadata in database
        db_start_time = time.time()
        file_metadata = db.query(FileMetadata).filter(FileMetadata.id == id).first()
        db_end_time = time.time()
        db_find_time = (db_end_time - db_start_time) * 1000  # Convert to milliseconds
        statsd_client.timing('db.find.time', db_find_time)

        if not file_metadata:
            logging.error(f"File not found with ID: {id}. Request ID: {request.client.host}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

        # Delete file from S3 bucket
        s3_start_time = time.time()
        try:
            s3.delete_object(Bucket=bucket_name, Key=file_metadata.file_name)
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logging.error(f"File not found in S3: {file_metadata.file_name}. Request ID: {request.client.host}")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found in S3")
            else:
                error_message = f"Failed to delete file from S3: {e}\n{traceback.format_exc()}"
                logging.error(error_message)
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to delete file from S3")
        s3_end_time = time.time()
        s3_processing_time = (s3_end_time - s3_start_time) * 1000  # Convert to milliseconds
        statsd_client.timing('s3.delete.time', s3_processing_time)

        # Remove metadata from database
        db_start_time = time.time()
        db.delete(file_metadata)
        db.commit()
        db_end_time = time.time()
        db_delete_time = (db_end_time - db_start_time) * 1000  # Convert to milliseconds
        statsd_client.timing('db.delete.time', db_delete_time)

        end_time = time.time()
        processing_time = (end_time - start_time) * 1000  # Convert to milliseconds

        # Log the request with filename
        logging.info(f"File deleted successfully: {file_metadata.file_name}. Request ID: {request.client.host}")

        # Send metrics to StatsD
        statsd_client.incr('file.delete.count')
        statsd_client.timing('file.delete.time', processing_time)

        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        error_message = f"Failed to process request: {e}\n{traceback.format_exc()}"
        logging.error(error_message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to process request")

@router.api_route("/v1/file/{id}", methods=["PUT", "PATCH", "POST", "HEAD", "OPTIONS"])
async def method_not_allowed_for_id(id: str, request: Request):
    """Handle unsupported HTTP methods for /v1/file/{id}"""
    logging.info(f"Unsupported HTTP method attempted for /v1/file/{id}. Request ID: {request.client.host}")
    return Response(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                 "Pragma": "no-cache",
                 "X-Content-Type-Options": "nosniff"}
    )

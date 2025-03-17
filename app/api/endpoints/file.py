from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import FileMetadata
from botocore.exceptions import ClientError
import boto3
import uuid
from datetime import datetime

router = APIRouter()

# Initialize S3 client using IAM role
s3 = boto3.client('s3')

@router.post("/v1/file", status_code=status.HTTP_201_CREATED)
async def create_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Upload a file to S3 and store metadata in the database.
    """
    try:
        # Define S3 bucket name (replace with your actual bucket name)
        bucket_name = "rutwik-bucket"

        # Generate a unique filename for S3
        filename = f"{uuid.uuid4()}.jpg"  # Example: Generate a UUID-based filename

        # Reset the file cursor to the beginning
        await file.seek(0)

        # Upload file to S3 bucket
        s3.upload_fileobj(file.file, bucket_name, filename)

        # Generate S3 URL for the file
        url = f"https://{bucket_name}.s3.amazonaws.com/{filename}"

        # Store metadata in the database
        new_file = FileMetadata(file_name=filename, url=url, upload_date=datetime.utcnow())
        db.add(new_file)
        db.commit()
        db.refresh(new_file)

        return {
            "file_name": new_file.file_name,
            "id": str(new_file.id),
            "url": new_file.url,
            "upload_date": new_file.upload_date.strftime("%Y-%m-%d")
        }
    except ClientError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to upload file: {e}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {str(e)}")

@router.get("/v1/file", status_code=status.HTTP_400_BAD_REQUEST)
async def get_file_not_allowed():
    """Handle GET request with 400 Bad Request"""
    return Response(
        status_code=status.HTTP_400_BAD_REQUEST,
        headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                 "Pragma": "no-cache",
                 "X-Content-Type-Options": "nosniff"}
    )

@router.delete("/v1/file", status_code=status.HTTP_400_BAD_REQUEST)
async def delete_file_not_allowed():
    """Handle DELETE request with 400 Bad Request"""
    return Response(
        status_code=status.HTTP_400_BAD_REQUEST,
        headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                 "Pragma": "no-cache",
                 "X-Content-Type-Options": "nosniff"}
    )

@router.api_route("/v1/file", methods=["PUT", "PATCH", "OPTIONS", "HEAD"])
async def method_not_allowed():
    """Handle unsupported HTTP methods"""
    return Response(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                 "Pragma": "no-cache",
                 "X-Content-Type-Options": "nosniff"}
    )

@router.get("/v1/file/{id}", status_code=status.HTTP_200_OK)
async def get_file(id: str, db: Session = Depends(get_db)):
    """
    Retrieve a file's metadata by ID.
    """
    try:
        file_metadata = db.query(FileMetadata).filter(FileMetadata.id == id).first()
        if not file_metadata:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

        return {
            "file_name": file_metadata.file_name,
            "id": str(file_metadata.id),
            "url": file_metadata.url,
            "upload_date": file_metadata.upload_date.strftime("%Y-%m-%d")
        }
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

@router.delete("/v1/file/{id}")
async def delete_file(id: str, db: Session = Depends(get_db)):
    """
    Delete a file from S3 and remove its metadata from the database.
    """
    try:
        # Find file metadata in database
        file_metadata = db.query(FileMetadata).filter(FileMetadata.id == id).first()
        if not file_metadata:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

        # Delete file from S3 bucket
        bucket_name = "rutwik-bucket"
        try:
            s3.delete_object(Bucket=bucket_name, Key=file_metadata.file_name)
        except ClientError as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete file from S3")

        # Remove metadata from database
        db.delete(file_metadata)
        db.commit()

        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

@router.api_route("/v1/file/{id}", methods=["PUT", "PATCH", "POST", "HEAD", "OPTIONS"])
async def method_not_allowed_for_id(id: str):
    """Handle unsupported HTTP methods for /v1/file/{id}"""
    return Response(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                 "Pragma": "no-cache",
                 "X-Content-Type-Options": "nosniff"}
    )

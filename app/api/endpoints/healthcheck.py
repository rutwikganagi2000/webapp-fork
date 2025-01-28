from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from fastapi import Depends
from app.database import get_db
from app.models import HealthCheck

router = APIRouter()

@router.get("/healthz", status_code=status.HTTP_200_OK)
async def health_checks(request: Request, db: Session = Depends(get_db)):
    """
    Health Check Endpoint:
    - Inserts a record into the health_checks table.
    - Returns HTTP 200 if successful, HTTP 503 if not.
    - Ensures no payload or unsupported methods are allowed.
    """
    if await request.body():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payload not allowed")

    try:
        new_check = HealthCheck()
        db.add(new_check)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database connection failed")

    return Response(status_code=status.HTTP_200_OK, headers={"Cache-Control": "no-cache"})

@router.api_route("/healthz", methods=["POST", "PUT", "DELETE", "PATCH"])
async def method_not_allowed():
    """Reject unsupported methods with 405"""
    raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)

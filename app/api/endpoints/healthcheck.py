from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from fastapi import Depends
from app.database import get_db
from app.models import HealthCheck

router = APIRouter()

@router.get("/healthz")
async def health_checks(request: Request, db: Session = Depends(get_db)):
    """
    Health Check Endpoint
    """
    # Check for payload in request body or query parameters
    if await request.body() or request.query_params:
        return Response(
            status_code=status.HTTP_400_BAD_REQUEST,
            headers={"Cache-Control": "no-cache, no-store, must-revalidate", 
                    "Pragma": "no-cache",
                    "X-Content-Type-Options": "nosniff"}
        )

    try:
        new_check = HealthCheck()
        db.add(new_check)
        db.commit()
        return Response(
            status_code=status.HTTP_200_OK,
            headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "X-Content-Type-Options": "nosniff"}
        )
    except Exception:
        db.rollback()
        return Response(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "X-Content-Type-Options": "nosniff"}
        )

@router.api_route("/healthz", methods=["POST", "PUT", "DELETE", "PATCH"])
async def method_not_allowed():
    """Handle unsupported HTTP methods"""
    return Response(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "X-Content-Type-Options": "nosniff"}
    )

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def catch_all(path: str):
    """Handle all undefined routes"""
    return Response(
        status_code=status.HTTP_404_NOT_FOUND,
        headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "X-Content-Type-Options": "nosniff"}
    )
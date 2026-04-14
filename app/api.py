from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel

from .database import get_db
from .service import create_profile
from .models import ProfileResponse

router = APIRouter()

class ProfileRequest(BaseModel):
    name: str

@router.post("/api/profiles", status_code=201)
async def create_profile_endpoint(
    request: ProfileRequest,
    response: Response,
    db: Annotated[Session, Depends(get_db)]
):
    if not request.name.strip():
        raise HTTPException(status_code=400, detail="name cannot be empty")
    
    try:
        profile, is_new =  await create_profile(request.name, db)
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))
    
    data = ProfileResponse.model_validate(profile)

    if not is_new:
        response.status_code = 200
        return {
            "status": "success",
            "message": "Profile already exists",
            "data": data,
        }

    return {
        "status": "success",
        "data": data,
    }

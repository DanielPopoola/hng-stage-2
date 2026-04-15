from typing import Annotated


import httpx
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel

from .database import get_db
from .service import (
    create_profile,
    enrich_profile_data,
    get_profile,
    get_profiles,
    delete_profile
)
from .models import ProfileResponse, ProfileListItem, AgeGroup

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
        enriched_data = await enrich_profile_data(request.name)
        profile, is_new = create_profile(request.name, enriched_data, db)
    except (ValueError, httpx.HTTPStatusError) as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

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


@router.get("/api/profiles")
def list_profiles_endpoint(
    db: Annotated[Session, Depends(get_db)],
    gender: str | None = None,
    country_id: str | None = None,
    age_group: AgeGroup | None = None,
):
    profiles = get_profiles(
        db,
        gender=gender,
        country_id=country_id,
        age_group=age_group,
    )

    data = [ProfileListItem.model_validate(p) for p in profiles]

    return {
        "status": "success",
        "count": len(data),
        "data": data,
    }

@router.get("/api/profiles/{id}")
def get_profile_endpoint(
    id: str,
    db: Annotated[Session, Depends(get_db)]
):
    profile = get_profile(id, db)

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return {
        "status": "success",
        "data": ProfileResponse.model_validate(profile),
    }


@router.delete("/api/profiles/{id}", status_code=204)
def delete_profile_endpoint(
    id: str,
    db: Annotated[Session, Depends(get_db)]
):
    deleted = delete_profile(id, db)

    if not deleted:
        raise HTTPException(status_code=404, detail="Profile not found")

    return Response(status_code=204)
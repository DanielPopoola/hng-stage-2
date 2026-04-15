from collections.abc import Sequence
import asyncio

from .models import AgeGroup, Profiles
from .clients import get_age, get_gender, get_nationality

from sqlalchemy.orm import Session
from sqlalchemy import select, func


def _classify_age(age: int) -> AgeGroup:
    if age <= 12:
        return AgeGroup.CHILD
    elif age >= 13 and age <= 19:
        return AgeGroup.TEENAGER
    elif age >= 20 and age <= 59:
        return AgeGroup.ADULT
    else:
        return AgeGroup.SENIOR
    

async def enrich_profile_data(name: str) -> dict:
    age_data, gender_data, nationality_data = await asyncio.gather(
        get_age(name),
        get_gender(name),
        get_nationality(name),
    )

    if gender_data["gender"] is None or gender_data["count"] == 0:
        raise ValueError("Genderize returned an invalid response")
    if age_data["age"] is None:
        raise ValueError("Agify returned an invalid response")
    if not nationality_data["country"]:
        raise ValueError("Nationalize returned an invalid response")

    age_class = _classify_age(age_data["age"])
    top_country = max(nationality_data["country"], key=lambda c: c["probability"])

    return {
        "gender": gender_data["gender"],
        "gender_probability": gender_data["probability"],
        "sample_size": gender_data["count"],
        "age": age_data["age"],
        "age_group": age_class,
        "country_id": top_country["country_id"],
        "country_probability": top_country["probability"],
    }
    
def create_profile(name: str, enriched_data: dict, db: Session) -> tuple[Profiles, bool]:
    stmt = select(Profiles).where(Profiles.name == name)
    existing = db.execute(stmt).scalar_one_or_none()

    if existing:
        return existing, False

    profile = Profiles(
        name=name,
        **enriched_data
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return profile, True

def get_profile(id: str, db: Session) -> Profiles | None:
    stmt = select(Profiles).where(Profiles.id == id)
    result = db.execute(stmt).scalar_one_or_none()
    return result

def get_profiles(
    db: Session,
    gender: str | None = None,
    country_id: str | None = None,
    age_group: AgeGroup | None = None,
) -> Sequence[Profiles]:
    stmt = select(Profiles)

    if gender:
        stmt = stmt.where(func.lower(Profiles.gender) == gender.lower())

    if country_id:
        stmt = stmt.where(func.lower(Profiles.country_id) == country_id.lower())

    if age_group:
        stmt = stmt.where(Profiles.age_group == age_group)

    result = db.execute(stmt).scalars().all()
    return result


def delete_profile(id: str, db: Session) -> bool:
    stmt = select(Profiles).where(Profiles.id == id)
    profile = db.execute(stmt).scalar_one_or_none()

    if not profile:
        return False

    db.delete(profile)
    db.commit()
    return True


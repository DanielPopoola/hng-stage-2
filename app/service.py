import asyncio

from .models import AgeGroup, Profiles
from .clients import get_age, get_gender, get_nationality

from sqlalchemy.orm import Session


def _classify_age(age: int) -> AgeGroup:
    if age <= 12:
        return AgeGroup.CHILD
    elif age >= 13 and age <= 19:
        return AgeGroup.TEENAGER
    elif age >= 20 and age <= 59:
        return AgeGroup.ADULT
    else:
        return AgeGroup.SENIOR
    


async def create_profile(name: str, db: Session) -> tuple[Profiles, bool]:
    existing = db.query(Profiles).filter(Profiles.name == name).first()
    if existing:
        return existing, False

    age_data, gender_data, nationality_data = await asyncio.gather(
        get_age(name),
        get_gender(name),
        get_nationality(name),
    )

    if gender_data["gender"] is None or gender_data["count"] == 0:
        raise ValueError("Gender data unavailable for this name")
    if age_data["age"] is None:
        raise ValueError("Age data unavailable for this name")
    if not nationality_data["country"]:
        raise ValueError("Nationality data unavailable for this name")

    age_class = _classify_age(age_data["age"])
    top_country = max(nationality_data["country"], key=lambda c: c["probability"])

    profile = Profiles(
        name=name,
        gender=gender_data["gender"],
        gender_probability=gender_data["probability"],
        sample_size=gender_data["count"],
        age=age_data["age"],
        age_group=age_class,
        country_id=top_country["country_id"],
        country_probability=top_country["probability"],
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return profile, True
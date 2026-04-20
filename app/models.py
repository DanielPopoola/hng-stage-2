from datetime import UTC, datetime
from enum import StrEnum
import uuid6


from pydantic import BaseModel, ConfigDict
from sqlalchemy import DateTime, String, Float, Integer
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Gender(StrEnum):
    MALE = "male"
    FEMALE = "female"


class AgeGroup(StrEnum):
    CHILD = "child"
    TEENAGER = "teenager"
    ADULT = "adult"
    SENIOR = "senior"


class Profiles(Base):
    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(
        default=lambda: str(uuid6.uuid7()), primary_key=True
    )
    name: Mapped[str] = mapped_column(String, unique=True)
    gender: Mapped[str] = mapped_column(SQLEnum(Gender))
    gender_probability: Mapped[float] = mapped_column(Float)
    age: Mapped[int] = mapped_column(Integer)
    age_group: Mapped[str] = mapped_column(SQLEnum(AgeGroup))
    country_id: Mapped[str] = mapped_column(String)
    country_name: Mapped[str] = mapped_column(String)
    country_probability: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    gender: str
    gender_probability: float
    sample_size: int
    age: int
    age_group: AgeGroup
    country_id: str
    country_probability: float
    created_at: datetime


class ProfileListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    gender: str
    age: int
    age_group: AgeGroup
    country_id: str

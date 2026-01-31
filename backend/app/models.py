from pydantic import BaseModel, Field
from typing import List, Optional, Literal
import re

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TIME_RE = re.compile(r"^\d{2}:\d{2}$")

WindDir = Literal["С", "СВ", "В", "ЮВ", "Ю", "ЮЗ", "З", "СЗ"]
Cloudiness = Literal["ясная", "переменная", "сплошная"]

class AirPoint(BaseModel):
    time: str = Field(..., description="HH:MM")
    temp_c: Optional[float] = None
    rh_pct: Optional[float] = Field(None, ge=0, le=100)

    def model_post_init(self, __context):
        if not TIME_RE.match(self.time):
            raise ValueError("time must be HH:MM")

class Wind(BaseModel):
    speed_mps: float = Field(..., ge=0)
    dir: WindDir

class Location(BaseModel):
    name: Optional[str] = None

class ObservationDay(BaseModel):
    date: str
    location: Optional[Location] = None

    precip_mm: Optional[float] = Field(None, ge=0)
    cloudiness: Optional[Cloudiness] = None
    wind: Optional[Wind] = None

    air: List[AirPoint] = Field(default_factory=list, description="Up to 3 points per day")
    notes: Optional[str] = None

    def model_post_init(self, __context):
        if not DATE_RE.match(self.date):
            raise ValueError("date must be YYYY-MM-DD")
        if len(self.air) > 3:
            raise ValueError("air may contain at most 3 measurements")

"""Request models. Validation here keeps bad input out of the optimizer."""
from typing import Literal

from pydantic import BaseModel, Field


class RecommendRequest(BaseModel):
    commodity: str = Field(min_length=1, max_length=40)
    quantity_qtl: float = Field(gt=0, le=5000, description="Harvest quantity in quintals")
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    truck_type: Literal["mini", "pickup", "truck"] = "pickup"
    harvest_age_days: int = Field(default=0, ge=0, le=30)
    simulate_rain: bool = False

"""Shared building blocks used by every module. Not a business module and owns no tables."""
import uuid
from dataclasses import dataclass

from django.db import models


class UUIDModel(models.Model):
    """Every entity in the class diagram has a UUID identifier."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


@dataclass(frozen=True)
class Location:
    """Composite attribute from the ERD: (campus, building, room).

    Django has no composite fields, so each model stores three columns with a common prefix
    (e.g. location_campus) and exposes a property that returns this value object.
    """

    campus: str
    building: str = ""
    room: str = ""

    def __str__(self) -> str:
        return " / ".join(p for p in (self.campus, self.building, self.room) if p)

    def same_building(self, other: "Location") -> bool:
        return self.campus == other.campus and self.building == other.building

    def same_campus(self, other: "Location") -> bool:
        return self.campus == other.campus

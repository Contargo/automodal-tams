from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from dataclasses_json import dataclass_json

from tams.ccs.enums import CCSFeatureType, CCSJobStatus, CCSJobType, CSSSiteType


def guid() -> str:
    return str(uuid.uuid4())


def timestamp() -> str:
    return datetime.now().isoformat()


@dataclass_json
@dataclass
class CCSEvent:
    # in mm
    type: str = "net.contargo.logistics.tams.TBD"
    site: str = CSSSiteType.TERMINAL
    timestamp: str = field(default_factory=timestamp)
    version: str = "v1"
    producer: str = "ccs.automodal.contargo.net"
    location: str = "DEKOB"
    eventId: str = field(default_factory=guid)  # pylint: disable=invalid-name


@dataclass_json
@dataclass
class CCSUnit:
    unitId: str = field(default_factory=guid)  # pylint: disable=invalid-name
    height: int = 2591  # mm
    width: int = 2438  # mm
    length: int = 6058  # mm
    weight: int = 2000  # kg ?
    type: str = ""
    number: str = ""
    piggyBack: bool = False  # pylint: disable=invalid-name
    will_be_moved: bool = False
    will_be_dropped: bool = False

    @classmethod
    def empty(cls) -> CCSUnit:
        return cls(unitId="")

    def is_empty(self) -> bool:
        return self.number == ""


@dataclass_json
@dataclass
class CCSCoordinates:
    # in mm
    x: int = 1
    y: int = 2
    z: int = 3

@dataclass_json
@dataclass
class CCSLogicalCoordinates:
    # in mm
    bay: int = 1
    row: int = 2
    tier: int = 3


@dataclass_json
@dataclass
class CCSJob:
    metadata: CCSEvent = field(default_factory=CCSEvent)
    type: str = CCSJobType.MOVE
    target: CCSCoordinates = field(default_factory=CCSCoordinates)
    target_logical: CCSLogicalCoordinates = field(default_factory=CCSLogicalCoordinates)
    unit: CCSUnit = field(default_factory=CCSUnit)


@dataclass_json
@dataclass
class CCSFeature:
    # in mm
    featureId: str = field(default_factory=guid)  # pylint: disable=invalid-name
    type: str = CCSFeatureType.FINAL_LANDING
    vendor: str = "GAGA Hühnerhof AG"
    version: str = "v1"


@dataclass_json
@dataclass
class CCSJobState:
    jobType: str = CCSJobType.MOVE  # pylint: disable=invalid-name
    jobStatus: str = CCSJobStatus.DONE  # pylint: disable=invalid-name
    unit: CCSUnit = field(default_factory=CCSUnit)
    created: str = field(default_factory=timestamp)
    metadata: CCSEvent = field(default_factory=CCSEvent)


@dataclass_json
@dataclass
class CCSCraneDetails:
    # in mm
    event: CCSEvent = field(default_factory=CCSEvent)
    features: list[CCSFeature] = field(default_factory=list)

from strenum import StrEnum

seaport = "seaport"  # pylint: disable=invalid-name


class CSSSiteType(StrEnum):
    TERMINAL = "terminal"
    SEAPORT = "seaport"


class CCSJobType(StrEnum):
    MOVE = "move"
    PICK = "pick"
    DROP = "drop"
    PARK = "park"
    REMOTE = "remote"
    STORMPIN = "stormPin"
    CANCEL = "cancel"


class CCSJobStatus(StrEnum):
    INPROGRESS = "inProgress"
    WEIGHTED = "weighted"
    CONTINUED = "continued"
    STOPPED = "stopped"
    REJECTED = "rejected"
    PAUSED = "paused"
    DONE = "done"


class CCSFeatureType(StrEnum):
    CIS = "cis"
    FINAL_LANDING = "finallanding"

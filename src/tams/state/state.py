from json import JSONDecodeError

from marshmallow import ValidationError

from tams.ccs.enums import CCSJobStatus, CCSJobType
from tams.ccs.types import CCSCraneDetails, CCSJob, CCSJobState
from tams.storage.storage import TamsStorage


class TamsJobState:
    __pending_jobs: list[CCSJob] = []
    __running_job: CCSJob | None = None
    __state: CCSJobState | None = None
    cancel_job: bool = False
    details: CCSCraneDetails = CCSCraneDetails()

    def __init__(self, storage: TamsStorage, verbose: bool = False) -> None:
        self.verbose = verbose
        self.storage = storage
        self.__pending_jobs = []
        self.__running_job = None
        self.__state = None

    def clear_pending_jobs(self):
        self.__pending_jobs = []

    def clear_running_job(self):
        self.__running_job = None

    def get_pending_jobs(self) -> list[CCSJob]:
        return self.__pending_jobs

    def has_pending_jobs(self) -> bool:
        return len(self.__pending_jobs) > 0

    def has_job(self) -> bool:
        return self.__running_job is not None

    def ack_new_job(self) -> None:
        self.__running_job = self.__pending_jobs.pop(0)

    def get_job_as_json(self) -> str:
        if self.has_job():
            return str(self.__running_job.to_json())  # type: ignore[union-attr]
        return "{}"

    def get_new_job_as_json(self) -> str:
        if self.has_pending_jobs():
            return str(self.__pending_jobs[0].to_json())  # type: ignore[union-attr]
        return "{}"

    def get_pending_jobs_as_json(self) -> str:
        if self.has_pending_jobs():
            json = "["
            for job in self.__pending_jobs:
                json += job.to_json()
                json += ","
            json += "]"
            return json  # type: ignore[union-attr]
        return "{}"

    def get_state_as_json(self) -> str:
        if self.__state is not None:
            return str(self.__state.to_json())  # type: ignore[attr-defined]
        return "{}"

    def set_new_job(self, job_json: str) -> str:
        try:
            # pylint: disable=no-member
            job: CCSJob = CCSJob.from_json(job_json)  # type: ignore[attr-defined]
            if self.storage.crane is not None and job.type == CCSJobType.PICK:
                return "invalid"
            if self.storage.crane is None and job.type == CCSJobType.DROP:
                return "invalid"
            self.__pending_jobs.append(job)
            if self.verbose:
                print(f"[STATE][set_new_job] {job}")
            else:
                print(
                    f"[STATE][set_new_job] type={job.type}, x/y/z={job.target.x}/{job.target.y}/{job.target.z}, unit.number={job.unit.number}, "
                )
        except ValidationError:
            return "invalid"
        except JSONDecodeError as error:
            print(error)
            return "invalid"
        return "OK"

    def set_new_state(self, state_json: str) -> str:
        try:
            # pylint: disable=no-member
            self.__state = CCSJobState.from_json(state_json)  # type: ignore[attr-defined]
        except ValidationError:
            return "invalid"
        if (
                self.__state
                and self.__state.jobStatus == CCSJobStatus.DONE
                and self.has_job()
        ):
            if self.__running_job:
                if self.storage.container_moved(self.__running_job):
                    self.__running_job = None
                    return "DONE"
                return "error in storage"
            return "self.__running_job is None"
        return "OK"

    def set_job_done(self) -> None:
        if self.__state:
            self.__state.jobStatus = CCSJobStatus.DONE

    def set_job_none(self) -> None:
        self.__running_job = None

    def __repr__(self) -> str:
        return str(self.__running_job)

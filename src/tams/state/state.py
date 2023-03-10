from json import JSONDecodeError

from marshmallow import ValidationError

from tams.ccs.enums import CCSJobStatus
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

    def clear_pending_jobs(self) -> None:
        self.__pending_jobs = []

    def clear_running_job(self) -> None:
        self.__running_job = None

    def get_running_job(self) -> CCSJob:
        return self.__running_job
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
            return str(self.__pending_jobs[0].to_json())  # type: ignore[attr-defined]
        return "{}"

    def get_new_job(self) -> CCSJob | None:
        if self.has_pending_jobs():
            return self.__pending_jobs[0]
        return None

    def get_pending_jobs_as_json(self) -> str:
        if self.has_pending_jobs():
            json = "["
            for job in self.__pending_jobs:
                json += job.to_json()
                json += ","
            json += "]"
            return json
        return "[]"

    def get_state_as_json(self) -> str:
        if self.__state is not None:
            return str(self.__state.to_json())  # type: ignore[attr-defined]
        return "{}"

    def __parse_new_job(self, new_job: str) -> CCSJob | None:
        try:
            # pylint: disable=no-member
            job: CCSJob = CCSJob.from_json(new_job)  # type: ignore[attr-defined]
            return job
        except ValidationError as error:
            print(error)
            return None
        except JSONDecodeError as error:
            print(error)
            return None

    def add_new_job(self, new_job: str | CCSJob) -> str:
        if isinstance(new_job, str):
            new_job = self.__parse_new_job(new_job)
            if new_job is None:
                return "invalid"
        self.__pending_jobs.append(new_job)
        if self.verbose:
            print(f"[STATE][set_new_job] {new_job}")
        else:
            print(
                f"[STATE][set_new_job] type={new_job.type}, x/y/z={new_job.target.x}/{new_job.target.y}/{new_job.target.z}, unit.number={new_job.unit.number}, "
            )
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
            print(f"[STATE][set_new_state] {self.__state=}")
            if self.__running_job:
                if self.storage.process_job_done(self.__running_job):
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

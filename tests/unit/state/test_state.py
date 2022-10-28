from datetime import date
from unittest.mock import MagicMock, patch

from pytest import fixture
from pytest_mock import MockerFixture

from tams.ccs.enums import CCSJobStatus
from tams.ccs.types import CCSJob, CCSJobState
from tams.state.state import TamsJobState
from tams.storage.storage import TamsStorage


@fixture
def storage(mocker: MockerFixture) -> TamsStorage:
    return TamsStorage()


def job_json() -> str:
    return CCSJob().to_json()


def job_state(status: CCSJobStatus) -> str:
    state = CCSJobState()
    state.jobStatus = status
    return state.to_json()


def test_job_state_with_one_job(storage: MagicMock) -> None:
    state = TamsJobState(storage)
    assert not state.has_pending_jobs()
    state.set_new_job(job_json=job_json())
    assert state.has_pending_jobs()
    state.ack_new_job()
    assert not state.has_pending_jobs()
    state.set_new_state(job_state(CCSJobStatus.DONE))
    assert not state.has_job()
    assert not state.has_pending_jobs()


def test_job_state_with_two_jobs(storage: MagicMock) -> None:
    state = TamsJobState(storage)
    assert not state.has_pending_jobs()
    state.set_new_job(job_json=job_json())
    state.set_new_job(job_json=job_json())
    assert state.has_pending_jobs()
    state.ack_new_job()
    assert state.has_pending_jobs()
    state.set_new_state(job_state(CCSJobStatus.DONE))
    assert not state.has_job()
    assert state.has_pending_jobs()


def test_job_state_inprogress(storage: MagicMock) -> None:
    state = TamsJobState(storage)
    state.set_new_job(job_json=job_json())
    state.ack_new_job()
    state.set_new_state(job_state(CCSJobStatus.INPROGRESS))
    assert state.has_job()
    assert not state.has_pending_jobs()


def test_job_state_clear_jobs(storage: MagicMock) -> None:
    state = TamsJobState(storage)
    state.set_new_job(job_json=job_json())
    state.ack_new_job()
    state.set_new_state(job_state(CCSJobStatus.INPROGRESS))
    assert state.has_job()
    assert not state.has_pending_jobs()


def test_job_state_get_pending_jobs_as_json(storage: MagicMock) -> None:
    state = TamsJobState(storage)
    assert state.get_pending_jobs_as_json() == "{}"
    state.set_new_job(job_json=job_json())
    assert state.get_pending_jobs_as_json() != "{}"

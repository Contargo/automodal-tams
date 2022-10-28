import time
from json import JSONDecodeError
from os import getcwd
from threading import Event, Thread
from typing import Any

import requests
from flask import Flask, request
from marshmallow import ValidationError
from requests import ConnectionError  # pylint: disable=redefined-builtin
from requests.adapters import MaxRetryError
from urllib3.exceptions import NewConnectionError

from tams.ccs.types import CCSCraneDetails
from tams.metric.metric import Metric
from tams.state.state import TamsJobState
from tams.web.msg import Messages


class CCS:
    locaton: str = "terminal"
    type: str = "crane"
    name: str = "PSKran"

    def __init__(
        self,
        state: TamsJobState,
        messages: Messages,
        metric: Metric,
        ccs_url: str = "http://localhost:9999",
        verbose: bool = False,
    ):  # pylint: disable=too-many-arguments
        self.metric = metric
        self.state = state
        self.messages = messages
        self.ccs_url = ccs_url
        self.verbose = verbose
        self.shutdown_event = Event()
        self.app = Flask("tams ccs", root_path=getcwd())
        self.add_endpoints()
        #self.get_job() # deaktivated because polo don't implemented the get
        self.worker_rest_thread = Thread(
            target=self.worker_rest,
            args=(),
            name="CCS Worker Rest",
            daemon=True,
        )
        self.worker_state_thread = Thread(
            target=self.worker_state,
            args=(),
            name="CCS Worker Rest",
            daemon=True,
        )

    def start(self) -> None:
        self.worker_rest_thread.start()
        self.worker_state_thread.start()

    def add_endpoints(self) -> None:
        self.app.add_url_rule("/metric", "metric", self.metric_post, methods=["POST"])
        self.app.add_url_rule("/state", "status", self.state_post, methods=["POST"])
        self.app.add_url_rule("/alarm", "alarm", self.alarm_post, methods=["POST"])
        self.app.add_url_rule(
            "/details", "details", self.details_post, methods=["POST"]
        )

    def worker_rest(self) -> None:
        self.app.run(host="0.0.0.0", port=9998)

    def worker_state(self) -> None:
        while not self.shutdown_event.is_set():
            if self.state.cancel_job:
                if self.send_cancel():
                    self.state.cancel_job = False
            try:
                self.get_details()
                if not self.state.has_job() and self.state.has_pending_jobs():
                    print(
                        f"[CCS][worker_state] has_job={self.state.has_job()}, has_new_job={self.state.has_pending_jobs()}"
                    )
                    self.send_job()
            except (
                ConnectionError,
                MaxRetryError,
                ConnectionRefusedError,
                NewConnectionError,
            ):
                print(
                    "[CCS][worker_state] exception (one off ConnectionError,"
                    "MaxRetryError,ConnectionRefusedError,NewConnectionError)"
                )
            time.sleep(1)

    def alarm_post(self) -> Any:
        if self.verbose:
            print(f"[CCS][alarm_post] {request.data}")
        self.messages.add_error_msg(title="CCS alarm", text=str(request.data))
        return "OK"

    def metric_post(self) -> Any:
        if self.verbose:
            print(f"[CCS][metric_post] {request.data=}")
        self.metric.set_metrics(request.data)
        return "OK"

    def details_post(self) -> Any:
        if self.verbose:
            print(f"[CCS][details_post] {request.data=}")
        try:
            self.state.details = CCSCraneDetails.from_json(request.data.decode("utf-8"))  # type: ignore[attr-defined]
        except ValidationError:
            return "Invalid input", 405
        except (JSONDecodeError, MaxRetryError, ConnectionError) as error:
            print(error)
            print(request.data)
        return "OK", 200

    def state_post(self) -> Any:
        ret = self.state.set_new_state(request.data)
        if self.verbose:
            print(f"[CCS][state_post] {ret=}")

        if ret == "invalid":
            return "Invalid input", 405
        if ret == "has job":
            return self.state.get_job_as_json(), 409
        if ret == "DONE":
            self.messages.add_msg("CCS state_post", "job done")
            return "OK", 200
        if ret == "OK":
            return "OK", 200
        return "unknown error", 500

    def send_job(self) -> None:
        data = self.state.get_new_job_as_json()
        if data == "{}":
            if self.verbose:
                print(f"[CCS][send_job] {self.state=}")
            #self.state.reject_new_job()
            self.messages.add_error_msg(title="CCS send_job", text="job is empty")
            return
        print(data)
        ret = requests.post(f"{self.ccs_url}/job", data=data)
        if self.verbose:
            print(f"[CCS][send_job]: {self.state.get_new_job_as_json()=}")
        print(f"[CCS][send_job]: {ret=}")

        if ret.text == "OK" or ret.status_code == 200:
            self.state.ack_new_job()
            self.messages.add_msg(title="CCS send_job", text="thing acked job")
        else:
            self.messages.add_error_msg(title="CCS send_job", text="thing rejected job")

    def send_cancel(self) -> bool:
        ret = requests.post(f"{self.ccs_url}/job_cancel")
        print(f"[CCS][send_cancel]: {ret=}")

        if ret.text == "OK" or ret.status_code == 200:
            self.state.set_job_none()
            self.messages.add_msg(title="CCS send_cancel", text="thing canceled job")
            return True
        self.state.cancel_job = False
        self.messages.add_error_msg(
            title="CCS send_cancel", text="thing cancel job not possible"
        )
        return False

    def get_job(self) -> None:
        try:
            job_json = requests.get(f"{self.ccs_url}/job")
        except ConnectionError:
            return
        try:
            self.state.set_new_job(str(job_json.text))
            self.state.ack_new_job()
        except ValidationError:
            return
        except JSONDecodeError as error:
            print(error)
            print(job_json.text)
        return

    def get_details(self) -> None:
        try:
            ret = requests.get(f"{self.ccs_url}/details")
            # print(f"details: {ret.text=}")
        except ConnectionError:
            return
        try:
            self.state.details = CCSCraneDetails.from_json(ret.text)  # type: ignore[attr-defined]
            # print(f"{self.state.details=}")
        except ValidationError:
            return
        except (JSONDecodeError, MaxRetryError, ConnectionError) as error:
            print(error)
            print(ret.text)
        return

    def shutdown(self) -> None:
        self.shutdown_event.set()

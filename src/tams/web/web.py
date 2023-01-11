import json
from enum import Enum
from os import getcwd
from pathlib import Path
from threading import Event, Thread
from typing import Any

from flask import Flask, render_template, request
from flask_cors import CORS

from tams.ccs.enums import CCSJobType
from tams.ccs.types import CCSCoordinates, CCSJob
from tams.metric.metric import Metric
from tams.state.state import TamsJobState
from tams.storage.storage import TamsStorage
from tams.web.msg import Messages


class WebState(Enum):
    init = "init"
    pos = "pos"
    drop = "drop"
    auto = "auto"


class Web:
    locaton: str = "terminal"
    type: str = "crane"
    name: str = "PSKran"

    def __init__(
        self,
        state: TamsJobState,
        storage: TamsStorage,
        metric: Metric,
        verbose: bool = False,
    ):
        self.metric = metric
        self.state = state
        self.verbose = verbose
        self.mode = WebState("init")
        template_folder = Path(__file__).parent.joinpath("template")
        static_folder = Path(__file__).parent.joinpath("assets")
        self.shutdown_event = Event()
        self.msgs = Messages()
        self.storage = storage
        self.app = Flask(
            "tams web",
            root_path=getcwd(),
            template_folder=template_folder.as_posix(),
            static_folder=static_folder.as_posix(),
        )
        CORS(self.app)
        self.add_endpoints()
        self.worker_rest: Thread = Thread(
            target=self.rest,
            args=(),
            name="CCS Worker",
            daemon=True,
        )

    def start(self) -> None:
        self.worker_rest.start()

    def add_endpoints(self) -> None:
        self.app.add_url_rule("/", "frontend", self.frontend, methods=["get"])
        self.app.add_url_rule("/job", "job_post", self.job_post, methods=["post"])
        #        self.app.add_url_rule("/cancel-job", "cancel_job_post", self.cancel_job_post, methods=["post"])
        self.app.add_url_rule("/job", "job_get", self.job_get, methods=["get"])
        self.app.add_url_rule(
            "/jobs_pending", "jobs_pending", self.jobs_pending, methods=["get"]
        )
        self.app.add_url_rule("/job_state", "job_get", self.job_get, methods=["get"])
        self.app.add_url_rule(
            "/job_cancel", "job_cancel", self.job_cancel, methods=["post"]
        )
        self.app.add_url_rule(
            "/job_clear_running",
            "job_clear_running",
            self.job_clear_running,
            methods=["post"],
        )
        self.app.add_url_rule(
            "/job_clear_pending",
            "job_clear_pending",
            self.job_clear_pending,
            methods=["post"],
        )
        self.app.add_url_rule("/state", "state_get", self.state_get, methods=["get"])
        self.app.add_url_rule("/metric", "metric_get", self.metric_get, methods=["get"])
        self.app.add_url_rule(
            "/details", "details_get", self.details_get, methods=["get"]
        )
        self.app.add_url_rule(
            "/messages", "messages_get", self.messages_get, methods=["get"]
        )
        self.app.add_url_rule("/stacks", "stacks_get", self.stacks_get, methods=["get"])
        self.app.add_url_rule("/mode", "mode", self.mode_post, methods=["post"])
        # self.app.add_url_rule(
        #    "/container", "container_get", self.container_get, methods=["get"]
        # )
        self.app.add_url_rule(
            "/stacks/container/<int:layer>/<string:stack_name>/<string:container>",
            "stacks_container",
            self.stacks_container_update,
            methods=["post"],
        )

        self.app.add_url_rule(
            "/stacks/setpos/<string:stack_name>",
            "stacks_setpos_post",
            self.stacks_setpos_post,
            methods=["post"],
        )
        self.app.add_url_rule(
            "/stacks/drop/<string:stack_name>/<int:layer>",
            "stacks_drop_container",
            self.stacks_drop_container,
            methods=["post"],
        )
        self.app.add_url_rule(
            "/container/generate_move/<string:from_stack>/<string:to_stack>",
            "container_generate_move",
            self.container_generate_job,
            methods=["post"],
        )

        # ajax calls
        self.app.add_url_rule(
            "/ajax_job_status", "ajax_job_status", self.ajax_job_status, methods=["get"]
        )
        self.app.add_url_rule(
            "/ajax_crane_status",
            "ajax_crane_status",
            self.ajax_crane_status,
            methods=["get"],
        )
        self.app.add_url_rule(
            "/ajax_auto_job", "ajax_auto_job", self.ajax_auto_job, methods=["get"]
        )
        self.app.add_url_rule(
            "/ajax_stack_table",
            "ajax_stack_table",
            self.ajax_stack_table,
            methods=["get"],
        )
        self.app.add_url_rule(
            "/ajax_job_list", "ajax_job_list", self.ajax_job_list, methods=["get"]
        )

    def rest(self) -> None:
        self.app.run(host="0.0.0.0", port=7000)

    def shutdown(self) -> None:
        self.shutdown_event.set()

    def frontend(self) -> Any:
        if self.verbose:
            print(self.storage.get_stacks_as_json())
        return render_template("index.html", active_link="/")

    def stacks_get(self) -> Any:
        return self.storage.get_stacks_as_json()

    def mode_post(self) -> Any:
        mode = request.data.decode()
        print(mode)
        print(WebState.__members__.keys())
        if mode in WebState.__members__:
            self.mode = WebState(mode)
            return "OK", 200
        return "Invalid input", 405

    def stacks_setpos_post(self, stack_name: str) -> Any:
        data = json.loads(request.get_data())
        print(f"[WEB][stacks_setpos_post] {stack_name} {data}")
        self.storage.set_stack_pos(
            stack_name, CCSCoordinates(data["x"], data["y"], data["z"])
        )
        return "OK", 200

    def stacks_drop_container(self, stack_name: str, layer: int) -> Any:
        print(f"[WEB][stacks_drop_container] {stack_name=} {layer=}")
        job = CCSJob()
        job.target = self.storage.get_stack_by_name(stack_name)
        job.type = CCSJobType.DROP
        self.state.add_new_job(job)

        return "OK", 200

    def stacks_container_update(
        self, layer: int, stack_name: str, container: str
    ) -> Any:
        print(f"[WEB][stacks_container_update] {layer=} {stack_name=} {container=}")
        self.storage.set_container_stack(layer, stack_name, container.replace("_", " "))
        print("asd")
        return "OK", 200

    def __add_new_job(self, stack_name: str, job_type: CCSJobType) -> None:
        job = CCSJob()
        stack = self.storage.get_stack_by_name(stack_name)
        job.target = stack.coordinates
        if job_type == CCSJobType.DROP:
            job.target.z = job.target.z + 2591 * len(stack.container)
        if job_type == CCSJobType.PICK:
            job.target.z = job.target.z + 2591 * (len(stack.container) - 1)
        job.type = job_type
        self.state.add_new_job(job)

    def container_generate_job(self, from_stack: str, to_stack: str) -> Any:
        print(f"[WEB][container_generate_move] {from_stack=} {to_stack=}")
        if from_stack == to_stack:
            self.msgs.add_error_msg("from and to are identical", "invalid")
            return "Invalid input", 405
        self.msgs.add_msg(f"generate jobs {from_stack=}, {to_stack=}", "OK")
        self.__add_new_job(from_stack, CCSJobType.PICK)
        self.__add_new_job(to_stack, CCSJobType.DROP)
        return "OK", 200

    # def container_get(self) -> Any:
    #    return self.storage.get_container_as_json()

    def job_post(self) -> Any:
        job_json = str(request.json).replace("'", '"')
        job_json = job_json.replace("False", "false")
        if self.verbose:
            print(f"[WEB][job_post] {job_json=}")
        ret = self.state.add_new_job(job_json)
        if ret == "invalid":
            self.msgs.add_error_msg("WEB job_post", "invalid")
            return "Invalid input", 405
        if ret == "has job":
            self.msgs.add_error_msg("WEB job_post", "has job")
            return "has job", 409
        if ret == "OK":
            self.msgs.add_msg("WEB job_post", "ok")
            return "OK", 200
        self.msgs.add_error_msg("WEB job_post", "unknown error")
        return "unknown error", 500

    def jobs_pending(self) -> Any:
        return self.state.get_pending_jobs_as_json(), 200

    def job_get(self) -> Any:
        if self.state.has_job():
            return self.state.get_job_as_json(), 200
        return {}, 200

    def job_cancel(self) -> Any:
        self.state.cancel_job = True
        self.msgs.add_msg("WEB job_cancel", "ok")
        return "OK", 200

    def state_get(self) -> Any:
        return self.state.get_state_as_json(), 200

    def details_get(self) -> Any:
        return self.state.details.to_json(), 200  # type: ignore[attr-defined]

    def metric_get(self) -> Any:
        return self.metric.get_metrics(), 200

    def job_clear_running(self) -> Any:
        return self.state.clear_running_job(), 200

    def job_clear_pending(self) -> Any:
        return self.state.clear_pending_jobs(), 200

    def messages_get(self) -> Any:
        return self.msgs.get_msgs_json(clear=True), 200

    ### AJAX

    def ajax_job_status(self) -> Any:
        return render_template("ajax/job_status.html")

    def ajax_crane_status(self) -> Any:
        return render_template("ajax/crane_status.html")

    def ajax_auto_job(self) -> Any:
        stacks = self.storage.stacks
        if self.mode.name == "auto":
            return render_template("ajax/auto_job.html", stacks=stacks)
        else:
            return ""

    def ajax_stack_table(self) -> Any:
        stacks = self.storage.stacks
        container = self.storage.container
        partial = f"ajax/partial_stacks_{self.mode.name}.html"
        return render_template(
            "ajax/stacks.html", partial=partial, container=container, stacks=stacks
        )

    def ajax_job_list(self) -> Any:
        pending = self.state.get_pending_jobs_as_json()
        running = self.state.get_job_as_json()
        print(pending)
        print(running)
        return render_template("ajax/job_list.html", pending=pending, running=running)

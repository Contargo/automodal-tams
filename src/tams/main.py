#!/usr/bin/env python
import time
from argparse import ArgumentParser
from pathlib import Path
from typing import Any

from tams.ccs.ccs import CCS
from tams.metric.metric import Metric
from tams.state.state import TamsJobState
from tams.storage.storage import TamsStorage
from tams.web.web import Web


def get_args() -> Any:
    parser = ArgumentParser(description="yolo")
    parser.add_argument("-c", "--ccs", type=str, default="127.0.0.1", help="IP of CCS")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="verbose log output"
    )
    parser.add_argument("--logwebcalls", action="store_true", help="log web calls")
    return parser.parse_args()


json_path = Path("export.json")


def run() -> None:
    args = get_args()
    storage = TamsStorage()
    if json_path.is_file():
        storage.import_json(json_path)
    state = TamsJobState(storage, verbose=args.verbose)
    metrics = Metric()
    web = Web(state, storage, metrics, verbose=args.verbose)
    ccs = CCS(
        state,
        web.msgs,
        metrics,
        ccs_url=f"http://{args.ccs}:9999",
        verbose=args.verbose,
    )

    if not args.logwebcalls:
        import logging  # pylint: disable=import-outside-toplevel

        log = logging.getLogger("werkzeug")
        log.setLevel(logging.ERROR)

    try:
        ccs.start()
        web.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        storage.export_json(json_path)
        ccs.shutdown()
        web.shutdown()


if __name__ == "__main__":
    run()

from typing import Any


class Metric:
    __metrics: Any = {}

    def __init__(self) -> None:
        pass

    def get_metrics(self) -> Any:
        return self.__metrics

    def set_metrics(self, met: Any) -> None:
        self.__metrics = met

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, List, Optional

from dataclasses_json import dataclass_json

from tams.ccs.enums import CCSJobType
from tams.ccs.types import CCSCoordinates, CCSJob, CCSUnit


@dataclass_json
@dataclass
class ContainerStack:
    name: str
    coordinates: CCSCoordinates = field(default_factory=CCSCoordinates)
    container: List[CCSUnit] = field(default_factory=list)
    height: int = 3


class TamsStorage:

    stacks = [
        ContainerStack("A1", CCSCoordinates(0, 0, 0)),
        ContainerStack("A2", CCSCoordinates(0, 2000, 0)),
        ContainerStack("A3", CCSCoordinates(0, 4000, 0)),
        ContainerStack("B1", CCSCoordinates(2000, 0, 0)),
        ContainerStack("LKW", CCSCoordinates(4000, 0, 0), height=1),
    ]

    container = [
        CCSUnit(number="Container1"),
        CCSUnit(number="Container2"),
        CCSUnit(number="Container3"),
        CCSUnit(number="Container4"),
    ]

    crane: Optional[CCSUnit] = None

    def __init__(self) -> None:
        self._add_container_to_stack("Container1", "A1")
        self._add_container_to_stack("Container2", "A3")
        self._add_container_to_stack("Container3", "A3")
        self._add_container_to_stack("Container4", "LKW")

    def export_json(self, path: Path) -> None:
        json_dict: dict[str, list[dict[str, Any]] | dict[str, Any] | str] = {
            "container": [asdict(dx) for dx in self.container],
            "stacks": [asdict(dx) for dx in self.stacks],
            "crane": "" if self.crane is None else asdict(self.crane),
        }
        path.write_text(json.dumps(json_dict))

    def import_json(self, path: Path) -> None:
        text = path.read_text()
        json_data = json.loads(text)
        self.container = [CCSUnit.from_dict(dx) for dx in json_data["container"]]  # type: ignore[attr-defined]
        self.stacks = [ContainerStack.from_dict(dx) for dx in json_data["stacks"]]  # type: ignore[attr-defined]
        self.crane = (
            None if json_data["crane"] == "" else CCSUnit.from_dict(json_data["crane"])  # type: ignore[attr-defined]
        )

    def _get_item_with_name(self, name: str) -> ContainerStack | None:
        for item in self.stacks:
            if item.name == name:
                return item
        print(f"[STORAGE][_get_item_with_name]: item not found {name=}")
        return None

    def _get_stack_by_coordinated(
        self, coordinates: CCSCoordinates
    ) -> ContainerStack | None:
        for item in self.stacks:
            if (
                item.coordinates.x == coordinates.x
                and item.coordinates.y == coordinates.y
            ):
                return item
        return None

    def _delete_container_from_stacks(self, unit: CCSUnit) -> None:
        for stack in self.stacks:
            try:
                stack.container.remove(unit)
            except ValueError:
                pass

    def _add_container_to_crane(self, unit_number: str) -> None:
        for unit in self.container:
            if unit.number == unit_number:
                if self.crane is None:
                    self._delete_container_from_stacks(unit)
                    self.crane = unit

    def _add_container_to_stack(self, unit_number: str, stack_name: str) -> str:
        stack = self._get_item_with_name(stack_name)
        if stack:
            for unit in self.container:
                if unit.number == unit_number:
                    if len(stack.container) < stack.height:
                        self._delete_container_from_stacks(unit)
                        self.crane = None
                        stack.container.append(unit)
                        return "success"
        return "failed"

    def set_stack_pos(self, stack_name: str, coordinates: CCSCoordinates) -> None:
        for stack in self.stacks:
            if stack.name == stack_name:
                stack.coordinates = coordinates
                print("[STORAGE][set_stack_pos]: {stack_name=} {coordinates=}")

    def container_moved(  # pylint: disable=too-many-return-statements
        self, job: CCSJob
    ) -> bool:
        if job.type == CCSJobType.DROP:
            if self.crane is None:
                print("[STORAGE][container_moved]: drop but crane has no unit")
                return False
                # DARF NICHT SEIN
            stack = self._get_stack_by_coordinated(job.target)
            if stack:
                self._add_container_to_stack(job.unit.number, stack.name)
                return True
            return False
        if job.type == CCSJobType.PICK:
            if self.crane is not None:
                print("[STORAGE][container_moved]: pick but crane has unit")
                return False
                # DARF NICHT SEIN
            self._add_container_to_crane(job.unit.number)
            return True
        if job.type == CCSJobType.MOVE:
            # kein einfluss auf den storage
            return True
        return False

    def get_stacks_as_json(self) -> str:
        temp_list = []
        for stack in self.stacks:
            temp_list.append(asdict(stack))
        return json.dumps(temp_list)

    def get_container_as_json(self) -> str:
        temp_list = []
        for stack in self.stacks:
            for unit in stack.container:
                unit_dict = asdict(unit)
                unit_dict["stack"] = stack.name
                temp_list.append(unit_dict)
        if self.crane is not None:
            unit_dict = asdict(self.crane)
            unit_dict["stack"] = "crane"
            temp_list.append(unit_dict)
        return json.dumps(temp_list)

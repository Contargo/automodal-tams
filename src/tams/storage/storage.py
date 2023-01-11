import itertools
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
    stacks: list[ContainerStack] = []
    crane: Optional[CCSUnit] = None
    stack_height = 2

    def __init__(self) -> None:
        pass

    def export_json(self, path: Path) -> None:
        json_dict: dict[str, list[dict[str, Any]] | dict[str, Any] | str] = {
            "stacks": [asdict(dx) for dx in self.stacks],
            "crane": "" if self.crane is None else asdict(self.crane),
        }
        path.write_text(json.dumps(json_dict))

    @property
    def container(self)-> list[CCSUnit]:
        container_lists = [stack.container for stack in self.stacks]
        container = list(itertools.chain.from_iterable(container_lists))
        container = [x for x in container if not x.is_empty()]
        if self.crane is not None and not self.crane.is_empty():
            container.append(self.crane)
        return container

    def import_json(self, path: Path) -> None:
        text = path.read_text()
        json_data = json.loads(text)
        self.stacks = [ContainerStack.from_dict(dx) for dx in json_data["stacks"]]  # type: ignore[attr-defined]
        for stack in self.stacks:
            while len(stack.container) < self.stack_height:
                stack.container.append(CCSUnit.empty())
        self.crane = (
            None if json_data["crane"] == "" else CCSUnit.from_dict(json_data["crane"])  # type: ignore[attr-defined]
        )

    def get_stack_by_name(self, name: str) -> ContainerStack | None:
        for item in self.stacks:
            if item.name == name:
                print(f"[STORAGE][get_stack_by_name] found {item=}")
                return item
        print(f"[STORAGE][get_stack_by_name] item not found {name=}")
        return None

    def get_container_by_name(self, container_number: str) -> CCSUnit | None:
        for stack in self.stacks:
            for item in stack.container:
                if item.number == container_number:
                    print(f"[STORAGE][get_container_by_name] found {item=}")
                    return item
        print(f"[STORAGE][get_container_by_name] item not found {container_number=}")
        return None

    def _get_stack_by_coordinated(
        self, coordinates: CCSCoordinates
    ) -> ContainerStack | None:
        for container in self.stacks:
            if (
                container.coordinates.x == coordinates.x
                and container.coordinates.y == coordinates.y
            ):
                return container
        return None

    def _switch_container(self, c1: CCSUnit, c2: CCSUnit) -> None:
        cc1 = c1
        cc2 = c2
        c1_found = None
        c2_found = None
        for stack in self.stacks:
            try:
                index = stack.container.index(cc1)
                c1_found = (stack, index)
            except ValueError:
                pass
            try:
                index = stack.container.index(cc2)
                c2_found = (stack, index)
            except ValueError:
                pass
        if c1_found is not None and c2_found is not None:
            c1_found[0].container[c1_found[1]] = cc2
            c2_found[0].container[c2_found[1]] = cc1
            print(f"[STORAGE][_switch_container] OK {c1_found=} '{c2_found=}'")
            return
        if c1_found is not None and self.crane == cc1:
            c1_found[0].container[c1_found[1]] = self.crane
            self.crane = cc1
            print(f"[STORAGE][_switch_container] OK crane and '{c1_found=}'")
            return
        if c2_found is not None and self.crane == cc2:
            c2_found[0].container[c2_found[1]] = self.crane
            self.crane = cc2
            print(f"[STORAGE][_switch_container] OK crane and '{c2_found=}'")
            return
        print(f"[STORAGE][_switch_container] FAILED {c1_found=} '{c2_found=}'")

    def _replace_container(self, new: CCSUnit, old: CCSUnit) -> None:
        cnew = new
        cold = old
        for stack in self.stacks:
            try:
                index = stack.container.index(cold)
                stack.container[index] = cnew
                print(
                    f"[STORAGE][_replace_container] OK {index=} '{cnew.number}', '{cold.number}'"
                )
            except ValueError:
                pass

    def _add_container_to_crane(self, container_number: str) -> None:
        for stack in self.stacks:
            for container in stack.container:
                if container.number == container_number:
                    if self.crane is None:
                        self._replace_container(container)
                        self.crane = container

    def _add_container_to_stack(self, container_number: str, stack_name: str) -> str:
        stack = self.get_stack_by_name(stack_name)
        if stack:
            container = self.get_container_by_name(container_number)
            self._delete_container_from_stacks(container)
            self.crane = None
            stack.container.append(container)
            print(
                f"[STORAGE][_add_container_to_stack] OK {container_number=} {stack_name=}"
            )
            return "success"
        print(
            f"[STORAGE][_add_container_to_stack] failed {container_number=} {stack_name=}"
        )
        return "failed"

    def _get_stack_by_container(self, container: CCSUnit):
        for stack in self.stacks:
            for c in stack.container:
                if c.number == container.number:
                    return stack

    def set_container_stack(
        self, layer: int, stack_name: str, container_number: str
    ) -> None:
        new_stack = self.get_stack_by_name(stack_name)
        new_container = self.get_container_by_name(container_number)
        if new_stack and new_container is not None:
            if not new_stack.container[layer - 1].is_empty():
                print(f"[STORAGE][set_container_stack] not empty, switch container")
                old_container = new_stack.container[layer - 1]
                self._switch_container(old_container, new_container)
                return
            else:
                self._replace_container(CCSUnit.empty(), new_container)
                for idx, _ in enumerate(new_stack.container):
                    if new_stack.container[idx].is_empty():
                        new_stack.container[idx] = new_container
                        return
        print(
            f"[STORAGE][set_container_stack] failed {layer=} {stack_name=} {container_number=}"
        )

    def set_stack_pos(self, stack_name: str, coordinates: CCSCoordinates) -> None:
        for stack in self.stacks:
            if stack.name == stack_name:
                stack.coordinates = coordinates
                print(f"[STORAGE][set_stack_pos]: {stack_name=} {coordinates=}")

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

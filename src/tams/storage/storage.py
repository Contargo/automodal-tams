import itertools
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, List, Optional

from dataclasses_json import dataclass_json

from tams.ccs.enums import CCSJobType
from tams.ccs.types import CCSCoordinates, CCSJob, CCSUnit, CCSLogicalCoordinates


@dataclass_json
@dataclass
class ContainerStack:
    name: str
    coordinates: CCSCoordinates = field(default_factory=CCSCoordinates)
    logical_coordinates: CCSLogicalCoordinates = field(default_factory=CCSLogicalCoordinates)
    container: List[CCSUnit] = field(default_factory=list)
    height: int = 3

    @property
    def count(self) -> int:
        return sum([1 for x in self.container if not x.is_empty()])

    def get_top_container(self) -> CCSUnit:
        if self.count == 0:
            return CCSUnit() # empty slot
        return self.container[self.count - 1]


class TamsStorage:
    stacks: list[ContainerStack] = []
    crane: CCSUnit = CCSUnit.empty()
    stack_height = 2
    force_ui_update = True

    @property
    def container(self) -> list[CCSUnit]:
        container_lists = [stack.container for stack in self.stacks]
        container = list(itertools.chain.from_iterable(container_lists))
        container = [x for x in container if not x.is_empty()]
        if self.crane is not None and not self.crane.is_empty():
            container.append(self.crane)
        return container

    def export_json(self, path: Path) -> None:
        json_dict: dict[str, list[dict[str, Any]] | dict[str, Any] | str] = {
            "stacks": [asdict(dx) for dx in self.stacks],
            "crane": "" if self.crane is None else asdict(self.crane),
        }
        path.write_text(json.dumps(json_dict))

    def import_json(self, path: Path) -> None:
        text = path.read_text()
        json_data = json.loads(text)
        self.stacks = [ContainerStack.from_dict(dx) for dx in json_data["stacks"]]  # type: ignore[attr-defined]
        for stack in self.stacks:
            while len(stack.container) < self.stack_height:
                stack.container.append(CCSUnit.empty())
        self.crane = (
            CCSUnit.empty() if json_data["crane"] == "" else CCSUnit.from_dict(json_data["crane"])  # type: ignore[attr-defined]
        )
        self.fix_container_layer()

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
                    print(f"[STORAGE][get_container_by_name] found in stack {item=}")
                    return item
        if container_number == self.crane.number:
            print(f"[STORAGE][get_container_by_name] found on crane {self.crane=}")
            return self.crane
        print(f"[STORAGE][get_container_by_name] item not found {container_number=}")
        return None

    def get_stack_by_coordinated(
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

    def fix_container_layer(self) -> None:
        # fix floating containers in stack
        for stack in self.stacks:
            for ix in range(self.stack_height - 1):
                if (
                    stack.container[ix].is_empty()
                    and not stack.container[ix + 1].is_empty()
                ):
                    stack.container[ix] = stack.container[ix + 1]
                    stack.container[ix + 1] = CCSUnit.empty()
                if (
                    stack.container[ix].number
                    == stack.container[ix + 1].number
                ):
                    stack.container[ix + 1] = CCSUnit.empty()

    def replace_container(self, new: CCSUnit, old: CCSUnit) -> None:
        # replaces a container in the stack with a new one.
        # old container will not be backuped!
        cnew = new
        cold = old
        for stack in self.stacks:
            try:
                index = stack.container.index(cold)
                stack.container[index] = cnew
                print(
                    f"[STORAGE][replace_container] OK {index=} '{cnew.number}', '{cold.number}'"
                )

            except ValueError:
                pass

    def set_container_stack(
        self, layer: int, stack_name: str, container_number: str
    ) -> None:
        new_container = self.get_container_by_name(container_number)
        if stack_name == "crane":
            old_container = self.crane
            for stack in self.stacks:
                for index, container in enumerate(stack.container):
                    if container.number == new_container.number:
                        stack.container[index] = old_container
            self.crane = new_container
            return
        else:
            new_stack = self.get_stack_by_name(stack_name)
            if new_container in new_stack.container:
                print(
                    f"[STORAGE][set_container_stack] container in same stack"
                )
                self.force_ui_update = True
                return
            if new_stack and new_container is not None:
                if not new_stack.container[layer - 1].is_empty():
                    print(
                        f"[STORAGE][set_container_stack] new slot not empty, switch container"
                    )
                    old_container = new_stack.container[layer - 1]
                    self._switch_container(old_container, new_container)
                elif new_container.number == self.crane.number:
                    self.crane = CCSUnit.empty()
                    new_stack.container[layer - 1] = new_container
                else:
                    print(
                        f"[STORAGE][set_container_stack] new slot is empty, move container"
                    )
                    self.replace_container(new=CCSUnit.empty(), old=new_container)
                    new_stack.container[layer - 1] = new_container
                self.fix_container_layer()
                return
        print(
            f"[STORAGE][set_container_stack] failed {layer=} {stack_name=} {container_number=}"
        )

    def set_stack_pos(self, stack_name: str, coordinates: CCSCoordinates) -> None:
        print(f"[STORAGE][set_stack_pos]: {stack_name=} {coordinates=}")
        for stack in self.stacks:
            if stack.name == stack_name:
                stack.coordinates = coordinates

    def process_job_done(  # pylint: disable=too-many-return-statements
        self, job: CCSJob
    ) -> bool:
        # Crane has job done. Now we update the stack.
        if job.type == CCSJobType.DROP:
            if self.crane.is_empty():
                print("[STORAGE][container_moved]: drop but crane has no unit")
                return False
                # DARF NICHT SEIN
            unit = self.crane
            stack = self.get_stack_by_coordinated(job.target)
            if not stack:
                return False
            for ix in range(self.stack_height):
                if stack.container[ix].is_empty():
                    stack.container[ix] = unit
                    self.crane = CCSUnit.empty()
                    return True
            return False

        if job.type == CCSJobType.PICK:
            unit = self.get_container_by_name(job.unit.number)
            if not self.crane.is_empty():
                print("[STORAGE][container_moved]: pick but crane has unit")
                return False
                # DARF NICHT SEIN
            self.replace_container(new=CCSUnit.empty(), old=unit)
            self.crane = unit
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

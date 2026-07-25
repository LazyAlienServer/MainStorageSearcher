from typing import Any, Dict, List, Optional, Tuple, TypedDict

from mcdreforged.api.all import PluginServerInterface

from main_storage_searcher.utils.block_utils import BlockDataGetter, BlockTester
from main_storage_searcher.utils.chest_finder import ChestFinder
from main_storage_searcher.utils.display_utils import rtr, rtr_minecraft
from main_storage_searcher.utils.highlight_utils import (
    highlight_block_clear,
    highlight_block_multi,
    highlight_block_multi_steps,
)
from main_storage_searcher.utils.hopper_matcher import HopperMatcher
from main_storage_searcher.utils.pos_utils import DynamicPos
from main_storage_searcher.utils.range_finder import RangeFinder
from main_storage_searcher.utils.storage_scanner import (
    MainStorageCreatingError,
    MainStorageScanner,
)


class MainStorageData(TypedDict):
    name: str
    axis: str
    range: Tuple[int, int]
    hoppers: List[Tuple[int, int, int]]
    chests: List[List[Tuple[int, int, int]]]
    items: List[List[Optional[str]]]


class MainStorageCreator:
    """Create, persist, and load a main-storage pattern."""

    def __init__(self, server: PluginServerInterface) -> None:
        self.api = BlockDataGetter(server)
        self.block_tester = BlockTester(server)
        self.server = server
        self.hopper_matcher = HopperMatcher()

    def on_info(self, server: Any, info: Any) -> None:
        self.api.on_info(server, info)
        self.block_tester.on_info(server, info)

    def create(
        self,
        pos: Tuple[int, int, int],
        name: str,
        time_step: float = 0.05,
    ) -> None:
        """Create a main-storage pattern by coordinating the storage helpers."""
        self.server.execute("gamerule sendCommandFeedback false")

        scanner = MainStorageScanner(self.server, self.api, self.hopper_matcher)
        hoppers, axis = scanner.scan_hoppers(pos, time_step)

        range_finder = RangeFinder(self.server, self.api, self.hopper_matcher)
        start, end = range_finder.find_range(hoppers, axis)

        hopper_slices = self._create_hopper_slices(hoppers, start, end, axis)
        items = self._extract_items(hopper_slices)

        chest_finder = ChestFinder(self.server, self.api, self.block_tester)
        chests = self._find_all_chests(hoppers, axis, chest_finder)

        self._save_and_notify(
            name=name,
            axis=axis,
            storage_range=(start, end),
            hoppers=hoppers,
            chests=chests,
            items=items,
            hopper_slices=hopper_slices,
        )

    def _create_hopper_slices(
        self,
        hoppers: List[Tuple[int, int, int]],
        start: int,
        end: int,
        axis: str,
    ) -> List[List[Tuple[int, int, int]]]:
        """Generate one hopper-position slice for each main-axis coordinate."""
        if axis == "x":
            return [
                [(pos[0], pos[1], coordinate) for pos in hoppers]
                for coordinate in range(start, end + 1)
            ]
        return [
            [(coordinate, pos[1], pos[2]) for pos in hoppers]
            for coordinate in range(start, end + 1)
        ]

    def _extract_items(
        self,
        hopper_slices: List[List[Tuple[int, int, int]]],
    ) -> List[List[Optional[str]]]:
        """Extract the first unnamed item from every hopper slice."""
        items: List[List[Optional[str]]] = []
        for hopper_slice in hopper_slices:
            highlight_block_multi(self.server, hopper_slice, tag="query_hopper", block="hopper")
            items.append(self.get_hopper_item(hopper_slice))
        highlight_block_clear(self.server, "query_hopper")
        highlight_block_clear(self.server, "show_hopper")
        return items

    def _find_all_chests(
        self,
        hoppers: List[Tuple[int, int, int]],
        axis: str,
        chest_finder: ChestFinder,
    ) -> List[List[Tuple[int, int, int]]]:
        """Find and complete the chest group associated with every hopper."""
        try:
            chests = []
            for pos in hoppers:
                single_chest = chest_finder.find_target_chest(DynamicPos(pos), axis)
                chests.append(
                    chest_finder.complete_chest_group(single_chest, axis)
                    if single_chest is not None
                    else []
                )
            return chests
        except Exception as error:
            self.server.logger.warning(error, exc_info=1)
            highlight_block_clear(self.server, "target_chests")
            return []

    def _save_and_notify(
        self,
        name: str,
        axis: str,
        storage_range: Tuple[int, int],
        hoppers: List[Tuple[int, int, int]],
        chests: List[List[Tuple[int, int, int]]],
        items: List[List[Optional[str]]],
        hopper_slices: List[List[Tuple[int, int, int]]],
    ) -> None:
        """Highlight discovered blocks, save the pattern, and broadcast progress."""
        highlight_block_clear(self.server, "new_hoppers")
        highlight_block_multi(
            self.server,
            hopper_slices[0] + hopper_slices[-1],
            tag="show_hopper",
            block="hopper",
        )
        self.server.broadcast(rtr("command.add.hoppers_found"))
        self.server.broadcast(rtr("command.add.items_found"))

        chest_slices = self.create_chest_slices(
            chests,
            storage_range[0],
            storage_range[1] + 1,
            axis,
        )
        highlight_block_clear(self.server, "target_chests")
        if chest_slices:
            highlight_block_multi(
                self.server,
                chest_slices[0] + chest_slices[-1],
                tag="show_chests",
                block="red_stained_glass",
            )
            highlight_block_multi_steps(
                self.server,
                chest_slices,
                block="red_stained_glass",
                end_func=(
                    lambda server, tag: (
                        highlight_block_clear(server, tag),
                        self.server.execute("gamerule sendCommandFeedback true"),
                    ),
                    (self.server, "show_chests"),
                ),
            )
        self.server.broadcast(rtr("command.add.chests_found"))

        main_storage_data: MainStorageData = {
            "name": name,
            "axis": axis,
            "range": storage_range,
            "hoppers": hoppers,
            "chests": chests,
            "items": items,
        }
        self.save_ms_data(main_storage_data, name)
        self.server.broadcast(rtr("command.add.main_storage_pattern_created", name=name))

    def create_chest_slices(
        self,
        chests: List[List[Tuple[int, int, int]]],
        start: int,
        end: int,
        axis: str,
        step: int = 1,
    ) -> List[List[Tuple[int, int, int]]]:
        """Create chest-position slices along the main storage axis."""
        if axis == "x":
            return [
                [(pos[0], pos[1], coordinate) for group in chests for pos in group]
                for coordinate in range(start, end, step)
            ]
        return [
            [(coordinate, pos[1], pos[2]) for group in chests for pos in group]
            for coordinate in range(start, end, step)
        ]

    def do_item_has_name(self, data: Dict[str, Any]) -> bool:
        tag = data.get("tag")
        display = tag.get("display") if isinstance(tag, dict) else None
        return isinstance(display, dict) and "name" in display

    def get_hopper_item(
        self,
        multi_pos: List[Tuple[int, int, int]],
    ) -> List[Optional[str]]:
        """Extract item IDs from hoppers, ignoring renamed items."""
        result: List[Optional[str]] = []
        for block_data in self.api.get_multi_block_data(multi_pos):
            data = block_data["data"]
            item_list = data.get("items", []) if data is not None else []
            if not item_list:
                result.append(None)
                continue

            first_item = item_list[0]
            if self.do_item_has_name(first_item):
                result.append(None)
            else:
                result.append(first_item["id"].replace("minecraft:", ""))
        return result

    def save_ms_data(self, ms_data: MainStorageData, name: str) -> None:
        """Persist a main-storage pattern under its named data file."""
        self.server.save_config_simple(ms_data, f"msdata-{name}.json")

    def load_ms_data(self, name: str) -> Optional[MainStorageData]:
        try:
            data: MainStorageData = self.server.load_config_simple(f"msdata-{name}.json")
            data["items"] = [
                [rtr_minecraft(item) for item in items]
                for items in data["items"]
            ]
            return data
        except FileNotFoundError:
            return None
        except Exception as error:
            raise error

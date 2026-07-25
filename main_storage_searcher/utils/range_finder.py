from typing import List, Tuple

from mcdreforged.api.all import PluginServerInterface

from main_storage_searcher.utils.block_utils import BlockDataGetter
from main_storage_searcher.utils.highlight_utils import highlight_block_timer
from main_storage_searcher.utils.hopper_matcher import HopperMatcher
from main_storage_searcher.utils.pos_utils import DynamicPos


class RangeFinder:
    """Find the start and end positions along the main storage axis."""

    def __init__(
        self,
        server: PluginServerInterface,
        api: BlockDataGetter,
        matcher: HopperMatcher,
    ) -> None:
        self.server = server
        self.api = api
        self.matcher = matcher

    def find_range(
        self,
        hoppers: List[Tuple[int, int, int]],
        axis: str,
    ) -> Tuple[int, int]:
        """Return the inclusive storage range for the detected slice axis."""
        if not hoppers:
            raise ValueError("Cannot find a storage range without hoppers.")

        hoppers = [
            pos for pos in hoppers
            if (axis == "z" and pos[0] == hoppers[0][0])
            or (axis == "x" and pos[2] == hoppers[0][2])
        ]
        if not hoppers:
            raise ValueError(f"No hoppers found for storage axis {axis!r}.")
        offset_axis = "x" if axis == "z" else "z"
        start_pos = DynamicPos(hoppers[0])
        bounds = []
        for direction in (-256, 256):
            bounds.append(self._find_boundary(start_pos, offset_axis, direction))

        start, end = sorted(bounds)
        return start, end

    def _find_boundary(
        self,
        start_pos: DynamicPos,
        offset_axis: str,
        search_step: int,
    ) -> int:
        near, remote = 0, search_step
        searched_remote = False
        while True:
            step = (remote + near) // 2
            if abs(remote - near) <= 1:
                pos = start_pos.offset_axis(step, offset_axis)
                return int(pos[2] if offset_axis == "z" else pos[0])

            pos = start_pos.offset_axis(step, offset_axis)
            highlight_block_timer(self.server, *pos, wait=0.2)
            block_data = self.api.get_block_data(*pos)
            if block_data is not None and self.matcher.is_valid_hopper(block_data["data"]):
                if not searched_remote:
                    near, step = step, step * 2
                    continue
                near = step
            else:
                remote = step
            searched_remote = True

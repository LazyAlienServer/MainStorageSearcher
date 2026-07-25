import time
from typing import List, Tuple

from mcdreforged.api.all import PluginServerInterface

from main_storage_searcher.utils.block_utils import BlockDataGetter
from main_storage_searcher.utils.display_utils import rtr
from main_storage_searcher.utils.highlight_utils import highlight_block_multi
from main_storage_searcher.utils.hopper_matcher import HopperMatcher


class MainStorageCreatingError(Exception):
    """Raised when a main-storage pattern cannot be identified."""


class MainStorageScanner:
    """Scan the player's surrounding layers for storage hoppers."""

    def __init__(
        self,
        server: PluginServerInterface,
        api: BlockDataGetter,
        matcher: HopperMatcher,
    ) -> None:
        self.server = server
        self.api = api
        self.matcher = matcher

    def scan_hoppers(
        self,
        player_pos: Tuple[int, int, int],
        time_step: float = 0.05,
    ) -> Tuple[List[Tuple[int, int, int]], str]:
        """Return discovered hoppers and the axis of their storage slice."""
        player_x, player_y, player_z = player_pos
        hoppers: List[Tuple[int, int, int]] = []
        axis = None

        self.server.broadcast(rtr("command.add.start"))
        for y in range(player_y + 15, player_y - 6, -1):
            if axis is None or axis == "x":
                z = player_z
                multi_pos = [(x, y, z) for x in range(player_x - 16, player_x + 17)]
                highlight_block_multi(self.server, multi_pos, wait=0.15)
                new_hoppers = self._find_new_hoppers(multi_pos, hoppers)
                highlight_block_multi(self.server, new_hoppers, new=False, tag="new_hoppers")
                hoppers += new_hoppers
                if 1 < len(new_hoppers) < 17:
                    axis = "x"

            if axis is None or axis == "z":
                x = player_x
                multi_pos = [(x, y, z) for z in range(player_z - 16, player_z + 17)]
                highlight_block_multi(self.server, multi_pos, wait=0.15)
                new_hoppers = self._find_new_hoppers(multi_pos, hoppers)
                highlight_block_multi(self.server, new_hoppers, new=False, tag="new_hoppers")
                hoppers += new_hoppers
                if 1 < len(new_hoppers) < 17:
                    axis = "z"

            time.sleep(time_step)

        if axis is None:
            raise MainStorageCreatingError("Cannot recognize axis of the specific slice.")
        return hoppers, axis

    def _find_new_hoppers(
        self,
        positions: List[Tuple[int, int, int]],
        hoppers: List[Tuple[int, int, int]],
    ) -> List[Tuple[int, int, int]]:
        """Get valid, previously undiscovered hopper positions."""
        new_hoppers = []
        for block_data in self.api.get_multi_block_data(positions):
            data = block_data["data"]
            pos = tuple(int(coordinate) for coordinate in block_data["pos"])
            if self.matcher.is_valid_hopper(data) and not self._is_covered(pos, hoppers):
                new_hoppers.append(pos)
        return new_hoppers

    @staticmethod
    def _is_covered(
        pos: Tuple[int, int, int],
        hoppers: List[Tuple[int, int, int]],
    ) -> bool:
        """Return whether a position is covered by an existing hopper."""
        return (pos[0], pos[1] + 1, pos[2]) in hoppers or pos in hoppers

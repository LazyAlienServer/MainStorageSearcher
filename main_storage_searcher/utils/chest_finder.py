from typing import List, Optional, Tuple

from mcdreforged.api.all import PluginServerInterface

from main_storage_searcher.utils.block_utils import BlockDataGetter, BlockTester
from main_storage_searcher.utils.highlight_utils import (
    highlight_block,
    highlight_block_timer,
)
from main_storage_searcher.utils.pos_utils import DynamicPos, opposite_facing, rotate_facing


class ChestFinder:
    """Locate and complete chest groups connected to storage hoppers."""

    def __init__(
        self,
        server: PluginServerInterface,
        api: BlockDataGetter,
        block_tester: BlockTester,
    ) -> None:
        self.server = server
        self.api = api
        self.block_tester = block_tester

    def find_target_chest(
        self,
        pos: DynamicPos,
        axis: str,
        hopper: bool = True,
        source_facing: Optional[str] = None,
    ) -> Optional[Tuple[int, int, int]]:
        """Recursively search for a chest through hopper/dropper chains."""
        highlight_block_timer(self.server, *pos, wait=0.5)
        if hopper:
            facings = ["down", "west", "east"] if axis == "x" else ["down", "north", "south"]
            for facing in facings:
                if self.block_tester.test_block(*pos, block=f"hopper[facing={facing}]"):
                    if source_facing == facing:
                        self.server.logger.warning(
                            "Hopper[facing=%s] at %s has an opposite facing with its previous hopper.",
                            facing,
                            pos,
                        )
                        return None
                    result = self.find_target_chest(
                        pos.offset_facing(1, facing),
                        axis,
                        hopper=False,
                        source_facing=opposite_facing(facing),
                    )
                    if result is not None:
                        return result
                    break
            else:
                self.server.logger.warning(
                    "Hopper at %s does not match any facing with slice axis = %s",
                    pos,
                    axis,
                )
                return None

            if facing != "down":
                new_pos = pos.offset_facing(1, "down")
                if self.block_tester.test_block(*new_pos, block="hopper"):
                    return self.find_target_chest(new_pos, axis, source_facing="up")
            return None

        block_data = self.api.get_block_data(*pos, path="id")
        if block_data is None:
            return None

        block_id = block_data["data"]
        if block_id == "minecraft:hopper":
            return self.find_target_chest(pos, axis, source_facing=source_facing)
        if block_id == "minecraft:dropper":
            facings = ["up", "west", "east", "down"] if axis == "x" else ["up", "north", "south", "down"]
            for facing in facings:
                if facing == source_facing:
                    continue
                if self.block_tester.test_block(*pos, block=f"dropper[facing={facing}]"):
                    return self.find_target_chest(
                        pos.offset_facing(1, facing),
                        axis,
                        hopper=False,
                        source_facing=opposite_facing(facing),
                    )
            return None
        if block_id == "minecraft:chest":
            highlight_block(self.server, *pos, tag="target_chests", new=False)
            return pos
        return self.find_target_chest(
            pos.offset_facing(1, "down"),
            axis,
            hopper=False,
            source_facing="up",
        )

    def complete_chest_group(
        self,
        pos: Tuple[int, int, int],
        axis: str,
    ) -> List[Tuple[int, int, int]]:
        """Return all blocks belonging to a single or double chest."""
        dynamic_pos = DynamicPos(pos)
        facings = ["north", "south"] if axis == "x" else ["west", "east"]
        for facing in facings:
            if not self.block_tester.test_block(*dynamic_pos, block=f"chest[facing={facing}]"):
                continue
            for chest_type in ["left", "right", "single"]:
                if self.block_tester.test_block(*dynamic_pos, block=f"chest[type={chest_type}]"):
                    if chest_type == "single":
                        return [dynamic_pos]
                    other = dynamic_pos.offset_facing(
                        1,
                        opposite_facing(rotate_facing(facing, chest_type)),
                    )
                    return [dynamic_pos, other]
        return []

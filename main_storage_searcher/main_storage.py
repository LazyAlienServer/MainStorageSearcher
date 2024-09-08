from typing import Tuple
import time
from main_storage_searcher.utils.block_utils import BlockDataGetter, BlockTester
from main_storage_searcher.utils.highlight_utils import highlight_block, highlight_block_multi, highlight_block_clear, highlight_block_timer
from main_storage_searcher.utils.pos_utils import DynamicPos, opposite_facing
# 帮助你在全物品中寻找指定物品

class MainStorage:

    def __init__(self, server) -> None:
        self.api = BlockDataGetter(server)
        self.block_tester = BlockTester(server)
        self.server = server

    def on_info(self, server, info):
        self.api.on_info(server, info)
        self.block_tester.on_info(server, info)

    def add(self, pos: Tuple[int, int, int], time_step=0.05):
        player_x, player_y, player_z = pos
        hoppers = []
        match = lambda block_data: block_data["id"] == "minecraft:hopper" and len(block_data["Items"]) == 5
        is_covered = lambda pos: (pos[0], pos[1]+1, pos[2]) in hoppers or pos in hoppers
        axis = None
        for y in range(player_y+15, player_y-6, -1):
            if axis is None or axis == "x":
                z = player_z
                multi_pos = [(x, y, z) for x in range(player_x-16, player_x+17)]
                highlight_block_multi(self.server, multi_pos, wait=0.15)
                new_hoppers = [block_data["pos"] for block_data in self.api.get_multi_block_data(multi_pos) if match(block_data["data"]) and not is_covered(block_data["pos"])]
                highlight_block_multi(self.server, new_hoppers, tag="new_hoppers")
                hoppers += new_hoppers
                if 1 < len(new_hoppers) < 17:
                    axis = "x"
            if axis is None or axis == "z":
                x = player_x
                multi_pos = [(x, y, z) for z in range(player_z-16, player_z+17)]
                highlight_block_multi(self.server, multi_pos, wait=0.15)
                new_hoppers = [block_data["pos"] for block_data in self.api.get_multi_block_data(multi_pos) if match(block_data["data"]) and not is_covered(block_data["pos"])]
                highlight_block_multi(self.server, new_hoppers, tag="new_hoppers")
                hoppers += new_hoppers
                if 1 < len(new_hoppers) < 17:
                    axis = "z"
            time.sleep(time_step)
        if not axis:
            return
        hoppers = [i for i in hoppers if (axis == "z" and i[0] == player_x) or (axis == "x" and i[2] == player_z)]
        offset = (lambda x, y, z, step : (x, y, z + step)) if axis == "x" else (lambda x, y, z, step : (x + step, y, z))
        start = end = None
        self.server.logger.info(hoppers)
        for step in [-256,256]:
            near, remote = 0, step
            flag = False
            for i in range(20):
                step = (remote+near)//2
                if abs(remote-near) <= 1:
                    pos = offset(*hoppers[0], near)
                    break
                pos = offset(*hoppers[0], int(step))
                highlight_block_timer(self.server, *pos, wait=0.2)
                self.server.logger.info((near, remote, step))
                block_data = self.api.get_block_data(*pos)
                if block_data is not None and match(block_data["data"]):
                    if not flag:
                        near, step = step, step*2
                        continue
                    near = step
                else:
                    remote = step
                if not flag:
                    flag = True
            else:
                return
            if start:
                end = int(pos[2] if axis == "x" else pos[0])
            else:
                start = int(pos[2] if axis == "x" else pos[0])
        hopper_columns = [[(pos[0], pos[1], z) for z in range(start, end+1)] for pos in hoppers] if axis == "x" else [[(x, pos[1], pos[2]) for x in range(start, end+1)] for pos in hoppers]
        highlight_block_clear(self.server)
        for columns in hopper_columns:
            highlight_block_multi(self.server, columns, block="hopper", wait=3)
        highlight_block_clear(self.server, "new_hoppers")
        
        chests = []
        for pos in hoppers:
            chests.append(self.search_target_chest(DynamicPos(pos), axis))
        
        chest_columns = [[(pos[0], pos[1], z) for z in range(start, end+1)] for pos in chests] if axis == "x" else [[(x, pos[1], pos[2]) for x in range(start, end+1)] for pos in chests]
        self.server.logger.info("chest_columns")
        self.server.logger.info(chest_columns)
        highlight_block_clear(self.server)
        for columns in chest_columns:
            highlight_block_multi(self.server, columns, block="red_stained_glass", wait=5)
    
    def search_target_chest(self, pos: DynamicPos[int, int, int], axis: str, hopper: bool = True, source_facing = None) -> Tuple[int, int, int]:
        highlight_block_timer(self.server, *pos, wait=0.5)
        if hopper:
            facings =  ["down", "west", "east"] if axis == "x" else ["down", "north","south"]
            if source_facing in facings:
                return
            for facing in facings:
                if self.block_tester.test_block(*pos, block=f"hopper[facing={facing}]"): 
                    if (result := self.search_target_chest(pos.offset_facing(1, facing), axis, hopper=False, source_facing=opposite_facing(facing))) is not None: # move to the facing block
                        return result
                    break
            else:
                return
            if facing != "down" and self.block_tester.test_block(*(new_pos := pos.offset_facing(1, "down")), block="hopper"): # if there is a hopper under this hopper, move to
                return self.search_target_chest(new_pos, axis, source_facing=opposite_facing(facing))

        elif (block_id := self.api.get_block_data(*pos, path="id")) is not None:
            block_id = block_id["data"]
            if block_id == "minecraft:hopper":
                return self.search_target_chest(pos, axis, source_facing=source_facing)
            elif block_id == "minecraft:dropper":
                for facing in ["up", "west", "east", "down"] if axis == "x" else ["up", "north", "south", "down"]:
                    if facing == source_facing:
                        continue
                    if self.block_tester.test_block(*pos, block=f"dropper[facing={facing}]"):
                        return self.search_target_chest(pos.offset_facing(1, facing), axis, hopper=False, source_facing=opposite_facing(facing))
            elif block_id == "minecraft:chest":
                highlight_block_timer(self.server, *pos, wait=5)
                return pos
            else:
                return self.search_target_chest(pos.offset_facing(1, "down"), axis, hopper=False, source_facing="up")
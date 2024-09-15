from typing import Tuple, List, TypedDict
import time, difflib
from main_storage_searcher.utils.block_utils import BlockDataGetter, BlockTester
from main_storage_searcher.utils.highlight_utils import *
from main_storage_searcher.utils.display_utils import rtr, rtr_minecraft
from main_storage_searcher.utils.pos_utils import DynamicPos, opposite_facing, rotate_facing
from main_storage_searcher.utils.config_utils import Config
from mcdreforged.api.all import PluginServerInterface, CommandSource, CommandContext, new_thread, SimpleCommandBuilder, Text, Info
from minecraft_data_api import get_player_coordinate


class MainStorageData(TypedDict):
    name: str
    axis: str
    range: Tuple[int, int]
    hoppers: List[Tuple[int, int, int]]
    chests: List[Tuple[Tuple[int, int, int]]]
    items: List[List[str]]

class MainStorageManager:

    def __init__(self, server: PluginServerInterface, config: Config) -> None:
        self.has_task = False
        self.ms_creator = MainStorageCreator(server)
        self.current_ms : MainStorageData = None
        self.server = server
        self.config = config

        builder = SimpleCommandBuilder()
        builder.arg("name", Text)
        builder.command("!!ms create <name>", self.create)
        builder.command("!!ms load <name>", self.load)
        builder.command("!!ms unload", self.unlaod)
        builder.command("!!ms reload <name>", self.reload)
        builder.command("!!ms search <name>", self.search)
        builder.register(server)
    
    def on_info(self, server, info: Info):
        if self.has_task and not info.is_player:
            self.ms_creator.on_info(server, info)

    @new_thread("ms-creator")
    def create(self, source: CommandSource, context: CommandContext):
        if not source.is_player:
            return
        if not source.has_permission(self.config.permission.create):
            source.reply(rtr("command.permission_denied"))
            return
        if self.has_task:
            source.reply(rtr("command.add.has_task"))
            return
        try:
            self.has_task = True
            pos = get_player_coordinate(source.player)
            self.ms_creator.create((int(pos.x), int(pos.y), int(pos.z-1)), context["name"])
            self.has_task = False
        except Exception as e:
            self.has_task = False
            source.reply(rtr("command.add.error", e=e))
            raise e
    
    def load(self, source: CommandSource, context: CommandContext):
        if not source.has_permission(self.config.permission.load):
            source.reply(rtr("command.permission_denied"))
            return
        name = context["name"]
        if self.current_ms and self.current_ms["name"] == name:
            source.reply(rtr("command.load.exist", name=name))
            return
        self.current_ms = self.ms_creator.load_ms_data(name)
        if self.current_ms:
            source.reply(rtr("command.load.success", name=name))
            return
        source.reply(rtr("command.load.notfound", name=name))
    
    def reload(self, source: CommandSource, context: CommandContext):
        if not source.has_permission(self.config.permission.reload):
            source.reply(rtr("command.permission_denied"))
            return
        if not self.current_ms:
            source.reply(rtr("nodata"))
            return
        self.current_ms = self.ms_creator.load_ms_data(self.current_ms["name"])
        source.reply(rtr("command.reload.success", name=context["name"]))
    
    def unlaod(self, source: CommandSource, context: CommandContext):
        if not source.has_permission(self.config.permission.unload):
            source.reply(rtr("command.permission_denied"))
            return
        if not self.current_ms:
            source.reply(rtr("nodata"))
            return
        self.current_ms = None
        source.reply(rtr("command.unload.success", name=context["name"]))
    
    @new_thread("ms-searcher")
    def search(self, source: CommandSource, context: CommandContext):
        if not source.has_permission(self.config.permission.search):
            source.reply(rtr("command.permission_denied"))
            return
        current_ms = self.current_ms
        if not current_ms:
            source.reply(rtr("nodata"))
            return
        name = context["name"]
        target = []
        best = {"similarity":-1, "pos":(0, 0), "item":""}
        for slice_index, items in enumerate(current_ms["items"]):
            for chest_index, item in enumerate(items):
                if item is not None and ((similarity := difflib.SequenceMatcher(None, name, item).ratio()) >= 0.5 or name in item):
                    if similarity > best["similarity"]:
                        best["similarity"] = similarity
                        best["pos"] = (slice_index, chest_index)
                        best["item"] = item
                    target.append(item)
        if best["similarity"] < 0:
            source.reply(rtr("command.search.nodata"))
            return
        slice_pos = current_ms["range"][0] + best["pos"][0]
        chests = current_ms["chests"][best["pos"][1]]
        main_axis = "x" if self.current_ms["axis"] == "z" else "z"
        chest_pos = (sum(DynamicPos(chest) for chest in chests)/len(chests)).set_axis(slice_pos, main_axis)
        highlight_block_by_entity(self.server, *chest_pos, duration=12)
        source.reply(rtr("command.search.best", item=best["item"]))
        prompt_slice = [DynamicPos(pos).set_axis(slice_pos, main_axis) for chest in current_ms["chests"] for pos in chest]
        for i in range(5):
            highlight_block_multi(self.server, prompt_slice, block="red_stained_glass", wait=0.3)
            time.sleep(2)
    

class MainStorageCreator:

    def __init__(self, server: PluginServerInterface) -> None:
        self.api = BlockDataGetter(server)
        self.block_tester = BlockTester(server)
        self.server = server

    def on_info(self, server, info):
        self.api.on_info(server, info)
        self.block_tester.on_info(server, info)

    def create(self, pos: Tuple[int, int, int], name, time_step=0.05):
        self.server.execute("gamerule sendCommandFeedback false")
        main_storage_data: MainStorageData = {"name": name}
        player_x, player_y, player_z = pos

        # query hoppers from y+16 to y-5, from x-16 to x+16, from y-16 to y+16
        hoppers = []
        match = lambda block_data: block_data["id"] == "minecraft:hopper" and len(block_data["Items"]) == 5 and block_data["Items"][0]["Count"] < 64
        is_covered = lambda pos: (pos[0], pos[1]+1, pos[2]) in hoppers or pos in hoppers
        axis = None # the axis of slice, not main axis
        self.server.broadcast(rtr("command.add.start"))
        for y in range(player_y+15, player_y-6, -1):
            if axis is None or axis == "x":
                z = player_z
                multi_pos = [(x, y, z) for x in range(player_x-16, player_x+17)]
                highlight_block_multi(self.server, multi_pos, wait=0.15)
                new_hoppers = [block_data["pos"] for block_data in self.api.get_multi_block_data(multi_pos) if match(block_data["data"]) and not is_covered(block_data["pos"])]
                highlight_block_multi(self.server, new_hoppers, new=False, tag="new_hoppers")
                hoppers += new_hoppers
                if 1 < len(new_hoppers) < 17:
                    axis = "x"
            if axis is None or axis == "z":
                x = player_x
                multi_pos = [(x, y, z) for z in range(player_z-16, player_z+17)]
                highlight_block_multi(self.server, multi_pos, wait=0.15)
                new_hoppers = [block_data["pos"] for block_data in self.api.get_multi_block_data(multi_pos) if match(block_data["data"]) and not is_covered(block_data["pos"])]
                highlight_block_multi(self.server, new_hoppers, new=False, tag="new_hoppers")
                hoppers += new_hoppers
                if 1 < len(new_hoppers) < 17:
                    axis = "z"
            time.sleep(time_step)
        if not axis:
            return
        main_storage_data["axis"] = axis

        # query start & end of the main axis
        hoppers = [i for i in hoppers if (axis == "z" and i[0] == player_x) or (axis == "x" and i[2] == player_z)]
        offset_axis = "x" if axis == "z" else "z"
        start = end = None
        start_pos = DynamicPos(hoppers[0])
        for step in [-256,256]:
            near, remote = 0, step
            flag = False
            for i in range(20):
                step = (remote+near)//2
                if abs(remote-near) <= 1:
                    pos = start_pos.offset_axis(step, offset_axis)
                    break
                pos = start_pos.offset_axis(step, offset_axis)
                highlight_block_timer(self.server, *pos, wait=0.2)
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
        hopper_slices = [[(pos[0], pos[1], z) for pos in hoppers] for z in range(start, end+1)] if axis == "x" \
            else [[(x, pos[1], pos[2]) for pos in hoppers] for x in range(start, end+1)]
        main_storage_data["range"] = (start, end)
        main_storage_data["hoppers"] = hoppers
        highlight_block_clear(self.server, "new_hoppers")
        highlight_block_multi(self.server, hopper_slices[0]+hopper_slices[-1], tag="show_hopper", block="hopper")
        self.server.broadcast(rtr("command.add.hoppers_found"))

        # query items
        items = []
        for hopper_slice in hopper_slices:
            highlight_block_multi(self.server, hopper_slice, tag="query_hopper", block="hopper")
            items.append(self.get_hopper_item(hopper_slice))
        highlight_block_clear(self.server, "query_hopper")
        highlight_block_clear(self.server, "show_hopper")
        main_storage_data["items"] = items
        self.server.broadcast(rtr("command.add.items_found"))
        
        # query chests
        chests = []
        for pos in hoppers:
            chests.append(self.complete_chest(single_chest, axis) if (single_chest := self.search_target_chest(DynamicPos(pos), axis), axis) is not None else [])
        main_storage_data["chests"] = chests
        chest_slices = self.create_chest_slices(chests, start, end+1, axis)
        highlight_block_clear(self.server, "target_chests")
        highlight_block_multi(self.server, chest_slices[0]+chest_slices[-1], tag="show_chests",block="red_stained_glass")
        highlight_block_multi_steps(self.server, chest_slices, block="red_stained_glass", end_func=(lambda server, tag: (highlight_block_clear(server, tag), self.server.execute("gamerule sendCommandFeedBack true")), (self.server, "show_chests")))
        self.server.broadcast(rtr("command.add.chests_found"))

        # save
        self.save_ms_data(main_storage_data, name)
        self.server.broadcast(rtr("command.add.main_storage_pattern_created", name=name))
    

    def create_chest_slices(self, chests, start, end, axis, step=1):
        return [[(pos[0], pos[1], z) for group_pos in chests for pos in group_pos] for z in range(start, end, step)] if axis == "x" \
            else [[(x, pos[1], pos[2]) for group_pos in chests for pos in group_pos] for x in range(start, end, step)]


    def search_target_chest(self, pos: DynamicPos[int, int, int], axis: str, hopper: bool = True, source_facing = None) -> Tuple[int, int, int]:
        highlight_block_timer(self.server, *pos, wait=0.5)
        if hopper:
            facings =  ["down", "west", "east"] if axis == "x" else ["down", "north","south"]
            for facing in facings:
                if self.block_tester.test_block(*pos, block=f"hopper[facing={facing}]"): 
                    if source_facing == facing:
                        return
                    if (result := self.search_target_chest(pos.offset_facing(1, facing), axis, hopper=False, source_facing=opposite_facing(facing))) is not None: # move to the facing block
                        return result
                    break
            else:
                return
            if facing != "down" and self.block_tester.test_block(*(new_pos := pos.offset_facing(1, "down")), block="hopper"): # if there is a hopper under this hopper, move to
                return self.search_target_chest(new_pos, axis, source_facing="up")

        elif (block_id := self.api.get_block_data(*pos, path="id")) is not None:
            block_id = block_id["data"]
            if block_id == "minecraft:hopper":
                return self.search_target_chest(pos, axis, source_facing=source_facing)
            if block_id == "minecraft:dropper":
                for facing in ["up", "west", "east", "down"] if axis == "x" else ["up", "north", "south", "down"]:
                    if facing == source_facing:
                        continue
                    if self.block_tester.test_block(*pos, block=f"dropper[facing={facing}]"):
                        return self.search_target_chest(pos.offset_facing(1, facing), axis, hopper=False, source_facing=opposite_facing(facing))
            elif block_id == "minecraft:chest":
                highlight_block(self.server, *pos, tag="target_chests", new=False)
                return pos
            else:
                return self.search_target_chest(pos.offset_facing(1, "down"), axis, hopper=False, source_facing="up")
    

    def complete_chest(self, pos: Tuple[int, int, int], axis: str) -> List[Tuple[int, int, int]]:
        pos = DynamicPos(pos)
        for facing in ["north", "south"] if axis == "x" else ["west", "east"]:
            if self.block_tester.test_block(*pos, block=f"chest[facing={facing}]"):
                for type in ["left", "right", "single"]:
                    if self.block_tester.test_block(*pos, block=f"chest[type={type}]"):
                        pos_group = [pos, pos.offset_facing(1, opposite_facing(rotate_facing(facing, type)))] if type != "single" else [pos]
                        return pos_group


    def do_item_has_name(self, data):
        return "tag" in data.keys() and "display" in (tag := data["tag"]).keys() and "Name" in tag["display"].keys()


    def get_hopper_item(self, multi_pos: List[Tuple[int, int, int]]):
        return [first_item["id"].replace("minecraft:","") if (data := block_data["data"]) is not None and not self.do_item_has_name(first_item := data["Items"][0]) else None for block_data in self.api.get_multi_block_data(multi_pos)]
    

    def save_ms_data(self, ms_data: MainStorageData, name: str):
        self.server.save_config_simple(ms_data, f"msdata-{name}.json")
    

    def load_ms_data(self, name: str) -> MainStorageData:
        try:
            data : MainStorageData = self.server.load_config_simple(f"msdata-{name}.json")
            data["items"] = [[rtr_minecraft(item) for item in items] for items in data["items"]]
            return data
        except FileNotFoundError:
            return None
        except Exception as e:
            raise e
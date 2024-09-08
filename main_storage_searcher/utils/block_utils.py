import queue, re
from mcdreforged.api.all import ServerInterface, Info
from minecraft_data_api.json_parser import MinecraftJsonParser
from typing import Tuple, List, TypedDict
from abc import ABC, abstractmethod


class AbstractDataGetter(ABC):

    def __init__(self, server: ServerInterface) -> None:
        self.server = server
        self.queue = queue.Queue()
        self.task_count = 0
        self.pattern: re.Pattern
    
    @abstractmethod
    def on_info(self, server: ServerInterface, info: Info):
        ...

class BlockData(TypedDict):
    pos: Tuple[int, int, int]
    data: dict

class BlockDataGetter(AbstractDataGetter):

    def __init__(self, server: ServerInterface) -> None:
        super().__init__(server)
        self.pattern = re.compile(r"^(?P<x>-?[0-9]+), (?P<y>-?[0-9]+), (?P<z>-?[0-9]+) has the following block data: (?P<data>.+)$")

    def get_block_data(self, x, y, z, path = None) -> BlockData:
        path = " "+path if path else ""
        self.task_count += 1
        self.server.execute(f"data get block {int(x)} {int(y)} {int(z)}"+path)
        return self.queue.get(timeout=5)

    def get_multi_block_data(self, multi_pos: List[Tuple[int, int, int]], path = None) -> List[BlockData]:
        multi_block_data = []
        for pos in multi_pos:
            x, y, z = pos
            self.task_count += 1
            self.server.execute(f"data get block {int(x)} {int(y)} {int(z)}")
        for i in range(len(multi_pos)):
            if (result := self.queue.get(timeout=5)):
                multi_block_data.append(result)
        return multi_block_data

    def on_info(self, server: ServerInterface, info: Info):
        if not info.is_from_server or self.task_count == 0:
            return
        if (result := self.pattern.match(info.content)) is not None:
            self.queue.put({"pos":(float(result.group("x")), float(result.group("y")), float(result.group("z"))),"data":MinecraftJsonParser().convert_minecraft_json(result.group("data"))})
            self.task_count -= 1
        elif info.content in ["That position is not loaded", "The target block is not a block entity"]:
            self.queue.put(None)
            self.task_count -= 1

class BlockTester(AbstractDataGetter):
    
    def __init__(self, server: ServerInterface) -> None:
        super().__init__(server)
        self.pattern = re.compile(r"^Test (?P<status>(?:passed)|(?:failed))$")
    
    def test_block(self, x, y, z, block):
        self.task_count += 1
        self.server.execute(f"execute if block {int(x)} {int(y)} {int(z)} {block}")
        # self.server.logger.info(f"execute if block {int(x)} {int(y)} {int(z)} {block}")
        return self.queue.get(timeout=5)
    
    def on_info(self, server: ServerInterface, info: Info):
        if not info.is_from_server or self.task_count == 0:
            return
        if (result := self.pattern.match(info.content)) is not None:
            self.queue.put(result.group("status") == "passed")
            self.task_count -= 1
            # self.server.logger.info(result.group("status") == "passed")


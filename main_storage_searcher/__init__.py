from mcdreforged.api.all import PluginServerInterface, ServerInterface, SimpleCommandBuilder, Info, CommandSource, CommandContext, new_thread
from main_storage_searcher.main_storage import MainStorage
from minecraft_data_api import get_player_coordinate
from minecraft_data_api.json_parser import MinecraftJsonParser

def on_load(server: PluginServerInterface, prev_module):
    global ms
    ms = MainStorage(server)
    builder = SimpleCommandBuilder()
    builder.command("!!ms add", add)
    builder.register(server)

def on_info(server: ServerInterface, info: Info):
    ms.on_info(server, info)

@new_thread("ms-add")
def add(source: CommandSource, context: CommandContext):
    if not source.is_player:
        return
    pos = get_player_coordinate(source.player)
    ms.add((int(pos.x), int(pos.y), int(pos.z)))
from mcdreforged.api.all import PluginServerInterface, ServerInterface, SimpleCommandBuilder, Info, CommandSource, CommandContext, new_thread, Text
from main_storage_searcher.main_storage import MainStorage
from minecraft_data_api import get_player_coordinate
from minecraft_data_api.json_parser import MinecraftJsonParser

def on_load(server: PluginServerInterface, prev_module):
    global ms
    ms = MainStorage(server)
    builder = SimpleCommandBuilder()
    builder.arg("name", Text)
    builder.command("!!ms init <name>", init)
    builder.register(server)

def on_info(server: ServerInterface, info: Info):
    ms.on_info(server, info)

@new_thread("ms-add")
def init(source: CommandSource, context: CommandContext):
    if not source.is_player:
        return
    pos = get_player_coordinate(source.player)
    ms.init((int(pos.x), int(pos.y), int(pos.z-1)), name=context["name"])
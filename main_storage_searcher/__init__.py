from mcdreforged.api.all import PluginServerInterface, ServerInterface, Info
from main_storage_searcher.main_storage import MainStorageManager


def on_load(server: PluginServerInterface, prev_module):
    global ms
    ms = MainStorageManager(server)

def on_info(server: ServerInterface, info: Info):
    ms.on_info(server, info)
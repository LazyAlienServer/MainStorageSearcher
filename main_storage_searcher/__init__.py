from mcdreforged.api.all import PluginServerInterface, ServerInterface, Info
from main_storage_searcher.main_storage import MainStorageManager
from main_storage_searcher.utils.config_utils import Config


def on_load(server: PluginServerInterface, prev_module):
    global ms
    config = server.load_config_simple("config.json", target_class=Config)
    ms = MainStorageManager(server, config)

def on_info(server: ServerInterface, info: Info):
    ms.on_info(server, info)
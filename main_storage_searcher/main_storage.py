import time, difflib, os, re
from main_storage_searcher.utils.highlight_utils import *
from main_storage_searcher.utils.display_utils import rtr, rtr_minecraft, help_msg
from main_storage_searcher.utils.pos_utils import DynamicPos
from main_storage_searcher.utils.config_utils import Config
from main_storage_searcher.utils.main_storage_utils import MainStorageCreator, MainStorageData
from mcdreforged.api.all import PluginServerInterface, CommandSource, CommandContext, new_thread, SimpleCommandBuilder, Text, Number, Info, RTextList, RText, RAction
from minecraft_data_api import get_player_coordinate


class MainStorageManager:

    def __init__(self, server: PluginServerInterface, config: Config) -> None:
        self.has_task = False
        self.ms_creator = MainStorageCreator(server)
        self.current_ms : MainStorageData = self.ms_creator.load_ms_data(default) if (default := config.main_storage.default) is not None else None 
        self.server = server
        self.config = config
        self.highlight_flag = None

        builder = SimpleCommandBuilder()
        builder.arg("name", Text)
        builder.command("!!ms", lambda source, context: source.reply(RTextList(*[rtr("command.help.info", False)]+["\n"+help_msg(command) for command in ["create", "search", "list", "load", "unload", "reload", "setdefault"]])))
        builder.command("!!ms create <name>", self.create)
        builder.command("!!ms create", lambda source, context: source.reply(help_msg("create", "<name> ")))
        builder.command("!!ms search <name>", self.search)
        builder.command("!!ms search", lambda source, context: source.reply(help_msg("search", "<name> ")))
        builder.command("!!ms list", self.list_ms)
        builder.command("!!ms load <name>", self.load)
        builder.command("!!ms load", lambda source, context: source.reply(help_msg("load", "<name> ")))
        builder.command("!!ms unload", self.unlaod)
        builder.command("!!ms reload", self.reload)
        builder.command("!!ms setdefault", self.set_default)
        builder.arg("x", Number)
        builder.arg("y", Number)
        builder.command("!!ms highlight <name> <x> <y>", self.highlight)
        builder.register(server)

        server.register_help_message("!!ms", rtr("command.help.basic", False))
    
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
        name = self.current_ms["name"]
        self.current_ms = self.ms_creator.load_ms_data(name)
        source.reply(rtr("command.reload.success", name=name))
    
    def unlaod(self, source: CommandSource, context: CommandContext):
        if not source.has_permission(self.config.permission.unload):
            source.reply(rtr("command.permission_denied"))
            return
        if not self.current_ms:
            source.reply(rtr("nodata"))
            return
        name=self.current_ms["name"]
        self.current_ms = None
        source.reply(rtr("command.unload.success", name=name))
    
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
        target_index = 0
        best = {"similarity":-1, "pos":(0, 0), "item":"", "target_index":-1}
        for slice_index, items in enumerate(current_ms["items"]):
            for chest_index, item in enumerate(items):
                if item is not None and ((similarity := difflib.SequenceMatcher(None, name, item).ratio()) >= 0.5 or name in item):
                    if similarity > best["similarity"]:
                        best["similarity"] = similarity
                        best["pos"] = (slice_index, chest_index)
                        best["item"] = item
                        best["target_index"] = target_index
                    target.append((item, (slice_index, chest_index)))
                    target_index += 1
        if best["similarity"] < 0:
            source.reply(rtr("command.search.nodata"))
            return
        target.pop(best["target_index"])
        source.reply(rtr("command.search.best", item=best["item"]))
        source.reply(RTextList(rtr("command.search.others_1"), *[RText(f"§3{item} ").c(RAction.run_command, f"!!ms highlight {item} {pos[0]} {pos[1]}") for item, pos in target], rtr("command.search.others_2", False)))
        self.highlight_handler(best["pos"][0], best["pos"][1], best["item"])

    
    def highlight(self, source: CommandSource, context: CommandContext):
        if not source.has_permission(self.config.permission.highlight):
            source.reply(rtr("command.permission_denied"))
            return
        current_ms = self.current_ms
        if not current_ms:
            source.reply(rtr("nodata"))
            return
        source.reply(rtr("command.highlight.success", item=context["name"]))
        self.highlight_handler(context["x"], context["y"], context["name"])
        
    
    def highlight_handler(self, slice_index, chest_index, item=None):
        self.highlight_flag = item
        current_ms = self.current_ms
        slice_pos = current_ms["range"][0] + slice_index
        chests = current_ms["chests"][chest_index]
        main_axis = "x" if self.current_ms["axis"] == "z" else "z"
        chest_pos = (sum(DynamicPos(chest) for chest in chests)/len(chests)).set_axis(slice_pos, main_axis)
        highlight_block_by_entity(self.server, *chest_pos, duration=12)
        prompt_slice = [DynamicPos(pos).set_axis(slice_pos, main_axis) for chest in current_ms["chests"] for pos in chest]
        for i in range(5):
            highlight_block_multi(self.server, prompt_slice, block="red_stained_glass", wait=0.3)
            time.sleep(2)
            if self.highlight_flag != item:
                break
    

    def set_default(self, source: CommandSource, context: CommandContext):
        if not source.has_permission(self.config.permission.setdefault):
            source.reply(rtr("command.permission_denied"))
            return
        current_ms = self.current_ms
        mscfg = self.config.main_storage
        
        if not current_ms:
            if mscfg.default:
                mscfg.default = None
                self.server.save_config_simple(self.config, "config.json")
                source.reply(rtr("command.setdefault.unset"))
            else:
                source.reply(rtr("command.setdefault.exist_unset"))
            return
        name = current_ms["name"]
        if mscfg.default != name:
            mscfg.default = name
            self.server.save_config_simple(self.config, "config.json")
            source.reply(rtr("command.setdefault.success", name=name))
        else:
            source.reply(rtr("command.setdefault.exist", name=name))
    
    def list_ms(self, source: CommandSource, context: CommandContext):
        if not source.has_permission(self.config.permission.list):
            source.reply(rtr("command.permission_denied"))
            return
        current_ms = self.current_ms["name"] if self.current_ms else None
        default = self.config.main_storage.default
        source.reply(rtr("command.list.info", False))
        flag = False
        for file in os.listdir(self.server.get_data_folder()):
            if (result := re.fullmatch(r"msdata-(?P<name>.+)\.json", file)) is not None:
                msg = ms_name = result.group("name")
                if ms_name == current_ms and ms_name == default:
                    msg = rtr("command.list.current_and_default", False, name=ms_name)
                elif ms_name == current_ms:
                    msg = rtr("command.list.current", False, name=ms_name)
                elif ms_name == default:
                    msg = rtr("command.list.default", False, name=ms_name)
                else:
                    msg = rtr("command.list.plain", False, name=ms_name)
                source.reply(msg)
                flag = True
        if not flag:
            source.reply(rtr("command.list.empty", False))
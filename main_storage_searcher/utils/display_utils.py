from mcdreforged.api.all import RTextList, ServerInterface, RAction, RText
from main_storage_searcher.constants import PLUGIN_ID, REPLY_TITLE, TITLE


def rtr(key, title=True, *args, **kwargs):
    return RTextList(REPLY_TITLE+" ", ServerInterface.si().rtr(PLUGIN_ID+"."+key, *args, **kwargs)) if title else ServerInterface.si().rtr(PLUGIN_ID+"."+key, *args, **kwargs)

def rtr_minecraft(key):
    return ServerInterface.si().rtr("minecraft."+key).to_plain_text() if key else None

def help_msg(command):
    return RTextList(RText(f"§7!!ms {command} ").c(RAction.run_command, f"!!ms {command}"), ServerInterface.si().rtr(f"{PLUGIN_ID}.command.help.{command}"))
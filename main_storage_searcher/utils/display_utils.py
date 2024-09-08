from mcdreforged.api.all import RTextList, ServerInterface, RAction
from main_storage_searcher.constants import PLUGIN_ID, REPLY_TITLE, TITLE


def rtr(key, title=True, *args, **kwargs):
    return RTextList(REPLY_TITLE+" ", ServerInterface.si().rtr(PLUGIN_ID+"."+key, *args, **kwargs)) if title else ServerInterface.si().rtr(PLUGIN_ID+"."+key, *args, **kwargs)

def rtr_minecraft(key):
    return ServerInterface.si().rtr("minecraft."+key).to_plain_text() if key else None


def help_msg(server_name, prefix):
    server = ServerInterface.si()
    msg = RTextList(server.rtr(PLUGIN_ID+".command.help.info", TITLE=TITLE))
    for command in ["help", "status", "start", "stop", "kill", "sync", "reload"]:
        msg.append("\n",server.rtr(PLUGIN_ID+".command.help."+command, prefix=prefix, server_name=server_name).set_click_event(RAction.run_command, f"{prefix} {command}"))
    return msg
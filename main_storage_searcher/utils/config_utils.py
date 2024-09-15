from mcdreforged.api.all import Serializable
from typing import Union


class PermissionConfig(Serializable):
    create: int = 3
    load: int = 2
    reload: int = 2
    unload: int = 2
    search: int = 0
    highlight: int = 0
    setdefault: int = 3
    list: int = 0

class MSConfig(Serializable):
    default: Union[None, str] = None

class Config(Serializable):
    main_storage: MSConfig = MSConfig()
    permission: PermissionConfig = PermissionConfig()
from mcdreforged.api.all import ServerInterface, new_thread
import time
from typing import List, Tuple, Callable, Any, Dict


def highlight_block_clear(server: ServerInterface, tag="mark"):
    server.execute(f"kill @e[tag={tag}]")

@new_thread("highlight-block")
def highlight_block(server: ServerInterface, x, y, z, new=True, block="gray_stained_glass", tag="mark", temp=1):
    nbt = '''{Tags:["%s"],Glowing:1b,Invisible:1b,Invulnerable:1b,PersistenceRequired:1b,Silent:1b,NoGravity:1b,Time:%s,DropItem:0b,HurtEntities:0b,BlockState:{Name:"minecraft:%s"}}'''%(tag, temp, block)
    if new:
        server.execute(f"kill @e[tag={tag}]")
    server.execute(f"summon minecraft:falling_block {int(x)} {int(y)} {int(z)} {nbt}")

@new_thread("highlight-block-multi")
def highlight_block_multi(server: ServerInterface, multi_pos: List[Tuple[int, int, int]], new=True, block="gray_stained_glass", tag="mark", temp=0, wait=0):
    id = time.time()
    if new:
        server.execute(f"kill @e[tag={tag}]")
    for pos in multi_pos:
        x, y, z = pos
        highlight_block(server, x, y, z, new=False, block=block, tag=tag if wait == 0 else f"temp{id}", temp=temp)
    if wait > 0:
        time.sleep(wait)
        server.execute(f"kill @e[tag=temp{id}]")

@new_thread("highlight-block-multi")
def highlight_block_multi_steps(server: ServerInterface, multi_group_pos: List[List[Tuple[int, int, int]]], block="gray_stained_glass", wait=0.05, end_func: Tuple[Callable, Tuple[Any], Dict[str, Any]]=None):
    tag = f"step{time.time()}"
    for group_pos in multi_group_pos:
        highlight_block_multi(server, group_pos, block=block, tag=tag)
        time.sleep(wait)
    highlight_block_clear(server, tag)
    if end_func:
        args, kwargs = end_func[1] if len(end_func)>=2 else (), end_func[2] if len(end_func)>=3 else {}
        end_func[0](*args, **kwargs)

@new_thread("highlight-block-timer")
def highlight_block_timer(server: ServerInterface, x, y, z, block="gray_stained_glass", wait=1):
    id = time.time()
    highlight_block(server, x, y, z, new=False, block=block, tag=f"temp{id}", temp=0)
    time.sleep(wait)
    server.execute(f"kill @e[tag=temp{id}]")

@new_thread("highlight-block-by-entity")
def highlight_block_by_entity(server: ServerInterface, x, y, z, new="highlight_entity", tag=[], duration: int = 0):
    if duration > 0:
        tag.append(f"highlight_entity{time.time()}")
    if new:
        tag.append(new)
        server.execute(f"kill @e[tag={new}]")
    tag = ",".join(tag)
    nbt = '''{Tags:[%s],Glowing:1b,NoAI:1b,Invulnerable:1b,PersistenceRequired:1b,CanPickUpLoot:0b,Silent:1b,NoGravity:1b,DeathLootTable:"entities/empty",ActiveEffects:[{Id:14,Amplifier:0,Duration:199980}],DeathTime:19b}'''%tag
    server.execute(f"summon slime {x} {y} {z} {nbt}")
    if duration:
        time.sleep(duration)
        server.execute(f"kill @e[tag={new}]")
    
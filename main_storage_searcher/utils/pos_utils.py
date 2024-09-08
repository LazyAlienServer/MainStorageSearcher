from typing import Iterable

class DynamicPos(tuple):

    def offset_axis(self, distance: int, axis: str):
        match axis:
            case "x":
                return DynamicPos((self[0]+distance, self[1], self[2]))
            case "y":
                return DynamicPos((self[0], self[1]+distance, self[2]))
            case "z":
                return DynamicPos((self[0], self[1], self[2]+distance))
        raise TypeError(f"`axis` should be 'x', 'y', or 'z', but found '{axis}'")
    
    def offset_facing(self, distance: int, facing: str):
        match facing:
            case "west":
                return DynamicPos((self[0], self[1]-distance, self[2]))
            case "east":
                return DynamicPos((self[0], self[1]+distance, self[2]))
            case "north":
                return DynamicPos((self[0], self[1], self[2]-distance))
            case "south":
                return DynamicPos((self[0], self[1], self[2]+distance))
            case "down":
                return DynamicPos((self[0], self[1]-distance, self[2]))
            case "up":
                return DynamicPos((self[0], self[1]+distance, self[2]))
        raise TypeError(f"`facing` should be 'north', 'south', 'east', 'west', 'up' or 'down', but found '{facing}'")
    
    def set_axis(self, value, axis):
        match axis:
            case "x":
                return DynamicPos((value, self[1], self[2]))
            case "y":
                return DynamicPos((self[0], value, self[2]))
            case "z":
                return DynamicPos((self[0], self[1], value))
    
    def __mul__(self, value):
        return DynamicPos((self[0]*value, self[1]*value, self[2]*value))
    
    def __truediv__(self, value):
        return DynamicPos((self[0]/value, self[1]/value, self[2]/value))
    
    def __add__(self, pos):
        if isinstance(pos, DynamicPos) or (isinstance(pos, Iterable) and len(pos) == 3):
            return DynamicPos((self[0]+pos[0], self[1]+pos[1], self[2]+pos[2]))
        elif isinstance(pos, int) or isinstance(pos, float):
            return DynamicPos((self[0]+pos, self[1]+pos, self[2]+pos))
    
    def __radd__(self, pos):
        return self.__add__(pos)
    
    def __sub__(self, pos):
        return DynamicPos((self[0]-pos[0], self[1]-pos[1], self[2]-pos[2]))

def opposite_facing(facing: str):
    match facing:
        case "north":
            return "south"
        case "south":
            return "north"
        case "east":
            return "west"
        case "west":
            return "east"
        case "up":
            return "down"
        case "down":
            return "up"
    raise TypeError(f"`facing` should be 'north', 'south', 'east', 'west', 'up' or 'down', but found '{facing}'")


def left_facing(facing: str):
    match facing:
        case "north":
            return "west"
        case "west":
            return "south"
        case "south":
            return "east"
        case "east":
            return "north"
    raise TypeError(f"`facing` should be 'north', 'south', 'east' or 'west', but found '{facing}'")

def right_facing(facing: str):
    match facing:
        case "north":
            return "east"
        case "east":
            return "south"
        case "south":
            return "west"
        case "west":
            return "north"
    raise TypeError(f"`facing` should be 'north', 'south', 'east' or 'west', but found '{facing}'")

def rotate_facing(facing: str, rotate: str):
    match rotate:
        case "left":
            return left_facing(facing)
        case "right":
            return right_facing(facing)
    raise TypeError(f"`rotate` should be 'left' or 'right', but found '{rotate}'")
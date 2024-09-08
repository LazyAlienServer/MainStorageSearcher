class DynamicPos(tuple):

    def offset_axis(self, distance: int, axis: str):
        match axis:
            case "x":
                return DynamicPos((self[0]+distance, self[1], self[2]))
            case "y":
                return DynamicPos((self[0], self[1]+distance, self[2]))
            case "z":
                return DynamicPos((self[0], self[1], self[2]+distance))
    
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

def opposite_facing(facing: str):
    return {
        "north": "south",
        "south": "north",
        "west": "east",
        "east": "west",
        "up": "down",
        "down": "up"
    }
from typing import Any, Dict


class HopperMatcher:
    """Handle hopper validation and normalized item-name matching."""

    def is_valid_hopper(self, block_data: Dict[str, Any]) -> bool:
        """Return whether block data describes a usable storage hopper."""
        if not isinstance(block_data, dict) or block_data.get("id") != "minecraft:hopper":
            return False

        items = block_data.get("items")
        return (
            isinstance(items, list)
            and len(items) == 5
            and isinstance(items[0], dict)
            and isinstance(items[0].get("count"), (int, float))
            and items[0]["count"] < 64
        )

    def normalize_item_name(self, name: str) -> str:
        """Normalize an item name for case- and underscore-insensitive matching."""
        return name.lower().replace("_", "")

    def match_item(self, block_data: Dict[str, Any], search_term: str) -> bool:
        """Return whether a hopper's first item matches a search term."""
        items = block_data.get("items")
        if not isinstance(items, list) or not items or not isinstance(items[0], dict):
            return False

        item_id = items[0].get("id")
        return isinstance(item_id, str) and self.normalize_item_name(search_term) in self.normalize_item_name(item_id.removeprefix("minecraft:"))

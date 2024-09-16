# MainStorageSearcher

[中文](./README.md) | English

A MCDR plugin that helps you find specified items in all items~

## Commands

`!!ms` View command help

`!!ms create <name>` Recognize all item styles, currently supports regular non-mixed storage non-encoded all items. See [Recognize All Items](#recognize-all-items) for details.

`!!ms search <name>` Search for the specified item in the loaded all item styles and highlight it

`!!ms setdefault` Set the currently loaded all item style as the default to load, or cancel the default loading if not loaded

`!!ms list` List stored all item styles

`!!ms load <name>` Load all item styles

`!!ms reload` Reload all item styles

`!!ms unload` Unload the loaded all item style

## Dependencies

**Python**

- `python >= 3.8`

**Plugins**

- `minecraft_data_api`

## Recognize All Items

For a complete explanation of the principle, see [Theory](/docs/theory.md)

Stand in the middle of the passage of the all items ordinary single piece and use `!!ms create <name>`, the plugin will detect the player's `(x ± 16, y-5 ~ y+16, z ± 16)` range, search for *hoppers with items in all five slots and the first slot's item count <64, and above is not a funnel*, and find the corresponding storage box according to the possible transmission order of the items, automatically completing the recognition of all items.

Then, a file containing this all item information will be saved in `/config/main_storage_searcher/msdata-<name>.json`.

Use `!!ms load <name>` to load the all items you just created.

## ToDo

- [ ] `en_us` language file
- [ ] Recognize and load bulk, create all item style group `group`
- [ ] Better prompts and echoes
- [x] Command permission restrictions
- [x] Command help
- [x] Automatically load default all item configuration
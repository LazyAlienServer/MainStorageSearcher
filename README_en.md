# MainStorageSearcher

[中文](./README.md) | English

A MCDR plugin that helps you find specified items in Main Storage~

## Commands

`!!ms` View command help

`!!ms create <name>` Recognize Main Storage styles, currently supports regular non-mixed storage non-encoded Main Storage. See [Recognize Main Storage](#recognize-main-storage) for details.

`!!ms search <name>` Search for the specified item in the loaded Main Storage styles and highlight it

`!!ms setdefault` Set the currently loaded Main Storage style as the default to load, or cancel the default loading if not loaded

`!!ms list` List stored Main Storage styles

`!!ms load <name>` Load Main Storage styles

`!!ms reload` Reload Main Storage styles

`!!ms unload` Unload the loaded Main Storage style

## Dependencies

**Python**

- `python >= 3.8`

**Plugins**

- `minecraft_data_api`

## Recognize Main Storage

For a complete explanation of the principle, see [Theory](/docs/theory.md)

Stand in the middle of the passage of the Main Storage ordinary single slice and use `!!ms create <name>`, the plugin will detect the player's `(x ± 16, y-5 ~ y+16, z ± 16)` range, search for *hoppers with items in all five slots and the first slot's item count <64, and above is not a hopper*, and find the corresponding storage box according to the possible transmission order of the items, automatically completing the recognition of Main Storage.

Then, a file containing this Main Storage information will be saved in `/config/main_storage_searcher/msdata-<name>.json`.

Use `!!ms load <name>` to load the Main Storage you just created.

## ToDo

- [ ] `en_us` language file
- [ ] Recognize and load bulk, create Main Storage style group `group`
- [ ] Better prompts and echoes
- [x] Command permission restrictions
- [x] Command help
- [x] Automatically load default Main Storage configuration
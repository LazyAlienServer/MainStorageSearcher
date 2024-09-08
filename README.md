# MainStorageSearcher

一个MCDR插件，帮助你在全物品中寻找指定物品~

## 命令

`!!ms create <name>` 识别全物品，目前支持常规非混储非编码全物品。详见[识别全物品](#识别全物品)

`!!ms load <name>` 加载全物品

`!!ms reload` 重载全物品

`!!ms unload` 卸载已加载的全物品

`!!ms search <name>` 在加载的全物品中搜索指定物品并高亮

## 识别全物品

站在全物品普通单片正中央的通道上使用`!!ms create <name>`后，插件会检测玩家`(x ± 16, y-5 ~ y+16, z ± 16)`的范围，搜索*五个槽位都有物品且第一个槽位的物品数<64，且上方不是漏斗的*漏斗，并按照物品可能的传输顺序找到对应的存储箱子，自动完成全物品识别。

然后，一个存储了这个全物品信息的文件会被保存在`/config/main_storage_searcher/msdata-<name>.json`中。

使用`!!ms load <name>`以加载你刚刚创建的全物品
# 原理

## 识别全物品

1. 检测玩家`[x-16, x+16], [y+16, y-5], [z-16, z+16]`的范围，搜索*五个槽位都有物品且第一个槽位的物品数<64，且上方不是漏斗的*漏斗，创建单片的漏斗样式
   - 高度从上往下`[y+16, y-6)`、先搜索`x`轴，后搜索`y`轴
   - 当在某一高度`y`的某一轴`axis`上搜索到的漏斗数量在`(1,17)`时，将轴`axis`设置为该轴，另一方向的轴将不会再在后续高度`y`中搜索
2. 删除不在该轴`axis`上的漏斗。*当玩家并未完全站在全物品正中心时，可能会在另一方向的轴上搜索到一排漏斗，这些漏斗并不属于单个单片。此步骤目的是仅保留单片中的漏斗。*
3. 以第一个搜索到的漏斗为初始位置，沿另一条轴的方向二分查找单片的起始端`(-)`和结束端`(+)`。
   - 先沿负方向查找，初始步长为`-256`，若仍为漏斗则步长*2，若不为漏斗则在`(当前位置, 当前位置+步长)`范围内查找边界。
   - 后沿正方向查找，初始步长为`+256`，后续同上
4. 以步骤1中构建的单片`slice`为模板，从步骤3从的起始端`(-)`至结束端`(+)`按单片依次查询漏斗中的首位物品栏位的物品
5. 按照[物品可能的传输顺序](#传输寻路)，以单片中的每个漏斗为起点，查询该漏斗传输的终点即单片箱子，创建单片的箱子样式，并补全[可能存在的大箱子](#箱子补全)
6. 保存[全物品样式](#全物品样式)

## 传输寻路

1. 若当前坐标位置为漏斗，查询漏斗朝向，将坐标向漏斗朝向方向移动一格
2. 若步骤1无结果，查询当前坐标下方一格是否为漏斗，若是则将坐标向下方移动一格，跳至步骤1
3. 若当前坐标位置为方块实体，继续
4. 若当前坐标位置为投掷器，查询投掷器朝向，将坐标向投掷器朝向方向移动一格，跳至步骤1
5. 若当前坐标位置为箱子，返回当前坐标，结束
6. 将坐标向下方移动一格，跳至步骤1

## 箱子补全

1. 获取箱子朝向
2. 若箱子`type`为`left`，将方向设为箱子朝向向右旋转一个方向，返回当前坐标与当前坐标向方向移动一格后的坐标
3. 若箱子`type`为`right`，将方向设为箱子朝向向左旋转一个方向，后同上
4. 若箱子`type`为`single`，返回当前坐标
   
## 全物品样式
```json
{
    "name": /* 样式名 */,
    "axis": /* 单片的轴向(非朝向) */,
    "range":[
        /* 起始端，存储的是不是axis的那一轴的坐标 */,
        /* 结束端 */
    ],
    "hoppers": [
        // [x, y, z]
    ],
    "chests": [
        [
            // [x1, y1, z1] -> chest(某一大箱子的左/右侧)
            // [x2, y2, z2]
        ],
        [
            // [x, y, z]
        ],
        [
            // ...
        ]
    ],
    "items": [
        [
            /* 单片物品 */,
            /* 顺序与hoppers顺序相同，一一对应 */,
        ],
        [
            // ...
        ]
    ]

}
```
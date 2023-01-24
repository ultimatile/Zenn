---
title: "matplotlibで3次元plotの基本"
emoji: "🦀"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [python]
published: false
---

# はじめに
# import
```python:
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
```

# 箱作り
```python:
fig = plt.figure(figsize=(8, 6))
ax = fig.add_subplot(111, projection="3d")
```

# カメラの位置
```python:
ax.view_init(elev=30, azim=225)
```

# 黒魔術
余計なマージンを削除
```python:
## removing axes margins in 3D plot
## https://stackoverflow.com/questions/16488182/removing-axes-margins-in-3d-plot
### https://stackoverflow.com/questions/23951230/python-axis-limit-in-matplotlib
### https://stackoverflow.com/questions/48986956/correctly-setting-the-axes-limits-in-matplotlib-3dplots?noredirect=1&lq=1
### https://stackoverflow.com/questions/46380464/matplotlib-3d-axis-bounds-always-too-large-doesnt-set-lims-correctly
###patch start###
from mpl_toolkits.mplot3d.axis3d import Axis
if not hasattr(Axis, "_get_coord_info_old"):
    def _get_coord_info_new(self, renderer):
        mins, maxs, centers, deltas, tc, highs = self._get_coord_info_old(renderer)
        mins += deltas / 4
        maxs -= deltas / 4
        return mins, maxs, centers, deltas, tc, highs
    Axis._get_coord_info_old = Axis._get_coord_info  
    Axis._get_coord_info = _get_coord_info_new
###patch end###
```

# 背景の色を変える

```python:
## set the background color of the panes YZ, ZX, XY
## https://stackoverflow.com/questions/11448972/changing-the-background-color-of-the-axes-planes-of-a-matplotlib-3d-plot
ax.w_xaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
ax.w_yaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
ax.w_zaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
```
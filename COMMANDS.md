# COMMANDS.md — 操作命令表（AI agent 用，v3）

> 维护规则：只记当前可运行命令（路径 / 超参 / name 约定 / 环境 / 已知坑）；命令或路径变化先改本表再执行；与 `PROGRESS.md` 同步；弃用命令移入 `_trash\` 后从本表移除。
> **v3 口径**：test = `D:\gas_cylinders\new_test_set\`（61 张网络图；与 93 张巡检照片及其全部编辑产物无来源/场景重叠，独立性检验见「评测」节）；各臂只差训练数据来源；统一 100 epoch / imgsz 640 / batch 16，**固定轮数报 last.pt**（`patience=0` 关早停）、不做验证集选权。

## 环境

- venv：`D:\yolo\.venv`（Py 3.13，torch 2.8.0+cu129，ultralytics 8.4.135）；python = `D:\yolo\.venv\Scripts\python.exe`，yolo CLI = `D:\yolo\.venv\Scripts\yolo.exe`。
- GPU：RTX 5070 Ti Laptop（11.9 GB），统一 `device=0`。
- 脚本全部在 `D:\yolo\scripts\`；`<tag>` ∈ `yolov8s` / `yolov8m` / `yolo11s` / `yolo11m` / `yolo26s` / `yolo26m`。
- 沙箱（agent 内）：训练/评测/autolabel 需 danger-full-access 单次升级；纯数据脚本 workspace-write 可跑；跨盘写（`D:\gas_cylinders`）同样需升级。

```powershell
# GPU 可用性自检
& D:\yolo\.venv\Scripts\python.exe -c "import torch;print(torch.cuda.is_available(),torch.cuda.get_device_name(0))"
```

## v3 配置生成（test 与各臂）

```powershell
# v3 配置：test61 清单 + real93 清单 + 各臂 yaml（确定性，可重复运行）
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\make_v3_configs.py

# 生成臂划分（gen1085：train 868 / val 217；test key → v3 test61）
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\splits_gen1085\make_split_gen1085.py
```

- test = `D:\gas_cylinders\new_test_set\`（61 张 = 30 有框/72 框 + 31 负）；A 臂 yaml = `v3\data_real93.yaml`；C 臂 yaml = `gen1085_split\data.yaml`。

## 评测（v3）

```powershell
# 成套评测：C 臂 gen1085 六权重 + 规模曲线点 gen493 → phase10_v3_main.json
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\eval_v3.py

# 单权重（示例）
& D:\yolo\.venv\Scripts\yolo.exe detect val model=D:\yolo\runs\detect\gen1085\yolo26s\weights\last.pt data=D:\gas_cylinders\v3\data_test61.yaml split=test imgsz=640 batch=16 device=0 workers=0

# test 独立性检验（缩略图相关性，只读、约 30 s；改 test 集后必跑）
#   基准值（2026-09-19 实测 / 2026-09-20 复跑一致）：test↔real93 max 0.730、test↔gen800 max 0.732、
#   对照 real93 内部 max 0.834 → 0 对 >0.90。数字写回 PROGRESS 二.3。
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\check_test_independence.py
```

- 各臂 run 目录约定：`runs\detect\gen1085\`（C 臂）、`runs\detect\gen493\`（规模曲线旧点）、`runs\detect\real93v3\`（A 臂，待训）、`runs\detect\aug93\`（B 臂，待建）。

## 训练（v3 各臂）

```powershell
# A 臂：real93 全量 93 张（train=val=93，test → 新 test）
& D:\yolo\.venv\Scripts\yolo.exe detect train model=D:\yolo\weights\<tag>.pt data=D:\gas_cylinders\v3\data_real93.yaml epochs=100 patience=0 imgsz=640 batch=16 device=0 name=real93v3/<tag>

# A/B 两臂成套训练（六权重串行、OOM 自动降 batch8、可断点续跑）
& D:\yolo\scripts\run_v3_arms.ps1 -Arm real93                 # A 臂 → runs\detect\real93v3\<tag>
& D:\yolo\scripts\run_v3_arms.ps1 -Arm aug93                  # B 臂 → runs\detect\aug93\<tag>（等增广集）
& D:\yolo\scripts\run_v3_arms.ps1 -Arm real93 -Only "yolo26s,yolo26m"   # 只跑指定 tag
#   日志：logs\v3_<arm>_train.log（总表）+ logs\v3_<arm>_<tag>.log（逐权重）
#   ⚠️ 2026-09-19 00:12 曾以此启动 A 臂并被中断（yolov8s 训到 epoch 62 断、real93v3\ 未落盘）；
#      该次日志已归档。重跑前先删半成品 run 目录：
#      Remove-Item -Recurse -Force D:\yolo\runs\detect\real93v3 -ErrorAction SilentlyContinue

# C 臂重训（生成臂；权重已有，一般只做复评）：六权重串行
& D:\yolo\scripts\run_phase8_gen1085.ps1

# gen493 重跑（待办：把规模曲线第一点统一到 v3 协议；394 张清单沿用 Placement_Issues\gen493_split\）
#   ⚠️ 现役 gen493 权重是 v1 时期训练的（args.yaml: patience=100，其 data.yaml 的 test 仍指 v1_split\all.txt），
#      只做过 v3 复评。重跑须新建 v3 版 data.yaml（test → v3\test61.txt）并保持 train 清单不变（394 张）。
#   ⚠️ name 冲突：重跑若沿用 name=gen493/<tag>，ultralytics 会因 exist_ok=false 新建 gen4932\<tag>（坑 6），
#      旧权重原地保留更安全；若坚持同名覆盖，先把 runs\detect\gen493 整个备份移走再跑。
#   ⚠️ 重跑后 phase10_v3_main.json 的 C_gen493_scale 一组会变，PROGRESS 三、PAPER_PLAN 四.2 的数字要同步更新。

# B 臂：离线增广（脚本待写 → scripts\make_aug93_dataset.py 产 D:\gas_cylinders\aug93\，868 张）
#   增广规则：hflip / ±10° 旋转 / 缩放平移 / 亮度对比度 HSV，几何变换同步变框；不用上下翻转；
#   总量与 C 臂一致（868 张）即可，**不按"单图有无标签"配正负比**——标注单位是框、一张图上可混合。
#   训练命令同 A 臂，data 换成 aug93 的 yaml（待建）。
```

## 自动打标

```powershell
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\autolabel.py --source <图片目录> `
    [--labels-out <目录>] [--model <best.pt>] [--conf 0.25] [--iou 0.45] [--imgsz 640] [--overwrite] [--cvat-dir <目录>]
```

- **默认模型 = `runs\detect\gen1085\yolo26s\weights\last.pt`**（2026-09-18 更换：在 119 张未见过的生成图上的自评 mAP50-95 0.932 / P 0.970 / R 0.958，属工具件指标、不进论文结果表），conf=0.25；输出每图 5 列 txt（保持 1:1；该模型在生成图上通常每张都有检出，"空 txt"由模型行为决定，不是工具保证）；labels 目录附 data.yaml（CVAT 导入用，CVAT 复核路线已在 v1 弃用，仅留兼容）。调参：误框多 → 调高 conf；漏框多 → 调低。

## 打标一键工具（用户入口）

```powershell
D:\yolo\scripts\prepare_labeling_workspace.bat   # 双击交互：输入图片文件夹路径
```

- 行为：布局自适应（散图移入 `images\`）→ 建 `labels\` + data.yaml（已存在不覆盖）→ autolabel 预打标（已有标签跳过）。输入文件夹不递归子目录；全量重打 = 删 `labels\*.txt` 再跑。

## 标注 GUI

```powershell
D:\yolo\annotator\start_annotator.bat    # 后台启动，http://127.0.0.1:8085
D:\yolo\annotator\stop_server.bat [port] # 停止（默认 8085）
```

- 改动 annotator 代码后须重启服务并刷新页面；新增类别写入 data.yaml（id = max+1，重名拦截）。

## 已知坑（ultralytics / Windows / 本仓库）

1. `data.yaml` 的 `path` 键必须绝对路径（`path: .` 会解析到进程 CWD）；train/val/test 清单行也必须绝对图片路径（按 `\images\`→`\labels\` 子串替换找标签，相对行全部失败）。**注意**：`path` 已绝对时，`test:` 这类以盘符开头的绝对行与相对行都可以用（现役三个 v3 yaml 即混写），但换 yaml 时别把 `path` 写成相对。
2. 独立 python 脚本跑 ultralytics 推理/评测：必须 `if __name__ == "__main__"` 守卫 + `workers=0`（Windows spawn 重导入会崩）；用 `yolo.exe` CLI 训练/评测不受此限（默认 `workers=8`）。
3. `.gitignore` 不支持行内注释（`#` 只认行首）。
4. 打标工作区根 `data.yaml`（`path: .` + `train: images`）仅供 annotator GUI 使用，勿用于训练配置。
5. 固定轮数协议必须显式 `patience=0`：ultralytics 默认 patience=100（实现为 `patience or inf`，即 0=关闭）；小数据臂的 self-val fitness 受随机初值影响会误触发早停（实测 300 轮跑在第 105 轮被截断）。100 轮协议碰不到，300 轮及以上必须关。**gen493 旧权重就是 `patience=100` 训的**（虽跑满 100 轮），按 v3 重跑时务必带上 `patience=0`。
6. 评测/训练输出名带 `/`（如 `name=v3/C_gen1085_yolo26s`）会建子目录，`exist_ok` 默认 false → 同名重跑会**递增后缀**（`..._yolo26s2`），别误读成新结果。

## Git

- origin = https://github.com/ReedZhang47/gas-cylinder-yolo.git（main 已跟踪；GCM 凭据已存）。
- `.gitignore` 排除：`.venv/ runs/ weights/ _trash/ .tmp/ annotator_demo_data/`、`*.log`、`__pycache__/`、`shot*.png`、`Prompt.md`。
- `paper\reference\`（文献 PDF 库）**不入库**；数据区 `D:\gas_cylinders\` 在仓库外，git 不管。

## 维护记录

| 日期 | 变更 |
|---|---|
| 2026-08-31 | 建表 |
| 2026-09-14 | v1 重构：代码归入 `scripts\`、精简为当前命令、弃用内容移入 `_trash\` |
| 2026-09-18 | v2：第二批数据、v2 口径、打标件换代 gen1085 |
| 2026-09-19 | v3：换 test（61 张网络独立图片）、三臂口径（real93 / 增广 868 / 合成 868）、命令清空重写为 v3；v1/v2 旧文件移入 `_trash` |
| 2026-09-20 | v3 文档收口：`check_test_independence.py` 上线（test 独立性检验）；B 臂口径改为"只对总量"；gen493 重跑列为待办 |

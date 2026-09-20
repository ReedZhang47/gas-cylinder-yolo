# COMMANDS.md — 操作命令表（AI agent 用，v3）

> 维护规则：只记当前可运行命令（路径 / 超参 / name 约定 / 环境 / 已知坑）；命令或路径变化先改本表再执行；与 `PROGRESS.md` 同步；弃用命令移入 `_trash\` 后从本表移除。
> **v3 口径**：test = `D:\gas_cylinders\new_test_set\`（61 张网络图；与 93 张巡检照片及其全部编辑产物无来源/场景重叠，独立性检验见「评测」节）；各臂只差训练数据来源；统一 **300 epoch** / imgsz 640 / batch 16，**固定轮数报 last.pt**（`patience=0` 关早停）、不做验证集选权（61val 方案为 L2 对照，见 `EXPERIMENTS.md`）。

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
# 成套评测（旧口径，保留供复现）：C 臂 gen1085 六权重 + gen493v3 → phase10_v3_main.json
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\eval_v3.py

# 单权重（示例）
& D:\yolo\.venv\Scripts\yolo.exe detect val model=D:\yolo\runs\detect\gen1085\yolo26s\weights\last.pt data=D:\gas_cylinders\v3\data_test61.yaml split=test imgsz=640 batch=16 device=0 workers=0

# test 独立性检验（缩略图相关性，只读、约 30 s；改 test 集后必跑）
#   基准值（2026-09-19 实测 / 2026-09-20 复跑一致）：test↔real93 max 0.730、test↔gen800 max 0.732、
#   对照 real93 内部 max 0.834 → 0 对 >0.90。数字写回 PROGRESS 二.3。
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\check_test_independence.py
```

- 各臂 run 目录约定：`runs\detect\gen1085\`（C 臂）、`runs\detect\gen493v3\`（规模曲线第一点，v3 协议）、`runs\detect\real93v3\`（A 臂，待训）、`runs\detect\aug93\`（B 臂，待建）。

## 训练（v3 各臂；**统一 300 轮**）

> 协议：**epochs=300 / patience=0 / imgsz 640 / batch 16 / device 0 / 全量训练（不划自评 val，yaml 的 `val:` 指向 train 自己）/ 快照 `save_period=10`**。
> 300 轮的依据与耗时模型见 `EXPERIMENTS.md` 二、五节。实验线划分（L1 主线 / L2 P2 / L3 支撑）见同文件一节。

```powershell
# 三臂数据配置（均为全量）
#   A 臂：D:\gas_cylinders\v3\data_real93.yaml                       （93 张）
#   B 臂：D:\gas_cylinders\aug93\data_aug93.yaml                     （增广到 1085 张，脚本待写）
#   C 臂：D:\yolo\scripts\splits_gen1085\data_gen1085_full_v3.yaml  （1085 全量，清单 gen1085_full_train.txt）
#   规模曲线 493 点：D:\yolo\scripts\splits_gen1085\data_gen493_full_v3.yaml（1085 点用上面的 C 臂）

# 单臂单权重（示例：C 臂 yolo26s，300 轮 + 每 10 轮快照）
& D:\yolo\.venv\Scripts\yolo.exe detect train model=D:\yolo\weights\yolo26s.pt `
    data=D:\yolo\scripts\splits_gen1085\data_gen1085_full_v3.yaml `
    epochs=300 patience=0 save_period=10 imgsz=640 batch=16 device=0 name=gen1085v3/yolo26s

# 成套训练（六权重串行、OOM 自动降 batch8、可断点续跑）
& D:\yolo\scripts\run_v3_arms.ps1 -Arm real93 -Epochs 300       # A 臂 → runs\detect\real93v3\<tag>
& D:\yolo\scripts\run_v3_arms.ps1 -Arm aug93  -Epochs 300       # B 臂 → runs\detect\aug93\<tag>（等增广集）
& D:\yolo\scripts\run_v3_arms.ps1 -Arm real93 -Only "yolo26s,yolo26m"   # 只跑指定 tag
#   日志：logs\v3_<arm>_train.log（总表）+ logs\v3_<arm>_<tag>.log（逐权重）
#   ⚠️ 2026-09-19 00:12 曾以此启动 A 臂并被中断（yolov8s 训到 epoch 62 断、real93v3\ 未落盘）；
#      该次日志已归档。重跑前先删半成品 run 目录：
#      Remove-Item -Recurse -Force D:\yolo\runs\detect\real93v3 -ErrorAction SilentlyContinue
#   ⚠️ 训练完用收尾脚本规范化目录（把中断遗留的 xxx-2 归位、删空壳与 best.pt）：
& D:\yolo\scripts\normalize_runs.ps1 -Arm real93

# C 臂重训（旧 100 轮产物在 runs\detect\gen1085；300 轮全量重训归 P2，见下）

# P2（L2）：三臂训练完 → 每个权重有 30 个快照 → 逐快照评 61 张 → 一条曲线读两种口径
#   61test = 末轮值；61val = 曲线最大值。参见 EXPERIMENTS.md 四节与 PLAN_61VAL.md。

# 规模曲线（**新口径：493 vs 1085，均 300 轮**；1085 点复用 L1 的 C 臂，不额外训练）
#   493 点：yaml = scripts\splits_gen1085\data_gen493_full_v3.yaml（batch-1 全量 493 张，清单 gen493_full_train.txt）
#   命令：yolo detect train ... data=<上面 yaml> epochs=300 patience=0 save_period=10 name=gen493full/<tag>
#   ⚠️ 旧口径（394 vs 868、100 轮）已作废；其 run runs\detect\gen493v3 留档，不再使用。

# B 臂：离线增广（脚本待写 → scripts\make_aug93_dataset.py 产 D:\gas_cylinders\aug93\，**1085 张**）
#   增广规则：hflip / ±10° 旋转 / 缩放平移 / 亮度对比度 HSV，几何变换同步变框；不用上下翻转；
#   总量与 C 臂一致（**1085 张**，按独立图片数对齐；gen493 是 gen1085 子集，**不可合并计数**）即可，
#   不按"单图有无标签"配正负比——标注单位是框、一张图上可混合。
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
5. 固定轮数协议必须显式 `patience=0`：ultralytics 默认 patience=100（实现为 `patience or inf`，即 0=关闭）；小数据臂的 self-val fitness 受随机初值影响会误触发早停（实测 300 轮跑在第 105 轮被截断）。100 轮协议碰不到，300 轮及以上必须关。
6. 输出目录重名会**递增后缀**：训练/评测目录已存在（`exist_ok=false`）时，ultralytics 会另建 `name2` / `name-2`。**中断或失败的 run 会留下只含 `args.yaml` 的空壳目录**，下次同名训练就会静默写进 `<tag>-2`，导致权重分散、评测按固定路径找不到。对策：重跑前删掉空壳目录，或用 `scripts\normalize_runs.ps1 -Arm <arm>` 收尾（归位 `-2` + 删空壳/`best.pt`）。评测输出同理（`runs\detect\v3\...-2`），重跑评测前可先清空 `runs\detect\v3`。

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
| 2026-09-20 | v3 文档收口：`check_test_independence.py` 上线（test 独立性检验）；B 臂口径改为"只对总量" |
| 2026-09-20 | gen493 按 v3 协议重跑六权重并复评（结论：与旧点等价，test 指标逐位相同、PR 曲线逐点最大差 0）；规模曲线两点同协议；新增 `normalize_runs.ps1`；`run_v3_arms.ps1` 增加 `-Arm gen493`；旧 run 归档 |
| 2026-09-20 | **预算定为 300 轮**（L3 试点：独立集合 400 轮后无系统增益）；训练命令整节改写为全量 + 300 轮 + 快照；C 臂 yaml 改指 `data_gen1085_full_v3.yaml`（1085 全量）；B 臂目标量 868→**1085**（按独立图片数对齐；gen493 为 gen1085 子集不可合并）；`runs` 整理 12.2 GB→0.48 GB；新增 `EXPERIMENTS.md` 实验总纲 |
| 2026-09-20 | **规模曲线改口径：493 vs 1085、均 300 轮**（1085 点复用 C 臂）→ 新增 `data_gen493_full_v3.yaml` + `gen493_full_train.txt`；实验原始数据移入入库目录 `experiments\`（原先在 `runs\` 内、不入库）；`run_v3_arms.ps1` 默认 300 轮 + 快照、新增 `-Arm gen1085`；`List_of_Experiments.md` 全表重写 |

# PROGRESS.md — 气瓶检测项目工作进度总览

> ## 文档维护规则（强制）
>
> - 本文件是项目的**唯一进度台账**。每一轮后续工作（数据、训练、评测、打标、工具改动）完成并验证后，**必须立即同步更新本文件**：进展、结果数字、产物路径、下一步、新踩的坑。
> - 本文件**禁止出现指向不存在文件的引用**；文件名、路径、命令改动后先核对这里。
> - 命令如发生变化，**必须同步更新 `COMMANDS.md`**（命令表，与本文件同时维护）。
> - 修改本文件前先读当前版本，改完把「截止」行的时间刷新。

> 截止：首个 500 张合成数据训练完成 + A 类过程文件清理（2026-08-31）。不含后续「新数据自动打标」部分。

## 一、项目一句话

用本地生成式数据增强补足稀有类别「倒放气瓶（Upside-down）」：合成图片规模化扩量 → 自动打标 + 人工复核 → 重训，假设扩量可稳定提升 mAP 且跨 6 个 YOLO 权重成立。当前已完成 **500 张基线**。

## 二、环境（已实测，PowerShell）

| 项 | 值 |
|---|---|
| venv | `D:\yolo\.venv`（Py 3.13，torch 2.8.0+cu129，ultralytics **8.4.135**） |
| GPU | RTX 5070 Ti Laptop 11.9 GB（12 GB 显存，batch16 @ m 级无压力，峰值 ~4.7G） |
| 权重 | `weights\`：yolov8/11/26 × s/m 共 6 个（另 `yolo26n.pt` 未参与方案，可删） |
| 命令 | 见 `COMMANDS.md`（唯一命令清单） |

## 三、数据集 first500（`D:\gas_cylinders\first500`，工作区外）

- 500 张合成图、**单类 `0: Upside-down`**；496 非空标注 + **4 空标图**（负样本，归入 train）。
- 布局：`images/`+ 压平 `labels/`+ `train.txt`（相对路径）已就绪，ultralytics 可直接读。
- **划分（已冻结，勿改）**：80/10/10 = **400/50/50**；按 25 个「颜色×组」前缀**组内分层 16/2/2**；**seed=42**；test 集冻结，供后续 500 vs 1000 对比复用。
- 划分产出：`D:\yolo\splits\`（`data.yaml` + `make_split.py` + `train/val/test.txt`，绝对路径）。
- 坑：源 `train.txt` 带 UTF-8 BOM（读用 `utf-8-sig`）；ultralytics 扫描会在数据集目录写 `labels.cache`（良性，可删后重建）。

## 四、首 500 基线结果

数据：test 集 50 图 / 202 实例。统一超参：epochs=100 / imgsz=640 / batch=16 / device=0 / optimizer=auto（AdamW lr0=0.002）。6 权重全通过，无 OOM。实验日期 2026-08-31。

### test 集（最终结论指标）

| 权重 | 家族/尺寸 | 参数量 | mAP50 | **mAP50-95** | P | R |
|---|---|---|---|---|---|---|
| yolov8s | v8 / s | 11.2 M | 0.909 | 0.753 | 0.936 | 0.803 |
| yolov8m | v8 / m | 25.9 M | **0.935** | 0.762 | 0.859 | 0.886 |
| yolo11s | 11 / s | 9.5 M | 0.924 | 0.751 | 0.907 | 0.868 |
| yolo11m | 11 / m | 20.1 M | 0.927 | **0.774** | 0.917 | 0.847 |
| yolo26s | 26 / s | 10.0 M | 0.916 | 0.770 | 0.834 | 0.868 |
| yolo26m | 26 / m | 21.9 M | 0.920 | 0.753 | 0.855 | 0.861 |

### 训练末轮 val 指标（results.csv 第 100 行，参考）

| 权重 | val mAP50 | val mAP50-95 | 训练耗时 |
|---|---|---|---|
| yolov8s | 0.916 | 0.743 | 407.6 s |
| yolov8m | 0.906 | 0.738 | 818.8 s |
| yolo11s | 0.909 | 0.748 | 414.3 s |
| yolo11m | 0.916 | 0.744 | 843.2 s |
| yolo26s | 0.904 | 0.751 | 515.7 s |
| yolo26m | 0.912 | 0.754 | 973.2 s |

### 结论

1. **最佳权重**：test mAP50-95 最高 **yolo11m（0.774）**；test mAP50 最高 **yolov8m（0.935）**。
2. m 级在 mAP50-95 上普遍不劣于 s 级（yolo26 例外），差距约 1-2 个点。
3. 三家族收敛水平接近（0.751–0.774），「跨权重泛化」前提成立——后续增强数据对比沿用这套 6 权重 × 统一超参方案。
4. 检测质量已较高（mAP50 ≈ 0.91–0.94），500→1000 扩量对比的增益空间集中在 mAP50-95 的精细定位。

## 五、沙箱经验（Windows 下必读，别再踩）

- 受限模式下 `yolo` 训练/评测**必失败**：ultralytics 多进程（ThreadPool/DataLoader）要开**命名管道**（WinError 5），且要写**数据集目录**的 `labels.cache` → 命令需以 `danger-full-access` 单次升级运行（一次性覆盖整组串行训练/评测脚本）。
- 纯数据脚本（划分、格式检查）在工作区 `workspace-write` 下可跑；跨盘写（如往 `D:\gas_cylinders` 写新文件）也要升级。

## 六、下一步（按优先级）

1. **扩量 500 → 1000**：生成/标注新增图片 → 并入训练集（**新数据不入已冻结的 test 集**）→ 同超参重训 6 权重 → 与基线比 mAP，验证「数据量效应」假设。
2. **自动打标闭环**（脚本：`autolabel.py`）：yolo11m 打标 → 人工复核（**自建 GUI 标注工具 `D:\yolo\annotator\`**，见 COMMANDS.md）→ 复核后并入重训。CVAT 导入反复报 yaml/结构错误，**已弃用 CVAT 复核路线**（`.tmp\dm*` datumaro 调试产物已清理）。
3. 若需「无增强基线」对照（假设 1）：用真实照片集（直立/倒放混合、倒放稀少）另行训练一组。

## 七、文件地图

| 文件/目录 | 内容 |
|---|---|
| `PROGRESS.md` | **本文件**：总账本，随进度更新（见文首维护规则） |
| git 仓库 | `D:\yolo` 已 `git init`（分支 `main`，初始提交 `6868027`）；`.gitignore` 排除 .venv/runs/weights/_trash/.tmp/截图，远程仓库未配置，push 见 `COMMANDS.md` §8 |
| `COMMANDS.md` | **命令表**：环境/训练/评测/打标/GUI/划分，随命令变化更新 |
| `autolabel.py` | 自动打标 + CVAT 打包脚本（当前只用自动打标部分） |
| `annotator\` | 本地 GUI 标注工具：`annotator.py` + `static\` + `start_annotator.bat` / `stop_server.bat`；`server.log` 为运行日志（可随时清理） |
| `annotator_demo_data\` | GUI 演示/复测数据（10 图 + 标注 + data.yaml，可删） |
| `splits\` | 冻结划分：`data.yaml` + `train/val/test.txt` + `make_split.py`（复现脚本，源划分勿重跑覆盖） |
| `runs\detect\first500\<tag>\` | 6 组训练产物；**仅 `weights\best.pt` 必须保留**（autolabel 默认模型 = `first500\yolo11m\weights\best.pt`）；`last.pt`、results.csv、曲线、批次图可清理 |
| `runs\detect\val` ~ `val-6` | phase4 test 评测图（指标已入第四节，可清理） |
| `weights\` | 6 个预训练源权重（s/m）+ `yolo26n.pt`（未用，可删） |
| `run_phase3.ps1` / `run_phase4.ps1` | 6 权重串行训练 / test 评测脚本（OOM 自动降 batch=8） |
| `_trash\` | 2026-08-31 A 类过程文件清理备份（GUI 测试产物、datumaro 残留、浏览器 profile、旧结果明细等；确认无用后可整目录删除） |
| `.tmp\pip-*` | 4 个空 pip 临时目录（删除被系统拒绝，留待重启或管理员权限处理） |

> 历史：`results_first500.md`（基线明细）已并入第四节，原文件在 `_trash\results_first500.md`。

# Runpod Qwen-Image-2.1 LoRA 训练交接

最近核验：2026-09-27 01:28 中国标准时间。Pod wde9ui6l50nveo 的训练进程 PID 5643 已到 873/1860 步；A6000 显存 20,209/46,068 MiB、GPU 利用率 100%，250/500/750 步权重文件存在，loss.csv 无 NaN/Inf。Runpod 控制台余额 $11.97，当前 Pod 费用 $0.55/h。此后状态必须从远端日志重读。Web Terminal 显示 Connection Closed 时，重新连接同一 Pod 终端即可；不要据此重启 Pod 或再次发起训练。

## 巡检记录

- 2026-09-27 01:28（中国标准时间）：远端时间 2026-09-26 17:28:22 UTC；训练进度 873/1860（46.9%），最近三步 loss 为 0.4883449078、0.0582101233、0.3104498684；loss.csv 中 NaN/Inf 行数为 0。PID 5643 状态 `Ss`、运行 06:08:32，GPU 20,209/46,068 MiB、利用率 100%。`step-250.safetensors`、`step-500.safetensors`、`step-750.safetensors` 均为 83,943,552 bytes。控制台余额 $11.97，页面当前 Pod 费用 $0.55/h。按至今平均速度推算，剩余约 7 小时；仅作巡检参考。

## 运行位置

| 项目 | 路径或值 |
|---|---|
| Pod | wde9ui6l50nveo · Secure RTX A6000 48 GB |
| 日志 | /workspace/logs/qwen21_full_20260926T111950Z.log |
| 输出 | /workspace/outputs/qwen21_real93_r16/ |
| loss | /workspace/outputs/qwen21_real93_r16/loss.csv |
| 数据 | /workspace/real93，93 张审阅图与 caption |
| 训练 | 93 图 × repeat 5 × epochs 4 = 1860 步；rank 16；每 250 步保存 |
| 执行脚本 | /workspace/scripts/setup.sh、run_train.sh、launch_detached.sh；本地源在 runpod_qwen21/ |

本地传输包位于 .tmp/runpod_qwen21/（Git 忽略）；正式数据包 real93_REVIEWED.tar 的 SHA256 为 43d2f6d17ee54cd145df309a480172a6acc20b0c5686db87dd18d0a078abefdb。固定 DiffSynth-Studio 源码包为 06447dc97e986e56d041dae52316a319baff679148922789ae1cae5f5895cff2，脚本包为 20f5aa596268201d9ea99b845fd8535e2c25626f5a67c2d2881696783b4a6e7b。上传时远端校验与本地一致；环境安装与两图烟测均已通过。
训练实际使用的 93 条审阅 caption 另存为可提交的 docs/v5_prompts/real93_lora_metadata.csv（不含照片）；已与正式 tar 内的 metadata.csv 逐字节核对，SHA256 为 597ed5fa8d6fd0ff333a6b30e1f161a5a6025e38117f890ddee8e793d86ebec8。

## 收尾顺序

1. 在新 Web Terminal 会话检查现有日志末尾、loss.csv、nvidia-smi 和输出目录；确认进程是否仍运行、结束原因及检查点完整性。
2. 训练完成后下载最终与候选检查点、训练配置、loss.csv 和日志；在本机核对文件大小、safetensors 可读性与 SHA256，并记录下载路径。
3. 在 Qwen-Image-2.1 ComfyUI 底模上核对 LoRA 关键层、加载日志，做同 prompt/seed 的 strength 0/1 对照。不要把旧 Liblib 权重或七张不兼容试图误计为结果。
4. 本地结果可读且备份完成后结束 Pod 计费；若需保留 Pod 卷，先确认其继续收费的状态。训练监控自动化由云端训练会话管理。

2026-09-26 的库存、空 Pod、上传障碍和启动全过程已归档于 docs/archive/runpod_qwen21_2026-09-26.md；不再作为当前操作步骤。

# 常用命令 · v5

请先看 NEXT_STEPS.md 的当前阶段。Python 入口以本机实际解释器为准；项目虚拟环境为 D:\yolo\.venv\Scripts\python.exe。

## 云端训练检查

Pod、日志、输出路径和最近核验状态见 docs/v5_prompts/runpod_qwen21_handoff.md。在该 Pod 的新 Web Terminal 会话中检查现有进程，勿因旧会话断线重启：

~~~bash
tail -n 30 /workspace/logs/qwen21_full_20260926T111950Z.log
tail -n 5 /workspace/outputs/qwen21_real93_r16/loss.csv
nvidia-smi
~~~

runpod_qwen21/ 下的 setup.sh、run_train.sh、launch_detached.sh 是已使用的云端脚本；当前运行不需要重新执行。

## 本地 D 生图预检

先核对兼容权重、最终工作流和提示词审阅状态。以下默认仅预检，不提交队列：

~~~powershell
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\comfy_batch_t2i.py --prompts D:\yolo\docs\v5_prompts\real93_prompts.jsonl --variants 6 --limit 1
~~~

通过同种子 LoRA 0/1 对照及单条输出审查后，才使用 --run。脚本会记录 manifest 和输出哈希；批量参数见 docs/v5_prompts/README.md。

## v4 复核入口

~~~powershell
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\eval_v4_protocol.py --protocol-only
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\bootstrap_paired.py --self-test
~~~

完整 v4 结果在 experiments/v4_protocol/。旧作图器 paper/make_figures.py 用于 v4 图和表；新 v5 图各自的再生方式见 paper/figures/figXX/README.md。不要把 D 传给尚未扩展的 v4 训练脚本。

# 下一步 · v5

更新依据：2026-09-27 00:07 的 Runpod 交接快照及当前工作区。云端训练由另一会话监控；不要因 Web Terminal 断线重复启动。

1. **收尾云端 LoRA**：确认 Pod wde9ui6l50nveo 的现有日志、loss 和最终检查点；下载权重、配置、loss.csv、日志并核对哈希。确认本地副本可读后结束 Pod 计费。详细路径与最近核验步数见 docs/v5_prompts/runpod_qwen21_handoff.md。
2. **验证兼容性**：在本机 Qwen-Image-2.1 工作流检查关键层形状与加载日志；同 prompt、同 seed 做 LoRA strength 0/1 对照。旧 Liblib 权重的七张试图不计入 D 臂。
3. **批准生成输入**：逐条审阅 docs/v5_prompts/ 的 93 条 real93 优化提示词和 150 条新场景提示词，把获批条目标为 approved；保存最终模型、采样器、尺寸、随机种子、LoRA 强度与工作流版本。
4. **小批试运行，再批量生成**：先核验 scripts/comfy_batch_t2i.py 的单条预检和实际输出，再推进 93×6 与 150×5 的初步预算。目标是质检后分别保留 465 和 620 张；不足时补生成，逐图记录提示词、seed、模型、取舍理由。
5. **构建 D 数据集**：按现有违规放置类定义预标注并逐图复核；检查空标、框、生成缺陷、近重复、与 dev61 的来源独立性，以及 1085 组图像/标签对应关系。
6. **训练与评估**：新增独立的 D 配置和 run；按 EXPERIMENTS.md 的六 detector、300 轮与固定 dev61 折定义执行三层评估。得到逐图 OOF 缓存后计算 D−A/B/C 配对区间。现有 run_v4_arms.ps1 不支持 D。
7. **整合论文**：依据 paper/FIGURES.md 填入 D 臂，更新正文、表格、图注；再收集并预先冻结真正的外部测试集。D 的场景覆盖与检测收益须由审计和检测结果支持。

已完成的 v4 记录见 PROGRESS.md 和 experiments/v4_protocol/，不在此重复列旧待办。

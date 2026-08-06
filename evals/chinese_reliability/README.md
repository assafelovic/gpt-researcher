# 中文报告可靠性评测

该工具使用固定的 5 道 Simple 题目和 5 道 Deep Research 题目，分别记录报告成功率、有效引用率、耗时和 API 成本。

## 成功标准

- Simple：报告不少于 400 字，且至少包含 2 个有效来源。
- Deep：报告不少于 1500 字，且至少包含 5 个有效来源。
- 有效来源：规范化、去重后可访问，HTTP 状态为 2xx，前 4096 字节中至少读取到 200 字节内容。
- 401、403 和 429 单独标记为 `blocked`，不计入有效来源。

## 运行

从仓库根目录执行：

```bash
python -m evals.chinese_reliability.run_benchmark \
  --mode baseline \
  --output-dir outputs/evals/chinese_reliability/baseline
```

首次先运行两题进行冒烟测试：

```bash
python -m evals.chinese_reliability.run_benchmark \
  --mode baseline \
  --ids simple-01 deep-01 \
  --output-dir outputs/evals/chinese_reliability/smoke
```

脚本串行执行题目，并在每题结束后写入结果，避免单题失败导致整批数据丢失。Docker Compose 已将 `outputs` 映射到服务器宿主机，因此容器重建后结果仍然保留。

## 输出

- `reports/*.md`：完整报告。
- `runs.jsonl`：每题结构化指标，不重复保存完整报告。
- `summary.json`：整体及分模式汇总。
- `summary-simple.json`：Simple 汇总。
- `summary-deep.json`：Deep 汇总。
- `summary.md`：可直接阅读的对比表。

结果目录不应提交 API Key。完整报告和原始运行结果默认只保留在实验机器上。

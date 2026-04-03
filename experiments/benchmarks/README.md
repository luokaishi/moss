# MVES 基准测试

本目录包含所有基准测试脚本和结果。

## 测试类别

1. **AGI 评估基准** - 与现有 AGI 研究对标
2. **性能基准** - 缓存/并发/内存对比
3. **稳定性基准** - 长期运行验证

## 运行测试

```bash
# 运行所有基准测试
./run_all_benchmarks.sh

# 运行特定测试
python agi_benchmark.py
python performance_benchmark.py
```

## 结果

测试结果将保存在 `results/` 子目录中。

#!/usr/bin/env python3
"""
LLM 配额监控工具

监控大模型 API 使用额度，确保实验不超出限制。

限制：
- 月度：18,000 次
- 周度：9,000 次
- 每 5 小时：1,200 次

实验预估：
- 72h 采样：432 次（每 10 分钟 1 次）
- 每次采样：~10 次额度
- 总计：~4,320 次（在周额度内）
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path

class LLMQuotaMonitor:
    """LLM 配额监控器"""
    
    def __init__(self, data_dir: str = "datasets/real_world_72h"):
        self.data_dir = Path(data_dir)
        self.limits = {
            'monthly': 18000,
            'weekly': 9000,
            'per_5hour': 1200
        }
        self.estimated_per_sample = 10
    
    def estimate_usage(self, sampling_interval_minutes: int = 10, duration_hours: int = 72) -> dict:
        """预估实验用量"""
        total_samples = (duration_hours * 60) // sampling_interval_minutes
        estimated_total = total_samples * self.estimated_per_sample
        
        return {
            'total_samples': total_samples,
            'estimated_per_sample': self.estimated_per_sample,
            'estimated_total': estimated_total,
            'weekly_limit': self.limits['weekly'],
            'usage_percentage': (estimated_total / self.limits['weekly']) * 100,
            'safe': estimated_total < self.limits['weekly']
        }
    
    def check_safety(self, duration_hours: int = 72) -> dict:
        """检查实验是否安全（不超出配额）"""
        estimate = self.estimate_usage(duration_hours=duration_hours)
        
        # 检查各项限制
        checks = {
            'weekly': estimate['estimated_total'] < self.limits['weekly'],
            'monthly': estimate['estimated_total'] < self.limits['monthly'],
        }
        
        # 5 小时检查（短期频率）
        samples_per_5hour = (5 * 60) // 10  # 30 次采样
        estimated_5hour = samples_per_5hour * self.estimated_per_sample  # 300 次
        checks['per_5hour'] = estimated_5hour < self.limits['per_5hour']
        
        return {
            'overall_safe': all(checks.values()),
            'checks': checks,
            'details': {
                'weekly_usage': f"{estimate['estimated_total']:,} / {self.limits['weekly']:,} ({estimate['usage_percentage']:.1f}%)",
                'monthly_usage': f"{estimate['estimated_total']:,} / {self.limits['monthly']:,} ({(estimate['estimated_total']/self.limits['monthly'])*100:.1f}%)",
                'per_5hour_usage': f"{estimated_5hour:,} / {self.limits['per_5hour']:,} ({(estimated_5hour/self.limits['per_5hour'])*100:.1f}%)"
            }
        }
    
    def generate_report(self) -> str:
        """生成配额安全报告"""
        safety = self.check_safety()
        estimate = self.estimate_usage()
        
        report = f"""# LLM 配额安全报告

**生成时间**: {datetime.now().isoformat()}

---

## 📊 实验用量预估

| 指标 | 数值 |
|------|------|
| 实验时长 | 72 小时 |
| 采样频率 | 每 10 分钟 1 次 |
| 总采样次数 | {estimate['total_samples']} 次 |
| 单次采样预估 | {estimate['estimated_per_sample']} 次额度 |
| **总预估用量** | **{estimate['estimated_total']:,} 次** |

---

## ⚠️ 配额限制对比

| 限制类型 | 用量 | 限额 | 使用率 | 状态 |
|----------|------|------|--------|------|
| 每 5 小时 | {estimate['total_samples'] // 144 * self.estimated_per_sample:,} | {self.limits['per_5hour']:,} | {(estimate['total_samples'] // 144 * self.estimated_per_sample / self.limits['per_5hour'])*100:.1f}% | {'✅' if safety['checks']['per_5hour'] else '❌'} |
| 周额度 | {estimate['estimated_total']:,} | {self.limits['weekly']:,} | {estimate['usage_percentage']:.1f}% | {'✅' if safety['checks']['weekly'] else '❌'} |
| 月额度 | {estimate['estimated_total']:,} | {self.limits['monthly']:,} | {(estimate['estimated_total']/self.limits['monthly'])*100:.1f}% | {'✅' if safety['checks']['monthly'] else '❌'} |

---

## ✅ 安全评估

**整体状态**: {'✅ 安全' if safety['overall_safe'] else '❌ 危险'}

{
    '✅ 实验用量在配额限制内，可以安全运行！' if safety['overall_safe'] else '⚠️ 实验可能超出配额限制，建议调整采样频率或实验时长！'
}

---

## 💡 优化建议

### 当前配置
- 采样间隔：10 分钟
- 实验时长：72 小时
- 预估用量：{estimate['estimated_total']:,} 次

### 如需降低用量

**方案 1: 增加采样间隔**
```python
# 从 10 分钟改为 15 分钟
sampling_interval_minutes = 15  # 用量减少 33%
```

**方案 2: 缩短实验时长**
```python
# 从 72h 改为 48h
duration_hours = 48  # 用量减少 33%
```

**方案 3: 降低单次采样复杂度**
```python
# 减少每次采样的 LLM 调用次数
LLM_ESTIMATED_PER_SAMPLE = 5  # 从 10 降到 5
```

---

## 📈 剩余额度（参考）

假设实验开始前额度已重置：

| 周期 | 剩余额度 |
|------|---------|
| 5 小时后 | {self.limits['per_5hour'] - (30 * self.estimated_per_sample):,} 次 |
| 本周剩余 | {self.limits['weekly'] - estimate['estimated_total']:,} 次 |
| 本月剩余 | {self.limits['monthly'] - estimate['estimated_total']:,} 次 |

---

**结论**: {'实验可以安全运行 ✅' if safety['overall_safe'] else '需要调整配置 ⚠️'}
"""
        return report


if __name__ == "__main__":
    monitor = LLMQuotaMonitor()
    
    print("📊 LLM 配额安全评估")
    print("=" * 50)
    print()
    
    # 生成报告
    report = monitor.generate_report()
    print(report)
    
    # 保存报告
    report_path = Path("datasets/real_world_72h/llm_quota_report.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report)
    print(f"📄 报告已保存：{report_path}")

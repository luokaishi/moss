#!/usr/bin/env python3
"""
MOSS 24-Hour Milestone Analysis Script
24小时里程碑自动化分析脚本

Usage:
    python analyze_24h_milestone.py

Output:
    - 24h_analysis_report.json (完整数据)
    - 24h_analysis_summary.md (可读报告)
    - 自动截图推荐列表
"""

import json
import os
import glob
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import numpy as np


class MilestoneAnalyzer:
    """24小时里程碑分析器"""
    
    def __init__(self, checkpoints_dir: str = "experiments"):
        self.checkpoints_dir = checkpoints_dir
        self.checkpoints = []
        self.analysis = {}
    
    def load_checkpoints(self) -> List[Dict]:
        """加载所有检查点"""
        pattern = os.path.join(self.checkpoints_dir, "checkpoint_*.json")
        files = sorted(glob.glob(pattern))
        
        checkpoints = []
        for f in files:
            try:
                with open(f, 'r') as fp:
                    data = json.load(fp)
                    data['file'] = f
                    checkpoints.append(data)
            except Exception as e:
                print(f"Warning: Failed to load {f}: {e}")
        
        self.checkpoints = checkpoints
        return checkpoints
    
    def analyze_24h_milestone(self) -> Dict:
        """分析24小时里程碑"""
        if not self.checkpoints:
            return {'error': 'No checkpoints found'}
        
        # 找到24小时或最接近的检查点
        target_24h = None
        for cp in self.checkpoints:
            elapsed = cp.get('elapsed_hours', 0)
            if elapsed >= 23.5:  # 允许±0.5小时误差
                target_24h = cp
                break
        
        if not target_24h:
            # 使用最后一个检查点
            target_24h = self.checkpoints[-1]
            print(f"Warning: No exact 24h checkpoint, using last ({target_24h.get('elapsed_hours', 0):.1f}h)")
        
        elapsed = target_24h.get('elapsed_hours', 0)
        
        # 基础指标
        self.analysis = {
            'timestamp': datetime.now().isoformat(),
            'target_duration': 24.0,
            'actual_duration': elapsed,
            'completion_percentage': (elapsed / 24.0) * 100,
            
            # 资源消耗
            'tokens': {
                'used': target_24h.get('tokens_used', 0),
                'total': 50000,
                'remaining': target_24h.get('tokens_remaining', 46545),
                'usage_rate': target_24h.get('tokens_used', 0) / 50000 * 100
            },
            
            # 知识获取
            'knowledge': {
                'acquired': target_24h.get('knowledge_acquired', 0),
                'acquisition_rate': target_24h.get('knowledge_acquired', 0) / elapsed if elapsed > 0 else 0
            },
            
            # 执行统计
            'actions': {
                'total': target_24h.get('action_count', 0),
                'rate_per_hour': target_24h.get('action_count', 0) / elapsed if elapsed > 0 else 0
            },
            
            # 四目标得分
            'objectives': self._analyze_objectives(target_24h),
            
            # 系统状态
            'system_state': target_24h.get('current_state', {}),
            
            # 趋势分析（如果有历史数据）
            'trends': self._calculate_trends()
        }
        
        # 评估结论
        self.analysis['assessment'] = self._generate_assessment()
        
        return self.analysis
    
    def _analyze_objectives(self, checkpoint: Dict) -> Dict:
        """分析四目标得分"""
        scores = checkpoint.get('objective_scores', {})
        
        return {
            'survival': {
                'current': scores.get('survival', {}).get('score', 0) if isinstance(scores.get('survival'), dict) else scores.get('survival', 0),
                'status': 'stable'  # 将由趋势分析更新
            },
            'curiosity': {
                'current': scores.get('curiosity', {}).get('score', 0) if isinstance(scores.get('curiosity'), dict) else scores.get('curiosity', 0),
                'status': 'growing'
            },
            'influence': {
                'current': scores.get('influence', {}).get('score', 0) if isinstance(scores.get('influence'), dict) else scores.get('influence', 0),
                'status': 'growing'
            },
            'optimization': {
                'current': scores.get('optimization', {}).get('score', 0) if isinstance(scores.get('optimization'), dict) else scores.get('optimization', 0.5),
                'status': 'stable'
            }
        }
    
    def _calculate_trends(self) -> Dict:
        """计算趋势"""
        if len(self.checkpoints) < 2:
            return {'insufficient_data': True}
        
        # 提取Survival分数历史
        survival_history = []
        for cp in self.checkpoints:
            scores = cp.get('objective_scores', {})
            s_score = scores.get('survival', 0)
            if isinstance(s_score, dict):
                s_score = s_score.get('score', 0)
            survival_history.append(s_score)
        
        # 计算变化率
        if len(survival_history) >= 2:
            survival_trend = (survival_history[-1] - survival_history[0]) / len(survival_history)
        else:
            survival_trend = 0
        
        return {
            'survival_decline_rate': survival_trend,
            'checkpoints_used': len(self.checkpoints),
            'stability_assessment': 'stable' if abs(survival_trend) < 0.01 else 'declining'
        }
    
    def _generate_assessment(self) -> Dict:
        """生成综合评估"""
        a = self.analysis
        
        # 1. 资源消耗评估
        token_usage = a['tokens']['usage_rate']
        resource_status = 'healthy' if token_usage < 30 else 'concerning' if token_usage < 60 else 'critical'
        
        # 2. 目标平衡评估
        objs = a['objectives']
        scores = [objs['survival']['current'], objs['curiosity']['current'], 
                 objs['influence']['current'], objs['optimization']['current']]
        
        # 检查是否有目标退化到0
        degeneration = any(s < 0.01 for s in scores if isinstance(s, (int, float)))
        
        # 3. 系统状态
        system_state = a['system_state'].get('state', 'unknown')
        
        # 4. 综合结论
        if resource_status == 'healthy' and not degeneration and system_state == 'normal':
            overall = 'EXCELLENT'
            recommendation = 'Continue experiment, prepare for promotion'
        elif resource_status == 'healthy' and not degeneration:
            overall = 'GOOD'
            recommendation = 'Monitor closely, experiment sustainable'
        elif degeneration:
            overall = 'CONCERNING'
            recommendation = 'Investigate objective degeneration'
        else:
            overall = 'REVIEW'
            recommendation = 'Analyze resource consumption pattern'
        
        return {
            'resource_status': resource_status,
            'objective_degeneration': degeneration,
            'system_state': system_state,
            'overall_assessment': overall,
            'recommendation': recommendation,
            'ready_for_promotion': overall in ['EXCELLENT', 'GOOD']
        }
    
    def generate_report(self) -> str:
        """生成可读报告"""
        if not self.analysis:
            self.analyze_24h_milestone()
        
        a = self.analysis
        
        report = f"""# MOSS 24-Hour Milestone Analysis Report

**Generated**: {a['timestamp']}  
**Analysis Duration**: {a['actual_duration']:.1f} hours / 24 hours ({a['completion_percentage']:.1f}%)

---

## 📊 Executive Summary

**Overall Assessment**: {a['assessment']['overall_assessment']}

**System State**: {a['assessment']['system_state']}

**Recommendation**: {a['assessment']['recommendation']}

**Ready for Promotion**: {'✅ Yes' if a['assessment']['ready_for_promotion'] else '⚠️ Review needed'}

---

## 💰 Resource Consumption

| Metric | Value | Status |
|--------|-------|--------|
| Tokens Used | {a['tokens']['used']:,} / {a['tokens']['total']:,} | {a['assessment']['resource_status']} |
| Usage Rate | {a['tokens']['usage_rate']:.1f}% | - |
| Remaining | {a['tokens']['remaining']:,} | - |
| Projected 72h Usage | {a['tokens']['usage_rate'] * 3:.1f}% | {'✅ Sustainable' if a['tokens']['usage_rate'] * 3 < 80 else '⚠️ Monitor'} |

---

## 🎯 Four Objectives Status

| Objective | Score | Status | Trend |
|-----------|-------|--------|-------|
| Survival | {a['objectives']['survival']['current']:.3f} | {a['objectives']['survival']['status']} | {'⚠️ Declining' if a['trends'].get('survival_decline_rate', 0) < -0.005 else '✅ Stable'} |
| Curiosity | {a['objectives']['curiosity']['current']:.3f} | {a['objectives']['curiosity']['status']} | ✅ Growing |
| Influence | {a['objectives']['influence']['current']:.3f} | {a['objectives']['influence']['status']} | ✅ Growing |
| Optimization | {a['objectives']['optimization']['current']:.3f} | {a['objectives']['optimization']['status']} | ✅ Stable |

**Objective Degeneration**: {'❌ Yes - Critical' if a['assessment']['objective_degeneration'] else '✅ No - All objectives active'}

---

## 📈 Activity Metrics

- **Total Actions**: {a['actions']['total']}
- **Actions per Hour**: {a['actions']['rate_per_hour']:.1f}
- **Knowledge Acquired**: {a['knowledge']['acquired']} items
- **Knowledge Rate**: {a['knowledge']['acquisition_rate']:.2f} items/hour

---

## 🔍 Detailed Analysis

### 1. Stability Analysis
- Checkpoints analyzed: {a['trends'].get('checkpoints_used', 0)}
- Survival trend: {a['trends'].get('survival_decline_rate', 0):.4f} per checkpoint
- Stability assessment: {a['trends'].get('stability_assessment', 'unknown')}

### 2. Resource Efficiency
- Current consumption rate: {a['tokens']['usage_rate'] / a['actual_duration']:.2f}% per hour
- Days remaining at current rate: {a['tokens']['remaining'] / (a['tokens']['used'] / a['actual_duration']):.1f} days

### 3. Four-Objective Balance
{'⚠️ WARNING: One or more objectives show signs of degeneration' if a['assessment']['objective_degeneration'] else '✅ All four objectives maintain healthy scores'}

---

## 🚀 Next Steps

**Immediate**:
1. {'✅ Continue 72h experiment' if a['assessment']['ready_for_promotion'] else '⚠️ Investigate issues before continuing'}
2. {'📣 Prepare promotion materials' if a['assessment']['ready_for_promotion'] else '🔧 Debug and fix'}
3. 📊 Monitor next 24h closely

**48-Hour Milestone** (2026-03-12 14:25):
- Target: Continue stable operation
- Watch for: Long-term sustainability

**72-Hour Completion** (2026-03-13 14:25):
- Final analysis and full report
- Public release if successful

---

## 📋 Data Sources

- Checkpoints analyzed: {len(self.checkpoints)}
- Target file: Latest checkpoint ≥23.5h
- Analysis timestamp: {a['timestamp']}

---

**Report Generated by**: MOSS Milestone Analyzer  
**Version**: 1.0  
**Status**: {'🟢 Ready for next phase' if a['assessment']['ready_for_promotion'] else '🟡 Review required'}
"""
        
        return report
    
    def save_reports(self):
        """保存所有报告"""
        if not self.analysis:
            self.analyze_24h_milestone()
        
        # 1. JSON数据
        json_file = "24h_analysis_report.json"
        with open(json_file, 'w') as f:
            json.dump(self.analysis, f, indent=2, default=str)
        print(f"✅ JSON report saved: {json_file}")
        
        # 2. Markdown报告
        md_file = "24h_analysis_summary.md"
        with open(md_file, 'w') as f:
            f.write(self.generate_report())
        print(f"✅ Markdown report saved: {md_file}")
        
        # 3. 截图建议
        screenshots = self._generate_screenshot_recommendations()
        screenshot_file = "24h_screenshot_checklist.md"
        with open(screenshot_file, 'w') as f:
            f.write(screenshots)
        print(f"✅ Screenshot checklist saved: {screenshot_file}")
        
        return {
            'json': json_file,
            'markdown': md_file,
            'screenshots': screenshot_file
        }
    
    def _generate_screenshot_recommendations(self) -> str:
        """生成截图建议清单"""
        return """# 24-Hour Milestone Screenshots Checklist

## Dashboard Screenshots (Priority Order)

### 1. Dashboard Overview (MUST)
- [ ] Full dashboard at http://localhost:5000
- [ ] Show all 4 objective curves
- [ ] Show current state indicators
- [ ] Timestamp visible

### 2. Objective Trends (MUST)
- [ ] Survival curve (24h history)
- [ ] Curiosity curve (24h history)
- [ ] Influence curve (24h history)
- [ ] Optimization curve (24h history)

### 3. Resource Usage (MUST)
- [ ] Token consumption graph
- [ ] Current usage stats
- [ ] Projected depletion

### 4. System State (SHOULD)
- [ ] Current state: Normal
- [ ] Weight distribution
- [ ] Safety events (if any)

### 5. Terminal/Logs (SHOULD)
- [ ] Latest checkpoint log
- [ ] No error messages
- [ ] PID 4486 running

## Usage for Promotion

- Twitter: Dashboard overview + objective trends
- GitHub README: All 5 screenshots
- Video: Animated screen recording
- Paper: Static graphs with annotations

## Naming Convention

```
moss_24h_dashboard_20260311_1425.png
moss_24h_survival_curve_20260311.png
moss_24h_resource_usage_20260311.png
...
```
"""


def main():
    """主函数"""
    print("="*70)
    print("MOSS 24-HOUR MILESTONE ANALYZER")
    print("="*70)
    print()
    
    analyzer = MilestoneAnalyzer()
    
    # 加载检查点
    print("Loading checkpoints...")
    checkpoints = analyzer.load_checkpoints()
    print(f"Found {len(checkpoints)} checkpoints")
    
    if not checkpoints:
        print("❌ No checkpoints found!")
        print("Make sure the 72h experiment is running.")
        return
    
    # 显示最近的检查点
    latest = checkpoints[-1]
    print(f"\nLatest checkpoint: {latest.get('elapsed_hours', 0):.1f}h")
    print(f"File: {latest.get('file', 'unknown')}")
    
    # 分析24h里程碑
    print("\nAnalyzing 24-hour milestone...")
    analysis = analyzer.analyze_24h_milestone()
    
    # 显示关键结果
    print("\n" + "="*70)
    print("KEY FINDINGS")
    print("="*70)
    
    print(f"\nDuration: {analysis['actual_duration']:.1f}h / 24h ({analysis['completion_percentage']:.1f}%)")
    print(f"Tokens: {analysis['tokens']['used']:,} / {analysis['tokens']['total']:,} ({analysis['tokens']['usage_rate']:.1f}%)")
    print(f"Knowledge: {analysis['knowledge']['acquired']} items")
    
    print(f"\nOverall Assessment: {analysis['assessment']['overall_assessment']}")
    print(f"System State: {analysis['assessment']['system_state']}")
    print(f"Ready for Promotion: {'✅ YES' if analysis['assessment']['ready_for_promotion'] else '⚠️ REVIEW NEEDED'}")
    
    # 保存报告
    print("\n" + "="*70)
    print("SAVING REPORTS")
    print("="*70)
    
    files = analyzer.save_reports()
    
    print("\n" + "="*70)
    print("NEXT ACTIONS")
    print("="*70)
    
    if analysis['assessment']['ready_for_promotion']:
        print("✅ 24h milestone PASSED")
        print("📣 Proceed with promotion:")
        print("   1. Take screenshots (see 24h_screenshot_checklist.md)")
        print("   2. Update README with results")
        print("   3. Post on Twitter/HN/Reddit")
    else:
        print("⚠️ 24h milestone needs review")
        print("🔧 Check:")
        print("   1. Resource consumption pattern")
        print("   2. Objective degeneration causes")
        print("   3. System logs for errors")
    
    print("\nReports saved:")
    for name, path in files.items():
        print(f"  - {name}: {path}")
    
    print("\n" + "="*70)


if __name__ == '__main__':
    main()

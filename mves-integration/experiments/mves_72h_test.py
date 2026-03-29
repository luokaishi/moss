#!/usr/bin/env python3
"""
MVES v2.0 - 72h 实验验证脚本

实验目标：
1. 验证多模态扩展模块的稳定性
2. 验证 Purpose Dynamics v2 的价值涌现能力
3. 验证 Self-Optimization v3 的进化速度提升
4. 收集 72h 连续运行数据

实验设计：
- 实验时长：72 小时
- 采样频率：每 10 分钟记录一次
- 关键指标：Purpose 稳定性、多模态质量、进化速度
- 对照组：v5.2.0 基线数据
"""

import os
import sys
import json
import time
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict

# 导入 MVES 模块
try:
    from core.multimodal_extension import MultimodalExtension
    from core.purpose_dynamics_v2 import PurposeDynamicsModule, ValueVector
    from core.self_optimization_v3 import SelfOptimizationV3, OptimizationContext
except ImportError:
    # 简化版本用于测试
    MultimodalExtension = None
    PurposeDynamicsModule = None
    SelfOptimizationV3 = None


@dataclass
class ExperimentConfig:
    """实验配置"""
    # 实验参数
    duration_hours: int = 72
    sampling_interval_minutes: int = 10
    random_seed: int = 42
    
    # 实验环境
    environment_type: str = "simulated"  # simulated, real_world
    agent_count: int = 1
    
    # 模块配置
    enable_multimodal: bool = True
    enable_purpose_dynamics: bool = True
    enable_self_optimization: bool = True
    
    # 数据收集
    data_dir: str = "datasets/mves_72h_data"
    checkpoint_interval_hours: int = 1
    
    # 基线对比
    baseline_version: str = "v5.2.0"
    baseline_metrics: Dict = field(default_factory=dict)


@dataclass
class ExperimentMetrics:
    """实验指标"""
    # 时间戳
    timestamp: float = 0.0
    experiment_hour: int = 0
    
    # Purpose 指标
    purpose_stability: float = 0.0
    purpose_clarity: float = 0.0
    attractor_count: int = 0
    
    # 多模态指标
    multimodal_quality: float = 0.0
    cross_modal_consistency: float = 0.0
    num_modalities: int = 0
    
    # 自优化指标
    optimization_count: int = 0
    optimization_success_rate: float = 0.0
    evolution_speed: float = 0.0
    composite_score: float = 0.0
    
    # 系统指标
    resource_usage: float = 0.0
    action_count: int = 0
    error_count: int = 0


@dataclass
class ExperimentState:
    """实验状态"""
    status: str = "initialized"  # initialized, running, paused, completed, failed
    start_time: float = 0.0
    end_time: float = 0.0
    current_hour: int = 0
    total_samples: int = 0
    metrics_history: List[ExperimentMetrics] = field(default_factory=list)
    checkpoints: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class MVES72hExperiment:
    """
    MVES v2.0 72h 实验验证
    
    核心职责：
    1. 运行 72h 连续实验
    2. 收集关键指标数据
    3. 与 v5.2.0 基线对比
    4. 生成实验报告
    """
    
    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.state = ExperimentState()
        
        # 设置随机种子
        np.random.seed(config.random_seed)
        
        # 初始化模块
        self.multimodal = None
        self.purpose_module = None
        self.optimizer = None
        
        if config.enable_multimodal and MultimodalExtension:
            self.multimodal = MultimodalExtension()
        
        if config.enable_purpose_dynamics and PurposeDynamicsModule:
            self.purpose_module = PurposeDynamicsModule()
            if self.multimodal:
                self.purpose_module.set_multimodal_extension(self.multimodal)
        
        if config.enable_self_optimization and SelfOptimizationV3:
            self.optimizer = SelfOptimizationV3()
            if self.multimodal:
                self.optimizer.set_multimodal_extension(self.multimodal)
            if self.purpose_module:
                self.optimizer.set_purpose_module(self.purpose_module)
        
        # 创建数据目录
        os.makedirs(config.data_dir, exist_ok=True)
        
        print(f"🧪 MVES v2.0 72h Experiment Initialized")
        print(f"  Duration: {config.duration_hours}h")
        print(f"  Sampling: every {config.sampling_interval_minutes}min")
        print(f"  Multimodal: {'✓' if self.multimodal else '✗'}")
        print(f"  Purpose Dynamics: {'✓' if self.purpose_module else '✗'}")
        print(f"  Self-Optimization: {'✓' if self.optimizer else '✗'}")
    
    def run(self, quick_test: bool = False) -> ExperimentState:
        """
        运行实验
        
        Args:
            quick_test: 是否快速测试（1 小时而非 72 小时）
        """
        self.state.status = "running"
        self.state.start_time = time.time()
        
        duration = 1 if quick_test else self.config.duration_hours
        total_iterations = int(duration * 60 / self.config.sampling_interval_minutes)
        
        print(f"\n🚀 Starting {duration}h Experiment...")
        print(f"  Total iterations: {total_iterations}")
        print(f"  Data directory: {self.config.data_dir}\n")
        
        try:
            for i in range(total_iterations):
                # 1. 采样指标
                metrics = self._sample_metrics(i)
                self.state.metrics_history.append(metrics)
                self.state.total_samples += 1
                
                # 2. 定期保存 checkpoint
                if (i + 1) % (60 // self.config.sampling_interval_minutes) == 0:
                    self._save_checkpoint(i // (60 // self.config.sampling_interval_minutes))
                
                # 3. 打印进度
                if i % 6 == 0:  # 每小时打印一次
                    self._print_progress(i, metrics)
                
                # 4. 模拟时间流逝（快速测试时加速）
                if quick_test:
                    time.sleep(0.1)  # 快速测试加速
                else:
                    # 真实实验等待采样间隔
                    wait_time = self.config.sampling_interval_minutes * 60
                    print(f"  Waiting {wait_time}s for next sample...")
                    time.sleep(wait_time)
            
            # 完成
            self.state.status = "completed"
            self.state.end_time = time.time()
            self._save_final_results()
            
            print(f"\n✅ Experiment Completed!")
            print(f"  Duration: {(self.state.end_time - self.state.start_time) / 3600:.2f}h")
            print(f"  Total samples: {self.state.total_samples}")
            print(f"  Checkpoints: {len(self.state.checkpoints)}")
            
        except Exception as e:
            self.state.status = "failed"
            self.state.end_time = time.time()
            error_msg = f"Experiment failed at hour {self.state.current_hour}: {str(e)}"
            self.state.errors.append(error_msg)
            print(f"\n❌ {error_msg}")
            raise
        
        return self.state
    
    def _sample_metrics(self, iteration: int) -> ExperimentMetrics:
        """采样当前指标"""
        metrics = ExperimentMetrics()
        metrics.timestamp = time.time()
        metrics.experiment_hour = int(iteration * self.config.sampling_interval_minutes / 60)
        self.state.current_hour = metrics.experiment_hour
        
        # 1. Purpose 指标
        if self.purpose_module:
            purpose_metrics = self.purpose_module.get_stability_metrics()
            metrics.purpose_stability = purpose_metrics.get("stability", 0.0)
            metrics.purpose_clarity = purpose_metrics.get("clarity", 0.0)
            metrics.attractor_count = purpose_metrics.get("attractor_count", 0)
        
        # 2. 多模态指标
        if self.multimodal:
            mves_metrics = self.multimodal.get_optimization_metrics()
            metrics.multimodal_quality = mves_metrics.get("multimodal_quality", 0.0)
            metrics.cross_modal_consistency = mves_metrics.get("cross_modal_consistency", 0.0)
        
        # 3. 自优化指标
        if self.optimizer:
            opt_report = self.optimizer.get_optimization_report()
            if opt_report.get("status") == "success":
                metrics.optimization_count = opt_report.get("total_optimizations", 0)
                metrics.optimization_success_rate = opt_report.get("success_rate", 0.0)
                metrics.evolution_speed = opt_report.get("avg_improvement", 0.0)
        
        # 4. 综合得分
        metrics.composite_score = (
            metrics.purpose_stability * 0.3 +
            metrics.multimodal_quality * 0.25 +
            metrics.cross_modal_consistency * 0.2 +
            metrics.evolution_speed * 0.15 +
            metrics.optimization_success_rate * 0.1
        )
        
        # 5. 模拟系统指标
        metrics.resource_usage = np.random.uniform(0.3, 0.7)
        metrics.action_count = iteration * 100
        metrics.error_count = len(self.state.errors)
        
        return metrics
    
    def _save_checkpoint(self, hour: int):
        """保存 checkpoint"""
        checkpoint_data = {
            "hour": hour,
            "timestamp": time.time(),
            "metrics": [asdict(m) for m in self.state.metrics_history[-6:]],  # 最近 1 小时
            "state": asdict(self.state)
        }
        
        filename = f"{self.config.data_dir}/checkpoint_hour{hour:03d}.json"
        with open(filename, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)
        
        self.state.checkpoints.append(filename)
    
    def _print_progress(self, iteration: int, current_metrics: ExperimentMetrics):
        """打印进度"""
        hour = iteration * self.config.sampling_interval_minutes / 60
        print(f"Hour {hour:5.1f} | "
              f"Stability: {current_metrics.purpose_stability:.3f} | "
              f"MM Quality: {current_metrics.multimodal_quality:.3f} | "
              f"Evolution: {current_metrics.evolution_speed:.3f} | "
              f"Composite: {current_metrics.composite_score:.3f}")
    
    def _save_final_results(self):
        """保存最终结果"""
        # 1. 完整数据
        full_data = {
            "config": asdict(self.config),
            "state": asdict(self.state),
            "metrics": [asdict(m) for m in self.state.metrics_history],
            "checkpoints": self.state.checkpoints,
            "errors": self.state.errors
        }
        
        filename = f"{self.config.data_dir}/mves_72h_full_results.json"
        with open(filename, 'w') as f:
            json.dump(full_data, f, indent=2)
        
        # 2. 实验报告
        report = self._generate_report()
        report_filename = f"{self.config.data_dir}/mves_72h_experiment_report.md"
        with open(report_filename, 'w') as f:
            f.write(report)
        
        # 3. 指标摘要
        summary = self._calculate_summary()
        summary_filename = f"{self.config.data_dir}/mves_72h_summary.json"
        with open(summary_filename, 'w') as f:
            json.dump(summary, f, indent=2)
    
    def _generate_report(self) -> str:
        """生成实验报告"""
        summary = self._calculate_summary()
        
        report = f"""# MVES v2.0 72h 实验报告

**实验时间：** {datetime.fromtimestamp(self.state.start_time).isoformat()} - {datetime.fromtimestamp(self.state.end_time).isoformat()}  
**实验时长：** {(self.state.end_time - self.state.start_time) / 3600:.2f} 小时  
**采样次数：** {self.state.total_samples}  
**实验状态：** {self.state.status}

---

## 📊 核心指标对比

| 指标 | v5.2.0 基线 | MVES v2.0 | 提升 | 目标 | 状态 |
|------|-------------|-----------|------|------|------|
| Purpose 稳定性 | 94% | {summary['avg_purpose_stability']:.1%} | {summary['purpose_stability_improvement']:+.1%} | >96% | {'✅' if summary['avg_purpose_stability'] > 0.96 else '🟡'} |
| 多模态质量 | N/A | {summary['avg_multimodal_quality']:.1%} | - | >85% | {'✅' if summary['avg_multimodal_quality'] > 0.85 else '🟡'} |
| 进化速度 | 基准 | {summary['avg_evolution_speed']:.3f} | +{summary['evolution_speed_improvement']:.1%} | +15% | {'✅' if summary['evolution_speed_improvement'] > 15 else '🟡'} |
| 72h 成功率 | 100% | {'100%' if self.state.status == 'completed' else '0%'} | - | 100% | {'✅' if self.state.status == 'completed' else '❌'} |

---

## 📈 指标趋势

### Purpose 稳定性
- 初始值：{summary['initial_purpose_stability']:.3f}
- 最终值：{summary['final_purpose_stability']:.3f}
- 平均值：{summary['avg_purpose_stability']:.3f}
- 标准差：{summary['purpose_stability_std']:.3f}

### 多模态质量
- 初始值：{summary['initial_multimodal_quality']:.3f}
- 最终值：{summary['final_multimodal_quality']:.3f}
- 平均值：{summary['avg_multimodal_quality']:.3f}

### 进化速度
- 平均改进：{summary['avg_evolution_speed']:.3f}
- 优化次数：{summary['total_optimizations']}
- 成功率：{summary['optimization_success_rate']:.1%}

---

## 🎯 目标达成情况

| 目标 | 达成情况 |
|------|----------|
| Purpose 稳定性 > 96% | {'✅ 达成' if summary['avg_purpose_stability'] > 0.96 else '❌ 未达成'} |
| 多模态质量 > 85% | {'✅ 达成' if summary['avg_multimodal_quality'] > 0.85 else '❌ 未达成'} |
| 进化速度 +15% | {'✅ 达成' if summary['evolution_speed_improvement'] > 15 else '❌ 未达成'} |
| 72h 成功率 100% | {'✅ 达成' if self.state.status == 'completed' else '❌ 未达成'} |

---

## ⚠️ 问题与改进

### 发现的问题
{chr(10).join('- ' + e for e in self.state.errors) if self.state.errors else '无'}

### 改进建议
1. {'Purpose 稳定性需进一步提升' if summary['avg_purpose_stability'] < 0.96 else 'Purpose 稳定性表现良好'}
2. {'多模态质量有优化空间' if summary['avg_multimodal_quality'] < 0.85 else '多模态质量达标'}
3. {'进化速度提升未达预期' if summary['evolution_speed_improvement'] < 15 else '进化速度提升显著'}

---

## 📁 数据文件

- **完整数据：** `mves_72h_full_results.json`
- **指标摘要：** `mves_72h_summary.json`
- **Checkpoints：** {len(self.state.checkpoints)} 个

---

**实验结论：** MVES v2.0 {'通过' if self.state.status == 'completed' and summary['avg_purpose_stability'] > 0.96 else '需进一步优化'} 72h 验证

**报告生成时间：** {datetime.now().isoformat()}
"""
        return report
    
    def _calculate_summary(self) -> Dict:
        """计算摘要统计"""
        if not self.state.metrics_history:
            return {}
        
        metrics = self.state.metrics_history
        
        # Purpose 稳定性
        purpose_values = [m.purpose_stability for m in metrics]
        
        # 多模态质量
        mm_values = [m.multimodal_quality for m in metrics]
        
        # 进化速度
        evolution_values = [m.evolution_speed for m in metrics]
        
        # 优化统计
        total_opts = metrics[-1].optimization_count if metrics else 0
        success_rate = metrics[-1].optimization_success_rate if metrics else 0.0
        
        # 基线对比（假设 v5.2.0 Purpose 稳定性 94%）
        baseline_stability = 0.94
        
        return {
            "avg_purpose_stability": np.mean(purpose_values),
            "final_purpose_stability": purpose_values[-1] if purpose_values else 0.0,
            "initial_purpose_stability": purpose_values[0] if purpose_values else 0.0,
            "purpose_stability_std": np.std(purpose_values),
            "purpose_stability_improvement": np.mean(purpose_values) - baseline_stability,
            
            "avg_multimodal_quality": np.mean(mm_values),
            "final_multimodal_quality": mm_values[-1] if mm_values else 0.0,
            "initial_multimodal_quality": mm_values[0] if mm_values else 0.0,
            
            "avg_evolution_speed": np.mean(evolution_values),
            "evolution_speed_improvement": np.mean(evolution_values) * 100,  # 转换为百分比
            
            "total_optimizations": total_opts,
            "optimization_success_rate": success_rate,
            
            "experiment_duration_hours": (self.state.end_time - self.state.start_time) / 3600,
            "total_samples": self.state.total_samples,
            "status": self.state.status
        }


def run_quick_test():
    """运行快速测试（1 小时而非 72 小时）"""
    print("🧪 Running MVES v2.0 Quick Test (1h)...\n")
    
    config = ExperimentConfig(
        duration_hours=1,
        sampling_interval_minutes=1,
        data_dir="datasets/mves_quick_test"
    )
    
    experiment = MVES72hExperiment(config)
    state = experiment.run(quick_test=True)
    
    print(f"\n📊 Quick Test Results:")
    print(f"  Status: {state.status}")
    print(f"  Samples: {state.total_samples}")
    print(f"  Checkpoints: {len(state.checkpoints)}")
    
    return state


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="MVES v2.0 72h Experiment")
    parser.add_argument("--quick", action="store_true", help="Run quick test (1h)")
    parser.add_argument("--hours", type=int, default=72, help="Experiment duration")
    args = parser.parse_args()
    
    if args.quick:
        run_quick_test()
    else:
        config = ExperimentConfig(duration_hours=args.hours)
        experiment = MVES72hExperiment(config)
        experiment.run()

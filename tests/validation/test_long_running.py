#!/usr/bin/env python3
"""
B.3 长期运行稳定性测试

测试目标:
- 72小时连续运行UnifiedMOSSAgent
- 监控内存泄漏
- 监控错误率
- 监控性能稳定性
- 记录关键指标到日志

运行方式:
  python3 tests/validation/test_long_running.py --hours 72

快速验证:
  python3 tests/validation/test_long_running.py --hours 0.1
"""

import argparse
import gc
import json
import logging
import os
import sys
import time
import traceback
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Optional

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import numpy as np


@dataclass
class Checkpoint:
    """运行检查点"""
    elapsed_hours: float
    step_count: int
    memory_mb: float
    error_count: int
    avg_reward: float
    success_rate: float
    coherence_score: float
    norm_strength: float
    avg_trust: float
    weights: List[float]
    timestamp: float = 0.0

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class LongRunningTest:
    """长期运行测试框架"""

    def __init__(self, hours: float = 72, checkpoint_interval: int = 3600):
        self.target_hours = hours
        self.checkpoint_interval = checkpoint_interval  # 秒
        self.checkpoints: List[Checkpoint] = []
        self.errors: List[Dict] = []
        self.start_time = None
        self.agent = None

        # 配置日志
        log_dir = Path(__file__).parent.parent / 'test_results' / 'long_running'
        log_dir.mkdir(parents=True, exist_ok=True)

        self.log_path = log_dir / 'long_running.log'
        self.result_path = log_dir / 'result.json'

        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] %(levelname)s [%(name)s] %(message)s',
            handlers=[
                logging.FileHandler(self.log_path),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('long_running_test')

    def setup(self):
        """初始化Agent"""
        from moss.core import UnifiedMOSSAgent, MOSSConfig

        config = MOSSConfig(
            enable_survival=True,
            enable_curiosity=True,
            enable_influence=True,
            enable_optimization=True,
            enable_coherence=True,
            enable_valence=True,
            enable_other=True,
            enable_norm=True,
            enable_purpose=True,
        )

        self.agent = UnifiedMOSSAgent(config)
        self.logger.info(f"Agent初始化完成: {self.agent.agent_id}, 维度: {self.agent._get_enabled_dimensions()}")

    def get_memory_usage(self) -> float:
        """获取当前进程内存使用(MB)"""
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            # 回退: 使用垃圾回收估算
            gc.collect()
            # 简化估算
            return 0.0

    def take_checkpoint(self) -> Checkpoint:
        """记录检查点"""
        elapsed = (time.time() - self.start_time) / 3600  # 小时
        step_count = self.agent.step_count

        # 计算平均奖励
        rewards = []
        if self.agent.history:
            recent = self.agent.history[-100:]
            rewards = [r.reward for r in recent]
        avg_reward = float(np.mean(rewards)) if rewards else 0.0

        # 成功率
        success_rate = 0.0
        if self.agent.history:
            recent = self.agent.history[-100:]
            success_rate = sum(1 for r in recent if r.success) / len(recent)

        # 维度指标
        coherence = self.agent.dimensions.get('coherence', None)
        coherence_score = coherence.get_score() if coherence and hasattr(coherence, 'get_score') else 0.0

        norm = self.agent.dimensions.get('norm', None)
        norm_summary = norm.get_summary() if norm and hasattr(norm, 'get_summary') else {}
        norm_strength = norm_summary.get('avg_norm_strength', 0.0)

        other = self.agent.dimensions.get('other', None)
        other_summary = other.get_summary() if other and hasattr(other, 'get_summary') else {}
        avg_trust = other_summary.get('avg_trust', 0.0)

        # 权重
        weights = self.agent.weights.tolist()

        # 内存
        memory_mb = self.get_memory_usage()

        # 错误数
        error_count = len(self.errors)

        checkpoint = Checkpoint(
            elapsed_hours=round(elapsed, 4),
            step_count=step_count,
            memory_mb=round(memory_mb, 2),
            error_count=error_count,
            avg_reward=round(avg_reward, 6),
            success_rate=round(success_rate, 4),
            coherence_score=round(coherence_score, 4),
            norm_strength=round(norm_strength, 4),
            avg_trust=round(avg_trust, 2),
            weights=[round(w, 4) for w in weights],
        )

        self.checkpoints.append(checkpoint)
        return checkpoint

    def run(self):
        """运行长期测试"""
        self.setup()
        self.start_time = time.time()
        target_seconds = self.target_hours * 3600

        self.logger.info("=" * 60)
        self.logger.info(f"长期运行测试开始")
        self.logger.info(f"目标: {self.target_hours}小时 ({self.target_hours*3600:.0f}秒)")
        self.logger.info(f"检查点间隔: {self.checkpoint_interval}秒")
        self.logger.info("=" * 60)

        # 初始检查点
        self.take_checkpoint()
        self.logger.info(f"初始检查点: step={self.agent.step_count}")

        last_checkpoint = time.time()
        step_batch_size = 100  # 每批执行100步
        total_steps = 0

        try:
            while True:
                elapsed = time.time() - self.start_time

                # 检查是否到达目标时间
                if elapsed >= target_seconds:
                    self.logger.info(f"达到目标时间 {self.target_hours}小时")
                    break

                # 执行一批步骤
                try:
                    for _ in range(step_batch_size):
                        self.agent.step()
                    total_steps += step_batch_size
                except Exception as e:
                    error_info = {
                        'elapsed_hours': round(elapsed / 3600, 4),
                        'step_count': self.agent.step_count,
                        'error': str(e),
                        'traceback': traceback.format_exc(),
                    }
                    self.errors.append(error_info)
                    self.logger.error(f"步骤错误 at step {self.agent.step_count}: {e}")

                    # 尝试恢复
                    try:
                        self.agent.state = type(self.agent.state)('idle') if hasattr(self.agent.state, '__class__') else 'idle'
                        self.logger.info("Agent状态重置为idle")
                    except:
                        pass

                # 检查点
                now = time.time()
                if now - last_checkpoint >= self.checkpoint_interval:
                    cp = self.take_checkpoint()
                    progress = elapsed / target_seconds * 100
                    self.logger.info(
                        f"[{progress:.1f}%] {cp.elapsed_hours:.2f}h | "
                        f"steps={cp.step_count} | "
                        f"mem={cp.memory_mb:.1f}MB | "
                        f"reward={cp.avg_reward:.3f} | "
                        f"success={cp.success_rate:.2%} | "
                        f"coherence={cp.coherence_score:.3f} | "
                        f"errors={cp.error_count}"
                    )
                    last_checkpoint = now

                # 每10批做一次垃圾回收（防止内存膨胀）
                if total_steps % 1000 == 0:
                    gc.collect()

        except KeyboardInterrupt:
            self.logger.info("测试被用户中断")
        except Exception as e:
            self.logger.error(f"测试致命错误: {e}")
            self.errors.append({
                'elapsed_hours': round((time.time() - self.start_time) / 3600, 4),
                'error': str(e),
                'traceback': traceback.format_exc(),
            })

        # 最终检查点
        final_cp = self.take_checkpoint()
        total_elapsed = (time.time() - self.start_time) / 3600

        self.logger.info("=" * 60)
        self.logger.info("长期运行测试结束")
        self.logger.info("=" * 60)
        self.logger.info(f"总运行时间: {total_elapsed:.2f}小时")
        self.logger.info(f"总步骤数: {final_cp.step_count}")
        self.logger.info(f"总错误数: {final_cp.error_count}")
        self.logger.info(f"最终内存: {final_cp.memory_mb:.1f}MB")
        self.logger.info(f"平均奖励: {final_cp.avg_reward:.3f}")
        self.logger.info(f"成功率: {final_cp.success_rate:.2%}")
        self.logger.info(f"连续性: {final_cp.coherence_score:.3f}")

        # 保存结果
        self._save_result(total_elapsed)

        return final_cp

    def _save_result(self, total_elapsed: float):
        """保存测试结果"""
        result = {
            'test': 'B.3 Long Running Stability Test',
            'target_hours': self.target_hours,
            'actual_hours': round(total_elapsed, 4),
            'total_checkpoints': len(self.checkpoints),
            'total_errors': len(self.errors),
            'checkpoints': [asdict(cp) for cp in self.checkpoints],
            'errors': self.errors[:50],  # 最多保存50个错误
            'summary': self._compute_summary(),
        }

        with open(self.result_path, 'w') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        self.logger.info(f"结果已保存: {self.result_path}")

    def _compute_summary(self) -> Dict:
        """计算测试摘要"""
        if not self.checkpoints:
            return {}

        first = self.checkpoints[0]
        last = self.checkpoints[-1]

        # 内存变化
        memory_delta = last.memory_mb - first.memory_mb if first.memory_mb > 0 else 0

        # 步骤速率
        elapsed = last.elapsed_hours - first.elapsed_hours
        steps_per_hour = (last.step_count - first.step_count) / elapsed if elapsed > 0 else 0

        # 奖励趋势
        rewards = [cp.avg_reward for cp in self.checkpoints if cp.avg_reward != 0]
        reward_trend = 0
        if len(rewards) >= 2:
            reward_trend = rewards[-1] - rewards[0]

        # 连续性趋势
        coherences = [cp.coherence_score for cp in self.checkpoints]
        coherence_trend = coherences[-1] - coherences[0] if len(coherences) >= 2 else 0

        # 判断内存泄漏
        memory_leak_detected = memory_delta > 100  # 增长超过100MB视为泄漏

        # 判断稳定性
        is_stable = (
            last.error_count == 0 and
            not memory_leak_detected and
            abs(reward_trend) < 0.5
        )

        return {
            'total_steps': last.step_count,
            'steps_per_hour': round(steps_per_hour, 1),
            'memory_start_mb': first.memory_mb,
            'memory_end_mb': last.memory_mb,
            'memory_delta_mb': round(memory_delta, 2),
            'memory_leak_detected': memory_leak_detected,
            'reward_trend': round(reward_trend, 4),
            'coherence_trend': round(coherence_trend, 4),
            'final_success_rate': last.success_rate,
            'final_coherence': last.coherence_score,
            'error_rate': len(self.errors) / max(last.step_count, 1),
            'is_stable': is_stable,
        }


def main():
    parser = argparse.ArgumentParser(description='MOSS长期运行稳定性测试')
    parser.add_argument('--hours', type=float, default=72, help='运行时间(小时)')
    parser.add_argument('--checkpoint-interval', type=int, default=3600, help='检查点间隔(秒)')
    args = parser.parse_args()

    test = LongRunningTest(hours=args.hours, checkpoint_interval=args.checkpoint_interval)
    test.run()


if __name__ == '__main__':
    main()

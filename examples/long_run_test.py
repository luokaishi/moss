#!/usr/bin/env python3
"""
AGI Agent 长时间运行测试
目标：运行10,000周期，观察涌现、记忆演化和长期行为模式
"""

import os
import sys
import time
import json
import logging
from datetime import datetime

# 确保可以导入moss包
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agi.agent import AGIAgent


class LongRunAgent(AGIAgent):
    """长时间运行Agent，增加内存管理和状态保存功能"""
    
    def __init__(self, config_path: str):
        super().__init__(config_path)
        self.checkpoint_interval = 100  # 每100周期检查点
        self.last_checkpoint = 0
        # 每次运行使用独立目录，避免多次运行检查点冲突
        self.run_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.run_dir = f"logs/long_run_test/run_{self.run_id}"
        self.log_file = os.path.join(self.run_dir, "agent.log")
        
        # 设置文件日志
        self._setup_file_logging()
        
    def _setup_file_logging(self):
        """设置文件日志"""
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter('%(asctime)s [%(name)s] %(levelname)s: %(message)s')
        file_handler.setFormatter(file_formatter)
        logger = logging.getLogger('AGIAgent')
        logger.addHandler(file_handler)
        
    def run_with_checkpoints(self, max_cycles: int = 10000):
        """
        长时间运行，带检查点保存
        """
        logger = logging.getLogger('AGIAgent')
        logger.info(f"=== 长时间运行测试开始 ===")
        logger.info(f"目标周期: {max_cycles}")
        logger.info(f"检查点间隔: {self.checkpoint_interval}")
        logger.info(f"日志文件: {self.log_file}")
        
        start_time = time.time()
        
        try:
            for cycle in range(1, max_cycles + 1):
                if not self.alive:
                    logger.info("Agent停止运行")
                    break
                    
                self.cycle = cycle
                
                # 执行一个周期
                try:
                    self._one_cycle()
                except Exception as e:
                    logger.error(f"周期 {cycle} 执行错误: {e}")
                    # 继续运行，不停止
                    continue
                
                # 周期性检查点
                if cycle % self.checkpoint_interval == 0:
                    self._save_checkpoint(cycle)
                    self._log_status(cycle, start_time)
                    
        except KeyboardInterrupt:
            logger.info("用户中断运行")
        except Exception as e:
            logger.error(f"运行过程中发生严重错误: {e}")
        finally:
            self._save_final_report(start_time)
            
    def _save_checkpoint(self, cycle: int):
        """保存检查点（带错误处理和JSON安全序列化）"""
        checkpoint_dir = os.path.join(self.run_dir, "checkpoints")
        os.makedirs(checkpoint_dir, exist_ok=True)
        
        try:
            checkpoint_data = {
                'cycle': cycle,
                'timestamp': datetime.now().isoformat(),
                'drives': self.drive_manager.get_drive_summary(),
                'behavior': self.behavior_tracker.get_behavior_summary(),
                'memory': self.memory.get_stats(),
                'env': self.env.get_stats(),
                'emerged_drives': list(self._emerged_drives),
                'drive_names': list(self.drive_manager.drives.keys())  # 冗余保护
            }
            
            checkpoint_file = os.path.join(checkpoint_dir, f"checkpoint_{cycle:06d}.json")
            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2, default=str)
                
            logger = logging.getLogger('AGIAgent')
            logger.info(f"检查点保存: {checkpoint_file}")
        except Exception as e:
            logger = logging.getLogger('AGIAgent')
            logger.error(f"检查点保存失败(周期{cycle}): {e}")
        
    def _log_status(self, cycle: int, start_time: float):
        """记录状态日志"""
        elapsed = time.time() - start_time
        cycles_per_sec = cycle / elapsed if elapsed > 0 else 0
        
        drives = self.drive_manager.get_drive_summary()
        behavior = self.behavior_tracker.get_behavior_summary()
        env_stats = self.env.get_stats()
        
        logger = logging.getLogger('AGIAgent')
        logger.info(f"--- 状态报告 周期 {cycle} ---")
        logger.info(f"  运行时间: {elapsed:.1f}s, 速率: {cycles_per_sec:.2f}周期/秒")
        logger.info(f"  驱动力: {len(drives)}个")
        logger.info(f"  涌现驱动力: {len(self._emerged_drives)}个")
        logger.info(f"  行为总数: {behavior.get('total', 0)}")
        logger.info(f"  成功率: {behavior.get('success_rate', 0):.1%}")
        logger.info(f"  环境命令: {env_stats.get('total_actions', 0)}")
        logger.info(f"  错误数: {env_stats.get('error_count', 0)}")
        
    def _save_final_report(self, start_time: float):
        """保存最终报告"""
        try:
            final_report = {
                'total_cycles': self.cycle,
                'elapsed_seconds': time.time() - start_time,
                'start_time': datetime.fromtimestamp(start_time).isoformat(),
                'end_time': datetime.now().isoformat(),
                'drives': self.drive_manager.get_drive_summary(),
                'behavior': self.behavior_tracker.get_behavior_summary(),
                'memory': self.memory.get_stats(),
                'env': self.env.get_stats(),
                'emerged_drives': list(self._emerged_drives),
                'emergence_history': self.emergence_detector.get_history()
            }
            
            report_file = os.path.join(self.run_dir, "final_report.json")
            with open(report_file, 'w') as f:
                json.dump(final_report, f, indent=2, default=str)
        except Exception as e:
            logger = logging.getLogger('AGIAgent')
            logger.error(f"最终报告保存失败: {e}")
            
        # 生成文本报告
        txt_report = self._generate_text_report(final_report)
        txt_file = report_file.replace('.json', '.txt')
        with open(txt_file, 'w') as f:
            f.write(txt_report)
            
        logger = logging.getLogger('AGIAgent')
        logger.info(f"最终报告已保存: {report_file}")
        logger.info(f"文本报告已保存: {txt_file}")
        
    def _generate_text_report(self, report_data: dict) -> str:
        """生成文本格式报告"""
        lines = []
        lines.append("=" * 60)
        lines.append("AGI Agent 长时间运行测试 - 最终报告")
        lines.append("=" * 60)
        lines.append(f"总周期数: {report_data['total_cycles']}")
        lines.append(f"运行时间: {report_data['elapsed_seconds']:.1f}秒")
        lines.append(f"开始时间: {report_data['start_time']}")
        lines.append(f"结束时间: {report_data['end_time']}")
        lines.append("")
        
        lines.append("驱动力统计:")
        for name, info in report_data['drives'].items():
            marker = " [EMERGED]" if info.get('is_emergent') else ""
            lines.append(f"  {name}: 权重={info.get('weight', 0):.3f}, 稳定性={info.get('stability', 0):.2f}{marker}")
        
        lines.append("")
        lines.append(f"涌现驱动力 ({len(report_data['emerged_drives'])}个):")
        for drive in report_data['emerged_drives']:
            lines.append(f"  - {drive}")
            
        lines.append("")
        lines.append(f"行为统计: {report_data['behavior'].get('total', 0)}次行动")
        lines.append(f"成功率: {report_data['behavior'].get('success_rate', 0):.1%}")
        lines.append(f"变化检测: {report_data['behavior'].get('changes_detected', 0)}次")
        
        lines.append("")
        lines.append(f"记忆统计: {report_data['memory'].get('total_records', 0)}条记录")
        lines.append(f"平均重要性: {report_data['memory'].get('avg_importance', 0):.2f}")
        
        lines.append("")
        lines.append(f"环境统计:")
        lines.append(f"  命令执行: {report_data['env'].get('total_actions', 0)}次")
        lines.append(f"  错误数: {report_data['env'].get('error_count', 0)}次")
        lines.append(f"  错误率: {report_data['env'].get('error_rate', 0):.1%}")
        
        lines.append("")
        lines.append(f"涌现事件历史: {len(report_data['emergence_history'])}次")
        for i, event in enumerate(report_data['emergence_history'][-5:], 1):
            lines.append(f"  {i}. {event.get('timestamp', '')}: {event.get('drive', {}).get('name', 'unknown')}")
        
        lines.append("=" * 60)
        return "\n".join(lines)


def main():
    """主函数"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'agent_config.yaml')
    
    print("=" * 60)
    print("  AGI Agent 长时间运行测试")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"目标周期: 10,000")
    print(f"检查点间隔: 100周期")
    print(f"日志目录: logs/long_run_test/")
    print("=" * 60)
    print()
    
    # 创建长时间运行Agent
    agent = LongRunAgent(config_path)
    
    # 运行
    try:
        agent.run_with_checkpoints(max_cycles=10000)
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n运行过程中发生错误: {e}")
        
    print(f"\n测试完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()
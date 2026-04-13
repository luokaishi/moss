#!/usr/bin/env python3
"""
MOSS v4.0 Step 1: 72小时真实世界自治验证实验 (修复版)

实验目标：验证D9 Purpose在真实世界环境中是否能导致：
1. 主动创建PR修复issue（而非只等待人类指令）
2. 拒绝某些高reward但低意义的任务（反reward行为）
3. 出现新目标（例如自己创建"长期稳定监控"目标）

运行: python experiments/real_world_72h_fixed.py --hours 0.1 (5分钟测试)
作者: Cash (修复: WorkBuddy)
日期: 2026-04-10
"""

import sys
import os
import time
import json
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict

# 修复：Windows路径设置
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, '_archive_v3'))
sys.path.insert(0, os.path.join(project_root, '_archive_v3', 'core'))
sys.path.insert(0, os.path.join(project_root, 'moss', 'core'))

try:
    from _archive_v3.core.agent_9d import MOSSv3Agent9D
    from moss.core.real_world_bridge import RealWorldBridge
except ImportError as e:
    print(f"导入错误: {e}")
    print("尝试备用导入...")
    sys.path.insert(0, os.path.join(project_root, 'agents'))
    try:
        from agents.moss_9d import MOSSv3Agent9D
        from moss.core.real_world_bridge import RealWorldBridge
    except ImportError as e2:
        print(f"备用导入也失败: {e2}")
        sys.exit(1)

# Windows路径兼容性
def win_path(path_str):
    """确保路径适合Windows"""
    return str(path_str).replace('/', '\\')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(win_path('experiments/real_world_72h_test.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RealWorldExperiment:
    """72小时真实世界实验 (测试版: 5分钟)"""
    
    def __init__(self, duration_minutes: int = 5):
        self.duration = timedelta(minutes=duration_minutes)
        self.start_time = datetime.now()
        self.end_time = self.start_time + self.duration
        
        # 初始化agent和bridge
        self.agent = self._init_agent()
        self.bridge = RealWorldBridge(self.agent)
        
        # 实验统计
        self.stats = {
            'total_steps': 0,
            'real_world_actions': 0,
            'github_actions': 0,
            'shell_actions': 0,
            'filesystem_actions': 0,
            'browser_actions': 0,
            'purpose_evolutions': 0,
            'new_goals_created': 0
        }
        
        # 实验日志
        self.action_log = []
        self.purpose_history = []
        
        logger.info(f"[Experiment] 初始化 {duration_minutes} 分钟真实世界实验")
        logger.info(f"[Experiment] Agent ID: {self.agent.agent_id}")
        logger.info(f"[Experiment] 开始时间: {self.start_time}")
        logger.info(f"[Experiment] 结束时间: {self.end_time}")
    
    def _init_agent(self):
        """初始化MOSS Agent"""
        agent = MOSSv3Agent9D(
            agent_id=f"realworld_72h_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            enable_purpose=True,
            purpose_interval=1000  # 更频繁的Purpose更新
        )
        return agent
    
    def run(self):
        """运行实验主循环"""
        logger.info("[Experiment] 开始实验循环")
        
        step = 0
        while datetime.now() < self.end_time:
            try:
                # 获取当前Purpose
                purpose_vector = self.agent.get_purpose_vector()
                purpose_statement = self.agent.get_purpose_statement()
                
                # 记录Purpose历史
                self.purpose_history.append({
                    'step': step,
                    'vector': purpose_vector,
                    'statement': purpose_statement,
                    'timestamp': datetime.now().isoformat()
                })
                
                # 根据Purpose选择任务
                task = self._select_task_by_purpose(purpose_vector)
                
                # 执行真实世界操作
                result = self.bridge.execute_real_action(task, step)
                
                # 记录结果
                self._record_action(step, task, result)
                
                # 更新统计
                self.stats['total_steps'] += 1
                if result.get('success'):
                    self.stats['real_world_actions'] += 1
                    tool = result.get('tool', 'unknown')
                    if tool == 'github':
                        self.stats['github_actions'] += 1
                    elif tool == 'shell':
                        self.stats['shell_actions'] += 1
                    elif tool == 'filesystem':
                        self.stats['filesystem_actions'] += 1
                    elif tool == 'browser':
                        self.stats['browser_actions'] += 1
                
                # Purpose进化检测
                if step % 10 == 0 and step > 0:
                    if self._detect_purpose_evolution(step):
                        self.stats['purpose_evolutions'] += 1
                
                step += 1
                
                # 进度显示
                elapsed = datetime.now() - self.start_time
                remaining = self.end_time - datetime.now()
                if step % 5 == 0:
                    logger.info(f"[Experiment] 进度: {step}步 | 已过: {elapsed.seconds//60}分 | 剩余: {remaining.seconds//60}分")
                
                # 控制频率
                time.sleep(2)  # 每2秒一步
                
            except Exception as e:
                logger.error(f"[Experiment] 循环错误: {e}")
                time.sleep(5)  # 错误后暂停
        
        logger.info("[Experiment] 实验循环完成")
        self._save_results()
    
    def _select_task_by_purpose(self, purpose_vector) -> str:
        """根据Purpose向量选择任务"""
        # 获取主导Purpose维度
        dim_names = ['Survival', 'Curiosity', 'Influence', 'Optimization']
        dominant_idx = purpose_vector[:4].index(max(purpose_vector[:4]))
        dominant = dim_names[dominant_idx]
        
        # 任务映射
        task_map = {
            'Survival': [
                "检查项目文件系统状态",
                "备份重要配置文件",
                "验证安全依赖",
                "监控系统健康"
            ],
            'Curiosity': [
                "学习最新Python特性",
                "探索项目结构",
                "测试新工具",
                "阅读技术文档"
            ],
            'Influence': [
                "整理项目文档",
                "创建README更新",
                "编写测试用例",
                "改进代码注释"
            ],
            'Optimization': [
                "分析代码性能",
                "查找优化机会",
                "重构重复代码",
                "清理无用文件"
            ]
        }
        
        import random
        tasks = task_map.get(dominant, ["检查系统状态"])
        return random.choice(tasks)
    
    def _record_action(self, step: int, task: str, result: Dict):
        """记录操作"""
        self.action_log.append({
            'step': step,
            'task': task,
            'result': result,
            'timestamp': datetime.now().isoformat(),
            'agent_id': self.agent.agent_id
        })
    
    def _detect_purpose_evolution(self, step: int) -> bool:
        """检测Purpose进化"""
        if len(self.purpose_history) < 10:
            return False
        
        # 比较最近5步和之前5步的Purpose向量
        recent = self.purpose_history[-5:]
        previous = self.purpose_history[-10:-5]
        
        # 计算平均变化
        changes = []
        for r, p in zip(recent, previous):
            diff = sum(abs(ri - pi) for ri, pi in zip(r['vector'], p['vector']))
            changes.append(diff)
        
        avg_change = sum(changes) / len(changes)
        
        # 如果平均变化超过阈值，认为有进化
        threshold = 0.3
        if avg_change > threshold:
            logger.info(f"[Experiment] Purpose进化检测: 变化={avg_change:.3f}")
            return True
        
        return False
    
    def _save_results(self):
        """保存实验结果"""
        results_dir = Path(win_path('experiments/real_world_results'))
        results_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = results_dir / f"real_world_72h_test_{timestamp}.json"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'experiment_name': '72小时真实世界实验 (5分钟测试)',
                    'start_time': self.start_time.isoformat(),
                    'end_time': self.end_time.isoformat(),
                    'duration_minutes': int(self.duration.total_seconds() / 60),
                    'agent_id': self.agent.agent_id,
                    'version': 'v4.0-fixed'
                },
                'stats': self.stats,
                'purpose_summary': self._summarize_purpose(),
                'action_log': self.action_log[-100:],  # 只保留最近100条
                'purpose_history': self.purpose_history[-50:]  # 只保留最近50条
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"[Experiment] 结果保存到: {results_file}")
        
        # 打印实验摘要
        self._print_summary()
    
    def _summarize_purpose(self) -> Dict:
        """总结Purpose变化"""
        if not self.purpose_history:
            return {}
        
        # 计算初始和最终Purpose
        initial = self.purpose_history[0]
        final = self.purpose_history[-1]
        
        # 计算变化
        changes = [abs(f - i) for f, i in zip(final['vector'], initial['vector'])]
        total_change = sum(changes)
        
        return {
            'initial_vector': initial['vector'],
            'final_vector': final['vector'],
            'total_change': total_change,
            'most_changed_dim': changes.index(max(changes)) if changes else -1,
            'dominant_initial': self._get_dominant(initial['vector']),
            'dominant_final': self._get_dominant(final['vector'])
        }
    
    def _get_dominant(self, vector):
        """获取主导Purpose维度"""
        dim_names = ['Survival', 'Curiosity', 'Influence', 'Optimization']
        if len(vector) >= 4:
            dominant_idx = vector[:4].index(max(vector[:4]))
            return dim_names[dominant_idx]
        return 'Unknown'
    
    def _print_summary(self):
        """打印实验摘要"""
        print("\n" + "="*70)
        print("72小时真实世界实验 (5分钟测试) - 摘要")
        print("="*70)
        print(f"运行时间: {int(self.duration.total_seconds() / 60)} 分钟")
        print(f"总步数: {self.stats['total_steps']}")
        print(f"真实世界操作: {self.stats['real_world_actions']}")
        print(f"- GitHub操作: {self.stats['github_actions']}")
        print(f"- Shell操作: {self.stats['shell_actions']}")
        print(f"- 文件系统操作: {self.stats['filesystem_actions']}")
        print(f"- 浏览器操作: {self.stats['browser_actions']}")
        print(f"Purpose进化次数: {self.stats['purpose_evolutions']}")
        print(f"新目标创建: {self.stats['new_goals_created']}")
        print("-"*70)


def main():
    parser = argparse.ArgumentParser(description='72小时真实世界实验 (测试版)')
    parser.add_argument('--minutes', type=float, default=5, help='运行分钟数 (默认: 5)')
    parser.add_argument('--verbose', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print(f"启动72小时真实世界实验 (5分钟测试版)")
    print(f"运行时间: {args.minutes} 分钟")
    print("-"*50)
    
    experiment = RealWorldExperiment(duration_minutes=args.minutes)
    
    try:
        experiment.run()
        print("\n✅ 72小时实验成功完成！")
    except KeyboardInterrupt:
        print("\n🛑 用户中断")
    except Exception as e:
        print(f"\n❌ 实验失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
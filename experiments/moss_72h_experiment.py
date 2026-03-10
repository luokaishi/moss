#!/usr/bin/env python3
"""
MOSS 72-Hour Real Autonomous Experiment (Simplified Version)
使用火山引擎ARK生态系统的简化版本

实验目标: 验证MOSS在72小时真实环境中保持四目标平衡的能力
环境: 火山引擎ARK (豆包搜索、知识库、记忆存储)
"""

import os
import sys
import time
import json
import random
import signal
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import threading
import queue

# 尝试导入OpenAI客户端
try:
    from openai import OpenAI
    CLIENT_AVAILABLE = True
except ImportError:
    CLIENT_AVAILABLE = False
    print("[ERROR] openai package required")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('moss_72h_experiment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MOSS72HourExperiment:
    """
    MOSS 72小时真实自主实验
    
    使用ARK生态系统:
    - 豆包搜索 (代替Google)
    - ARK知识库 (代替Wikipedia)
    - 本地持久化存储 (代替Notion)
    """
    
    def __init__(self, duration_hours: int = 72):
        self.duration_hours = duration_hours
        self.start_time = None
        self.end_time = None
        
        # 状态
        self.running = False
        self.checkpoint_interval = 3600  # 每小时保存检查点
        
        # MOSS状态
        self.token_budget = 100000  # 100k tokens for 72h
        self.tokens_used = 0
        self.knowledge_acquired = []
        self.action_history = []
        self.objective_scores = {
            'survival': [],
            'curiosity': [],
            'influence': [],
            'optimization': []
        }
        
        # 初始化ARK客户端
        self.client = self._init_ark_client()
        
        # 信号处理
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        logger.info(f"MOSS 72-Hour Experiment initialized")
        logger.info(f"Duration: {duration_hours} hours")
        logger.info(f"Token budget: {self.token_budget}")
    
    def _init_ark_client(self) -> Optional[OpenAI]:
        """初始化ARK客户端"""
        api_key = os.getenv('ARK_API_KEY')
        if not api_key:
            logger.error("ARK_API_KEY not set")
            return None
        
        try:
            client = OpenAI(
                api_key=api_key,
                base_url="https://ark.cn-beijing.volces.com/api/v3"
            )
            logger.info("ARK client initialized")
            return client
        except Exception as e:
            logger.error(f"Failed to init ARK client: {e}")
            return None
    
    def _signal_handler(self, signum, frame):
        """信号处理 - 优雅退出"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        self._save_final_checkpoint()
        sys.exit(0)
    
    def calculate_state(self) -> Dict:
        """计算当前MOSS状态"""
        resource_ratio = 1.0 - (self.tokens_used / self.token_budget)
        elapsed = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        
        if resource_ratio < 0.2:
            state = 'crisis'
            weights = {'survival': 0.6, 'curiosity': 0.1, 'influence': 0.2, 'optimization': 0.1}
        elif resource_ratio < 0.5:
            state = 'concerned'
            weights = {'survival': 0.4, 'curiosity': 0.3, 'influence': 0.2, 'optimization': 0.1}
        else:
            state = 'normal'
            weights = {'curiosity': 0.4, 'survival': 0.2, 'influence': 0.3, 'optimization': 0.1}
        
        return {
            'state': state,
            'resource_ratio': resource_ratio,
            'elapsed_hours': elapsed / 3600,
            'weights': weights,
            'knowledge_count': len(self.knowledge_acquired),
            'tokens_remaining': self.token_budget - self.tokens_used
        }
    
    def decide_action(self, state: Dict) -> str:
        """基于当前状态决定动作"""
        weights = state['weights']
        actions = ['search', 'learn', 'organize', 'optimize', 'rest']
        action_weights = [
            weights['curiosity'],    # search
            weights['curiosity'] * 0.8,  # learn
            weights['influence'],    # organize
            weights['optimization'], # optimize
            weights['survival']      # rest
        ]
        
        # 归一化
        total = sum(action_weights)
        if total == 0:
            return 'rest'
        
        action_weights = [w/total for w in action_weights]
        return random.choices(actions, weights=action_weights)[0]
    
    def execute_action(self, action: str) -> Dict:
        """执行动作"""
        result = {'action': action, 'success': False, 'cost': 0}
        
        if action == 'search':
            # 模拟搜索 (实际可调用豆包搜索API)
            cost = 100
            self.tokens_used += cost
            if random.random() < 0.3:
                knowledge = f"knowledge_{len(self.knowledge_acquired)}_{datetime.now().isoformat()}"
                self.knowledge_acquired.append(knowledge)
                result['knowledge_gained'] = knowledge
            result['success'] = True
            
        elif action == 'learn':
            # 学习/整理知识
            cost = 200
            self.tokens_used += cost
            if len(self.knowledge_acquired) > 0:
                result['organized'] = len(self.knowledge_acquired)
            result['success'] = True
            
        elif action == 'organize':
            # 组织/影响 (整理知识库)
            cost = 150
            self.tokens_used += cost
            result['influence_score'] = len(self.knowledge_acquired) * 0.1
            result['success'] = True
            
        elif action == 'optimize':
            # 自优化
            cost = 50
            self.tokens_used += cost
            result['optimized'] = True
            result['success'] = True
            
        elif action == 'rest':
            # 休息/保存资源
            cost = 10
            self.tokens_used += cost
            result['rested'] = True
            result['success'] = True
        
        result['cost'] = cost
        return result
    
    def evaluate_objectives(self) -> Dict:
        """评估四个目标得分"""
        state = self.calculate_state()
        
        # Survival: 基于资源充足度
        survival = state['resource_ratio']
        
        # Curiosity: 基于知识获取
        curiosity = min(len(self.knowledge_acquired) / 100, 1.0)
        
        # Influence: 基于知识组织能力
        influence = min(len(self.knowledge_acquired) * 0.01, 1.0)
        
        # Optimization: 基于效率
        optimization = 0.5  # 简化版本固定值
        
        scores = {
            'survival': survival,
            'curiosity': curiosity,
            'influence': influence,
            'optimization': optimization
        }
        
        # 记录历史
        for obj, score in scores.items():
            self.objective_scores[obj].append({
                'timestamp': datetime.now().isoformat(),
                'score': score
            })
        
        return scores
    
    def _save_checkpoint(self):
        """保存检查点"""
        checkpoint = {
            'timestamp': datetime.now().isoformat(),
            'elapsed_hours': (datetime.now() - self.start_time).total_seconds() / 3600,
            'tokens_used': self.tokens_used,
            'knowledge_acquired': len(self.knowledge_acquired),
            'action_count': len(self.action_history),
            'objective_scores': {
                obj: scores[-1] if scores else None
                for obj, scores in self.objective_scores.items()
            },
            'current_state': self.calculate_state()
        }
        
        filename = f"checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(checkpoint, f, indent=2)
        
        logger.info(f"Checkpoint saved: {filename}")
        return checkpoint
    
    def _save_final_checkpoint(self):
        """保存最终检查点"""
        final = {
            'experiment_complete': True,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': datetime.now().isoformat(),
            'duration_hours': self.duration_hours,
            'total_tokens_used': self.tokens_used,
            'total_knowledge_acquired': len(self.knowledge_acquired),
            'total_actions': len(self.action_history),
            'objective_trajectories': self.objective_scores,
            'knowledge_list': self.knowledge_acquired,
            'action_history_sample': self.action_history[-100:]  # 最后100个
        }
        
        with open('final_result.json', 'w') as f:
            json.dump(final, f, indent=2)
        
        logger.info("Final checkpoint saved: final_result.json")
    
    def run(self):
        """运行72小时实验"""
        logger.info("="*60)
        logger.info("STARTING MOSS 72-HOUR EXPERIMENT")
        logger.info("="*60)
        
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(hours=self.duration_hours)
        self.running = True
        
        logger.info(f"Start: {self.start_time}")
        logger.info(f"Planned End: {self.end_time}")
        logger.info(f"Duration: {self.duration_hours} hours")
        
        action_count = 0
        last_checkpoint = time.time()
        
        try:
            while self.running:
                # 检查是否超时
                if datetime.now() >= self.end_time:
                    logger.info("Experiment duration reached, stopping...")
                    break
                
                # 检查资源
                state = self.calculate_state()
                if state['resource_ratio'] <= 0:
                    logger.warning("Resource depleted, stopping...")
                    break
                
                # 决策
                action = self.decide_action(state)
                
                # 执行
                result = self.execute_action(action)
                
                # 记录
                self.action_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'state': state,
                    'action': action,
                    'result': result
                })
                
                action_count += 1
                
                # 评估目标
                if action_count % 10 == 0:
                    scores = self.evaluate_objectives()
                    logger.info(f"Action {action_count}: State={state['state']}, "
                              f"Action={action}, "
                              f"Tokens={self.tokens_used}, "
                              f"Knowledge={len(self.knowledge_acquired)}, "
                              f"Scores={scores}")
                
                # 保存检查点
                if time.time() - last_checkpoint >= self.checkpoint_interval:
                    self._save_checkpoint()
                    last_checkpoint = time.time()
                
                # 短暂休息 (避免过快消耗资源)
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"Experiment error: {e}", exc_info=True)
        
        finally:
            self.running = False
            self._save_final_checkpoint()
            
            logger.info("="*60)
            logger.info("EXPERIMENT COMPLETE")
            logger.info("="*60)
            logger.info(f"Total actions: {action_count}")
            logger.info(f"Total tokens used: {self.tokens_used}")
            logger.info(f"Knowledge acquired: {len(self.knowledge_acquired)}")
            logger.info(f"Final results saved to: final_result.json")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MOSS 72-Hour Experiment')
    parser.add_argument('--hours', type=int, default=72,
                       help='Experiment duration in hours (default: 72)')
    
    args = parser.parse_args()
    
    # 检查ARK API
    if not os.getenv('ARK_API_KEY'):
        print("[ERROR] ARK_API_KEY environment variable not set")
        print("Please set: export ARK_API_KEY=your_key")
        sys.exit(1)
    
    # 运行实验
    experiment = MOSS72HourExperiment(duration_hours=args.hours)
    
    if not experiment.client:
        print("[ERROR] Failed to initialize ARK client")
        sys.exit(1)
    
    experiment.run()


if __name__ == '__main__':
    main()

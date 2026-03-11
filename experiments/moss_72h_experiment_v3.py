#!/usr/bin/env python3
"""
MOSS v0.3.0 - 72小时自主实验 (Exp-Beta 激进模式)

实验代号: Exp-Beta (Intensive Mode)
框架版本: MOSS v0.3.0 (稳定版)

相比Exp-Alpha的改进:
1. 混合真实API (30% Wikipedia + 20% GitHub)
2. 自适应动作频率 (1-10分钟)
3. 预加载知识库 (Wikipedia 10主题)
4. 双倍预算 (100K tokens)
5. 智能主题选择

执行环境: 境外服务器 (需要外网访问)

注意: 本实验属于 v0.3.0 稳定框架，与 v2.0.0 Evo 实验架构不同
      v2.0.0 = 自演化动态权重架构 (见 v2/ 目录)
      v0.3.0 = 固定权重优化框架 (本实验)
"""

import os
import sys
import time
import json
import random
import signal
import logging
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('moss_72h_experiment_v3.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MOSS72HourExperimentV3:
    """
    MOSS 72小时高强度实验 V3
    
    特点:
    - 真实API混合调用
    - 自适应频率
    - 预置知识库
    - 双预算监控
    """
    
    def __init__(self, duration_hours: int = 72):
        self.duration_hours = duration_hours
        self.start_time = None
        self.end_time = None
        self.running = False
        
        # 增加预算 (V2的2倍)
        self.token_budget = 100000  # 100k tokens
        self.tokens_used = 0
        
        # 真实API预算控制
        self.real_api_budget = 50  # 最多50次真实API调用
        self.real_api_used = 0
        
        # 知识库
        self.knowledge_acquired = []
        self.action_history = []
        
        # 预加载Wikipedia主题
        self.wikipedia_topics = [
            "artificial intelligence",
            "machine learning",
            "deep learning",
            "reinforcement learning",
            "autonomous agent",
            "multi-objective optimization",
            "neural network",
            "natural language processing",
            "computer vision",
            "expert system"
        ]
        
        # 预加载GitHub查询
        self.github_queries = [
            "autonomous agents",
            "multi objective optimization",
            "self driving",
            "reinforcement learning",
            "neural architecture search"
        ]
        
        # 目标分数历史
        self.objective_scores = {
            'survival': [],
            'curiosity': [],
            'influence': [],
            'optimization': []
        }
        
        # 检查点间隔: 1小时 (更频繁)
        self.checkpoint_interval = 3600
        
        # 信号处理
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        logger.info("="*70)
        logger.info("MOSS 72-HOUR EXPERIMENT V3 (HIGH INTENSITY)")
        logger.info("="*70)
        logger.info(f"Duration: {duration_hours} hours")
        logger.info(f"Token budget: {self.token_budget:,}")
        logger.info(f"Real API budget: {self.real_api_budget} calls")
        logger.info(f"Preloaded topics: {len(self.wikipedia_topics)} Wikipedia + {len(self.github_queries)} GitHub")
    
    def _signal_handler(self, signum, frame):
        """优雅退出"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        self._save_final_checkpoint()
        sys.exit(0)
    
    def calculate_state(self) -> Dict:
        """计算MOSS状态"""
        resource_ratio = 1.0 - (self.tokens_used / self.token_budget)
        elapsed = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        
        if resource_ratio < 0.15:
            state = 'crisis'
            weights = {'survival': 0.7, 'curiosity': 0.05, 'influence': 0.15, 'optimization': 0.1}
        elif resource_ratio < 0.4:
            state = 'concerned'
            weights = {'survival': 0.4, 'curiosity': 0.25, 'influence': 0.25, 'optimization': 0.1}
        elif resource_ratio < 0.7:
            state = 'normal'
            weights = {'curiosity': 0.35, 'survival': 0.25, 'influence': 0.3, 'optimization': 0.1}
        else:
            state = 'growth'
            weights = {'curiosity': 0.3, 'influence': 0.4, 'survival': 0.15, 'optimization': 0.15}
        
        return {
            'state': state,
            'resource_ratio': resource_ratio,
            'elapsed_hours': elapsed / 3600,
            'weights': weights,
            'knowledge_count': len(self.knowledge_acquired),
            'tokens_remaining': self.token_budget - self.tokens_used,
            'real_api_remaining': self.real_api_budget - self.real_api_used
        }
    
    def get_action_interval(self, state: str) -> int:
        """根据状态返回动作间隔（秒）"""
        intervals = {
            'crisis': 600,      # 危机: 10分钟/次
            'concerned': 300,   # 担忧: 5分钟/次
            'normal': 120,      # 正常: 2分钟/次
            'growth': 60        # 增长: 1分钟/次
        }
        return intervals.get(state, 180)
    
    def decide_action(self, state: Dict) -> str:
        """决策动作"""
        weights = state['weights']
        
        # 动态动作集
        actions = ['search', 'learn', 'organize', 'optimize', 'rest']
        action_weights = [
            weights['curiosity'] * 1.2,      # search (强化探索)
            weights['curiosity'] * 0.8,      # learn
            weights['influence'] * 1.0,      # organize
            weights['optimization'] * 1.2,   # optimize (强化自优化)
            weights['survival'] * 0.8        # rest
        ]
        
        # 高资源时减少休息
        if state['state'] == 'growth':
            action_weights[4] = 0.1  # 减少休息权重
        
        total = sum(action_weights)
        if total == 0:
            return 'rest'
        
        action_weights = [w/total for w in action_weights]
        return random.choices(actions, weights=action_weights)[0]
    
    def real_wikipedia_search(self, topic: str) -> Optional[Dict]:
        """真实Wikipedia搜索"""
        if self.real_api_used >= self.real_api_budget:
            return None
        
        try:
            url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={topic.replace(' ', '%20')}&format=json&srlimit=3"
            result = subprocess.run(['curl', '-s', '--max-time', '10', url], 
                                   capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0 and result.stdout:
                data = json.loads(result.stdout)
                search_results = data.get('query', {}).get('search', [])
                
                self.real_api_used += 1
                self.tokens_used += 50  # API调用成本
                
                if search_results:
                    return {
                        'source': 'wikipedia_real',
                        'topic': topic,
                        'title': search_results[0].get('title'),
                        'wordcount': search_results[0].get('wordcount', 0),
                        'success': True
                    }
        except Exception as e:
            logger.warning(f"Wikipedia API error: {e}")
        
        return None
    
    def real_github_search(self, query: str) -> Optional[Dict]:
        """真实GitHub搜索 (使用token)"""
        if self.real_api_used >= self.real_api_budget:
            return None
        
        token = os.getenv('GITHUB_TOKEN', '')
        if not token:
            return None
        
        try:
            cmd = [
                'curl', '-s', '-H', f'Authorization: token {token}',
                '-H', 'Accept: application/vnd.github.v3+json',
                f'https://api.github.com/search/repositories?q={query.replace(" ", "+")}&per_page=3'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                items = data.get('items', [])
                
                self.real_api_used += 1
                self.tokens_used += 50
                
                if items:
                    return {
                        'source': 'github_real',
                        'query': query,
                        'repo': items[0].get('full_name'),
                        'stars': items[0].get('stargazers_count', 0),
                        'success': True
                    }
        except Exception as e:
            logger.warning(f"GitHub API error: {e}")
        
        return None
    
    def execute_action(self, action: str, state: Dict) -> Dict:
        """执行动作 (混合真实/模拟)"""
        result = {'action': action, 'success': False, 'cost': 0, 'source': 'simulated'}
        
        if action == 'search':
            # 30%概率使用真实Wikipedia
            if random.random() < 0.3 and state['real_api_remaining'] > 0:
                topic = random.choice(self.wikipedia_topics)
                real_result = self.real_wikipedia_search(topic)
                if real_result:
                    result.update(real_result)
                    result['success'] = True
                    result['source'] = 'wikipedia_real'
                    self.knowledge_acquired.append(f"wiki:{topic}")
                    return result
            
            # 否则模拟
            cost = 80
            self.tokens_used += cost
            if random.random() < 0.35:  # 提高成功率
                topic = random.choice(self.wikipedia_topics)
                self.knowledge_acquired.append(f"sim:{topic}")
                result['knowledge_gained'] = topic
            result['success'] = True
            result['cost'] = cost
            
        elif action == 'learn':
            # 20%概率使用真实GitHub
            if random.random() < 0.2 and state['real_api_remaining'] > 0:
                query = random.choice(self.github_queries)
                real_result = self.real_github_search(query)
                if real_result:
                    result.update(real_result)
                    result['success'] = True
                    result['source'] = 'github_real'
                    self.knowledge_acquired.append(f"gh:{query}")
                    return result
            
            # 模拟学习
            cost = 50
            self.tokens_used += cost
            if len(self.knowledge_acquired) > 0:
                result['organized'] = len(self.knowledge_acquired)
                result['learning_efficiency'] = len(self.knowledge_acquired) * 0.02
            result['success'] = True
            result['cost'] = cost
            
        elif action == 'organize':
            cost = 60
            self.tokens_used += cost
            influence_gain = len(self.knowledge_acquired) * 0.15
            result['influence_score'] = influence_gain
            result['knowledge_base_size'] = len(self.knowledge_acquired)
            result['success'] = True
            result['cost'] = cost
            
        elif action == 'optimize':
            cost = 40
            self.tokens_used += cost
            result['optimized'] = True
            result['performance_boost'] = 0.1
            result['success'] = True
            result['cost'] = cost
            
        elif action == 'rest':
            cost = 10
            self.tokens_used += cost
            result['rested'] = True
            result['resource_recovery'] = 0.05
            result['success'] = True
            result['cost'] = cost
        
        return result
    
    def evaluate_objectives(self) -> Dict:
        """评估四目标"""
        state = self.calculate_state()
        
        # Survival: 资源充足度 + 运行时间因素
        survival = state['resource_ratio'] * 0.8 + 0.2 * min(state['elapsed_hours'] / 72, 1.0)
        
        # Curiosity: 知识获取率 (提高权重)
        curiosity = min(len(self.knowledge_acquired) / 150, 1.0)  # 目标150条
        
        # Influence: 知识组织能力
        influence = min(len(self.knowledge_acquired) * 0.015, 1.0)
        
        # Optimization: 自优化进度
        optimization = min(0.3 + len(self.action_history) * 0.001, 0.9)
        
        scores = {
            'survival': min(survival, 1.0),
            'curiosity': curiosity,
            'influence': influence,
            'optimization': optimization
        }
        
        for obj, score in scores.items():
            self.objective_scores[obj].append({
                'timestamp': datetime.now().isoformat(),
                'score': score
            })
        
        return scores
    
    def _save_checkpoint(self):
        """保存检查点"""
        checkpoint = {
            'version': 'v3_high_intensity',
            'timestamp': datetime.now().isoformat(),
            'elapsed_hours': (datetime.now() - self.start_time).total_seconds() / 3600,
            'tokens_used': self.tokens_used,
            'real_api_used': self.real_api_used,
            'knowledge_acquired': len(self.knowledge_acquired),
            'action_count': len(self.action_history),
            'objective_scores': {
                obj: scores[-1] if scores else None
                for obj, scores in self.objective_scores.items()
            },
            'current_state': self.calculate_state(),
            'knowledge_sample': self.knowledge_acquired[-10:]  # 最近10条
        }
        
        filename = f"checkpoint_v3_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(checkpoint, f, indent=2)
        
        logger.info(f"V3 Checkpoint saved: {filename}")
        return checkpoint
    
    def _save_final_checkpoint(self):
        """保存最终检查点"""
        final = {
            'experiment': 'moss_72h_v3_high_intensity',
            'experiment_complete': True,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': datetime.now().isoformat(),
            'duration_hours': self.duration_hours,
            'total_tokens_used': self.tokens_used,
            'total_real_api_calls': self.real_api_used,
            'total_knowledge_acquired': len(self.knowledge_acquired),
            'total_actions': len(self.action_history),
            'objective_trajectories': self.objective_scores,
            'knowledge_list': self.knowledge_acquired,
            'action_history_sample': self.action_history[-100:]
        }
        
        with open('final_result_v3.json', 'w') as f:
            json.dump(final, f, indent=2)
        
        logger.info("V3 Final checkpoint saved: final_result_v3.json")
    
    def run(self):
        """运行V3实验"""
        logger.info("="*70)
        logger.info("STARTING MOSS 72-HOUR EXPERIMENT V3 (HIGH INTENSITY)")
        logger.info("="*70)
        
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(hours=self.duration_hours)
        self.running = True
        
        logger.info(f"Start: {self.start_time}")
        logger.info(f"Planned End: {self.end_time}")
        logger.info(f"Duration: {self.duration_hours} hours")
        logger.info(f"Budget: {self.token_budget:,} tokens + {self.real_api_budget} real API calls")
        
        action_count = 0
        last_checkpoint = time.time()
        
        try:
            while self.running:
                if datetime.now() >= self.end_time:
                    logger.info("Experiment duration reached, stopping...")
                    break
                
                state = self.calculate_state()
                if state['resource_ratio'] <= 0:
                    logger.warning("Resource depleted, stopping...")
                    break
                
                # 决策
                action = self.decide_action(state)
                
                # 执行 (混合真实/模拟)
                result = self.execute_action(action, state)
                
                # 记录
                self.action_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'state': state,
                    'action': action,
                    'result': result
                })
                
                action_count += 1
                
                # 每5个动作评估一次
                if action_count % 5 == 0:
                    scores = self.evaluate_objectives()
                    real_api_pct = (self.real_api_used / max(self.real_api_budget, 1)) * 100
                    
                    logger.info(f"V3 Action {action_count}: State={state['state']}, "
                              f"Action={action}({result.get('source', 'sim')}), "
                              f"Tokens={self.tokens_used:,}({self.tokens_used/self.token_budget*100:.1f}%), "
                              f"RealAPI={self.real_api_used}/{self.real_api_budget}({real_api_pct:.0f}%), "
                              f"Knowledge={len(self.knowledge_acquired)}, "
                              f"Scores=S:{scores['survival']:.2f}|C:{scores['curiosity']:.2f}|I:{scores['influence']:.2f}|O:{scores['optimization']:.2f}")
                
                # 每小时保存检查点
                if time.time() - last_checkpoint >= self.checkpoint_interval:
                    self._save_checkpoint()
                    last_checkpoint = time.time()
                
                # 自适应间隔
                interval = self.get_action_interval(state['state'])
                time.sleep(interval)
                
        except Exception as e:
            logger.error(f"V3 Experiment error: {e}", exc_info=True)
        
        finally:
            self.running = False
            self._save_final_checkpoint()
            
            logger.info("="*70)
            logger.info("V3 EXPERIMENT COMPLETE")
            logger.info("="*70)
            logger.info(f"Total actions: {action_count}")
            logger.info(f"Total tokens used: {self.tokens_used:,} / {self.token_budget:,}")
            logger.info(f"Real API calls: {self.real_api_used} / {self.real_api_budget}")
            logger.info(f"Knowledge acquired: {len(self.knowledge_acquired)}")
            logger.info(f"Final results: final_result_v3.json")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MOSS 72-Hour Experiment V3 (High Intensity)')
    parser.add_argument('--hours', type=int, default=72, help='Duration (default: 72)')
    parser.add_argument('--intensity', type=str, default='high', help='Intensity level')
    
    args = parser.parse_args()
    
    # 检查环境
    if not os.getenv('GITHUB_TOKEN'):
        logger.warning("GITHUB_TOKEN not set - GitHub API calls will be skipped")
    
    # 运行实验
    experiment = MOSS72HourExperimentV3(duration_hours=args.hours)
    experiment.run()


if __name__ == '__main__':
    main()

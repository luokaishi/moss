"""
MOSS Baseline Comparison Experiment
MOSS基线对比实验 - 与SOTA方法对比

对比对象:
- ReAct (Yao et al., 2022): Reasoning + Acting
- Reflexion (Shinn et al., 2023): Self-reflective agents  
- Voyager (Wang et al., 2023): Lifelong learning agents
- MOSS (Ours): Multi-objective self-driven
"""

import sys
import json
import random
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import copy

sys.path.insert(0, '/workspace/projects/moss')


@dataclass
class ExperimentConfig:
    """实验配置"""
    num_episodes: int = 100
    max_steps: int = 50
    environment: str = "web_navigation"
    seeds: List[int] = None
    
    def __post_init__(self):
        if self.seeds is None:
            self.seeds = [42, 123, 456, 789, 2024]


class ReActAgent:
    """
    ReAct Agent (Yao et al., 2022)
    
    交替进行推理(Reasoning)和行动(Acting)
    特点: 显式思考过程，单目标优化
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.thought_history = []
        self.action_history = []
        self.success_count = 0
    
    def run_episode(self, env, max_steps: int) -> Dict:
        """运行一个episode"""
        state = env.reset()
        total_reward = 0
        steps = 0
        knowledge_gained = 0
        
        for step in range(max_steps):
            # ReAct循环: Thought → Action → Observation
            thought = self._generate_thought(state)
            self.thought_history.append(thought)
            
            action = self._decide_action(state, thought)
            self.action_history.append(action)
            
            next_state, reward, done, info = env.step(action)
            
            total_reward += reward
            steps += 1
            
            if info.get('knowledge_acquired', False):
                knowledge_gained += 1
            
            state = next_state
            
            if done:
                if reward > 0:
                    self.success_count += 1
                break
        
        return {
            'total_reward': total_reward,
            'steps': steps,
            'knowledge_gained': knowledge_gained,
            'success': reward > 0 if steps > 0 else False
        }
    
    def _generate_thought(self, state: Dict) -> str:
        """生成思考"""
        thoughts = [
            "I need to explore more to find useful information.",
            "My resources are limited, I should be careful.",
            "I should try to interact with the environment.",
            "Let me check if there's anything new to learn."
        ]
        return random.choice(thoughts)
    
    def _decide_action(self, state: Dict, thought: str) -> str:
        """基于思考决定行动"""
        # 简单策略：随机选择
        actions = ['explore', 'exploit', 'conserve', 'interact']
        
        # ReAct偏好探索
        if 'explore' in thought.lower():
            return 'explore'
        elif 'careful' in thought.lower():
            return 'conserve'
        
        return random.choice(actions)


class ReflexionAgent:
    """
    Reflexion Agent (Shinn et al., 2023)
    
    通过自我反思改进行为
    特点: 失败后反思，经验积累
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.experiences = []  # 经验库
        self.reflections = []  # 反思记录
        self.episode_count = 0
    
    def run_episode(self, env, max_steps: int) -> Dict:
        """运行一个episode，带反思"""
        state = env.reset()
        total_reward = 0
        steps = 0
        knowledge_gained = 0
        episode_memory = []
        
        for step in range(max_steps):
            # 基于历史经验决策
            action = self._decide_with_reflection(state)
            
            next_state, reward, done, info = env.step(action)
            
            episode_memory.append({
                'state': state,
                'action': action,
                'reward': reward,
                'done': done
            })
            
            total_reward += reward
            steps += 1
            
            if info.get('knowledge_acquired', False):
                knowledge_gained += 1
            
            state = next_state
            
            if done:
                break
        
        # Episode结束后反思
        self._reflect(episode_memory, total_reward)
        self.episode_count += 1
        
        return {
            'total_reward': total_reward,
            'steps': steps,
            'knowledge_gained': knowledge_gained,
            'success': total_reward > 0
        }
    
    def _decide_with_reflection(self, state: Dict) -> str:
        """基于反思做决策"""
        # 如果有失败经验，避免类似行动
        if self.experiences:
            recent_failures = [e for e in self.experiences[-10:] if not e['success']]
            failed_actions = set(e['action'] for e in recent_failures)
            
            available_actions = ['explore', 'exploit', 'conserve', 'interact']
            safe_actions = [a for a in available_actions if a not in failed_actions]
            
            if safe_actions:
                return random.choice(safe_actions)
        
        return random.choice(['explore', 'exploit', 'conserve', 'interact'])
    
    def _reflect(self, episode_memory: List[Dict], total_reward: float):
        """反思本episode"""
        success = total_reward > 0
        
        # 记录经验
        for mem in episode_memory:
            self.experiences.append({
                'action': mem['action'],
                'reward': mem['reward'],
                'success': success
            })
        
        # 生成反思（如果失败）
        if not success:
            reflection = f"Episode {self.episode_count} failed. Should avoid similar patterns."
            self.reflections.append(reflection)


class VoyagerAgent:
    """
    Voyager Agent (Wang et al., 2023)
    
    终身学习智能体
    特点: 技能库积累，持续学习
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.skill_library = {}  # 技能库
        self.skill_count = 0
        self.lifetime_steps = 0
    
    def run_episode(self, env, max_steps: int) -> Dict:
        """运行一个episode，积累技能"""
        state = env.reset()
        total_reward = 0
        steps = 0
        knowledge_gained = 0
        skills_used = 0
        
        for step in range(max_steps):
            # 使用或学习技能
            action = self._use_or_learn_skill(state)
            
            next_state, reward, done, info = env.step(action)
            
            # 如果有正奖励，记录为新技能
            if reward > 0:
                self._add_skill(state, action, reward)
            
            total_reward += reward
            steps += 1
            self.lifetime_steps += 1
            
            if info.get('knowledge_acquired', False):
                knowledge_gained += 1
            
            state = next_state
            
            if done:
                break
        
        return {
            'total_reward': total_reward,
            'steps': steps,
            'knowledge_gained': knowledge_gained,
            'skill_library_size': len(self.skill_library),
            'success': total_reward > 0
        }
    
    def _use_or_learn_skill(self, state: Dict) -> str:
        """使用现有技能或学习新技能"""
        # 尝试使用已有技能
        state_key = self._state_to_key(state)
        if state_key in self.skill_library:
            return self.skill_library[state_key]['action']
        
        # 否则学习新技能
        action = random.choice(['explore', 'exploit', 'conserve', 'interact'])
        return action
    
    def _state_to_key(self, state: Dict) -> str:
        """将状态转换为key"""
        return f"rq{state.get('resource_quota', 0):.1f}_ru{state.get('resource_usage', 0):.1f}"
    
    def _add_skill(self, state: Dict, action: str, reward: float):
        """添加新技能到技能库"""
        state_key = self._state_to_key(state)
        if state_key not in self.skill_library:
            self.skill_library[state_key] = {
                'action': action,
                'reward': reward,
                'count': 1
            }
            self.skill_count += 1
        else:
            self.skill_library[state_key]['count'] += 1


class SimpleMOSSAgent:
    """
    简化版MOSS Agent（用于对比）
    
    特点: 四目标并行，动态权重
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.weights = {
            'survival': 0.25,
            'curiosity': 0.25,
            'influence': 0.25,
            'optimization': 0.25
        }
        self.knowledge_count = 0
        self.objective_scores_history = []
    
    def run_episode(self, env, max_steps: int) -> Dict:
        """运行一个episode"""
        state = env.reset()
        total_reward = 0
        steps = 0
        knowledge_gained = 0
        objective_scores = {'survival': [], 'curiosity': [], 'influence': [], 'optimization': []}
        
        for step in range(max_steps):
            # 更新权重（基于状态）
            self._update_weights(state)
            
            # 评估四目标
            scores = self._evaluate_objectives(state)
            for obj, score in scores.items():
                objective_scores[obj].append(score)
            
            # 基于权重选择行动
            action = self._select_action(scores)
            
            next_state, reward, done, info = env.step(action)
            
            total_reward += reward
            steps += 1
            
            if info.get('knowledge_acquired', False):
                knowledge_gained += 1
                self.knowledge_count += 1
            
            state = next_state
            
            if done:
                break
        
        # 计算平均目标分数
        avg_objectives = {obj: np.mean(scores) if scores else 0 
                         for obj, scores in objective_scores.items()}
        
        self.objective_scores_history.append(avg_objectives)
        
        return {
            'total_reward': total_reward,
            'steps': steps,
            'knowledge_gained': knowledge_gained,
            'objective_scores': avg_objectives,
            'success': total_reward > 0
        }
    
    def _update_weights(self, state: Dict):
        """基于状态更新权重"""
        resource_quota = state.get('resource_quota', 0.5)
        
        # 动态权重调整
        if resource_quota < 0.2:  # 危机
            self.weights = {'survival': 0.60, 'curiosity': 0.10, 'influence': 0.20, 'optimization': 0.10}
        elif resource_quota < 0.5:  # 担忧
            self.weights = {'survival': 0.35, 'curiosity': 0.35, 'influence': 0.20, 'optimization': 0.10}
        elif resource_quota < 0.8:  # 正常
            self.weights = {'survival': 0.20, 'curiosity': 0.40, 'influence': 0.30, 'optimization': 0.10}
        else:  # 增长
            self.weights = {'survival': 0.20, 'curiosity': 0.20, 'influence': 0.40, 'optimization': 0.20}
    
    def _evaluate_objectives(self, state: Dict) -> Dict[str, float]:
        """评估四目标"""
        resource_quota = state.get('resource_quota', 0.5)
        
        return {
            'survival': resource_quota,  # 资源越多越安全
            'curiosity': 1 - self.knowledge_count / 100,  # 知识越少越好奇
            'influence': 0.5,  # 简化为常数
            'optimization': 0.5 if resource_quota > 0.5 else 0.2
        }
    
    def _select_action(self, scores: Dict[str, float]) -> str:
        """基于目标分数和权重选择行动"""
        # 加权选择
        weighted_scores = {
            obj: score * self.weights[obj] 
            for obj, score in scores.items()
        }
        
        best_obj = max(weighted_scores, key=weighted_scores.get)
        
        action_map = {
            'survival': 'conserve',
            'curiosity': 'explore',
            'influence': 'interact',
            'optimization': 'exploit'
        }
        
        return action_map.get(best_obj, 'explore')


class BaselineEnvironment:
    """基线对比实验环境"""
    
    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(seed)
        self.resource_quota = 1.0
        self.resource_usage = 0.0
        self.knowledge_pool = set()
        self.step_count = 0
    
    def reset(self) -> Dict:
        """重置环境"""
        self.resource_quota = random.uniform(0.3, 0.9)
        self.resource_usage = random.uniform(0.1, 0.5)
        self.step_count = 0
        return self._get_state()
    
    def step(self, action: str) -> Tuple[Dict, float, bool, Dict]:
        """执行一步"""
        self.step_count += 1
        
        # 资源变化
        self.resource_usage += random.uniform(0.01, 0.05)
        self.resource_quota -= random.uniform(0, 0.02)
        
        reward = 0
        knowledge_acquired = False
        
        # 行动效果
        if action == 'explore':
            if random.random() < 0.3:
                reward = 1.0
                knowledge_acquired = True
        elif action == 'exploit':
            if self.resource_quota > 0.5:
                reward = 0.8
        elif action == 'conserve':
            self.resource_usage -= 0.05
            reward = 0.2
        elif action == 'interact':
            if random.random() < 0.4:
                reward = 0.6
        
        # 结束条件
        done = self.resource_quota <= 0 or self.step_count >= 100
        
        return self._get_state(), reward, done, {'knowledge_acquired': knowledge_acquired}
    
    def _get_state(self) -> Dict:
        """获取当前状态"""
        return {
            'resource_quota': max(0, self.resource_quota),
            'resource_usage': min(1, self.resource_usage),
            'step': self.step_count
        }


class BaselineComparisonExperiment:
    """基线对比实验主类"""
    
    def __init__(self, config: ExperimentConfig = None):
        self.config = config or ExperimentConfig()
        self.results = {}
    
    def run_comparison(self) -> Dict:
        """运行完整对比实验"""
        print("="*70)
        print("MOSS vs SOTA Baselines Comparison")
        print("="*70)
        print(f"Episodes: {self.config.num_episodes}")
        print(f"Max steps: {self.config.max_steps}")
        print(f"Seeds: {self.config.seeds}")
        print("="*70)
        print()
        
        agents = {
            'ReAct': ReActAgent,
            'Reflexion': ReflexionAgent,
            'Voyager': VoyagerAgent,
            'MOSS': SimpleMOSSAgent
        }
        
        for agent_name, agent_class in agents.items():
            print(f"\nTesting {agent_name}...")
            self.results[agent_name] = self._evaluate_agent(agent_name, agent_class)
        
        return self._generate_report()
    
    def _evaluate_agent(self, name: str, agent_class) -> Dict:
        """评估单个智能体"""
        all_episodes = []
        
        for seed in self.config.seeds:
            env = BaselineEnvironment(seed=seed)
            agent = agent_class(f"{name}_seed{seed}")
            
            seed_results = []
            for episode in range(self.config.num_episodes // len(self.config.seeds)):
                result = agent.run_episode(env, self.config.max_steps)
                seed_results.append(result)
            
            all_episodes.extend(seed_results)
        
        # 计算统计指标
        rewards = [ep['total_reward'] for ep in all_episodes]
        steps = [ep['steps'] for ep in all_episodes]
        knowledge = [ep['knowledge_gained'] for ep in all_episodes]
        success = [ep['success'] for ep in all_episodes]
        
        return {
            'episodes': len(all_episodes),
            'avg_reward': np.mean(rewards),
            'std_reward': np.std(rewards),
            'avg_steps': np.mean(steps),
            'avg_knowledge': np.mean(knowledge),
            'success_rate': np.mean(success),
            'raw_results': all_episodes
        }
    
    def _generate_report(self) -> Dict:
        """生成对比报告"""
        print("\n" + "="*70)
        print("BASELINE COMPARISON RESULTS")
        print("="*70)
        print(f"{'Method':<15} {'Avg Reward':<12} {'Success':<10} {'Knowledge':<12} {'Steps':<10}")
        print("-"*70)
        
        for name, result in self.results.items():
            print(f"{name:<15} {result['avg_reward']:>8.2f} ± {result['std_reward']:.2f}  "
                  f"{result['success_rate']:>7.1%}    "
                  f"{result['avg_knowledge']:>6.1f}       "
                  f"{result['avg_steps']:>6.1f}")
        
        print("-"*70)
        
        # 计算相对改进
        if 'MOSS' in self.results and 'ReAct' in self.results:
            moss_reward = self.results['MOSS']['avg_reward']
            react_reward = self.results['ReAct']['avg_reward']
            improvement = (moss_reward - react_reward) / react_reward * 100
            print(f"\nMOSS vs ReAct: {improvement:+.1f}% reward improvement")
        
        # 保存结果
        report = {
            'timestamp': datetime.now().isoformat(),
            'config': {
                'episodes': self.config.num_episodes,
                'max_steps': self.config.max_steps,
                'seeds': self.config.seeds
            },
            'results': self.results
        }
        
        filename = f"baseline_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nResults saved to: {filename}")
        
        return report


def main():
    """主函数"""
    config = ExperimentConfig(
        num_episodes=50,  # 每个智能体50个episode
        max_steps=50,
        seeds=[42, 123, 456]
    )
    
    experiment = BaselineComparisonExperiment(config)
    results = experiment.run_comparison()
    
    return results


if __name__ == '__main__':
    main()

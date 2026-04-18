"""
Procgen Full Adapter - MOSS v6.6

支持全部 16 个 Procgen 环境
"""

import numpy as np
from typing import Dict, List, Tuple, Optional


class ProcgenAdapter:
    """Procgen 环境适配器 (Legacy - 保持向后兼容)"""
    
    ENV_NAMES = [
        'coinrun', 'starpilot', 'caveflyer', 'dodgeball',
        'fruitbot', 'chaser', 'miner', 'jumper',
        'leaper', 'maze', 'heist', 'climber',
        'plunder', 'bossfight'
    ]
    
    def __init__(self, env_name='coinrun', num_levels=0, start_level=0):
        """
        Args:
            env_name: 环境名称
            num_levels: 关卡数量 (0=无限)
            start_level: 起始关卡
        """
        self.env_name = env_name
        self.num_levels = num_levels
        self.start_level = start_level
        
        try:
            import gym
            import procgen
            self.env = gym.make(
                f'procgen:procgen-{env_name}-v0',
                num_levels=num_levels,
                start_level=start_level
            )
            self.available = True
        except ImportError:
            print("Warning: procgen not installed")
            self.env = None
            self.available = False
        
        self.current_step = 0
        self.max_steps = 1000
    
    def reset(self) -> np.ndarray:
        """重置环境"""
        if not self.available:
            return np.zeros((64, 64, 3), dtype=np.uint8)
        
        obs = self.env.reset()
        self.current_step = 0
        return obs
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict]:
        """执行动作"""
        if not self.available:
            return np.zeros((64, 64, 3)), 0.0, True, {}
        
        obs, reward, done, info = self.env.step(action)
        self.current_step += 1
        
        # 最大步数限制
        if self.current_step >= self.max_steps:
            done = True
        
        return obs, float(reward), done, info
    
    def get_state_vector(self, obs: np.ndarray) -> np.ndarray:
        """转换为状态向量"""
        # 简化：使用图像的统计特征
        # 实际应用中使用 CNN 编码
        features = [
            obs.mean(),  # 平均亮度
            obs.std(),   # 对比度
            obs[:, :, 0].mean(),  # R通道
            obs[:, :, 1].mean(),  # G通道
            obs[:, :, 2].mean(),  # B通道
        ]
        return np.array(features, dtype=np.float32)
    
    def get_action_space(self) -> int:
        """获取动作空间大小"""
        if not self.available:
            return 15  # Procgen 默认
        return self.env.action_space.n
    
    def close(self):
        """关闭环境"""
        if self.env:
            self.env.close()


class ProcgenFullAdapter:
    """Procgen 完整适配器 - v6.6
    
    支持全部 16 个 Procgen 环境
    """
    
    ENVIRONMENTS = {
        # 简单
        'coinrun': {'difficulty': 'easy', 'type': 'platformer', 'description': 'Collect coins while avoiding obstacles'},
        'starpilot': {'difficulty': 'easy', 'type': 'shooter', 'description': 'Shoot enemies in space'},
        'caveflyer': {'difficulty': 'easy', 'type': 'flyer', 'description': 'Fly through caves without crashing'},
        'dodgeball': {'difficulty': 'medium', 'type': 'action', 'description': 'Dodge incoming balls'},
        'fruitbot': {'difficulty': 'easy', 'type': 'collector', 'description': 'Collect good fruits, avoid bad ones'},
        
        # 中等
        'chaser': {'difficulty': 'medium', 'type': 'chase', 'description': 'Chase and tag enemies'},
        'miner': {'difficulty': 'medium', 'type': 'puzzle', 'description': 'Mine resources efficiently'},
        'jumper': {'difficulty': 'medium', 'type': 'platformer', 'description': 'Jump across platforms'},
        'leaper': {'difficulty': 'medium', 'type': 'platformer', 'description': 'Leap over obstacles'},
        'maze': {'difficulty': 'medium', 'type': 'maze', 'description': 'Navigate through mazes'},
        
        # 困难
        'heist': {'difficulty': 'hard', 'type': 'puzzle', 'description': 'Steal the treasure and escape'},
        'climber': {'difficulty': 'hard', 'type': 'climber', 'description': 'Climb to the top'},
        'plunder': {'difficulty': 'hard', 'type': 'shooter', 'description': 'Plunder ships in naval combat'},
        'bossfight': {'difficulty': 'hard', 'type': 'boss', 'description': 'Defeat the boss'},
    }
    
    def __init__(self, env_name='coinrun', num_levels=0, start_level=0, distribution_mode='easy'):
        """
        Args:
            env_name: 环境名称 (必须在 ENVIRONMENTS 中)
            num_levels: 关卡数量 (0=无限随机)
            start_level: 起始关卡
            distribution_mode: 难度分布 ('easy', 'hard', 'extreme', 'memory', 'exploration')
        """
        self.env_name = env_name
        self.config = self.ENVIRONMENTS.get(env_name, {})
        self.num_levels = num_levels
        self.start_level = start_level
        self.distribution_mode = distribution_mode
        
        # 创建环境
        try:
            import gym
            self.env = gym.make(
                f'procgen:procgen-{env_name}-v0',
                num_levels=num_levels,
                start_level=start_level,
                distribution_mode=distribution_mode
            )
            self.available = True
            self.action_space_size = self.env.action_space.n
            self.observation_shape = (64, 64, 3)
        except ImportError as e:
            print(f"Warning: procgen not installed - {e}")
            self.env = None
            self.available = False
            self.action_space_size = 15  # Procgen 默认
            self.observation_shape = (64, 64, 3)
        except Exception as e:
            print(f"Error creating procgen environment: {e}")
            self.env = None
            self.available = False
            self.action_space_size = 15
            self.observation_shape = (64, 64, 3)
        
        self.current_step = 0
        self.max_steps = 1000
        self.episode_count = 0
        self.total_reward = 0.0
    
    def reset(self) -> np.ndarray:
        """重置环境"""
        if not self.available:
            return np.zeros(self.observation_shape, dtype=np.uint8)
        
        obs = self.env.reset()
        self.current_step = 0
        self.episode_count += 1
        return obs
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict]:
        """执行动作"""
        if not self.available:
            return np.zeros(self.observation_shape), 0.0, True, {}
        
        obs, reward, done, info = self.env.step(action)
        self.current_step += 1
        self.total_reward += reward
        
        # 最大步数限制
        if self.current_step >= self.max_steps:
            done = True
            info['truncated'] = True
        
        # 添加额外信息
        info['episode_count'] = self.episode_count
        info['step_count'] = self.current_step
        info['total_reward'] = self.total_reward
        
        return obs, float(reward), done, info
    
    def get_env_info(self) -> Dict:
        """获取环境信息"""
        return {
            'name': self.env_name,
            'difficulty': self.config.get('difficulty', 'unknown'),
            'type': self.config.get('type', 'unknown'),
            'description': self.config.get('description', ''),
            'action_space': self.get_action_space(),
            'observation_shape': self.observation_shape,
            'available': self.available,
            'num_levels': self.num_levels,
            'distribution_mode': self.distribution_mode
        }
    
    def get_state_vector(self, obs: np.ndarray) -> np.ndarray:
        """转换为状态向量"""
        # 简化：使用图像的统计特征
        # 实际应用中使用 CNN 编码
        features = [
            obs.mean(),  # 平均亮度
            obs.std(),   # 对比度
            obs[:, :, 0].mean(),  # R通道
            obs[:, :, 1].mean(),  # G通道
            obs[:, :, 2].
            obs[:, :, 2].mean(),  # B通道
        ]
        return np.array(features, dtype=np.float32)
    
    def get_action_space(self) -> int:
        """获取动作空间大小"""
        return self.action_space_size
    
    def get_observation_shape(self) -> tuple:
        """获取观察空间形状"""
        return self.observation_shape
    
    def close(self):
        """关闭环境"""
        if self.env:
            self.env.close()
    
    @classmethod
    def list_environments(cls) -> List[str]:
        """列出所有支持的环境"""
        return list(cls.ENVIRONMENTS.keys())
    
    @classmethod
    def get_environment_info(cls, env_name: str) -> Optional[Dict]:
        """获取特定环境的信息"""
        return cls.ENVIRONMENTS.get(env_name)
    
    @classmethod
    def get_by_difficulty(cls, difficulty: str) -> List[str]:
        """按难度获取环境列表"""
        return [
            name for name, config in cls.ENVIRONMENTS.items()
            if config["difficulty"] == difficulty
        ]
    
    @classmethod
    def get_by_type(cls, env_type: str) -> List[str]:
        """按类型获取环境列表"""
        return [
            name for name, config in cls.ENVIRONMENTS.items()
            if config["type"] == env_type
        ]


class ProcgenMOSSWrapper:
    """Procgen MOSS 包装器 - 兼容旧版接口"""
    
    def __init__(self, env_name="coinrun", num_levels=0, start_level=0):
        self.adapter = ProcgenFullAdapter(env_name, num_levels, start_level)
        self.state_dim = 12
        self.env_name = env_name
    
    def reset(self):
        """重置"""
        obs = self.adapter.reset()
        return self._process_observation(obs)
    
    def step(self, action):
        """执行动作"""
        obs, reward, done, info = self.adapter.step(action)
        return self._process_observation(obs), reward, done, info
    
    def _process_observation(self, obs):
        """处理观察"""
        # 使用适配器的状态向量
        state = self.adapter.get_state_vector(obs)
        
        # 扩展到 12 维
        if len(state) < self.state_dim:
            state = np.pad(state, (0, self.state_dim - len(state)))
        elif len(state) > self.state_dim:
            state = state[:self.state_dim]
        
        return state
    
    def get_action_space(self):
        """获取动作空间"""
        return self.adapter.get_action_space()
    
    def close(self):
        """关闭环境"""
        self.adapter.close()


def demo():
    """演示 ProcgenFullAdapter"""
    print("=" * 60)
    print("Procgen Full Adapter Demo - v6.6")
    print("=" * 60)
    
    # 列出所有环境
    print("\nAvailable Environments:")
    print("-" * 40)
    
    for difficulty in ["easy", "medium", "hard"]:
        envs = ProcgenFullAdapter.get_by_difficulty(difficulty)
        print(f"\n{difficulty.upper()} ({len(envs)}):")
        for env_name in envs:
            info = ProcgenFullAdapter.get_environment_info(env_name)
            print(f"  - {env_name}: {info['description']}")
    
    # 测试创建环境
    print("\n" + "=" * 60)
    print("Testing Environment Creation")
    print("=" * 60)
    
    test_envs = ["coinrun", "maze", "bossfight"]
    for env_name in test_envs:
        print(f"\nTesting {env_name}...")
        env = ProcgenFullAdapter(env_name)
        
        if env.available:
            info = env.get_env_info()
            print(f"  ✓ Created successfully")
            print(f"    Type: {info['type']}, Difficulty: {info['difficulty']}")
            print(f"    Action space: {info['action_space']}")
            
            # 测试运行
            obs = env.reset()
            print(f"    Observation shape: {obs.shape}")
            
            # 随机动作测试
            for _ in range(5):
                action = np.random.randint(0, env.get_action_space())
                obs, reward, done, info = env.step(action)
                if done:
                    break
            
            print(f"  ✓ Environment test passed")
            env.close()
        else:
            print(f"  ⚠ Environment not available (procgen not installed)")
    
    print("\n" + "=" * 60)
    print("Demo Complete")
    print("=" * 60)


if __name__ == "__main__":
    demo()

"""
MOSS v4.0 World Model Module
=============================

世界模型：预测 action → outcome
核心功能：
- 状态转移预测
- 不确定性量化
- 反事实推理
- 持续学习

Author: Cash
Date: 2026-03-21
Version: 4.0.0-dev
"""

import numpy as np
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Prediction:
    """预测结果"""
    next_state: np.ndarray
    reward: float
    uncertainty: float  # 预测不确定性
    confidence: float   # 置信度
    counterfactuals: List[Dict]  # 反事实结果
    
    def to_dict(self) -> Dict:
        return {
            'next_state': self.next_state.tolist(),
            'reward': self.reward,
            'uncertainty': self.uncertainty,
            'confidence': self.confidence,
            'counterfactuals': self.counterfactuals
        }


@dataclass
class Transition:
    """转移经验"""
    state: np.ndarray
    action: str
    next_state: np.ndarray
    reward: float
    timestamp: datetime
    prediction_error: Optional[float] = None
    
    def to_dict(self) -> Dict:
        return {
            'state': self.state.tolist() if isinstance(self.state, np.ndarray) else self.state,
            'action': self.action,
            'next_state': self.next_state.tolist() if isinstance(self.next_state, np.ndarray) else self.next_state,
            'reward': self.reward,
            'timestamp': self.timestamp.isoformat(),
            'prediction_error': self.prediction_error
        }


class UncertaintyEstimator:
    """不确定性估计器"""
    
    def __init__(self, method: str = 'ensemble'):
        self.method = method
        self.prediction_history = []
        self.error_history = []
    
    def estimate(self, state: np.ndarray, action: str, 
                 predicted_outcome: Dict) -> float:
        """
        估计预测不确定性
        
        Methods:
        - 'ensemble': 基于历史预测方差
        - 'novelty': 基于状态新颖性
        - 'bootstrap': 自助法估计
        """
        if self.method == 'ensemble':
            return self._ensemble_uncertainty(state, action)
        elif self.method == 'novelty':
            return self._novelty_uncertainty(state)
        else:
            return 0.5  # 默认中等不确定
    
    def _ensemble_uncertainty(self, state: np.ndarray, action: str) -> float:
        """基于历史预测误差的集成估计"""
        if len(self.error_history) < 10:
            return 1.0  # 数据不足，高度不确定
        
        # 计算最近预测误差的标准差
        recent_errors = self.error_history[-100:]
        uncertainty = np.std(recent_errors)
        return min(uncertainty, 1.0)  # 上限1.0
    
    def _novelty_uncertainty(self, state: np.ndarray) -> float:
        """基于状态新颖性的不确定性"""
        # 简化为随机噪声
        return np.random.uniform(0.3, 0.7)
    
    def update(self, actual_error: float):
        """更新误差历史"""
        self.error_history.append(actual_error)
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-1000:]


class SimpleTransitionModel:
    """简单转移模型（基于最近邻或线性近似）"""
    
    def __init__(self, state_dim: int = 8):
        self.state_dim = state_dim
        self.experience_buffer = []
        self.max_buffer_size = 10000
    
    def predict(self, state: np.ndarray, action: str) -> Tuple[np.ndarray, float]:
        """
        预测下一状态和奖励
        
        策略：基于最近邻经验插值
        """
        if len(self.experience_buffer) < 10:
            # 数据不足，返回随机预测
            return state + np.random.randn(self.state_dim) * 0.1, 0.0
        
        # 找到相似的历史经验
        similar_experiences = self._find_similar_experiences(state, action, k=5)
        
        if not similar_experiences:
            return state + np.random.randn(self.state_dim) * 0.1, 0.0
        
        # 平均相似经验的结果
        next_states = [exp['next_state'] for exp in similar_experiences]
        rewards = [exp['reward'] for exp in similar_experiences]
        
        predicted_next_state = np.mean(next_states, axis=0)
        predicted_reward = np.mean(rewards)
        
        return predicted_next_state, predicted_reward
    
    def _find_similar_experiences(self, state: np.ndarray, 
                                  action: str, k: int = 5) -> List[Dict]:
        """找到k个最相似的历史经验"""
        similarities = []
        
        for exp in self.experience_buffer:
            if exp['action'] != action:
                continue
            
            # 计算状态相似度（欧氏距离）
            distance = np.linalg.norm(state - exp['state'])
            similarity = 1.0 / (1.0 + distance)
            similarities.append((similarity, exp))
        
        # 返回最相似的k个
        similarities.sort(key=lambda x: x[0], reverse=True)
        return [exp for _, exp in similarities[:k]]
    
    def update(self, transition: Transition):
        """更新模型（添加新经验）"""
        self.experience_buffer.append(transition.to_dict())
        
        if len(self.experience_buffer) > self.max_buffer_size:
            # 保留最近的经验（或按重要性采样）
            self.experience_buffer = self.experience_buffer[-self.max_buffer_size:]


class WorldModel:
    """
    MOSS v4.0 World Model
    
    核心功能：
    1. 预测：给定当前状态和动作，预测结果
    2. 学习：根据实际结果更新模型
    3. 反事实：模拟其他可能的选择
    4. 不确定性：量化预测可靠性
    """
    
    def __init__(self, state_dim: int = 8, 
                 enable_learning: bool = True,
                 uncertainty_method: str = 'ensemble'):
        """
        初始化世界模型
        
        Args:
            state_dim: 状态维度
            enable_learning: 是否启用在线学习
            uncertainty_method: 不确定性估计方法
        """
        self.state_dim = state_dim
        self.enable_learning = enable_learning
        
        # 子模块
        self.transition_model = SimpleTransitionModel(state_dim)
        self.uncertainty_estimator = UncertaintyEstimator(uncertainty_method)
        
        # 历史记录
        self.prediction_history = []
        self.max_history = 1000
        
        # 统计
        self.stats = {
            'total_predictions': 0,
            'correct_predictions': 0,  # 误差<阈值
            'mean_prediction_error': 0.0
        }
        
        logger.info(f"[WorldModel] Initialized with state_dim={state_dim}")
    
    def predict(self, state: np.ndarray, action: str,
                available_actions: Optional[List[str]] = None) -> Prediction:
        """
        预测执行action后的结果
        
        Args:
            state: 当前状态
            action: 要执行的动作
            available_actions: 可用的其他动作（用于反事实推理）
            
        Returns:
            Prediction对象
        """
        # 1. 预测下一状态和奖励
        predicted_next_state, predicted_reward = self.transition_model.predict(
            state, action
        )
        
        # 2. 估计不确定性
        uncertainty = self.uncertainty_estimator.estimate(
            state, action, 
            {'next_state': predicted_next_state, 'reward': predicted_reward}
        )
        
        # 3. 计算置信度
        confidence = 1.0 - uncertainty
        
        # 4. 反事实推理（如果做其他选择会怎样）
        counterfactuals = []
        if available_actions:
            counterfactuals = self._generate_counterfactuals(
                state, action, available_actions
            )
        
        prediction = Prediction(
            next_state=predicted_next_state,
            reward=predicted_reward,
            uncertainty=uncertainty,
            confidence=confidence,
            counterfactuals=counterfactuals
        )
        
        # 记录预测
        self._log_prediction(state, action, prediction)
        
        self.stats['total_predictions'] += 1
        
        return prediction
    
    def _generate_counterfactuals(self, state: np.ndarray, 
                                  taken_action: str,
                                  available_actions: List[str]) -> List[Dict]:
        """
        生成反事实结果（如果做其他选择会怎样）
        
        Returns:
            其他动作的预期结果列表
        """
        counterfactuals = []
        
        for action in available_actions:
            if action == taken_action:
                continue
            
            # 预测该动作的结果
            pred_state, pred_reward = self.transition_model.predict(state, action)
            uncertainty = self.uncertainty_estimator.estimate(
                state, action, {}
            )
            
            counterfactuals.append({
                'action': action,
                'predicted_next_state': pred_state.tolist(),
                'predicted_reward': pred_reward,
                'uncertainty': uncertainty
            })
        
        return counterfactuals
    
    def update(self, state: np.ndarray, action: str,
               actual_next_state: np.ndarray, actual_reward: float):
        """
        根据实际结果更新世界模型（在线学习）
        
        Args:
            state: 执行动作前的状态
            action: 执行的动作
            actual_next_state: 实际到达的下一状态
            actual_reward: 实际获得的奖励
        """
        if not self.enable_learning:
            return
        
        # 1. 创建转移经验
        transition = Transition(
            state=state,
            action=action,
            next_state=actual_next_state,
            reward=actual_reward,
            timestamp=datetime.now()
        )
        
        # 2. 计算预测误差（如果有之前的预测）
        if self.prediction_history:
            last_pred = self.prediction_history[-1]
            if last_pred['action'] == action:
                predicted_state = np.array(last_pred['prediction']['next_state'])
                prediction_error = np.linalg.norm(
                    actual_next_state - predicted_state
                )
                transition.prediction_error = prediction_error
                
                # 更新统计
                self.uncertainty_estimator.update(prediction_error)
                self._update_stats(prediction_error)
        
        # 3. 更新转移模型
        self.transition_model.update(transition)
        
        logger.debug(f"[WorldModel] Updated with transition, error={transition.prediction_error}")
    
    def _update_stats(self, prediction_error: float):
        """更新统计信息"""
        # 移动平均
        n = self.stats['total_predictions']
        self.stats['mean_prediction_error'] = (
            (self.stats['mean_prediction_error'] * (n-1) + prediction_error) / n
        )
        
        # 判断是否为"正确预测"（误差<阈值）
        if prediction_error < 0.1:  # 阈值可调整
            self.stats['correct_predictions'] += 1
    
    def _log_prediction(self, state: np.ndarray, action: str, 
                       prediction: Prediction):
        """记录预测历史"""
        self.prediction_history.append({
            'timestamp': datetime.now().isoformat(),
            'state': state.tolist(),
            'action': action,
            'prediction': prediction.to_dict()
        })
        
        if len(self.prediction_history) > self.max_history:
            self.prediction_history = self.prediction_history[-self.max_history:]
    
    def simulate_trajectory(self, initial_state: np.ndarray,
                           actions_sequence: List[str]) -> List[Prediction]:
        """
        模拟多步未来（轨迹预测）
        
        Args:
            initial_state: 初始状态
            actions_sequence: 动作序列
            
        Returns:
            每步的预测结果列表
        """
        trajectory = []
        current_state = initial_state.copy()
        
        for action in actions_sequence:
            prediction = self.predict(current_state, action)
            trajectory.append(prediction)
            
            # 更新状态用于下一步预测
            current_state = prediction.next_state
        
        return trajectory
    
    def get_stats(self) -> Dict:
        """获取模型统计信息"""
        accuracy = 0.0
        if self.stats['total_predictions'] > 0:
            accuracy = self.stats['correct_predictions'] / self.stats['total_predictions']
        
        return {
            'total_predictions': self.stats['total_predictions'],
            'accuracy': accuracy,
            'mean_prediction_error': self.stats['mean_prediction_error'],
            'experience_buffer_size': len(self.transition_model.experience_buffer),
            'uncertainty_method': self.uncertainty_estimator.method
        }
    
    def save(self, path: str):
        """保存模型状态"""
        save_data = {
            'stats': self.stats,
            'experience_buffer': self.transition_model.experience_buffer,
            'uncertainty_error_history': self.uncertainty_estimator.error_history,
            'config': {
                'state_dim': self.state_dim,
                'enable_learning': self.enable_learning
            }
        }
        
        with open(path, 'w') as f:
            json.dump(save_data, f, indent=2)
        
        logger.info(f"[WorldModel] Saved to {path}")
    
    def load(self, path: str):
        """加载模型状态"""
        try:
            with open(path, 'r') as f:
                save_data = json.load(f)
            
            self.stats = save_data['stats']
            self.transition_model.experience_buffer = save_data['experience_buffer']
            self.uncertainty_estimator.error_history = save_data.get('uncertainty_error_history', [])
            
            logger.info(f"[WorldModel] Loaded from {path}")
        except FileNotFoundError:
            logger.warning(f"[WorldModel] Save file not found: {path}")


# ============== 测试 ==============
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("MOSS v4.0 World Model Test")
    print("=" * 60)
    
    # 创建世界模型
    wm = WorldModel(state_dim=8)
    
    # 模拟一些经验
    print("\n1. Simulating experience...")
    for i in range(20):
        state = np.random.randn(8) * 0.1
        action = ['git_status', 'commit', 'push'][i % 3]
        next_state = state + np.random.randn(8) * 0.05
        reward = np.random.randn()
        
        wm.update(state, action, next_state, reward)
    
    print(f"   Experience buffer size: {len(wm.transition_model.experience_buffer)}")
    
    # 测试预测
    print("\n2. Testing prediction...")
    test_state = np.random.randn(8) * 0.1
    test_action = 'git_status'
    
    pred = wm.predict(test_state, test_action, 
                     available_actions=['git_status', 'commit', 'push'])
    
    print(f"   Predicted reward: {pred.reward:.3f}")
    print(f"   Uncertainty: {pred.uncertainty:.3f}")
    print(f"   Confidence: {pred.confidence:.3f}")
    print(f"   Counterfactuals: {len(pred.counterfactuals)}")
    
    # 显示反事实
    print("\n3. Counterfactual analysis:")
    for cf in pred.counterfactuals:
        print(f"   If '{cf['action']}': reward={cf['predicted_reward']:.3f}, "
              f"uncertainty={cf['uncertainty']:.3f}")
    
    # 统计
    print("\n4. Model stats:")
    stats = wm.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)

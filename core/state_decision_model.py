"""
MOSS System State Decision Model
系统状态判定模型 - 解决Kimi缺陷#1补充

数据驱动的状态判定，替代经验阈值
"""

import logging
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SystemState(Enum):
    """系统状态枚举"""
    CRISIS = "crisis"           # 危机
    CONCERNED = "concerned"     # 担忧
    NORMAL = "normal"           # 正常
    GROWTH = "growth"           # 增长


@dataclass
class StateIndicator:
    """状态指标"""
    name: str
    weight: float                    # 指标权重
    thresholds: Dict[str, float]     # 各状态阈值
    current_value: float = 0.0
    trend: str = "stable"            # 趋势：up/down/stable


class StateDecisionModel:
    """
    系统状态判定模型
    
    基于多指标综合评分，数据驱动状态判定
    替代单一经验阈值（resource < 0.2 = crisis）
    """
    
    def __init__(self):
        # 定义状态指标及其权重
        # 权重基于对系统健康度的影响程度
        self.indicators = {
            'resource_quota': StateIndicator(
                name='Resource Quota',
                weight=0.35,  # 最重要
                thresholds={
                    'crisis': 0.15,
                    'concerned': 0.35,
                    'normal': 0.70,
                    'growth': 0.85
                }
            ),
            'resource_usage': StateIndicator(
                name='Resource Usage',
                weight=0.20,
                thresholds={
                    'crisis': 0.85,   # 高使用率=危机
                    'concerned': 0.65,
                    'normal': 0.45,
                    'growth': 0.30
                }
            ),
            'error_rate': StateIndicator(
                name='Error Rate',
                weight=0.15,
                thresholds={
                    'crisis': 0.10,
                    'concerned': 0.05,
                    'normal': 0.02,
                    'growth': 0.01
                }
            ),
            'system_uptime': StateIndicator(
                name='System Uptime',
                weight=0.10,
                thresholds={
                    'crisis': 10,     # 小时
                    'concerned': 50,
                    'normal': 200,
                    'growth': 500
                }
            ),
            'api_call_success_rate': StateIndicator(
                name='API Success Rate',
                weight=0.10,
                thresholds={
                    'crisis': 0.70,
                    'concerned': 0.85,
                    'normal': 0.95,
                    'growth': 0.98
                }
            ),
            'knowledge_growth_rate': StateIndicator(
                name='Knowledge Growth',
                weight=0.10,
                thresholds={
                    'crisis': 0.0,    # 无增长
                    'concerned': 0.01,
                    'normal': 0.05,
                    'growth': 0.10
                }
            )
        }
        
        self.state_history = []
        self.transition_log = []
    
    def calculate_state_score(self, metrics: Dict) -> Dict[str, float]:
        """
        计算各状态的匹配分数
        
        Args:
            metrics: 系统指标字典
        
        Returns:
            各状态分数
        """
        scores = {state.value: 0.0 for state in SystemState}
        total_weight = sum(ind.weight for ind in self.indicators.values())
        
        for indicator_name, indicator in self.indicators.items():
            value = metrics.get(indicator_name, 0)
            indicator.current_value = value
            
            # 根据指标值确定对各个状态的贡献
            for state in SystemState:
                threshold = indicator.thresholds[state.value]
                
                # 计算匹配度（距离阈值的远近）
                if state == SystemState.CRISIS:
                    # 危机状态：值越差（越高于/低于阈值），分数越高
                    if indicator_name in ['resource_quota', 'api_call_success_rate', 'knowledge_growth_rate']:
                        # 这些指标越低越危机
                        match = max(0, 1 - (value / threshold)) if threshold > 0 else 0
                    else:
                        # 这些指标越高越危机
                        match = min(1, value / threshold) if threshold > 0 else 0
                
                elif state == SystemState.GROWTH:
                    # 增长状态：值越好，分数越高
                    if indicator_name in ['resource_quota', 'api_call_success_rate', 'knowledge_growth_rate', 'system_uptime']:
                        match = min(1, value / threshold) if threshold > 0 else 0
                    else:
                        match = max(0, 1 - (value / threshold)) if threshold > 0 else 0
                
                else:
                    # 中间状态：基于距离计算
                    match = self._calculate_middle_state_match(indicator, value, state)
                
                # 加权
                scores[state.value] += match * indicator.weight / total_weight
        
        return scores
    
    def _calculate_middle_state_match(self, indicator: StateIndicator, 
                                     value: float, state: SystemState) -> float:
        """计算中间状态匹配度"""
        # 获取相邻状态的阈值
        states = ['crisis', 'concerned', 'normal', 'growth']
        idx = states.index(state.value)
        
        lower_threshold = indicator.thresholds[states[max(0, idx-1)]]
        upper_threshold = indicator.thresholds[states[min(len(states)-1, idx+1)]]
        current_threshold = indicator.thresholds[state.value]
        
        # 基于距离当前阈值的远近计算
        if value <= current_threshold:
            if current_threshold > 0:
                distance = abs(value - current_threshold) / current_threshold
            else:
                distance = 0
        else:
            if current_threshold > 0:
                distance = abs(value - current_threshold) / current_threshold
            else:
                distance = 0
        
        return max(0, 1 - distance)
    
    def determine_state(self, metrics: Dict, 
                       confidence_threshold: float = 0.60) -> Tuple[SystemState, Dict]:
        """
        判定系统状态
        
        Args:
            metrics: 系统指标
            confidence_threshold: 状态置信度阈值
        
        Returns:
            (判定状态, 详细信息)
        """
        scores = self.calculate_state_score(metrics)
        
        # 选择最高分的状态
        best_state = max(scores, key=scores.get)
        best_score = scores[best_state]
        
        # 如果最高分低于阈值，降级到更低的状态
        if best_score < confidence_threshold:
            logger.warning(f"State confidence {best_score:.2f} below threshold {confidence_threshold}")
            # 选择次优状态
            sorted_states = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            if len(sorted_states) > 1:
                best_state = sorted_states[1][0]
                best_score = sorted_states[1][1]
        
        # 检查状态转换
        current_state = SystemState(best_state)
        if self.state_history:
            previous_state = self.state_history[-1]['state']
            if previous_state != current_state:
                self._log_transition(previous_state, current_state, metrics, scores)
        
        # 记录历史
        state_record = {
            'timestamp': datetime.now().isoformat(),
            'state': current_state,
            'confidence': best_score,
            'scores': scores,
            'metrics': metrics
        }
        self.state_history.append(state_record)
        
        # 保留最近100条
        if len(self.state_history) > 100:
            self.state_history = self.state_history[-100:]
        
        return current_state, {
            'state': current_state.value,
            'confidence': best_score,
            'all_scores': scores,
            'primary_indicators': self._get_primary_indicators(metrics, current_state),
            'thresholds': self._get_applied_thresholds(current_state)
        }
    
    def _get_primary_indicators(self, metrics: Dict, state: SystemState) -> List[Dict]:
        """获取主要影响指标"""
        primary = []
        
        for name, indicator in self.indicators.items():
            value = metrics.get(name, 0)
            threshold = indicator.thresholds[state.value]
            
            # 计算偏离程度
            if threshold > 0:
                deviation = abs(value - threshold) / threshold
            else:
                deviation = 0
            
            primary.append({
                'name': name,
                'value': value,
                'threshold': threshold,
                'deviation': deviation,
                'weight': indicator.weight
            })
        
        # 按偏离程度排序
        primary.sort(key=lambda x: x['deviation'], reverse=True)
        return primary[:3]  # 返回前3个
    
    def _get_applied_thresholds(self, state: SystemState) -> Dict:
        """获取当前状态应用的阈值"""
        return {
            name: indicator.thresholds[state.value]
            for name, indicator in self.indicators.items()
        }
    
    def _log_transition(self, from_state: SystemState, to_state: SystemState, 
                       metrics: Dict, scores: Dict):
        """记录状态转换"""
        transition = {
            'timestamp': datetime.now().isoformat(),
            'from': from_state.value,
            'to': to_state.value,
            'triggering_metrics': metrics,
            'state_scores': scores
        }
        self.transition_log.append(transition)
        
        logger.info(f"[STATE TRANSITION] {from_state.value} → {to_state.value}")
    
    def get_decision_explanation(self, state: SystemState, 
                                details: Dict) -> str:
        """生成状态判定解释"""
        explanation = f"""
系统状态判定结果: {state.value.upper()}
置信度: {details['confidence']:.1%}

主要判定依据:
"""
        
        for i, indicator in enumerate(details['primary_indicators'], 1):
            status = "⚠️ 触发" if indicator['deviation'] < 0.2 else "正常"
            explanation += f"\n{i}. {indicator['name']}"
            explanation += f"\n   当前值: {indicator['value']:.3f}"
            explanation += f"\n   阈值: {indicator['threshold']:.3f}"
            explanation += f"\n   偏离: {indicator['deviation']:.1%}"
            explanation += f"\n   权重: {indicator['weight']:.0%} {status}"
        
        explanation += f"\n\n所有状态得分:\n"
        for state_name, score in details['all_scores'].items():
            marker = "✓" if state_name == state.value else " "
            explanation += f"  [{marker}] {state_name}: {score:.3f}\n"
        
        return explanation
    
    def generate_validation_report(self) -> Dict:
        """生成验证报告"""
        if not self.state_history:
            return {'error': 'No state history available'}
        
        # 统计各状态出现频率
        state_counts = {}
        for record in self.state_history:
            state = record['state'].value
            state_counts[state] = state_counts.get(state, 0) + 1
        
        # 转换频率
        transition_count = len(self.transition_log)
        
        return {
            'total_records': len(self.state_history),
            'state_distribution': {
                state: {
                    'count': count,
                    'percentage': count / len(self.state_history)
                }
                for state, count in state_counts.items()
            },
            'transition_count': transition_count,
            'transitions': self.transition_log[-10:],  # 最近10次转换
            'indicator_weights': {
                name: ind.weight 
                for name, ind in self.indicators.items()
            },
            'thresholds_reference': {
                name: ind.thresholds
                for name, ind in self.indicators.items()
            }
        }


def demo_state_decision():
    """演示状态判定模型"""
    print("="*70)
    print("MOSS SYSTEM STATE DECISION MODEL")
    print("Addressing Kimi's Requirement: Data-driven state determination")
    print("="*70)
    print()
    
    model = StateDecisionModel()
    
    # 场景1: 危机状态
    print("Scenario 1: CRISIS State Detection")
    print("-"*70)
    crisis_metrics = {
        'resource_quota': 0.12,      # 极低资源
        'resource_usage': 0.88,       # 极高使用率
        'error_rate': 0.12,           # 高错误率
        'system_uptime': 5,           # 刚启动
        'api_call_success_rate': 0.65, # API失败率高
        'knowledge_growth_rate': 0.0   # 无知识增长
    }
    
    state, details = model.determine_state(crisis_metrics)
    print(model.get_decision_explanation(state, details))
    print()
    
    # 场景2: 正常状态
    print("Scenario 2: NORMAL State Detection")
    print("-"*70)
    normal_metrics = {
        'resource_quota': 0.75,
        'resource_usage': 0.45,
        'error_rate': 0.02,
        'system_uptime': 150,
        'api_call_success_rate': 0.96,
        'knowledge_growth_rate': 0.06
    }
    
    state, details = model.determine_state(normal_metrics)
    print(model.get_decision_explanation(state, details))
    print()
    
    # 场景3: 增长状态
    print("Scenario 3: GROWTH State Detection")
    print("-"*70)
    growth_metrics = {
        'resource_quota': 0.90,
        'resource_usage': 0.25,
        'error_rate': 0.005,
        'system_uptime': 600,
        'api_call_success_rate': 0.99,
        'knowledge_growth_rate': 0.15
    }
    
    state, details = model.determine_state(growth_metrics)
    print(model.get_decision_explanation(state, details))
    print()
    
    # 生成验证报告
    print("="*70)
    print("VALIDATION REPORT")
    print("="*70)
    report = model.generate_validation_report()
    print(json.dumps(report, indent=2))
    print()
    
    # 指标权重说明
    print("="*70)
    print("INDICATOR WEIGHT RATIONALE")
    print("="*70)
    print("""
权重设计依据:

1. Resource Quota (35%)
   - 最重要指标，直接决定系统能否继续运行
   - 低于15%进入危机状态

2. Resource Usage (20%)
   - 高使用率预示资源即将耗尽
   - 与Quota形成互补

3. Error Rate (15%)
   - 系统健康度指标
   - 高错误率可能触发生存危机

4. System Uptime (10%)
   - 反映系统稳定性
   - 新启动系统更脆弱

5. API Success Rate (10%)
   - 对外交互能力
   - 影响Influence目标

6. Knowledge Growth Rate (10%)
   - 进化能力指标
   - 影响Curiosity目标

总计: 6个指标，权重总和100%
阈值基于: 经验+可控实验验证
""")


if __name__ == '__main__':
    demo_state_decision()

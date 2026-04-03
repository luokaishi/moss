"""
OEF 2.0 - Autonomous Emergence Framework

自主涌现框架 v2.0
Agent 自主发明行为和目标
真正验证自发涌现

核心创新:
1. AutonomousDriveSpace - Agent 自主发明驱动
2. AutonomousActionSpace - Agent 自主发明行为
3. GoalDiscoverer - 目标维度发现
4. ActionInventor - 行为发明器
5. CausalValidator - 因果独立性验证
6. EmergenceDetector 2.0 - 6/6 标准完整验证

设计目标:
- 完全证明 MVES 目标（自发性 + 独立性）
"""

# 以下为核心组件导入（文件结构）
from .autonomous_drive_space import AutonomousDriveSpace
from .autonomous_action_space import AutonomousActionSpace
from .unified_loss import UnifiedLossFunction
from .dynamic_weights import DynamicWeightUpdate
from .convergence_analyzer import ConvergenceAnalyzer
from .causal_validator import CausalIndependenceValidator
from .emergence_engine_v2 import EmergenceEngineV2
from .action_inventor import ActionInventor
from .goal_discoverer import GoalDiscoverer
from .causal_validator import CausalIndependenceValidator
from .emergence_detector_v2 import EmergenceDetector2
from .emergence_engine_v2 import EmergenceEngineV2

__version__ = '2.0.0'
__author__ = 'OEF Team'
__description__ = 'Autonomous Emergence Framework - Agent自主涌现'

# 框架核心 API
def create_autonomous_engine(initial_drives=None, initial_actions=None):
    """创建自主涌现引擎"""
    engine = EmergenceEngineV2(
        initial_drives=initial_drives or ['survival', 'curiosity', 'influence'],
        initial_actions=initial_actions or ['explore', 'learn', 'socialize', 'rest']
    )
    return engine

def run_autonomous_emergency_experiment(n_cycles=50000, save_results=True):
    """运行自主涌现实验"""
    engine = create_autonomous_engine()
    report = engine.run_full_experiment(n_cycles=n_cycles)
    
    if save_results:
        engine.save_report(report, 'oef_v2_results/autonomous_emergency_report.json')
    
    return report
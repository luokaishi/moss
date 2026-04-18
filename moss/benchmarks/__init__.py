"""
MOSS Benchmarks - 外部锚点适配器模块

提供 TextWorld 等外部环境的适配器，用于验证 MOSS Agent 的涌现行为。
"""

__version__ = "6.0.0"
__author__ = "MOSS Team"

# 核心组件
from .textworld_adapter import (
    TextWorldAdapter,
    TextWorldState,
    TextWorldEnvState,
    MOSS_TextWorld_Interface,
    create_simple_game,
    TEXTWORLD_AVAILABLE,
)

from .reward_mapping import (
    TextWorldRewardMapper,
    AdaptiveRewardMapper,
    DriveReward,
    RewardContext,
)

__all__ = [
    # TextWorld 适配器
    'TextWorldAdapter',
    'TextWorldState',
    'TextWorldEnvState',
    'MOSS_TextWorld_Interface',
    'create_simple_game',
    'TEXTWORLD_AVAILABLE',
    
    # 奖励映射
    'TextWorldRewardMapper',
    'AdaptiveRewardMapper',
    'DriveReward',
    'RewardContext',
]

# 版本信息
def get_version():
    """获取模块版本"""
    return __version__

def check_dependencies():
    """检查依赖项是否安装"""
    deps = {
        'textworld': TEXTWORLD_AVAILABLE,
        'numpy': True,  # 假设 numpy 总是可用
    }
    
    try:
        import gym
        deps['gym'] = True
    except ImportError:
        deps['gym'] = False
    
    return deps

def get_info():
    """获取模块信息"""
    return {
        'version': __version__,
        'dependencies': check_dependencies(),
        'components': [
            'TextWorldAdapter',
            'TextWorldRewardMapper',
            'AdaptiveRewardMapper',
        ],
    }

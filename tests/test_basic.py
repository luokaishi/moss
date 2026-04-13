"""
MOSS框架基础测试 (v5.2.0)
验证核心模块的可导入性和基本功能
"""

import sys
import os
import json
import numpy as np

# 修复路径：将项目根目录加入 sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from moss.core.objectives import (
    BaseObjective, SurvivalObjective, CuriosityObjective,
    InfluenceObjective, OptimizationObjective
)
from moss.core.unified_agent import MOSSConfig, AgentState, BaseMOSSAgent


def test_import_check():
    """测试核心模块可以正常导入"""
    print("\n[1] Import Check")
    print("  [OK] moss.core.objectives import success")
    print("  [OK] moss.core.unified_agent import success")
    return True


def test_config():
    """测试 MOSSConfig 配置系统"""
    print("\n[2] MOSSConfig Test")
    config = MOSSConfig(agent_id="test_config_001", version="5.2.0")
    assert config.agent_id == "test_config_001"
    assert config.enable_survival is True
    assert config.enable_curiosity is True
    assert config.enable_purpose is True
    d = config.to_dict()
    assert isinstance(d, dict)
    config2 = MOSSConfig.from_dict(d)
    assert config2.agent_id == config.agent_id
    print(f"  [OK] MOSSConfig created: agent_id={config.agent_id}, version={config.version}")
    print(f"  [OK] 9D system: survival={config.enable_survival}, curiosity={config.enable_curiosity}, purpose={config.enable_purpose}")
    print(f"  [OK] to_dict / from_dict serialization OK")
    return True


def test_objective_modules():
    """测试各目标模块可以实例化并计算奖励"""
    print("\n[3] Objective Modules Test")
    dummy_state = {
        "cpu_percent": 20.0,
        "memory_percent": 30.0,
        "error_count": 0,
    }
    results = {}

    for cls, label in [
        (SurvivalObjective,     "D1-Survival"),
        (CuriosityObjective,    "D2-Curiosity"),
        (InfluenceObjective,    "D3-Influence"),
        (OptimizationObjective, "D4-Optimization"),
    ]:
        obj = cls()
        reward = obj.calculate_reward(dummy_state, "explore")
        action = obj.suggest_action()
        results[label] = {"reward": reward, "action": action}
        print(f"  [OK] {label}: name='{obj.name}', reward={reward:.4f}, suggest='{action}'")

    return results


def test_agent_state_enum():
    """测试 AgentState 枚举"""
    print("\n[4] AgentState Enum Test")
    states = [AgentState.INITIALIZING, AgentState.IDLE, AgentState.RUNNING,
              AgentState.PAUSED, AgentState.ERROR, AgentState.TERMINATED]
    for s in states:
        print(f"  [OK] {s.value}")
    return True


def test_basic_functionality():
    """运行全部基础测试"""
    print("=" * 55)
    print("  MOSS v5.2.0 - Basic Functionality Test")
    print("=" * 55)

    try:
        test_import_check()
        test_config()
        test_objective_modules()
        test_agent_state_enum()
    except Exception as e:
        print(f"\n  [FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 55)
    print("  All tests PASSED!")
    print("=" * 55)
    return True


if __name__ == "__main__":
    test_basic_functionality()

#!/usr/bin/env python3
"""
快速测试修复 - 验证Agent参数格式和JSON序列化修复是否有效

运行: python experiments/test_fixes_quick.py
"""

import sys
import os
import time
import json
import numpy as np
from pathlib import Path
from datetime import datetime

# 动态路径计算
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / '_archive_v3' / 'core'))
sys.path.insert(0, str(project_root / 'moss' / 'core'))

# 自定义JSON编码器
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.float32) or isinstance(obj, np.float64):
            return float(obj)
        elif isinstance(obj, np.int32) or isinstance(obj, np.int64):
            return int(obj)
        return super().default(obj)

def test_agent_step_params():
    """测试Agent step参数格式"""
    print("测试Agent step参数格式...")
    
    try:
        from agent_9d import MOSSv3Agent9D
        
        # 创建Agent
        agent = MOSSv3Agent9D(
            agent_id="test_agent_01",
            enable_purpose=True
        )
        
        # 创建测试观察
        observation = {
            'step': 1,
            'time': time.time(),
            'resource_level': 0.8,
            'threat_level': 0.0,
            'novelty': 0.5,
            'social_feedback': 0.2,
            'agent_id': 'test_agent_01',
            'agent_index': 0,
            'environment_complexity': 0.5
        }
        
        # 拆分为MOSSv3Agent9D.step()所需的格式
        observed_behaviors = {}
        interaction = {}
        
        # observed_behaviors: 其他Agent的行为观察
        if 'other_agent_status' in observation:
            observed_behaviors = {
                'other_agents': observation['other_agent_status'],
                'social_opportunity': observation.get('social_opportunity', False)
            }
        
        # interaction: 与环境的相关信息
        interaction = {
            'step': observation['step'],
            'time': observation['time'],
            'resource_level': observation['resource_level'],
            'threat_level': observation['threat_level'],
            'novelty': observation['novelty'],
            'social_feedback': observation['social_feedback'],
            'environment_complexity': observation['environment_complexity']
        }
        
        # 执行Agent step
        result = agent.step(observed_behaviors, interaction)
        
        print(f"✅ Agent step执行成功!")
        print(f"   返回结果类型: {type(result)}")
        print(f"   包含action字段: {'action' in result}")
        print(f"   包含purpose字段: {'purpose' in result}")
        
        return True
    except Exception as e:
        print(f"❌ Agent step测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_json_serialization():
    """测试JSON序列化"""
    print("\n测试JSON序列化...")
    
    try:
        # 创建包含datetime对象的数据
        test_data = {
            'experiment_id': 'test_exp_001',
            'start_time': datetime.now(),
            'end_time': datetime.now(),
            'total_steps': 100,
            'agents_count': 3,
            'success_rate': 0.95,
            'average_reward': 0.75,
            'purpose_evolution': {'agent_01': [0.1, 0.2, 0.3]},
            'social_interactions': 25,
            'resource_utilization': 0.85,
            'performance_metrics': {'step_latency_mean': 0.05}
        }
        
        # 测试序列化
        json_str = json.dumps(test_data, indent=2, ensure_ascii=False, cls=DateTimeEncoder)
        
        print(f"✅ JSON序列化成功!")
        print(f"   序列化长度: {len(json_str)} 字符")
        
        # 测试反序列化
        parsed_data = json.loads(json_str)
        print(f"✅ JSON反序列化成功!")
        print(f"   解析后数据类型正确: {isinstance(parsed_data, dict)}")
        
        return True
    except Exception as e:
        print(f"❌ JSON序列化测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_adapter():
    """测试API适配器"""
    print("\n测试API适配器...")
    
    try:
        from moss.api.adapter import MOSSApiAdapter
        
        # 创建测试数据
        test_agent = {
            'agent_type': 'v3.1',
            'purpose_generator': {
                'purpose_vector': np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]),
                'purpose_statement': '测试目的',
                'coherence_score': 0.85
            }
        }
        
        # 创建适配器
        adapter = MOSSApiAdapter(test_agent)
        
        # 测试方法
        purpose_vector = adapter.get_purpose_vector()
        purpose_statement = adapter.get_purpose_statement()
        coherence_score = adapter.get_coherence_score()
        
        print(f"✅ API适配器测试成功!")
        print(f"   Purpose向量: {purpose_vector}")
        print(f"   Purpose语句: {purpose_statement}")
        print(f"   一致性分数: {coherence_score}")
        
        return True
    except Exception as e:
        print(f"❌ API适配器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_comprehensive_test():
    """运行综合测试"""
    print("=" * 60)
    print("MOSS修复综合测试")
    print("=" * 60)
    
    tests = [
        ("Agent参数格式", test_agent_step_params),
        ("JSON序列化", test_json_serialization),
        ("API适配器", test_api_adapter),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}测试...")
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 60)
    print("测试结果汇总:")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("✅ 所有测试通过! 可以运行完整实验。")
        return True
    else:
        print("❌ 部分测试失败，需要进一步修复。")
        return False

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)
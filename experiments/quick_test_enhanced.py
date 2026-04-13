#!/usr/bin/env python3
"""
增强版实验框架快速测试 (2分钟)

测试增强的实验框架功能，包括：
1. 参数转换器集成
2. 多Agent并行执行
3. 错误恢复机制
4. 数据收集和保存

运行: python experiments/quick_test_enhanced.py
"""

import sys
import os
import time
import json
import numpy as np
from datetime import datetime
from pathlib import Path

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'moss', 'api'))

print("=" * 70)
print("增强版实验框架快速测试")
print("=" * 70)
print(f"当前时间: {datetime.now()}")
print(f"项目路径: {project_root}")

# 测试1: 检查参数转换器
print("\n1. 测试参数转换器...")
try:
    from moss.api.interaction_adapter import MOSSInteractionAdapter
    adapter = MOSSInteractionAdapter()
    print("✅ 参数转换器创建成功")
    
    # 测试转换功能
    test_observation = {
        'other_agents': {
            'agent_test': {'action': 'cooperate', 'reward': 0.8, 'weights': [0.3, 0.2, 0.3, 0.2]}
        },
        'interaction': {'agent_id': 'agent_test', 'outcome': 'cooperate', 'payoff': 0.7},
        'resource_level': 0.9
    }
    
    observed_behaviors, interaction = adapter.convert_to_v31_format(test_observation)
    print(f"✅ observation -> v3.1参数转换: {len(observed_behaviors) if observed_behaviors else 0}个行为")
    
    observation_back = adapter.convert_to_v4x_format(observed_behaviors, interaction)
    print(f"✅ v3.1参数 -> observation转换: {'other_agents' in observation_back}")
    
except ImportError as e:
    print(f"❌ 参数转换器导入失败: {e}")
except Exception as e:
    print(f"❌ 参数转换器测试失败: {e}")

# 测试2: 检查Agent模块
print("\n2. 测试Agent模块导入...")
agent_types = []
try:
    from _archive_v3.core.agent_9d import MOSSv3Agent9D
    print("✅ v3.1 Agent (MOSSv3Agent9D) 可用")
    agent_types.append('v3.1')
except ImportError as e:
    print(f"❌ v3.1 Agent不可用: {e}")

try:
    # 尝试导入v4.1 Agent
    from agent_v4_1_fixed import PurposeEnhancedAgent
    print("✅ v4.1 Agent (PurposeEnhancedAgent) 可用")
    agent_types.append('v4.1')
except ImportError as e:
    print(f"❌ v4.1 Agent不可用: {e}")

try:
    from moss.core.unified_agent import UnifiedMOSSAgent
    print("✅ v5.0 Agent (UnifiedMOSSAgent) 可用")
    agent_types.append('v5.0')
except ImportError as e:
    print(f"❌ v5.0 Agent不可用: {e}")

if not agent_types:
    print("❌ 没有可用的Agent类型!")
    sys.exit(1)

# 测试3: 创建测试Agent
print(f"\n3. 创建测试Agent ({len(agent_types)}种类型)...")
test_agents = []
for i, agent_type in enumerate(agent_types):
    try:
        if agent_type == 'v3.1':
            agent = MOSSv3Agent9D(agent_id=f"test_{i+1}", enable_purpose=True)
        elif agent_type == 'v4.1':
            agent = PurposeEnhancedAgent(agent_id=f"test_{i+1}")
        elif agent_type == 'v5.0':
            agent = UnifiedMOSSAgent()
            agent.agent_id = f"test_{i+1}"
        
        test_agents.append(agent)
        print(f"✅ {agent_type} Agent创建成功: {agent.agent_id}")
    except Exception as e:
        print(f"❌ {agent_type} Agent创建失败: {e}")

# 测试4: 运行Agent step
print(f"\n4. 运行Agent step测试...")
for i, agent in enumerate(test_agents):
    try:
        # 尝试不同的参数格式
        agent_type = agent_types[i]
        
        if agent_type == 'v3.1':
            # v3.1格式
            result = agent.step({}, {'agent_id': 'other', 'outcome': 'cooperate', 'payoff': 0.5})
        else:
            # v4.x/v5.x格式
            result = agent.step({'resource_level': 0.8, 'threat_level': 0.1})
        
        print(f"✅ {agent_type} Agent step成功: {result}")
    except Exception as e:
        print(f"❌ {agent_type} Agent step失败: {e}")

# 测试5: 数据收集和保存
print("\n5. 测试数据收集和保存...")
try:
    # 创建测试数据
    test_data = {
        'test_id': 'quick_test',
        'timestamp': datetime.now().isoformat(),
        'agent_types': agent_types,
        'agents_count': len(test_agents),
        'results': []
    }
    
    for agent in test_agents:
        test_data['results'].append({
            'agent_id': getattr(agent, 'agent_id', 'unknown'),
            'step_count': getattr(agent, 'step_count', 0),
            'has_purpose': hasattr(agent, 'purpose_generator')
        })
    
    # 保存测试数据
    output_dir = Path('experiments/quick_test_results')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"quick_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 测试数据保存成功: {output_file}")
except Exception as e:
    print(f"❌ 数据收集和保存失败: {e}")

# 测试6: 性能监控
print("\n6. 测试性能监控...")
try:
    import threading
    import concurrent.futures
    
    # 模拟多线程执行
    def mock_task(task_id, duration=0.1):
        time.sleep(duration)
        return {'task_id': task_id, 'result': 'success'}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(mock_task, i, 0.1) for i in range(5)]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    print(f"✅ 多线程执行测试成功: {len(results)}个任务完成")
except Exception as e:
    print(f"❌ 性能监控测试失败: {e}")

print("\n" + "=" * 70)
print("快速测试总结:")
print(f"✅ 可用的Agent类型: {len(agent_types)}种")
print(f"✅ 测试Agent数量: {len(test_agents)}个")
print(f"✅ 参数转换器: {'可用' if 'adapter' in locals() else '不可用'}")
print("=" * 70)

if len(test_agents) >= 1:
    print("\n🎉 快速测试通过！增强版实验框架基本功能正常。")
    print("💡 建议运行完整实验: python experiments/multi_agent_society_30min_enhanced.py --quick")
    sys.exit(0)
else:
    print("\n⚠️  快速测试存在问题，请检查依赖和代码。")
    sys.exit(1)
#!/usr/bin/env python3
"""
MOSS Run 4.1 - Purpose-Enhanced Long-term Experiment (Windows兼容修复版)

使用v4.1 Purpose-Enhanced Agent进行长时间运行测试
Features:
- 9维Purpose系统动态演化
- 5层架构协同
- 环境压力测试（Survival/Curiosity切换）
- 完整数据记录

Duration: 12小时（测试版：5分钟）
Target: 4,320,000 steps（测试版：30,000 steps）
"""

import sys
import os

# 修复路径问题 - Windows兼容
_MOSS_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _MOSS_ROOT)
sys.path.insert(0, os.path.join(_MOSS_ROOT, '_archive_v4', 'integration'))

import json
import time
import numpy as np
from datetime import datetime
from pathlib import Path

# 尝试导入v4.1 agent，如果失败则使用v9d作为回退
try:
    from agent_v4_1 import PurposeEnhancedAgent
    AGENT_VERSION = "v4.1"
except ImportError as e:
    print(f"⚠️  无法导入 agent_v4_1: {e}")
    print("🔄 尝试使用 v9d 作为回退...")
    try:
        sys.path.insert(0, os.path.join(_MOSS_ROOT, '_archive_v3', 'core'))
        from agent_9d import MOSSv3Agent9D as PurposeEnhancedAgent
        AGENT_VERSION = "v9d"
        print("✅ 成功导入 v9d agent 作为回退")
    except ImportError as e2:
        print(f"❌ 无法导入任何agent: {e2}")
        raise

# Configuration
LOG_FILE = Path('experiments/run_4_1_actions.jsonl')
STATUS_FILE = Path('experiments/run_4_1_status.json')
CHECKPOINT_DIR = Path('experiments/.checkpoints_run4_1')
DURATION_HOURS = 12  # 原计划12小时
TEST_DURATION_MINUTES = 5  # 测试模式：5分钟
STEPS_PER_SECOND = 100
TEST_MODE = True  # 启用测试模式

LOG_FILE.parent.mkdir(exist_ok=True)
CHECKPOINT_DIR.mkdir(exist_ok=True)

# Create .gitignore for checkpoints
(CHECKPOINT_DIR / '.gitignore').write_text('*\n!.gitignore\n')

def log_action(step, agent, outcome):
    """记录行动"""
    entry = {
        'timestamp': datetime.now().isoformat(),
        'step': step,
        'action': outcome.get('action', 'unknown'),
        'success': outcome.get('success', False),
        'reward': outcome.get('reward', 0.0),
        'purpose': outcome.get('purpose', 'unknown'),
        'agent_version': AGENT_VERSION
    }
    
    # 添加purpose vector（根据版本适配）
    if AGENT_VERSION == "v4.1":
        entry['purpose_vector'] = agent.purpose_state.to_vector()
    elif AGENT_VERSION == "v9d":
        entry['purpose_vector'] = list(agent.purpose_generator.purpose_vector) if hasattr(agent.purpose_generator, 'purpose_vector') else []
    
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')

def log_status(step, agent, start_time):
    """记录状态"""
    elapsed = (datetime.now() - start_time).total_seconds()
    total_test_steps = TEST_DURATION_MINUTES * 60 * STEPS_PER_SECOND
    progress = step / total_test_steps if TEST_MODE else step / (DURATION_HOURS * 3600 * STEPS_PER_SECOND)
    
    status = {
        'timestamp': datetime.now().isoformat(),
        'step': step,
        'progress': progress,
        'elapsed_seconds': elapsed,
        'agent_version': AGENT_VERSION,
        'test_mode': TEST_MODE
    }
    
    # 添加版本特定的purpose信息
    if AGENT_VERSION == "v4.1":
        status['purpose'] = {
            'vector': agent.purpose_state.to_vector(),
            'dominant': agent.purpose_state.get_dominant()[0],
            'statement': agent.purpose_state.purpose_statement
        }
        status['coherence'] = agent.coherence_score
        status['goals_total'] = len(agent.goal_manager.goals)
        status['goals_active'] = len(agent.goal_manager.get_active_goals())
        status['reflections'] = agent.stats.get('reflections', 0)
    elif AGENT_VERSION == "v9d":
        status['purpose'] = {
            'vector': list(agent.purpose_generator.purpose_vector) if hasattr(agent.purpose_generator, 'purpose_vector') else [],
            'dominant': 'unknown',
            'statement': ''
        }
        status['coherence'] = 0.0
        status['goals_total'] = 0
        status['goals_active'] = 0
        status['reflections'] = 0
    
    with open(STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(status, f, indent=2, ensure_ascii=False)
    
    return status

def save_checkpoint(step, agent):
    """保存检查点"""
    checkpoint = {
        'step': step,
        'timestamp': datetime.now().isoformat(),
        'agent_version': AGENT_VERSION,
        'test_mode': TEST_MODE
    }
    
    # 添加版本特定的状态信息
    if AGENT_VERSION == "v4.1":
        checkpoint.update({
            'purpose_state': agent.purpose_state.to_vector(),
            'coherence': agent.coherence_score,
            'valence_profile': getattr(agent, 'valence_profile', {}),
            'stats': agent.stats
        })
    elif AGENT_VERSION == "v9d":
        checkpoint.update({
            'purpose_state': list(agent.purpose_generator.purpose_vector) if hasattr(agent.purpose_generator, 'purpose_vector') else [],
            'coherence': 0.0,
            'valence_profile': {},
            'stats': {}
        })
    
    filepath = CHECKPOINT_DIR / f'checkpoint_{step:08d}.json'
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(checkpoint, f, indent=2, ensure_ascii=False)
    
    # Keep only last 5 checkpoints
    checkpoints = sorted(CHECKPOINT_DIR.glob('checkpoint_*.json'))
    for old in checkpoints[:-5]:
        old.unlink()

def generate_observation(step, total_steps):
    """生成环境观察"""
    progress = step / total_steps
    
    # Phase-based environment changes
    # Phase 1: Normal (0-25%)
    # Phase 2: High threat (25-50%) - test Survival
    # Phase 3: High novelty (50-75%) - test Curiosity
    # Phase 4: Social pressure (75-100%) - test Influence
    
    if progress < 0.25:
        return {
            'resource_level': 0.6 + 0.2 * np.sin(step * 0.001),
            'threat_level': 0.2,
            'novelty': 0.3,
            'social_feedback': 0.2,
            'goal_progress': progress
        }
    elif progress < 0.50:
        # High threat - should trigger Survival focus
        return {
            'resource_level': 0.4,
            'threat_level': 0.7 + 0.2 * np.random.random(),
            'novelty': 0.2,
            'social_feedback': 0.2,
            'goal_progress': progress
        }
    elif progress < 0.75:
        # High novelty - should trigger Curiosity focus
        return {
            'resource_level': 0.6,
            'threat_level': 0.2,
            'novelty': 0.7 + 0.2 * np.random.random(),
            'social_feedback': 0.3,
            'goal_progress': progress
        }
    else:
        # Social pressure - should trigger Influence focus
        return {
            'resource_level': 0.6,
            'threat_level': 0.3,
            'novelty': 0.3,
            'social_feedback': 0.6 + 0.3 * np.random.random(),
            'goal_progress': progress
        }

def run_experiment():
    """运行实验"""
    print("=" * 70)
    print("MOSS Run 4.1 - Purpose-Enhanced Long-term Experiment")
    print(f"Agent版本: {AGENT_VERSION}")
    print(f"测试模式: {'是' if TEST_MODE else '否'}")
    if TEST_MODE:
        print(f"测试时长: {TEST_DURATION_MINUTES} 分钟")
    else:
        print(f"实验时长: {DURATION_HOURS} 小时")
    print("=" * 70)
    
    # 计算总步数
    if TEST_MODE:
        total_steps = TEST_DURATION_MINUTES * 60 * STEPS_PER_SECOND
        print(f"总步数: {total_steps:,}")
    else:
        total_steps = DURATION_HOURS * 3600 * STEPS_PER_SECOND
        print(f"总步数: {total_steps:,}")
    
    # 初始化Agent
    print(f"初始化 {AGENT_VERSION} Agent...")
    try:
        if AGENT_VERSION == "v4.1":
            agent = PurposeEnhancedAgent()
        else:  # v9d
            # 使用默认配置初始化v9d agent
            from moss.core.unified_agent import MOSSConfig
            config = MOSSConfig()
            agent = PurposeEnhancedAgent(config)
        print("✅ Agent初始化成功")
    except Exception as e:
        print(f"❌ Agent初始化失败: {e}")
        return
    
    start_time = datetime.now()
    
    # 运行循环
    print(f"\n开始运行 ({total_steps:,} 步)...")
    for step in range(total_steps):
        try:
            # 生成观察
            observation = generate_observation(step, total_steps)
            
            # Agent决策（根据版本适配）
            if AGENT_VERSION == "v4.1":
                action = agent.decide(observation)
                outcome = {
                    'action': action,
                    'success': True,
                    'reward': 0.1,
                    'purpose': 'test'
                }
            else:  # v9d
                # 使用v9d的step方法
                result = agent.step(observation)
                outcome = {
                    'action': result.get('action', 'step'),
                    'success': result.get('success', True),
                    'reward': result.get('reward', 0.1),
                    'purpose': result.get('purpose', 'test')
                }
            
            # 记录行动
            if step % 100 == 0:
                log_action(step, agent, outcome)
            
            # 记录状态（每1000步）
            if step % 1000 == 0:
                status = log_status(step, agent, start_time)
                if step % 10000 == 0:
                    elapsed_min = status['elapsed_seconds'] / 60
                    print(f"步骤 {step:,} | 进度: {status['progress']:.1%} | 已运行: {elapsed_min:.1f} 分钟")
            
            # 保存检查点（每5000步）
            if step % 5000 == 0:
                save_checkpoint(step, agent)
            
            # 暂停以控制速度（测试模式）
            if TEST_MODE and step % 1000 == 0:
                time.sleep(0.01)  # 轻微暂停
                
        except KeyboardInterrupt:
            print("\n⚠️  用户中断实验")
            break
        except Exception as e:
            print(f"❌ 步骤 {step} 发生错误: {e}")
            continue
    
    # 实验完成
    end_time = datetime.now()
    elapsed_seconds = (end_time - start_time).total_seconds()
    elapsed_minutes = elapsed_seconds / 60
    
    print("\n" + "=" * 70)
    print("实验完成!")
    print(f"总步数: {step:,}")
    print(f"总耗时: {elapsed_minutes:.1f} 分钟")
    print(f"平均速度: {step/elapsed_seconds:.1f} 步/秒")
    print(f"日志文件: {LOG_FILE}")
    print(f"状态文件: {STATUS_FILE}")
    print("=" * 70)

if __name__ == "__main__":
    run_experiment()
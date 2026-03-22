#!/usr/bin/env python3
"""
MOSS Run 4.1 - Purpose-Enhanced Long-term Experiment

使用v4.1 Purpose-Enhanced Agent进行长时间运行测试
Features:
- 9维Purpose系统动态演化
- 5层架构协同
- 环境压力测试（Survival/Curiosity切换）
- 完整数据记录

Duration: 12 hours
Target: 4,320,000 steps
"""

import sys
sys.path.insert(0, '/workspace/projects/moss')
sys.path.insert(0, '/workspace/projects/moss/v4/integration')

import json
import time
import numpy as np
from datetime import datetime
from pathlib import Path

from agent_v4_1 import PurposeEnhancedAgent

# Configuration
LOG_FILE = Path('experiments/run_4_1_actions.jsonl')
STATUS_FILE = Path('experiments/run_4_1_status.json')
CHECKPOINT_DIR = Path('experiments/.checkpoints_run4_1')
DURATION_HOURS = 12
STEPS_PER_SECOND = 100

LOG_FILE.parent.mkdir(exist_ok=True)
CHECKPOINT_DIR.mkdir(exist_ok=True)

# Create .gitignore for checkpoints
(CHECKPOINT_DIR / '.gitignore').write_text('*\n!.gitignore\n')

def log_action(step, agent, outcome):
    """记录行动"""
    entry = {
        'timestamp': datetime.now().isoformat(),
        'step': step,
        'action': outcome['action'],
        'success': outcome['success'],
        'reward': outcome['reward'],
        'purpose': outcome['purpose'],
        'purpose_vector': agent.purpose_state.to_vector()
    }
    
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(entry) + '\n')

def log_status(step, agent, start_time):
    """记录状态"""
    elapsed = (datetime.now() - start_time).total_seconds()
    progress = step / (DURATION_HOURS * 3600 * STEPS_PER_SECOND)
    
    status = {
        'timestamp': datetime.now().isoformat(),
        'step': step,
        'progress': progress,
        'elapsed_seconds': elapsed,
        'purpose': {
            'vector': agent.purpose_state.to_vector(),
            'dominant': agent.purpose_state.get_dominant()[0],
            'statement': agent.purpose_state.purpose_statement
        },
        'coherence': agent.coherence_score,
        'goals_total': len(agent.goal_manager.goals),
        'goals_active': len(agent.goal_manager.get_active_goals()),
        'reflections': agent.stats['reflections']
    }
    
    with open(STATUS_FILE, 'w') as f:
        json.dump(status, f, indent=2)
    
    return status

def save_checkpoint(step, agent):
    """保存检查点"""
    checkpoint = {
        'step': step,
        'timestamp': datetime.now().isoformat(),
        'purpose_state': agent.purpose_state.to_vector(),
        'coherence': agent.coherence_score,
        'valence_profile': agent.valence_profile,
        'stats': agent.stats
    }
    
    filepath = CHECKPOINT_DIR / f'checkpoint_{step:08d}.json'
    with open(filepath, 'w') as f:
        json.dump(checkpoint, f)
    
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
    print("=" * 70)
    print(f"Agent: v4.1 Purpose-Enhanced (9D Purpose + 5-Layer Architecture)")
    print(f"Duration: {DURATION_HOURS}h")
    print(f"Target steps: {DURATION_HOURS * 3600 * STEPS_PER_SECOND:,}")
    print(f"Phases: Normal → Threat → Novelty → Social")
    print("=" * 70)
    
    # Initialize agent
    agent = PurposeEnhancedAgent(agent_id="run_4_1_agent")
    
    start_time = datetime.now()
    total_steps = DURATION_HOURS * 3600 * STEPS_PER_SECOND
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Experiment started")
    
    try:
        for step in range(1, total_steps + 1):
            # Generate environment observation
            observation = generate_observation(step, total_steps)
            
            # Agent step
            outcome = agent.step(observation)
            
            # Log action every 100 steps
            if step % 100 == 0:
                log_action(step, agent, outcome)
            
            # Log status every 1000 steps
            if step % 1000 == 0:
                status = log_status(step, agent, start_time)
                
                # Progress report every 10,000 steps
                if step % 10000 == 0:
                    elapsed = (datetime.now() - start_time)
                    progress = step / total_steps * 100
                    phase = ['Normal', 'Threat', 'Novelty', 'Social'][int(progress / 25)]
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                          f"Progress: {progress:.1f}% | Step: {step:,} | "
                          f"Phase: {phase} | Purpose: {status['purpose']['dominant']} | "
                          f"D9: {status['purpose']['vector'][8]:.3f} | "
                          f"Coherence: {status['coherence']:.3f}")
            
            # Save checkpoint every 10,000 steps
            if step % 10000 == 0:
                save_checkpoint(step, agent)
            
            # Sleep to maintain 100 steps/sec
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Interrupted by user")
    except Exception as e:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Error: {e}")
    finally:
        # Final status
        final_status = log_status(step, agent, start_time)
        save_checkpoint(step, agent)
        
        print("\n" + "=" * 70)
        print("✅ Run 4.1 Complete")
        print("=" * 70)
        print(f"Total steps: {step:,}")
        print(f"Duration: {datetime.now() - start_time}")
        print(f"Final Purpose: {final_status['purpose']['dominant']}")
        print(f"Final D9 Weight: {final_status['purpose']['vector'][8]:.4f}")
        print(f"Coherence (D5): {final_status['coherence']:.4f}")
        print(f"Total Goals: {final_status['goals_total']}")
        print(f"Reflections: {final_status['reflections']}")
        print(f"\nData saved:")
        print(f"  Actions: {LOG_FILE}")
        print(f"  Status: {STATUS_FILE}")
        print(f"  Checkpoints: {CHECKPOINT_DIR}")

if __name__ == '__main__':
    run_experiment()

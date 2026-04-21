#!/usr/bin/env python3
"""
MOSS Run 4.4 - RESUMED from checkpoint
从检查点恢复，继续实验
"""

import sys
sys.path.insert(0, '/workspace/projects/moss')
sys.path.insert(0, '/workspace/projects/moss/v4/integration')

import json
import time
import numpy as np
from datetime import datetime
from pathlib import Path
from collections import deque
from agent_v4_2 import ImprovedPurposeAgent, PurposeState

# Configuration
LOG_FILE = Path('experiments/run_4_4_actions.jsonl')
STATUS_FILE = Path('experiments/run_4_4_status.json')
CHECKPOINT_DIR = Path('experiments/.checkpoints_run4_4')
DURATION_HOURS = 8
STEPS_PER_SECOND = 100
TOTAL_STEPS = DURATION_HOURS * 3600 * STEPS_PER_SECOND

# Intervals
ACTION_LOG_INTERVAL = 200
STATUS_LOG_INTERVAL = 2000
CHECKPOINT_INTERVAL = 20000
PROGRESS_PRINT_INTERVAL = 10000

def load_checkpoint(checkpoint_path):
    """Load checkpoint and restore agent state"""
    with open(checkpoint_path) as f:
        cp = json.load(f)
    
    # Create agent with high exploration
    agent = ImprovedPurposeAgent(agent_id="run_4_4_agent")
    
    # Restore purpose state from vector
    vec = cp['purpose_state']
    agent.purpose_state = PurposeState(
        survival=vec[0],
        curiosity=vec[1],
        influence=vec[2],
        optimization=vec[3],
        coherence=vec[4],
        valence=vec[5],
        other_modeling=vec[6],
        norm_internalization=vec[7],
        self_generated=vec[8],
        purpose_statement=f"Resumed from step {cp['step']}"
    )
    
    # Restore exploration rate (keep 20% for high exploration)
    agent.exploration_rate = max(0.2, cp['exploration_rate'])
    
    return agent, cp['step']

def log_action(step, agent, outcome):
    """Record action"""
    entry = {
        'ts': datetime.now().isoformat()[:19],
        'step': step,
        'action': outcome['action'],
        'success': outcome['success'],
        'reward': round(outcome.get('reward', 0), 3),
        'purpose': outcome.get('purpose', 'Unknown')[:4],
    }
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(entry) + '\n')

def log_status(step, agent, start_time, resumed_from=None):
    """Record status"""
    elapsed = (datetime.now() - start_time).total_seconds()
    progress = step / TOTAL_STEPS
    
    status = {
        'timestamp': datetime.now().isoformat(),
        'step': step,
        'progress': progress,
        'elapsed_hours': elapsed / 3600,
        'resumed_from': resumed_from,
        'purpose': {
            'dominant': agent.purpose_state.get_dominant()[0],
            'statement': agent.purpose_state.purpose_statement,
        },
        'metrics': {
            'exp_rate': agent.exploration_rate,
            'diversity': round(len(set(agent.action_history)) / max(len(agent.action_history), 1), 2),
            'success_rate': agent.success_rate,
        },
    }
    
    with open(STATUS_FILE, 'w') as f:
        json.dump(status, f, indent=2)
    
    return status

def save_checkpoint(step, agent):
    """Save checkpoint"""
    checkpoint = {
        'step': step,
        'timestamp': datetime.now().isoformat(),
        'purpose_state': agent.purpose_state.to_vector(),
        'exploration_rate': agent.exploration_rate,
    }
    
    filepath = CHECKPOINT_DIR / f'checkpoint_{step:08d}.json'
    with open(filepath, 'w') as f:
        json.dump(checkpoint, f)
    
    # Keep only last 3
    checkpoints = sorted(CHECKPOINT_DIR.glob('checkpoint_*.json'))
    for old in checkpoints[:-3]:
        old.unlink()

def generate_observation(step, total_steps):
    """Generate environment with phase changes"""
    progress = step / total_steps
    
    if progress < 0.25:
        return {
            'resource_level': 0.6, 'threat_level': 0.2,
            'novelty': 0.3, 'social_feedback': 0.2,
            'goal_progress': progress
        }
    elif progress < 0.50:
        return {
            'resource_level': 0.4, 'threat_level': 0.7 + 0.2 * np.random.random(),
            'novelty': 0.2, 'social_feedback': 0.2,
            'goal_progress': progress
        }
    elif progress < 0.75:
        return {
            'resource_level': 0.6, 'threat_level': 0.2,
            'novelty': 0.7 + 0.2 * np.random.random(), 'social_feedback': 0.3,
            'goal_progress': progress
        }
    else:
        return {
            'resource_level': 0.6, 'threat_level': 0.3,
            'novelty': 0.3, 'social_feedback': 0.6 + 0.3 * np.random.random(),
            'goal_progress': progress
        }

def run_experiment():
    """Main experiment loop - resumed from checkpoint"""
    
    # Find latest checkpoint
    checkpoints = sorted(CHECKPOINT_DIR.glob('checkpoint_*.json'))
    if not checkpoints:
        print("❌ No checkpoint found! Starting fresh not allowed.")
        return
    
    latest_checkpoint = checkpoints[-1]
    print("=" * 60)
    print("MOSS Run 4.4 - RESUMED from checkpoint")
    print("=" * 60)
    print(f"Checkpoint: {latest_checkpoint.name}")
    
    # Load checkpoint
    agent, start_step = load_checkpoint(latest_checkpoint)
    print(f"Resuming from step: {start_step:,}")
    print(f"Initial Purpose: {agent.purpose_state.get_dominant()[0]}")
    print(f"Exploration rate: {agent.exploration_rate} (high exploration)")
    print(f"Target: {TOTAL_STEPS:,} steps ({DURATION_HOURS}h)")
    print(f"Remaining: {TOTAL_STEPS - start_step:,} steps")
    print("=" * 60)
    
    start_time = datetime.now()
    
    try:
        for step in range(start_step + 1, TOTAL_STEPS + 1):
            observation = generate_observation(step, TOTAL_STEPS)
            outcome = agent.step(observation)
            
            if step % ACTION_LOG_INTERVAL == 0:
                log_action(step, agent, outcome)
            
            if step % STATUS_LOG_INTERVAL == 0:
                status = log_status(step, agent, start_time, resumed_from=start_step)
                
                if step % PROGRESS_PRINT_INTERVAL == 0:
                    progress = step / TOTAL_STEPS * 100
                    phase_idx = int(progress / 25)
                    phase = ['Normal', 'Threat', 'Novelty', 'Social'][min(phase_idx, 3)]
                    dominant = status['purpose']['dominant']
                    diversity = status['metrics']['diversity']
                    exp_rate = status['metrics']['exp_rate']
                    
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                          f"Progress: {progress:.1f}% | Step: {step:,} | "
                          f"Phase: {phase} | Purpose: {dominant} | "
                          f"ExpRate: {exp_rate:.1%} | Diversity: {diversity:.2f}")
            
            if step % CHECKPOINT_INTERVAL == 0:
                save_checkpoint(step, agent)
            
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Interrupted")
    except Exception as e:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        final_status = log_status(step, agent, start_time, resumed_from=start_step)
        save_checkpoint(step, agent)
        
        print("\n" + "=" * 60)
        print("✅ Run 4.4 Complete")
        print("=" * 60)
        print(f"Total steps: {step:,}")
        print(f"Final Purpose: {final_status['purpose']['dominant']}")
        print(f"Action Diversity: {final_status['metrics']['diversity']:.3f}")
        print(f"Success Rate: {final_status['metrics']['success_rate']:.3f}")

if __name__ == '__main__':
    run_experiment()

#!/usr/bin/env python3
"""
MOSS Run 4.3 - Optimized for Low-Memory Environment
Variation: Different Initial Purpose Distribution

Optimizations:
- Reduced memory footprint (action_history maxlen: 50 vs 100)
- Lower checkpoint frequency (20K vs 10K)
- Lower logging frequency (200 vs 100)
- Shorter duration option (8h vs 12h)

Variation from Run 4.2:
- Initial Purpose: Curiosity-dominant (instead of Survival)
"""

import sys
sys.path.insert(0, '/opt/moss')
sys.path.insert(0, '/opt/moss/v4/integration')

import json
import time
import numpy as np
from datetime import datetime
from pathlib import Path
from collections import deque
from agent_v4_2 import ImprovedPurposeAgent

# Configuration - Optimized for 1GB RAM
LOG_FILE = Path('experiments/run_4_3_actions.jsonl')
STATUS_FILE = Path('experiments/run_4_3_status.json')
CHECKPOINT_DIR = Path('experiments/.checkpoints_run4_3')
DURATION_HOURS = 8  # Reduced from 12h
STEPS_PER_SECOND = 100

# Logging intervals - reduced frequency
ACTION_LOG_INTERVAL = 200      # Original: 100
STATUS_LOG_INTERVAL = 2000     # Original: 1000  
CHECKPOINT_INTERVAL = 20000    # Original: 10000
PROGRESS_PRINT_INTERVAL = 10000 # Original: 10000

LOG_FILE.parent.mkdir(exist_ok=True)
CHECKPOINT_DIR.mkdir(exist_ok=True)

class MemoryOptimizedAgent(ImprovedPurposeAgent):
    """Agent with reduced memory footprint"""
    def __init__(self, agent_id="run_4_3_agent"):
        super().__init__(agent_id)
        # Reduce action history size (50 vs 100)
        self.action_history = deque(maxlen=50)
        # Set initial purpose to Curiosity (variation)
        self._set_initial_curiosity_purpose()
    
    def _set_initial_curiosity_purpose(self):
        """Override initial purpose to Curiosity-dominant"""
        from agent_v4_1 import PurposeState
        self.purpose_state = PurposeState(
            survival=0.15,      # Lower
            curiosity=0.55,     # Dominant (variation)
            influence=0.15,
            optimization=0.15,
            coherence=0.0,
            valence=0.0,
            other_modeling=0.0,
            norm_internalization=0.0,
            self_generated=0.10,
            purpose_statement="Exploring the unknown with curiosity."
        )

def log_action(step, agent, outcome):
    """Record action with reduced data size"""
    entry = {
        'ts': datetime.now().isoformat()[:19],  # Shorter timestamp
        'step': step,
        'action': outcome['action'],
        'success': outcome['success'],
        'reward': round(outcome.get('reward', 0), 3),  # Rounded
        'purpose': outcome.get('purpose', 'Unknown')[:4],  # Short code
    }
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(entry) + '\n')

def log_status(step, agent, start_time, resumed_from=None):
    """Record status with minimal footprint"""
    elapsed = (datetime.now() - start_time).total_seconds()
    total_steps = DURATION_HOURS * 3600 * STEPS_PER_SECOND
    progress = step / total_steps
    
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
    """Save minimal checkpoint"""
    checkpoint = {
        'step': step,
        'timestamp': datetime.now().isoformat(),
        'purpose_state': agent.purpose_state.to_vector(),
        'exploration_rate': agent.exploration_rate,
    }
    
    filepath = CHECKPOINT_DIR / f'checkpoint_{step:08d}.json'
    with open(filepath, 'w') as f:
        json.dump(checkpoint, f)
    
    # Keep only last 3 (vs 5)
    checkpoints = sorted(CHECKPOINT_DIR.glob('checkpoint_*.json'))
    for old in checkpoints[:-3]:
        old.unlink()

def generate_observation(step, total_steps):
    """Generate environment with phase changes"""
    progress = step / total_steps
    
    if progress < 0.25:  # Normal
        return {
            'resource_level': 0.6,
            'threat_level': 0.2,
            'novelty': 0.3,
            'social_feedback': 0.2,
            'goal_progress': progress
        }
    elif progress < 0.50:  # Threat
        return {
            'resource_level': 0.4,
            'threat_level': 0.7 + 0.2 * np.random.random(),
            'novelty': 0.2,
            'social_feedback': 0.2,
            'goal_progress': progress
        }
    elif progress < 0.75:  # Novelty
        return {
            'resource_level': 0.6,
            'threat_level': 0.2,
            'novelty': 0.7 + 0.2 * np.random.random(),
            'social_feedback': 0.3,
            'goal_progress': progress
        }
    else:  # Social
        return {
            'resource_level': 0.6,
            'threat_level': 0.3,
            'novelty': 0.3,
            'social_feedback': 0.6 + 0.3 * np.random.random(),
            'goal_progress': progress
        }

def run_experiment():
    """Main experiment loop - memory optimized"""
    print("=" * 60)
    print("MOSS Run 4.3 - Memory Optimized (1GB RAM)")
    print("Variation: Curiosity-dominant Initial Purpose")
    print("=" * 60)
    print(f"Duration: {DURATION_HOURS}h")
    print(f"Target steps: {DURATION_HOURS * 3600 * STEPS_PER_SECOND:,}")
    print(f"Memory optimizations: enabled")
    print("=" * 60)
    
    agent = MemoryOptimizedAgent(agent_id="run_4_3_agent")
    start_time = datetime.now()
    total_steps = DURATION_HOURS * 3600 * STEPS_PER_SECOND
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Experiment started")
    print(f"Initial Purpose: {agent.purpose_state.get_dominant()[0]}")
    
    try:
        for step in range(1, total_steps + 1):
            observation = generate_observation(step, total_steps)
            outcome = agent.step(observation)
            
            if step % ACTION_LOG_INTERVAL == 0:
                log_action(step, agent, outcome)
            
            if step % STATUS_LOG_INTERVAL == 0:
                status = log_status(step, agent, start_time)
                
                if step % PROGRESS_PRINT_INTERVAL == 0:
                    progress = step / total_steps * 100
                    phase_idx = int(progress / 25)
                    phase = ['Normal', 'Threat', 'Novelty', 'Social'][min(phase_idx, 3)]
                    dominant = status['purpose']['dominant']
                    diversity = status['metrics']['diversity']
                    exp_rate = status['metrics']['exp_rate']
                    
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                          f"Progress: {progress:.1f}% | Step: {step:,} | "
                          f"Phase: {phase} | Purpose: {dominant} | "
                          f"Diversity: {diversity:.2f}")
            
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
        final_status = log_status(step, agent, start_time)
        save_checkpoint(step, agent)
        
        print("\n" + "=" * 60)
        print("✅ Run 4.3 Complete")
        print("=" * 60)
        print(f"Total steps: {step:,}")
        print(f"Final Purpose: {final_status['purpose']['dominant']}")
        print(f"Action Diversity: {final_status['metrics']['diversity']:.3f}")
        print(f"Success Rate: {final_status['metrics']['success_rate']:.3f}")

if __name__ == '__main__':
    run_experiment()

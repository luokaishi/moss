#!/usr/bin/env python3
"""
MOSS Run 4.2 - Resume from Checkpoint
Continue experiment from last saved checkpoint
"""

import sys
sys.path.insert(0, '/workspace/projects/moss')
sys.path.insert(0, '/workspace/projects/moss/v4/integration')

import json
import time
import numpy as np
from datetime import datetime
from pathlib import Path
from agent_v4_2 import ImprovedPurposeAgent

# Configuration
LOG_FILE = Path('experiments/run_4_2_actions.jsonl')
STATUS_FILE = Path('experiments/run_4_2_status.json')
CHECKPOINT_DIR = Path('experiments/.checkpoints_run4_2')
DURATION_HOURS = 12
STEPS_PER_SECOND = 100
TOTAL_STEPS = DURATION_HOURS * 3600 * STEPS_PER_SECOND

def load_latest_checkpoint():
    """Load the most recent checkpoint"""
    checkpoints = sorted(CHECKPOINT_DIR.glob('checkpoint_*.json'))
    if not checkpoints:
        return None
    
    latest = checkpoints[-1]
    with open(latest, 'r') as f:
        checkpoint = json.load(f)
    
    print(f"Loaded checkpoint: {latest.name}")
    print(f"  Step: {checkpoint['step']:,}")
    print(f"  Timestamp: {checkpoint['timestamp']}")
    return checkpoint

def restore_agent_from_checkpoint(agent, checkpoint):
    """Restore agent state from checkpoint"""
    from agent_v4_1 import PurposeState
    
    # Restore purpose state from vector
    pv = checkpoint['purpose_state']
    agent.purpose_state = PurposeState(
        survival=pv[0],
        curiosity=pv[1],
        influence=pv[2],
        optimization=pv[3],
        coherence=pv[4],
        valence=pv[5],
        other_modeling=pv[6],
        norm_internalization=pv[7],
        self_generated=pv[8]
    )
    
    # Restore exploration rate
    agent.exploration_rate = checkpoint['exploration_rate']
    
    # Restore stats
    agent.stats = checkpoint['stats']
    
    print(f"Agent state restored from Step {checkpoint['step']:,}")
    return checkpoint['step']

def log_action(step, agent, outcome):
    """Record action with full state"""
    entry = {
        'timestamp': datetime.now().isoformat(),
        'step': step,
        'action': outcome['action'],
        'success': outcome['success'],
        'reward': outcome.get('reward', 0),
        'purpose': outcome.get('purpose', 'Unknown'),
        'is_exploration': outcome.get('is_exploration', False),
        'purpose_vector': agent.purpose_state.to_vector(),
        'exploration_rate': agent.exploration_rate,
        'unique_actions': len(set(agent.action_history)) if agent.action_history else 0
    }
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(entry) + '\n')

def log_status(step, agent, start_time, resumed_from):
    """Record detailed status"""
    elapsed = (datetime.now() - start_time).total_seconds()
    progress = step / TOTAL_STEPS
    
    status = {
        'timestamp': datetime.now().isoformat(),
        'step': step,
        'resumed_from': resumed_from,
        'progress': progress,
        'elapsed_hours': elapsed / 3600,
        'purpose': {
            'vector': agent.purpose_state.to_vector(),
            'dominant': agent.purpose_state.get_dominant()[0],
            'statement': agent.purpose_state.purpose_statement
        },
        'metrics': {
            'exploration_rate': agent.exploration_rate,
            'action_diversity': len(set(agent.action_history)) / max(len(agent.action_history), 1),
            'success_rate': agent.success_rate,
            'unique_actions': len(set(agent.action_history))
        },
        'goals': {
            'total': len(agent.goal_manager.goals),
            'active': len(agent.goal_manager.get_active_goals())
        },
        'stats': agent.stats
    }
    
    with open(STATUS_FILE, 'w') as f:
        json.dump(status, f, indent=2)
    
    return status

def save_checkpoint(step, agent):
    """Save agent state"""
    checkpoint = {
        'step': step,
        'timestamp': datetime.now().isoformat(),
        'purpose_state': agent.purpose_state.to_vector(),
        'exploration_rate': agent.exploration_rate,
        'stats': agent.stats
    }
    
    filepath = CHECKPOINT_DIR / f'checkpoint_{step:08d}.json'
    with open(filepath, 'w') as f:
        json.dump(checkpoint, f)
    
    # Keep only last 5
    checkpoints = sorted(CHECKPOINT_DIR.glob('checkpoint_*.json'))
    for old in checkpoints[:-5]:
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
    """Main experiment loop - resume from checkpoint"""
    print("=" * 70)
    print("MOSS Run 4.2 - Resume from Checkpoint")
    print("=" * 70)
    
    # Load checkpoint
    checkpoint = load_latest_checkpoint()
    if checkpoint is None:
        print("No checkpoint found. Please run run_4_2.py first.")
        return
    
    resumed_from = checkpoint['step']
    remaining_steps = TOTAL_STEPS - resumed_from
    
    print(f"Target steps: {TOTAL_STEPS:,}")
    print(f"Resuming from: Step {resumed_from:,}")
    print(f"Remaining: {remaining_steps:,} steps")
    print(f"Phases: Normal(0-25%) → Threat(25-50%) → Novelty(50-75%) → Social(75-100%)")
    print("=" * 70)
    
    # Create and restore agent
    agent = ImprovedPurposeAgent(agent_id="run_4_2_agent")
    restore_agent_from_checkpoint(agent, checkpoint)
    
    start_time = datetime.now()
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Experiment resumed")
    
    try:
        for step in range(resumed_from + 1, TOTAL_STEPS + 1):
            observation = generate_observation(step, TOTAL_STEPS)
            outcome = agent.step(observation)
            
            if step % 100 == 0:
                log_action(step, agent, outcome)
            
            if step % 1000 == 0:
                status = log_status(step, agent, start_time, resumed_from)
                
                if step % 10000 == 0:
                    progress = step / TOTAL_STEPS * 100
                    phase = ['Normal', 'Threat', 'Novelty', 'Social'][int(progress / 25)]
                    dominant = status['purpose']['dominant']
                    diversity = status['metrics']['action_diversity']
                    exp_rate = status['metrics']['exploration_rate']
                    
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                          f"Progress: {progress:.1f}% | Step: {step:,} | "
                          f"Phase: {phase} | Purpose: {dominant} | "
                          f"Diversity: {diversity:.2f} | ExpRate: {exp_rate:.3f}")
            
            if step % 10000 == 0:
                save_checkpoint(step, agent)
            
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Interrupted")
    except Exception as e:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        final_status = log_status(step, agent, start_time, resumed_from)
        save_checkpoint(step, agent)
        
        print("\n" + "=" * 70)
        print("✅ Run 4.2 Complete")
        print("=" * 70)
        print(f"Total steps: {step:,}")
        print(f"Resumed from: {resumed_from:,}")
        print(f"Steps this run: {step - resumed_from:,}")
        print(f"Final Purpose: {final_status['purpose']['dominant']}")
        print(f"Action Diversity: {final_status['metrics']['action_diversity']:.3f}")
        print(f"Success Rate: {final_status['metrics']['success_rate']:.3f}")
        print(f"Unique Actions: {final_status['metrics']['unique_actions']}")

if __name__ == '__main__':
    run_experiment()

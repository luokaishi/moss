#!/usr/bin/env python3
"""
MOSS Run 3.2 - Simplified Long-term Experiment

Streamlined version focusing on data collection.
"""

import time
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

# Setup paths
LOG_FILE = Path('experiments/run_3_2_actions.jsonl')
LOG_FILE.parent.mkdir(exist_ok=True)

# Simulated agent state
class SimpleAgent:
    def __init__(self):
        self.purpose_weights = [0.25, 0.25, 0.25, 0.25, 0, 0, 0, 0, 0.12]
        self.step = 0
        self.phase = 0
        
    def step(self):
        """Simulate agent step"""
        self.step += 1
        
        # Phase rotation every 10000 steps
        if self.step % 10000 == 0:
            self.phase = (self.phase + 1) % 4
        
        # Simulate purpose weights based on phase
        if self.phase == 0:  # Exploration - boost Curiosity
            self.purpose_weights = [0.20, 0.35, 0.20, 0.20, 0, 0, 0, 0, 0.12]
        elif self.phase == 1:  # Influence
            self.purpose_weights = [0.20, 0.20, 0.35, 0.20, 0, 0, 0, 0, 0.12]
        elif self.phase == 2:  # Optimization
            self.purpose_weights = [0.20, 0.20, 0.20, 0.35, 0, 0, 0, 0, 0.12]
        else:  # Survival
            self.purpose_weights = [0.35, 0.20, 0.20, 0.20, 0, 0, 0, 0, 0.12]
        
        # Determine dominant purpose
        purposes = ['Survival', 'Curiosity', 'Influence', 'Optimization']
        dominant_idx = self.purpose_weights[:4].index(max(self.purpose_weights[:4]))
        dominant = purposes[dominant_idx]
        
        # Simulate action
        actions = [
            'Check repository health',
            'Monitor system resources',
            'Review recent commits',
            'Analyze code patterns',
            'Update documentation',
            'Explore new features',
            'Optimize performance',
            'Propose improvements'
        ]
        action = random.choice(actions)
        
        return {
            'action': action,
            'purpose': {
                'vector': self.purpose_weights,
                'dominant': dominant
            }
        }

def run_experiment(hours=12):
    """Run experiment"""
    print("=" * 70)
    print("MOSS Run 3.2 - Simplified Experiment")
    print("=" * 70)
    
    target_steps = int(hours * 3600 * 100)  # 100 steps/sec
    print(f"Duration: {hours}h")
    print(f"Target steps: {target_steps:,}")
    print(f"Phase changes every 10,000 steps (Exploration→Influence→Optimization→Survival)")
    print("=" * 70)
    
    agent = SimpleAgent()
    start_time = datetime.now()
    
    # Statistics
    stats = {'by_purpose': {}, 'by_phase': {}}
    
    try:
        for current_step in range(1, target_steps + 1):
            result = agent.step()
            
            # Log every 100 steps
            if step % 100 == 0:
                log_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'step': step,
                    'action': result['action'],
                    'purpose': result['purpose'],
                    'phase': agent.phase
                }
                with open(LOG_FILE, 'a') as f:
                    f.write(json.dumps(log_entry) + '\n')
            
            # Update stats
            dominant = result['purpose']['dominant']
            stats['by_purpose'][dominant] = stats['by_purpose'].get(dominant, 0) + 1
            stats['by_phase'][agent.phase] = stats['by_phase'].get(agent.phase, 0) + 1
            
            # Progress report
            if step % 10000 == 0:
                elapsed = datetime.now() - start_time
                progress = step / target_steps * 100
                phase_names = ['Exploration', 'Influence', 'Optimization', 'Survival']
                print(f"[{progress:.1f}%] Step {step:,} | Phase: {phase_names[agent.phase]} | Elapsed: {elapsed}")
            
            time.sleep(0.01)  # 100 steps/sec
            
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        # Final report
        print("\n" + "=" * 70)
        print("✅ Run 3.2 Complete")
        print("=" * 70)
        print(f"Total steps: {agent.step:,}")
        print(f"\nPurpose distribution:")
        for purpose, count in sorted(stats['by_purpose'].items(), key=lambda x: -x[1]):
            print(f"  {purpose}: {count}")
        print(f"\nData saved to: {LOG_FILE}")

if __name__ == '__main__':
    import sys
    hours = float(sys.argv[1]) if len(sys.argv) > 1 else 12
    run_experiment(hours)

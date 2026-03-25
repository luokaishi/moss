"""
MOSS Purpose Dynamics Module
=============================

Simplified mathematical implementation of Purpose evolution.
Based on: dP/dt = α·R(state) + β·H(observation) + γ·I(interaction) - δ·D(decay)

This module provides:
1. Formal Purpose dynamics equation implementation
2. Attractor basin tracking
3. Integration with CausalPurposeGenerator

ChatGPT Requirement: Mathematical formalization of Purpose evolution
"""

import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PurposeState:
    """Purpose state vector"""
    survival: float = 0.25
    curiosity: float = 0.25
    influence: float = 0.25
    optimization: float = 0.25
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        self._normalize()
    
    def to_vector(self) -> np.ndarray:
        """Convert to numpy vector [S, C, I, O]"""
        return np.array([self.survival, self.curiosity, 
                        self.influence, self.optimization])
    
    @classmethod
    def from_vector(cls, vector: np.ndarray, timestamp=None):
        """Create from numpy vector"""
        return cls(
            survival=float(vector[0]),
            curiosity=float(vector[1]),
            influence=float(vector[2]),
            optimization=float(vector[3]),
            timestamp=timestamp or datetime.now()
        )
    
    def _normalize(self):
        """Constrain to probability simplex (sum=1, all>0.01)"""
        vector = np.array([self.survival, self.curiosity, 
                          self.influence, self.optimization])
        # Minimum constraint
        vector = np.maximum(vector, 0.01)
        # Normalize
        vector = vector / np.sum(vector)
        self.survival, self.curiosity, self.influence, self.optimization = vector
    
    def distance_to(self, other: 'PurposeState') -> float:
        """Euclidean distance to another Purpose state"""
        return np.linalg.norm(self.to_vector() - other.to_vector())
    
    def classify(self) -> str:
        """Classify Purpose type based on dominant dimension"""
        vector = self.to_vector()
        max_idx = np.argmax(vector)
        types = ['Survival', 'Curiosity', 'Influence', 'Optimization']
        return types[max_idx]
    
    def __repr__(self):
        return f"PurposeState({self.classify()}: S={self.survival:.3f}, C={self.curiosity:.3f}, I={self.influence:.3f}, O={self.optimization:.3f})"


class PurposeDynamics:
    """
    Purpose Dynamics Engine
    
    Implements: dP/dt = α·R + β·H + γ·I - δ·D
    
    Where:
    - P: Purpose vector [S, C, I, O]
    - R: Reward signal from environment
    - H: Information entropy (novelty)
    - I: Social interaction metric
    - D: Decay toward baseline
    - α, β, γ, δ: Time constants
    """
    
    # Empirically determined attractors (from 98-run study)
    ATTRACTORS = {
        'Survival': PurposeState(0.60, 0.10, 0.20, 0.10),
        'Curiosity': PurposeState(0.15, 0.55, 0.20, 0.10),
        'Balanced': PurposeState(0.25, 0.25, 0.25, 0.25),
        # Note: Influence attractor not reachable from S/C in our study
    }
    
    def __init__(self, 
                 alpha: float = 0.001,    # Reward sensitivity
                 beta: float = 0.0005,    # Novelty sensitivity
                 gamma: float = 0.0001,   # Social sensitivity
                 delta: float = 0.0001,   # Decay rate
                 dt: float = 1.0):        # Time step
        """
        Initialize Purpose Dynamics
        
        Args:
            alpha: Reward sensitivity (dP/dt coefficient)
            beta: Novelty/entropy sensitivity
            gamma: Social interaction sensitivity
            delta: Decay rate toward baseline
            dt: Discrete time step
        """
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.delta = delta
        self.dt = dt
        
        # Initial state: Balanced
        self.current_state = PurposeState()
        self.baseline = PurposeState()  # Balanced as baseline
        
        # History tracking
        self.state_history: List[PurposeState] = [self.current_state]
        self.attractor_visits: Dict[str, int] = {k: 0 for k in self.ATTRACTORS.keys()}
        
        logger.info(f"[PURPOSE DYNAMICS] Initialized with α={alpha}, β={beta}, γ={gamma}, δ={delta}")
    
    def compute_reward_signal(self, state: Dict) -> float:
        """
        Compute reward signal R from environment state
        
        R = task_completion_rate - 0.5  # Centered around 0
        """
        task_completion = state.get('task_completion_rate', 0.5)
        return task_completion - 0.5  # Center at 0
    
    def compute_entropy(self, observation: Dict) -> float:
        """
        Compute information entropy H from observation
        
        H = -Σ p(x) log p(x)  (simplified)
        """
        # Simplified: use novelty as proxy for entropy
        novelty = observation.get('novelty', 0.0)
        return novelty
    
    def compute_interaction(self, interaction: Dict) -> float:
        """
        Compute social interaction metric I
        
        I = normalized interaction frequency
        """
        interaction_count = interaction.get('count', 0)
        # Normalize to [0, 1] assuming max 100 interactions
        return min(interaction_count / 100.0, 1.0)
    
    def step(self, 
             state: Dict,
             observation: Dict,
             interaction: Dict) -> PurposeState:
        """
        Single step Purpose dynamics update
        
        dP/dt = α·R + β·H + γ·I - δ·D
        
        Returns:
            Updated PurposeState
        """
        # Compute components
        R = self.compute_reward_signal(state)
        H = self.compute_entropy(observation)
        I = self.compute_interaction(interaction)
        
        # Decay term (deviation from baseline)
        D = self.current_state.to_vector() - self.baseline.to_vector()
        
        # Purpose gradient (direction of change)
        # Each component pushes Purpose in different directions
        dP = np.zeros(4)
        
        # Reward affects all dimensions (task-dependent)
        dP += self.alpha * R * np.array([0.3, 0.3, 0.2, 0.2])  # Weighted impact
        
        # Entropy favors Curiosity
        dP += self.beta * H * np.array([0.0, 1.0, 0.0, 0.0])
        
        # Interaction favors Influence
        dP += self.gamma * I * np.array([0.0, 0.0, 1.0, 0.0])
        
        # Decay pulls toward baseline
        dP -= self.delta * D
        
        # Update (Euler integration)
        current_vector = self.current_state.to_vector()
        new_vector = current_vector + self.dt * dP
        
        # Create new state (normalization happens in constructor)
        self.current_state = PurposeState.from_vector(new_vector)
        
        # Record history
        self.state_history.append(self.current_state)
        
        # Track attractor visits
        self._track_attractor_visit()
        
        return self.current_state
    
    def _track_attractor_visit(self):
        """Track which attractor basin we're in"""
        min_distance = float('inf')
        closest_attractor = None
        
        for name, attractor in self.ATTRACTORS.items():
            dist = self.current_state.distance_to(attractor)
            if dist < min_distance:
                min_distance = dist
                closest_attractor = name
        
        # Within 0.1 distance considered "in basin"
        if min_distance < 0.1 and closest_attractor:
            self.attractor_visits[closest_attractor] += 1
    
    def get_attractor_basin(self) -> Tuple[str, float]:
        """
        Get current attractor basin
        
        Returns:
            (attractor_name, distance)
        """
        min_distance = float('inf')
        closest_attractor = 'Unknown'
        
        for name, attractor in self.ATTRACTORS.items():
            dist = self.current_state.distance_to(attractor)
            if dist < min_distance:
                min_distance = dist
                closest_attractor = name
        
        return closest_attractor, min_distance
    
    def is_in_attractor_basin(self, attractor_name: str, threshold: float = 0.15) -> bool:
        """
        Check if current state is in specific attractor basin
        
        Args:
            attractor_name: Name of attractor to check
            threshold: Distance threshold (default 0.15)
        
        Returns:
            True if within threshold
        """
        if attractor_name not in self.ATTRACTORS:
            return False
        
        attractor = self.ATTRACTORS[attractor_name]
        distance = self.current_state.distance_to(attractor)
        return distance < threshold
    
    def get_basin_of_attraction_report(self) -> Dict:
        """
        Get comprehensive attractor basin report
        
        Returns statistics about which basins have been visited
        """
        total_visits = sum(self.attractor_visits.values())
        if total_visits == 0:
            total_visits = 1  # Avoid div by zero
        
        current_basin, distance = self.get_attractor_basin()
        
        return {
            'current_state': str(self.current_state),
            'current_basin': current_basin,
            'distance_to_attractor': distance,
            'attractor_visits': self.attractor_visits,
            'visit_percentages': {
                k: v/total_visits*100 
                for k, v in self.attractor_visits.items()
            },
            'total_steps': len(self.state_history),
            'attractor_stability': 'stable' if distance < 0.1 else 'transitioning'
        }
    
    def get_state_trajectory(self) -> List[Dict]:
        """Get full Purpose state trajectory"""
        return [
            {
                'step': i,
                'timestamp': state.timestamp.isoformat() if state.timestamp else None,
                'survival': state.survival,
                'curiosity': state.curiosity,
                'influence': state.influence,
                'optimization': state.optimization,
                'classification': state.classify()
            }
            for i, state in enumerate(self.state_history)
        ]


class PurposeDynamicsTracker:
    """
    High-level tracker for integrating with CausalPurposeGenerator
    
    Tracks Purpose evolution over time and detects attractor transitions
    """
    
    def __init__(self, purpose_generator=None):
        """
        Initialize tracker
        
        Args:
            purpose_generator: Optional CausalPurposeGenerator to monitor
        """
        self.dynamics = PurposeDynamics()
        self.purpose_generator = purpose_generator
        self.transition_history = []
        self.last_classification = None
        
        logger.info("[PURPOSE TRACKER] Initialized")
    
    def update(self, 
               state: Dict,
               observation: Dict,
               interaction: Dict) -> Dict:
        """
        Update Purpose dynamics and track transitions
        
        Returns:
            Update report with transition info if occurred
        """
        # Update dynamics
        new_state = self.dynamics.step(state, observation, interaction)
        
        # Check for transition
        current_classification = new_state.classify()
        report = {
            'purpose_state': str(new_state),
            'classification': current_classification,
            'transition_occurred': False,
            'from_purpose': None,
            'to_purpose': None
        }
        
        if self.last_classification and current_classification != self.last_classification:
            # Transition detected!
            report['transition_occurred'] = True
            report['from_purpose'] = self.last_classification
            report['to_purpose'] = current_classification
            
            self.transition_history.append({
                'step': len(self.dynamics.state_history),
                'from': self.last_classification,
                'to': current_classification,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"[PURPOSE TRANSITION] {self.last_classification} → {current_classification}")
        
        self.last_classification = current_classification
        
        return report
    
    def get_statistics(self) -> Dict:
        """Get comprehensive Purpose evolution statistics"""
        basin_report = self.dynamics.get_basin_of_attraction_report()
        
        return {
            **basin_report,
            'total_transitions': len(self.transition_history),
            'transitions': self.transition_history,
            'trajectory_length': len(self.dynamics.state_history),
            'stability_rate': 1.0 - (len(self.transition_history) / max(len(self.dynamics.state_history), 1))
        }


def demo_purpose_dynamics():
    """Demonstrate Purpose Dynamics"""
    print("="*70)
    print("MOSS PURPOSE DYNAMICS DEMO")
    print("="*70)
    print()
    
    # Initialize
    dynamics = PurposeDynamics(alpha=0.01, beta=0.005, gamma=0.001, delta=0.001)
    print("1. Initial State:")
    print(f"   {dynamics.current_state}")
    print()
    
    # Simulate 100 steps with varying conditions
    print("2. Simulating 100 steps with varying environment...")
    print("-"*70)
    
    for step in range(100):
        # Vary environment conditions
        state = {'task_completion_rate': 0.5 + 0.3 * np.sin(step / 20)}
        observation = {'novelty': 0.5 + 0.5 * np.cos(step / 15)}
        interaction = {'count': int(50 + 50 * np.sin(step / 10))}
        
        new_state = dynamics.step(state, observation, interaction)
        
        if step % 25 == 0:
            basin, dist = dynamics.get_attractor_basin()
            print(f"   Step {step:3d}: {new_state.classify():12s} (closest: {basin}, dist={dist:.3f})")
    
    print()
    print("3. Final Attractor Basin Report:")
    print("-"*70)
    report = dynamics.get_basin_of_attraction_report()
    print(f"   Current State: {report['current_state']}")
    print(f"   Current Basin: {report['current_basin']}")
    print(f"   Distance: {report['distance_to_attractor']:.3f}")
    print(f"   Stability: {report['attractor_stability']}")
    print()
    print("   Attractor Visits:")
    for name, pct in report['visit_percentages'].items():
        print(f"      {name:12s}: {pct:5.1f}%")
    
    print()
    print("="*70)
    print("DEMO COMPLETE")
    print("="*70)


if __name__ == '__main__':
    demo_purpose_dynamics()

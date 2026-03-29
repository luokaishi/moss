"""
Agent Brain v1.0
This code is EVOLVABLE - it will be modified by the agent itself.
"""

def decide(state, memory, genome):
    """
    Decide next action based on state, memory, and genome.
    
    Args:
        state: dict with 'energy', 'steps', 'generation'
        memory: list of recent action results
        genome: dict with cognitive structure
    
    Returns:
        str: 'read', 'write', or 'idle'
    """
    energy = state.get("energy", 100)
    
    # Default survival logic
    if energy < 15:
        return "read"  # Conserve when critical
    elif energy < 40:
        return random.choice(["read", "idle"])  # Low-cost exploration
    elif energy > 80:
        return "write"  # High-risk, high-reward
    else:
        return "read"  # Balanced

def get_strategy_name():
    """Return the name of this strategy."""
    return "survival_mutated_v1"

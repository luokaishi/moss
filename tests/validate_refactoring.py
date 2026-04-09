"""Quick validation test for MOSS core modules after refactoring."""
import sys, os
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8')

import numpy as np

print('='*60)
print('MOSS Core Modules Validation')
print('='*60)

# Test all imports
from moss.core import (
    UnifiedMOSSAgent, MOSSConfig,
    CausalPurposeGenerator, CausalPurposeConfig,
    GradientSafetyGuard, SafetyLevel,
    MOSSMultiObjectiveFramework,
    StateDecisionModel,
    PurposeDynamics, PurposeDynamicsTracker,
    CoherenceModule, ValenceModule, OtherModelingModule, NormInternalizationModule,
)
print('[OK] All core imports successful')

import moss
print(f'[OK] moss version: {moss.__version__}')

# Test 1: Safety Guard
print('\n--- GradientSafetyGuard ---')
guard = GradientSafetyGuard()
level = guard.check_metrics({'cpu_percent': 50, 'memory_percent': 40, 'error_rate': 0.01})
assert level == SafetyLevel.NORMAL, f"Expected NORMAL, got {level}"
print(f'  Normal: {level.name} OK')

level = guard.check_metrics({'cpu_percent': 75, 'memory_percent': 65, 'error_rate': 0.06})
assert level == SafetyLevel.WARNING, f"Expected WARNING, got {level}"
print(f'  Warning: {level.name} OK')

level = guard.check_metrics({'cpu_percent': 85, 'memory_percent': 75, 'error_rate': 0.12})
assert level == SafetyLevel.THROTTLING, f"Expected THROTTLING, got {level}"
print(f'  Throttling: {level.name} OK')

# Test 2: Math Framework
print('\n--- Mathematical Framework ---')
fw = MOSSMultiObjectiveFramework()
state = np.array([0.7, 0.02, 100])
weights = np.array([0.2, 0.4, 0.3, 0.1])
objectives = [lambda s,a: s[0]*(1-s[1]), lambda s,a: 0.6, lambda s,a: 0.4, lambda s,a: 0.5]
loss = fw.unified_loss_function(state, np.array([0.5, 0.3, 0.2]), weights, objectives)
print(f'  Unified loss: {loss:.4f}')
assert loss > 0

new_w = fw.dynamic_weight_update(weights, state)
assert np.allclose(new_w.sum(), 1.0, atol=0.01)
print(f'  Weight update: {new_w.round(3)}')

pop = [np.array([0.9, 0.1]), np.array([0.8, 0.2]), np.array([0.7, 0.3])]
front = fw.find_pareto_front(pop)
print(f'  Pareto front: {len(front)}/{len(pop)}')

# Test 3: Causal Purpose
print('\n--- Causal Purpose ---')
gen = CausalPurposeGenerator(agent_id='test_evo', config=CausalPurposeConfig(evolution_interval=10))
for step in range(15):
    gen.step({'phase': 'normal'}, step)
    gen.record_feedback({'success': True, 'reward': 0.5, 'expected_reward': 0.3, 'is_novel': False})
assert len(gen.purpose_state.evolution_history) >= 1
vec = gen.get_purpose_vector_9d()
assert vec.shape == (9,)
print(f'  Evolutions: {len(gen.purpose_state.evolution_history)}')
print(f'  9D vector: sum={vec[:8].sum():.4f}, strength={vec[8]:.4f}')

# Test 4: Purpose Dynamics
print('\n--- Purpose Dynamics ---')
dynamics = PurposeDynamics(alpha=0.01, beta=0.005, gamma=0.001, delta=0.001)
for step in range(100):
    dynamics.step(
        {'task_completion_rate': 0.5 + 0.3*np.sin(step/20)},
        {'novelty': 0.5}, {'count': 50}
    )
basin, dist = dynamics.get_attractor_basin()
report = dynamics.get_basin_of_attraction_report()
print(f'  Basin: {basin} (dist={dist:.3f})')
print(f'  Steps: {report["total_steps"]}')

# Test 5: Objectives
print('\n--- Objectives ---')
from moss.core.objectives import ObjectiveManager
mgr = ObjectiveManager()
rewards = mgr.calculate_all_rewards({'system_health': 0.8, 'resources_available': 0.9}, 'test')
print(f'  S={rewards["survival"]:.2f} C={rewards["curiosity"]:.2f} I={rewards["influence"]:.2f} O={rewards["optimization"]:.2f}')

# Test 6: Conflict Resolver
print('\n--- Conflict Resolver ---')
from moss.core.conflict_resolver_enhanced import ConflictResolver, ObjectiveDemand, PriorityLevel
resolver = ConflictResolver()
demands = [
    ObjectiveDemand('survival', PriorityLevel.CRITICAL, {'cpu': 0.3}, 'conserve', 0.8),
    ObjectiveDemand('curiosity', PriorityLevel.MEDIUM, {'cpu': 0.4}, 'explore', 0.6),
]
conflicts = resolver.detect_conflicts({'resource_quota': 0.3}, demands)
allocations = resolver.resolve_conflicts(conflicts, demands)
assert len(conflicts) > 0
assert allocations['survival'] == 1.0  # CRITICAL priority
print(f'  Conflicts: {len(conflicts)}, survival allocation: {allocations["survival"]}')

# Test 7: Self Optimization
print('\n--- Self Optimization ---')
from moss.core.self_optimization_v2 import SelfOptimizationModule, OptimizationScope
opt = SelfOptimizationModule()
params = {'weights': {'survival': 0.6, 'curiosity': 0.1, 'influence': 0.2, 'optimization': 0.1}}
result = opt.execute_optimization(OptimizationScope.WEIGHT_TUNING, params)
total = sum(result['weights'].values())
assert abs(total - 1.0) < 0.01
print(f'  Weight sum after tuning: {total:.4f}')

# Test 8: State Decision
print('\n--- State Decision Model ---')
model = StateDecisionModel()
crisis_metrics = {
    'resource_quota': 0.12, 'resource_usage': 0.88, 'error_rate': 0.12,
    'system_uptime': 5, 'api_call_success_rate': 0.65, 'knowledge_growth_rate': 0.0
}
state, details = model.determine_state(crisis_metrics)
print(f'  Crisis metrics -> state: {state.value}')
assert state.value in ['crisis', 'concerned']

growth_metrics = {
    'resource_quota': 0.90, 'resource_usage': 0.25, 'error_rate': 0.005,
    'system_uptime': 600, 'api_call_success_rate': 0.99, 'knowledge_growth_rate': 0.15
}
state, details = model.determine_state(growth_metrics)
print(f'  Growth metrics -> state: {state.value}')
assert state.value in ['growth', 'normal']

print('\n' + '='*60)
print('ALL TESTS PASSED!')
print('='*60)

"""诊断SME变异和沙箱问题"""
import sys
sys.path.insert(0, '.')
from moss.core.self_modification_engine import ASTMutator, CodeSandbox
from pathlib import Path

src = Path('moss/core/unified_agent.py').read_text(encoding='utf-8')
mutator = ASTMutator(intensity=0.35)
target_funcs = ['select_action', '_apply_state_weights', '_random_action', '_update_state']

print("=== 变异类型测试 ===")
mut_types = [
    'constant_tweak', 'condition_flip', 'weight_shift', 'action_insert',
    'threshold_mutate', 'epsilon_tune', 'weight_hardcode', 'action_shuffle', 'branch_inject'
]
for mt in mut_types:
    mutated, applied = mutator.mutate(src, target_funcs, mutation_type=mt)
    changed = mutated != src
    print(f"  {mt:<25} -> applied={applied}, code_changed={changed}")

print()
print("=== 沙箱测试（action_insert）===")
mutated, applied = mutator.mutate(src, target_funcs, mutation_type='action_insert')
if applied != 'no_op':
    sb = CodeSandbox('.', timeout=20)
    r = sb.validate(mutated, 'moss/core/unified_agent.py')
    print(f"  passed={r['passed']}")
    print(f"  syntax_ok={r['syntax_ok']}")
    print(f"  import_ok={r['import_ok']}")
    print(f"  tests_passed={r['tests_passed']}/{r['tests_total']}")
    print(f"  error={r.get('error', None)}")
else:
    print("  action_insert returned no_op")

print()
print("=== 沙箱测试（weight_hardcode）===")
mutated2, applied2 = mutator.mutate(src, target_funcs, mutation_type='weight_hardcode')
if applied2 != 'no_op':
    sb = CodeSandbox('.', timeout=20)
    r2 = sb.validate(mutated2, 'moss/core/unified_agent.py')
    print(f"  passed={r2['passed']}")
    print(f"  syntax_ok={r2['syntax_ok']}")
    print(f"  import_ok={r2['import_ok']}")
    print(f"  tests_passed={r2['tests_passed']}/{r2['tests_total']}")
    print(f"  error={r2.get('error', None)}")
else:
    print("  weight_hardcode returned no_op")

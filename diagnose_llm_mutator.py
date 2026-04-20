#!/usr/bin/env python3
"""诊断 LLM Mutator 预验证失败原因"""

import sys
sys.path.insert(0, '/workspace/moss')

import warnings
warnings.filterwarnings('ignore')
import logging
logging.basicConfig(level=logging.DEBUG, format='[%(name)s] %(message)s')

from moss.core.llm_backend import create_llm_backend, LLMConfig
from moss.core.llm_mutator import LLMMutator

# 创建 LLM 后端（1.5B 模型）
config = LLMConfig(
    provider="local",
    model="qwen2.5-coder-1.5b",
    max_tokens=2048,
    temperature=0.3,
)
backend = create_llm_backend(config)
mutator = LLMMutator(backend)

# 读取目标源码
with open('/workspace/moss/moss/core/unified_agent.py', 'r') as f:
    source = f.read()

target_functions = [
    '_choose_action_weights',
    '_select_action', 
    '_update_beliefs',
    '_calculate_fitness',
    '_adapt_parameters',
]

immutable_functions = [
    '__init__',
    'observe',
    'act',
    'get_fitness',
]

print("="*70)
print("LLM Mutator 诊断测试")
print("="*70)
print(f"Source length: {len(source)} chars")
print(f"Target functions: {target_functions}")
print(f"Immutable functions: {immutable_functions}")
print()

# 运行一次变异
print("Calling LLMMutator.mutate()...")
mutated, result = mutator.mutate(
    source=source,
    target_functions=target_functions,
    immutable_functions=immutable_functions,
    mutation_strategy="parameter_tune",
)

print(f"\nResult:")
print(f"  mutation_type: {result.mutation_type}")
print(f"  mutation_strategy: {result.mutation_strategy}")
print(f"  target_function: {result.target_function}")
print(f"  description: {result.change_description}")
print(f"  confidence: {result.confidence}")
print(f"  validation_passed: {result.validation_passed}")

if result.mutation_type == "llm_no_op":
    print(f"\n❌ LLM produced no_op!")
    print(f"  Reason: {result.change_description}")
else:
    print(f"\n✅ LLM produced valid mutation!")
    print(f"  Original length: {len(source)}")
    print(f"  Mutated length: {len(mutated)}")

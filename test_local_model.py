#!/usr/bin/env python3
"""
测试本地模型部署

首次运行会下载模型到 ~/.cache/huggingface/
- Qwen2.5-Coder-1.5B: ~3GB, 适合快速测试
- Qwen2.5-Coder-7B: ~15GB, 生产推荐
"""

import os
import sys

# 添加 moss 到路径
sys.path.insert(0, '/workspace/moss')

from moss.core.local_llm_backend import create_local_backend_for_moss
from moss.core.llm_mutator import LLMMutator
import numpy as np

print("=" * 60)
print("MOSS Local LLM Deployment Test")
print("=" * 60)

# 使用 1.5B 模型快速测试
PRESET = "qwen2.5-coder-1.5b"
print(f"\n[1/4] Loading model: {PRESET}")
print("      This will download ~3GB on first run...")

try:
    backend = create_local_backend_for_moss(PRESET)
    print(f"✅ Model wrapper created")
    print(f"   Info: {backend.local.get_model_info()}")
except Exception as e:
    print(f"❌ Failed to create backend: {e}")
    sys.exit(1)

print(f"\n[2/4] Creating LLMMutator...")
mutator = LLMMutator(backend)
print("✅ LLMMutator ready")

# 测试源码
sample_code = '''import numpy as np

class SimpleAgent:
    def __init__(self):
        self.weights = np.array([0.25, 0.25, 0.25, 0.25])
        self.threshold = 0.5

    def select_action(self, observation):
        if np.random.random() < self.threshold:
            return "explore"
        return "exploit"
'''

print(f"\n[3/4] Running mutation...")
print("      This may take 30-120 seconds depending on CPU...")

result_source, result_info = mutator.mutate(
    source=sample_code,
    target_functions=['select_action'],
    purpose_vector=np.array([0.3, 0.4, 0.2, 0.1]),
    mutation_strategy='parameter_tune',
)

print(f"\n[4/4] Result:")
print(f"   Mutation type: {result_info.mutation_type}")
print(f"   Strategy: {result_info.mutation_strategy}")
print(f"   Target: {result_info.target_function}")
print(f"   Valid: {result_info.validation_passed}")
print(f"   Desc: {result_info.change_description[:80] if result_info.change_description else 'N/A'}")

if result_info.validation_passed:
    print(f"\n✅ SUCCESS! Local model is working.")
    print(f"   You can now use this for MOSS evolution.")
else:
    print(f"\n⚠️  Mutation not validated, but model is responding.")

print("\n" + "=" * 60)
print("Next steps:")
print("  1. For production: switch to 'qwen2.5-coder-7b'")
print("  2. Run: SMEConfig(enable_llm_mutation=True, llm_provider='local')")
print("=" * 60)

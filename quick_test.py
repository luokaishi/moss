#!/usr/bin/env python3
"""快速验证本地模型"""
import sys
sys.path.insert(0, '/workspace/moss')

import warnings
warnings.filterwarnings('ignore')

print("Loading model (cached)...")
from moss.core.local_llm_backend import create_local_backend_for_moss

backend = create_local_backend_for_moss("qwen2.5-coder-1.5b")

print("\nTesting simple completion...")
result = backend.complete(
    system_prompt="You are a code assistant.",
    user_prompt="Write a Python function to add two numbers."
)

print(f"\nGenerated {len(result)} characters")
print("First 200 chars:")
print(result[:200])
print("\n✅ Model is working!")

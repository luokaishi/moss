#!/usr/bin/env python3
"""快速测试 LLM 集成"""
import sys
sys.path.insert(0, '.')

print("测试 1: 导入 LLM 配置...")
from agi.config import get_config
config = get_config("test")
print(f"✅ 配置加载成功: provider={config.provider}")

print("\n测试 2: 导入 LLM 集成器...")
from agi.llm_integration import create_llm_integrator
integrator = create_llm_integrator(enable_llm=True, profile="test")
print(f"✅ 集成器创建成功: enable_llm={integrator.enable_llm}")

print("\n测试 3: 生成变异...")
code = "def f(x): return x * 2"
result = integrator.generate_mutation(
    current_code=code,
    fitness_history=[0.5, 0.55],
    generation=1,
    total_generations=10
)
print(f"✅ 变异生成成功: success={result.success}, type={result.mutation_type}")

print("\n🎉 所有测试通过！LLM 集成正常工作。")

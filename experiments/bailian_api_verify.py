#!/usr/bin/env python3
"""百炼 API 验证 - 快速版"""

import os, sys
from pathlib import Path

BASE_URL = "https://coding.dashscope.aliyuncs.com/v1"
API_KEY = "sk-sp-dc2cd82985ce487f99d0c462673863eb"

print("=" * 60)
print("百炼 API 验证")
print("=" * 60)

try:
    from openai import OpenAI
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    print("✅ 客户端初始化成功")
except Exception as e:
    print(f"❌ 客户端失败: {e}")
    sys.exit(1)

# 测试模型
models = ["qwen3.5-plus", "qwen3-max", "qwen3-coder-plus", "glm-5", "kimi-k2.5"]
working_models = []

print("\n测试模型...")
for model in models:
    try:
        print(f"  {model}...", end=" ", flush=True)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "优化代码: add(x, y)"}],
            max_tokens=50,
            timeout=15,
        )
        print("✅")
        working_models.append(model)
        print(f"    响应: {response.choices[0].message.content[:40]}...")
    except Exception as e:
        print(f"❌ {str(e)[:30]}")

print("\n" + "=" * 60)
print(f"可用模型: {len(working_models)}/{len(models)}")
for m in working_models:
    print(f"  - {m}")

if working_models:
    print("\n✅ 百炼 API 验证成功！")
else:
    print("\n⚠️ 无可用模型")

print("=" * 60)

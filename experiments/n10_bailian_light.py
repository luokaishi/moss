#!/usr/bin/env python3
"""N=10 百炼轻量级验证 - 减少调用次数"""

import os, sys, json, random, numpy as np, time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from agi.genetic_programmer import random_tree

BASE_URL = "https://coding.dashscope.aliyuncs.com/v1"
API_KEY = "sk-sp-dc2cd82985ce487f99d0c462673863eb"

print("=" * 60)
print("N=10 百炼轻量级验证")
print("=" * 60)

try:
    from openai import OpenAI
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    print("✅ 客户端初始化成功")
except Exception as e:
    print(f"❌ {e}")
    sys.exit(1)

# 只测试一个模型
print("\n测试 qwen3.5-plus...")
try:
    response = client.chat.completions.create(
        model="qwen3.5-plus",
        messages=[{"role": "user", "content": "优化代码: add(x, y)"}],
        max_tokens=100,
        timeout=30,
    )
    print("✅ 模型可用")
    print(f"响应: {response.choices[0].message.content[:50]}...")
    success = True
except Exception as e:
    print(f"❌ {e}")
    success = False

if success:
    print("\n🎉 百炼 API 验证成功！")
else:
    print("\n⚠️ 需要调整模型名称或参数")

print("=" * 60)

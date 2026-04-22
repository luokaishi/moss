#!/usr/bin/env python3
"""
检查 LLM 配置和可用性
"""

import os
import sys

def check_config():
    """检查配置"""
    print("=" * 60)
    print("LLM 配置检查")
    print("=" * 60)
    
    # 检查环境变量
    dashscope_key = os.environ.get("DASHSCOPE_API_KEY", "")
    ark_key = os.environ.get("ARK_API_KEY", "")
    
    print(f"\n1. 环境变量:")
    print(f"   DASHSCOPE_API_KEY: {'✅ 已设置' if dashscope_key and dashscope_key != 'your_api_key_here' else '❌ 未设置'}")
    print(f"   ARK_API_KEY: {'✅ 已设置' if ark_key and ark_key != 'your_api_key_here' else '❌ 未设置'}")
    
    # 检查依赖
    print(f"\n2. Python 依赖:")
    
    try:
        import dashscope
        print(f"   dashscope: ✅ 已安装")
    except ImportError:
        print(f"   dashscope: ❌ 未安装 (pip install dashscope)")
    
    try:
        import openai
        print(f"   openai: ✅ 已安装")
    except ImportError:
        print(f"   openai: ❌ 未安装 (pip install openai)")
    
    try:
        import scipy
        print(f"   scipy: ✅ 已安装")
    except ImportError:
        print(f"   scipy: ❌ 未安装 (pip install scipy)")
    
    # 检查 LLM 模块
    print(f"\n3. MOSS LLM 模块:")
    sys.path.insert(0, '/home/admin/.openclaw/workspace')
    
    try:
        from agi.llm_integration import create_llm_integrator
        print(f"   agi.llm_integration: ✅ 可用")
    except Exception as e:
        print(f"   agi.llm_integration: ❌ {e}")
    
    try:
        from agi.config import get_config
        print(f"   agi.config: ✅ 可用")
    except Exception as e:
        print(f"   agi.config: ❌ {e}")
    
    # 配置建议
    print(f"\n4. 配置建议:")
    
    if not dashscope_key or dashscope_key == 'your_api_key_here':
        print(f"   ⚠️  DASHSCOPE_API_KEY 未设置")
        print(f"      获取方式: https://dashscope.aliyun.com/")
        print(f"      设置命令: export DASHSCOPE_API_KEY='your-key'")
    
    if not ark_key or ark_key == 'your_api_key_here':
        print(f"   ⚠️  ARK_API_KEY 未设置")
        print(f"      获取方式: https://www.volcengine.com/product/ark")
        print(f"      设置命令: export ARK_API_KEY='your-key'")
    
    # 运行建议
    print(f"\n5. 运行建议:")
    
    if (dashscope_key and dashscope_key != 'your_api_key_here') or \
       (ark_key and ark_key != 'your_api_key_here'):
        print(f"   ✅ 可以运行真实 LLM 实验")
        print(f"      命令: python3 /home/admin/.openclaw/workspace/experiments/n10_real_llm.py")
        print(f"      成本: ~2-5 元 (N=10, 10代)")
    else:
        print(f"   ❌ 无法运行真实 LLM 实验")
        print(f"      原因: API Key 未配置")
        print(f"      替代: 继续使用 mock 模式")
    
    print(f"\n" + "=" * 60)

if __name__ == "__main__":
    check_config()

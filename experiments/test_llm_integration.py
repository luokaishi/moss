#!/usr/bin/env python3
"""
LLM 集成测试脚本
验证 LLM 模块是否正确集成到 mves AGI 架构

日期：2026-04-22
"""

import sys
import logging
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_llm_backend():
    """测试 LLM Backend"""
    logger.info("=" * 60)
    logger.info("测试 1: LLM Backend 导入")
    logger.info("=" * 60)
    
    try:
        from agi.llm_backend import LLMBackend, LLMConfig
        logger.info("✅ LLM Backend 导入成功")
        
        # 测试 mock 后端
        config = LLMConfig(provider="mock", model="test")
        backend = LLMBackend(config)
        logger.info("✅ LLM Backend 初始化成功 (mock)")
        
        # 测试对话
        response = backend.chat(
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.3,
        )
        logger.info(f"✅ LLM 对话成功：{response.get('content', '')[:50]}...")
        
        return True
    
    except ImportError as e:
        logger.error(f"❌ LLM Backend 导入失败：{e}")
        return False
    except Exception as e:
        logger.error(f"❌ LLM Backend 测试失败：{e}")
        return False


def test_llm_config():
    """测试 LLM 配置"""
    logger.info("=" * 60)
    logger.info("测试 2: LLM 配置")
    logger.info("=" * 60)
    
    try:
        from agi.config import get_config, LLMConfig
        
        # 测试预设配置
        config_high = get_config("high_perf")
        logger.info(f"✅ high_perf 配置：model={config_high.model}, token_budget={config_high.llm_daily_token_budget}")
        
        config_economy = get_config("economy")
        logger.info(f"✅ economy 配置：model={config_economy.model}, token_budget={config_economy.llm_daily_token_budget}")
        
        config_test = get_config("test")
        logger.info(f"✅ test 配置：provider={config_test.provider}")
        
        return True
    
    except Exception as e:
        logger.error(f"❌ LLM 配置测试失败：{e}")
        return False


def test_llm_integrator():
    """测试 LLM 集成器"""
    logger.info("=" * 60)
    logger.info("测试 3: LLM 集成器")
    logger.info("=" * 60)
    
    try:
        from agi.llm_integration import AGILLMIntegrator, create_llm_integrator
        
        # 测试创建集成器 (使用 mock)
        integrator = create_llm_integrator(enable_llm=True, profile="test")
        logger.info(f"✅ LLM 集成器创建成功 (enable_llm={integrator.enable_llm})")
        
        # 测试变异生成
        test_code = """
def fitness_function(x):
    return x * 2 + 1
"""
        result = integrator.generate_mutation(
            current_code=test_code,
            fitness_history=[0.5, 0.55, 0.58],
            generation=5,
            total_generations=30,
        )
        
        logger.info(f"✅ 变异生成成功：success={result.success}, type={result.mutation_type}")
        
        return True
    
    except Exception as e:
        logger.error(f"❌ LLM 集成器测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def test_hybrid_mutation():
    """测试 Hybrid 变异策略"""
    logger.info("=" * 60)
    logger.info("测试 4: Hybrid 变异策略")
    logger.info("=" * 60)
    
    try:
        from agi.hybrid_mutation import HybridMutationStrategy
        from agi.config import get_config
        
        config = get_config("test")
        strategy = HybridMutationStrategy(config)
        logger.info("✅ Hybrid 策略初始化成功")
        
        # 测试决策逻辑
        for gen in [0, 5, 10, 15, 20, 25, 29]:
            use_llm = strategy.should_use_llm(
                generation=gen,
                total_generations=30,
                fitness_history=[0.5 + i*0.01 for i in range(gen+1)],
            )
            logger.info(f"  Gen {gen:2d}: use_llm={use_llm}")
        
        return True
    
    except Exception as e:
        logger.error(f"❌ Hybrid 策略测试失败：{e}")
        return False


def main():
    """主测试函数"""
    logger.info("\n" + "=" * 60)
    logger.info("MOSS mves - LLM 集成测试")
    logger.info("=" * 60 + "\n")
    
    results = {
        "LLM Backend": test_llm_backend(),
        "LLM 配置": test_llm_config(),
        "LLM 集成器": test_llm_integrator(),
        "Hybrid 策略": test_hybrid_mutation(),
    }
    
    logger.info("\n" + "=" * 60)
    logger.info("测试结果汇总")
    logger.info("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        logger.info(f"{test_name}: {status}")
    
    total_passed = sum(results.values())
    total_tests = len(results)
    
    logger.info(f"\n总计：{total_passed}/{total_tests} 通过")
    
    if total_passed == total_tests:
        logger.info("\n🎉 所有测试通过！LLM 集成成功！")
        return 0
    else:
        logger.warning(f"\n⚠️ {total_tests - total_passed} 个测试失败，请检查配置")
        return 1


if __name__ == "__main__":
    sys.exit(main())

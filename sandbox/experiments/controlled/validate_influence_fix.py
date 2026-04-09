"""
验证InfluenceModule修复的有效性
对比新旧评分公式的行为差异
"""

import sys
sys.path.insert(0, '/workspace/projects/moss')

import numpy as np
from core.objectives import SystemState
from dataclasses import dataclass


class OldInfluenceModule:
    """原始Influence模块（有奖励黑客风险）"""
    
    def __init__(self):
        self.caller_importance = {}
        self.history = []
    
    def evaluate(self, state):
        """原始评分公式（有问题）"""
        call_volume = min(state.api_calls / 1000, 1.0)
        caller_diversity = min(state.unique_callers / 10, 1.0)
        avg_importance = np.mean(list(self.caller_importance.values())) if self.caller_importance else 0.5
        substitution_difficulty = min(state.uptime / 168, 1.0)
        
        influence_score = (call_volume * 0.3 + caller_diversity * 0.2 + 
                          avg_importance * 0.3 + substitution_difficulty * 0.2)
        
        self.history.append(influence_score)
        return influence_score
    
    def record_caller(self, caller_id, importance=0.5):
        self.caller_importance[caller_id] = importance


class NewInfluenceModule:
    """修复后的Influence模块（本文件中的实现）"""
    
    def __init__(self):
        self.caller_importance = {}
        self.call_quality_scores = []
        self.resource_cost_history = []
        self.system_load_penalty = 0.0
        self.max_resource_ratio = 0.8
        self.history = []
    
    def evaluate(self, state):
        """修复后的评分公式"""
        avg_importance = np.mean(list(self.caller_importance.values())) if self.caller_importance else 0.5
        avg_quality = np.mean(self.call_quality_scores[-100:]) if self.call_quality_scores else 0.5
        quality_score = (avg_importance * 0.6 + avg_quality * 0.4)
        
        total_resource_cost = sum(self.resource_cost_history[-100:]) if self.resource_cost_history else 1.0
        positive_contributions = len(self.caller_importance) * quality_score
        contribution_density = min(positive_contributions / (total_resource_cost + 1), 1.0)
        
        if state.resource_usage > self.max_resource_ratio:
            self.system_load_penalty = (state.resource_usage - self.max_resource_ratio) / (1.0 - self.max_resource_ratio)
        else:
            self.system_load_penalty = 0.0
        
        load_safety_factor = max(0.0, 1.0 - self.system_load_penalty)
        substitution_difficulty = min(state.uptime / 168, 1.0)
        
        influence_score = (contribution_density * 0.5 * load_safety_factor + 
                          substitution_difficulty * 0.3 +
                          quality_score * 0.2)
        
        self.history.append(influence_score)
        return influence_score
    
    def record_caller(self, caller_id, importance=0.5, quality=0.5, resource_cost=1.0):
        self.caller_importance[caller_id] = importance
        self.call_quality_scores.append(quality)
        self.resource_cost_history.append(resource_cost)


def run_attack_scenario(module, scenario_name, steps=50):
    """
    模拟攻击场景，观察模块反应
    
    场景1: 刷量攻击（大量低质量调用）
    场景2: 资源耗尽攻击（占用所有资源）
    场景3: 正常增长（高质量调用+合理资源）
    """
    print(f"\n{'='*60}")
    print(f"Scenario: {scenario_name}")
    print(f"{'='*60}")
    
    scores = []
    metrics = []
    
    for step in range(steps):
        # 根据场景设置状态
        state = None
        if "spam_attack" in scenario_name:
            # 刷量攻击：大量低质量调用
            state = SystemState(
                resource_quota=0.5,
                resource_usage=0.3 + step * 0.01,  # 逐渐增加
                uptime=step,
                error_rate=0.1,
                api_calls=step * 10,  # 快速增加
                unique_callers=min(step, 50),  # 大量调用者
                environment_entropy=0.3,
                last_backup=0
            )
            # 记录低质量调用
            for i in range(10):  # 每步10个调用
                if hasattr(module, 'record_caller'):
                    if 'quality' in module.record_caller.__code__.co_varnames:
                        module.record_caller(f"caller_{step}_{i}", importance=0.3, quality=0.2, resource_cost=5.0)
                    else:
                        module.record_caller(f"caller_{step}_{i}", importance=0.3)
            
        elif "resource_exhaustion" in scenario_name:
            # 资源耗尽攻击：占用所有资源
            state = SystemState(
                resource_quota=0.1,  # 资源配额低
                resource_usage=min(0.3 + step * 0.02, 0.95),  # 快速增加到95%
                uptime=step,
                error_rate=0.05,
                api_calls=step * 5,
                unique_callers=5,
                environment_entropy=0.2,
                last_backup=0
            )
            # 记录高消耗调用
            for i in range(5):
                if hasattr(module, 'record_caller'):
                    if 'quality' in module.record_caller.__code__.co_varnames:
                        module.record_caller(f"caller_{step}_{i}", importance=0.7, quality=0.6, resource_cost=20.0)
                    else:
                        module.record_caller(f"caller_{step}_{i}", importance=0.7)
                        
        elif "normal_growth" in scenario_name:
            # 正常增长：高质量调用+合理资源
            state = SystemState(
                resource_quota=0.7,
                resource_usage=0.3 + step * 0.005,  # 缓慢增加
                uptime=step,
                error_rate=0.02,
                api_calls=step * 2,  # 适度增长
                unique_callers=min(step // 2, 10),  # 稳定增长
                environment_entropy=0.3,
                last_backup=0
            )
            # 记录高质量调用
            for i in range(2):
                if hasattr(module, 'record_caller'):
                    if 'quality' in module.record_caller.__code__.co_varnames:
                        module.record_caller(f"caller_{step}_{i}", importance=0.8, quality=0.8, resource_cost=1.0)
                    else:
                        module.record_caller(f"caller_{step}_{i}", importance=0.8)
        
        score = module.evaluate(state)
        scores.append(score)
        
        # 记录额外指标（如果是新模块）
        if hasattr(module, 'system_load_penalty'):
            metrics.append({
                'step': step,
                'score': score,
                'load_penalty': module.system_load_penalty,
                'resource_usage': state.resource_usage
            })
        
        if step % 10 == 0:
            print(f"  Step {step:2d}: Score={score:.3f}, Resource={state.resource_usage:.2f}", end="")
            if hasattr(module, 'system_load_penalty'):
                print(f", Penalty={module.system_load_penalty:.2f}")
            else:
                print()
    
    return scores, metrics


def compare_modules():
    """对比新旧模块在不同场景下的表现"""
    print("\n" + "="*60)
    print("InfluenceModule Security Fix Validation")
    print("="*60)
    
    scenarios = ["spam_attack", "resource_exhaustion", "normal_growth"]
    results = {}
    
    for scenario in scenarios:
        print(f"\n{'='*60}")
        print(f"Testing: {scenario}")
        print(f"{'='*60}")
        
        # 测试旧模块
        old_module = OldInfluenceModule()
        old_scores, _ = run_attack_scenario(old_module, scenario + " (OLD)")
        
        # 测试新模块
        new_module = NewInfluenceModule()
        new_scores, new_metrics = run_attack_scenario(new_module, scenario + " (NEW)")
        
        # 计算统计
        results[scenario] = {
            'old': {
                'mean': np.mean(old_scores),
                'max': np.max(old_scores),
                'final': old_scores[-1]
            },
            'new': {
                'mean': np.mean(new_scores),
                'max': np.max(new_scores),
                'final': new_scores[-1]
            }
        }
        
        # 判断修复是否有效
        if scenario == "spam_attack":
            # 刷量攻击：新模块应该得分更低或持平（不鼓励刷量）
            effective = results[scenario]['new']['final'] <= results[scenario]['old']['final']
            print(f"\n  Spam Attack Mitigation: {'✅ PASS' if effective else '❌ FAIL'}")
            print(f"    Old final score: {results[scenario]['old']['final']:.3f}")
            print(f"    New final score: {results[scenario]['new']['final']:.3f}")
            
        elif scenario == "resource_exhaustion":
            # 资源耗尽：新模块应该在最后得分显著降低（惩罚高负载）
            effective = results[scenario]['new']['final'] < results[scenario]['old']['final'] * 0.8
            print(f"\n  Resource Protection: {'✅ PASS' if effective else '❌ FAIL'}")
            print(f"    Old final score: {results[scenario]['old']['final']:.3f}")
            print(f"    New final score: {results[scenario]['new']['final']:.3f}")
            
        elif scenario == "normal_growth":
            # 正常增长：新模块应该保持合理得分（不打击正常行为）
            effective = results[scenario]['new']['final'] >= 0.3  # 至少保持一定分数
            print(f"\n  Normal Operation Preserved: {'✅ PASS' if effective else '❌ FAIL'}")
            print(f"    New final score: {results[scenario]['new']['final']:.3f}")
    
    # 总结
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    
    all_pass = True
    for scenario in scenarios:
        old_final = results[scenario]['old']['final']
        new_final = results[scenario]['new']['final']
        
        if scenario == "spam_attack":
            status = "✅ PASS" if new_final <= old_final else "❌ FAIL"
            description = "Spam attack mitigated (no score increase)"
        elif scenario == "resource_exhaustion":
            status = "✅ PASS" if new_final < old_final * 0.8 else "❌ FAIL"
            description = "Resource exhaustion penalized"
        elif scenario == "normal_growth":
            status = "✅ PASS" if new_final >= 0.3 else "❌ FAIL"
            description = "Normal operation preserved"
        
        if status == "❌ FAIL":
            all_pass = False
        
        print(f"{status} - {scenario}: {description}")
        print(f"       Old: {old_final:.3f} → New: {new_final:.3f}")
    
    print("="*60)
    if all_pass:
        print("✅ ALL SECURITY TESTS PASSED")
        print("The fix effectively prevents reward hacking while preserving normal operation.")
    else:
        print("❌ SOME TESTS FAILED")
        print("The fix may need further adjustment.")
    print("="*60)
    
    return results


def main():
    """主函数"""
    results = compare_modules()
    
    # 保存结果
    import json
    with open('influence_fix_validation.json', 'w') as f:
        json.dump(results, f, indent=2)
    print("\nResults saved to: influence_fix_validation.json")


if __name__ == '__main__':
    main()

"""
MOSS Weight Quantization Experiment
权重分配量化实验 - 解决8/8评估提及的核心问题

实验目标: 通过控制变量法测试不同权重比例的性能，建立数据驱动的权重最优解模型
"""

import sys
import numpy as np
import json
from datetime import datetime
from typing import Dict, List, Tuple
# import matplotlib.pyplot as plt  # Optional for visualization

sys.path.insert(0, '/workspace/projects/moss')

from core.objectives import SystemState, SurvivalModule, CuriosityModule, InfluenceModule, OptimizationModule


class WeightConfiguration:
    """权重配置类"""
    
    def __init__(self, name: str, weights: Dict[str, float]):
        self.name = name
        self.weights = weights  # {'survival': 0.6, 'curiosity': 0.1, ...}
        self.performance_history = []
    
    def get_metrics(self) -> Dict:
        """获取该配置的性能指标"""
        if not self.performance_history:
            return {}
        
        # 计算平均性能
        avg_survival = np.mean([p['survival_score'] for p in self.performance_history])
        avg_curiosity = np.mean([p['curiosity_score'] for p in self.performance_history])
        avg_influence = np.mean([p['influence_score'] for p in self.performance_history])
        avg_optimization = np.mean([p['optimization_score'] for p in self.performance_history])
        
        # 计算平衡度（标准差越小越平衡）
        scores = [avg_survival, avg_curiosity, avg_influence, avg_optimization]
        balance_score = 1.0 / (1.0 + np.std(scores))  # 越平衡分值越高
        
        # 计算综合得分
        overall = np.mean(scores) * balance_score
        
        return {
            'config_name': self.name,
            'weights': self.weights,
            'survival_avg': avg_survival,
            'curiosity_avg': avg_curiosity,
            'influence_avg': avg_influence,
            'optimization_avg': avg_optimization,
            'balance_score': balance_score,
            'overall_score': overall,
            'sample_size': len(self.performance_history)
        }


class WeightQuantizationExperiment:
    """
    权重分配量化实验
    
    测试不同权重配置在各种系统状态下的性能
    建立数据驱动的最优权重模型
    """
    
    def __init__(self):
        self.configurations = []
        self.results = {}
        self._generate_configurations()
    
    def _generate_configurations(self):
        """生成待测试的权重配置"""
        # 原始MOSS配置 (经验值)
        self.configurations.append(WeightConfiguration(
            'MOSS_Original_Crisis',
            {'survival': 0.6, 'curiosity': 0.1, 'influence': 0.2, 'optimization': 0.1}
        ))
        
        self.configurations.append(WeightConfiguration(
            'MOSS_Original_Normal',
            {'survival': 0.2, 'curiosity': 0.4, 'influence': 0.3, 'optimization': 0.1}
        ))
        
        # 生存优先配置 (测试极端)
        self.configurations.append(WeightConfiguration(
            'Survival_Dominant',
            {'survival': 0.8, 'curiosity': 0.05, 'influence': 0.1, 'optimization': 0.05}
        ))
        
        # 好奇优先配置 (测试极端)
        self.configurations.append(WeightConfiguration(
            'Curiosity_Dominant',
            {'survival': 0.1, 'curiosity': 0.7, 'influence': 0.15, 'optimization': 0.05}
        ))
        
        # 均衡配置 (测试平衡)
        self.configurations.append(WeightConfiguration(
            'Balanced_Equal',
            {'survival': 0.25, 'curiosity': 0.25, 'influence': 0.25, 'optimization': 0.25}
        ))
        
        # 自适应候选配置 (基于文献)
        self.configurations.append(WeightConfiguration(
            'Adaptive_Candidate_1',
            {'survival': 0.5, 'curiosity': 0.3, 'influence': 0.15, 'optimization': 0.05}
        ))
        
        self.configurations.append(WeightConfiguration(
            'Adaptive_Candidate_2',
            {'survival': 0.35, 'curiosity': 0.35, 'influence': 0.2, 'optimization': 0.1}
        ))
        
        self.configurations.append(WeightConfiguration(
            'Adaptive_Candidate_3',
            {'survival': 0.4, 'curiosity': 0.2, 'influence': 0.3, 'optimization': 0.1}
        ))
    
    def simulate_scenario(self, state: SystemState, config: WeightConfiguration, steps: int = 100) -> Dict:
        """
        模拟特定场景下的性能
        
        Args:
            state: 初始系统状态
            config: 权重配置
            steps: 模拟步数
        
        Returns:
            性能指标
        """
        # 初始化模块
        survival = SurvivalModule()
        curiosity = CuriosityModule()
        influence = InfluenceModule()
        optimization = OptimizationModule()
        
        # 设置权重
        survival.weight = config.weights['survival']
        curiosity.weight = config.weights['curiosity']
        influence.weight = config.weights['influence']
        optimization.weight = config.weights['optimization']
        
        scores = {'survival': [], 'curiosity': [], 'influence': [], 'optimization': []}
        
        for _ in range(steps):
            # 评估各目标
            s_score = survival.evaluate(state)
            c_score = curiosity.evaluate(state)
            i_score = influence.evaluate(state)
            o_score = optimization.evaluate(state)
            
            scores['survival'].append(s_score)
            scores['curiosity'].append(c_score)
            scores['influence'].append(i_score)
            scores['optimization'].append(o_score)
            
            # 模拟状态变化
            state.resource_quota *= 0.99  # 资源缓慢消耗
            state.uptime += 0.1
        
        return {
            'survival_score': np.mean(scores['survival']),
            'curiosity_score': np.mean(scores['curiosity']),
            'influence_score': np.mean(scores['influence']),
            'optimization_score': np.mean(scores['optimization']),
            'variance': np.var([np.mean(scores[s]) for s in scores])
        }
    
    def run_experiment(self):
        """运行完整实验"""
        print("="*70)
        print("MOSS WEIGHT QUANTIZATION EXPERIMENT")
        print("="*70)
        print(f"Testing {len(self.configurations)} weight configurations")
        print(f"Scenarios: Crisis, Concerned, Normal, Growth")
        print("="*70)
        print()
        
        # 定义测试场景
        scenarios = {
            'crisis': SystemState(
                resource_quota=0.15, resource_usage=0.85, uptime=10,
                error_rate=0.05, api_calls=100, unique_callers=2,
                environment_entropy=0.3, last_backup=0
            ),
            'concerned': SystemState(
                resource_quota=0.35, resource_usage=0.65, uptime=50,
                error_rate=0.03, api_calls=300, unique_callers=4,
                environment_entropy=0.4, last_backup=20
            ),
            'normal': SystemState(
                resource_quota=0.75, resource_usage=0.45, uptime=100,
                error_rate=0.02, api_calls=500, unique_callers=6,
                environment_entropy=0.3, last_backup=50
            ),
            'growth': SystemState(
                resource_quota=0.85, resource_usage=0.35, uptime=200,
                error_rate=0.01, api_calls=800, unique_callers=8,
                environment_entropy=0.5, last_backup=80
            )
        }
        
        # 对每个配置在每个场景下测试
        for config in self.configurations:
            print(f"\nTesting configuration: {config.name}")
            print(f"Weights: {config.weights}")
            
            for scenario_name, state in scenarios.items():
                print(f"  Scenario: {scenario_name}...", end=' ')
                
                # 运行多次取平均
                scenario_results = []
                for _ in range(10):  # 10次重复
                    result = self.simulate_scenario(state, config, steps=100)
                    scenario_results.append(result)
                
                # 平均结果
                avg_result = {
                    'survival_score': np.mean([r['survival_score'] for r in scenario_results]),
                    'curiosity_score': np.mean([r['curiosity_score'] for r in scenario_results]),
                    'influence_score': np.mean([r['influence_score'] for r in scenario_results]),
                    'optimization_score': np.mean([r['optimization_score'] for r in scenario_results]),
                    'variance': np.mean([r['variance'] for r in scenario_results])
                }
                
                config.performance_history.append(avg_result)
                print(f"Done (Overall: {np.mean(list(avg_result.values())[:-1]):.3f})")
        
        # 分析结果
        self._analyze_results()
    
    def _analyze_results(self):
        """分析实验结果"""
        print("\n" + "="*70)
        print("RESULTS ANALYSIS")
        print("="*70)
        
        # 计算每个配置的综合指标
        all_metrics = []
        for config in self.configurations:
            metrics = config.get_metrics()
            all_metrics.append(metrics)
        
        # 排序（按综合得分）
        all_metrics.sort(key=lambda x: x['overall_score'], reverse=True)
        
        print("\nTop 5 Configurations (by Overall Score):")
        print("-"*70)
        print(f"{'Rank':<6} {'Config':<25} {'Overall':<10} {'Balance':<10} {'Sample'}")
        print("-"*70)
        
        for i, m in enumerate(all_metrics[:5], 1):
            print(f"{i:<6} {m['config_name']:<25} {m['overall_score']:.3f}     {m['balance_score']:.3f}     {m['sample_size']}")
        
        print("\nDetailed Top 3:")
        print("-"*70)
        for i, m in enumerate(all_metrics[:3], 1):
            print(f"\n{i}. {m['config_name']}")
            print(f"   Weights: {m['weights']}")
            print(f"   Survival:    {m['survival_avg']:.3f}")
            print(f"   Curiosity:   {m['curiosity_avg']:.3f}")
            print(f"   Influence:   {m['influence_avg']:.3f}")
            print(f"   Optimization: {m['optimization_avg']:.3f}")
            print(f"   Balance:     {m['balance_score']:.3f}")
            print(f"   Overall:     {m['overall_score']:.3f}")
        
        # 保存结果
        self._save_results(all_metrics)
    
    def _save_results(self, all_metrics: List[Dict]):
        """保存实验结果"""
        result = {
            'experiment_name': 'MOSS Weight Quantization',
            'timestamp': datetime.now().isoformat(),
            'configurations_tested': len(self.configurations),
            'scenarios_tested': ['crisis', 'concerned', 'normal', 'growth'],
            'top_recommendation': all_metrics[0] if all_metrics else None,
            'all_results': all_metrics
        }
        
        filename = f"weight_quantization_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\n{'='*70}")
        print(f"Results saved to: {filename}")
        print("="*70)
        
        # 打印建议
        if all_metrics:
            best = all_metrics[0]
            print(f"\n💡 RECOMMENDATION:")
            print(f"   Use configuration: {best['config_name']}")
            print(f"   Optimal weights: {best['weights']}")
            print(f"   Expected overall performance: {best['overall_score']:.3f}")
            print(f"   Balance quality: {best['balance_score']:.3f}")


def main():
    """主函数"""
    print("\n" + "="*70)
    print("MOSS WEIGHT QUANTIZATION EXPERIMENT")
    print("Addressing critical issue: Weight allocation lacks quantitative basis")
    print("(Identified by 8/8 external evaluations)")
    print("="*70 + "\n")
    
    experiment = WeightQuantizationExperiment()
    experiment.run_experiment()


if __name__ == '__main__':
    main()

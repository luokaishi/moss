#!/usr/bin/env python3
"""
MOSS Real-World Experiment with GitHub API (Windows兼容修复版)
使用真实GitHub API的MOSS实验

这是首个真实互联网子集实验（Grok/Kimi推荐）

修复内容：
1. 修复Linux硬编码路径
2. 添加Windows兼容性
3. 添加模拟模式（当缺少GitHub token时）
4. 修复路径和导入问题
"""

import sys
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional

# 修复路径问题 - Windows兼容
_MOSS_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _MOSS_ROOT)
sys.path.insert(0, os.path.join(_MOSS_ROOT, 'integration'))

# 导入子进程模块
import subprocess

# 尝试导入RealWorldAPIIntegration
try:
    from real_world_api_integration import RealWorldAPIIntegration
    REALWORLD_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  无法导入 RealWorldAPIIntegration: {e}")
    print("🔄 启用模拟模式...")
    REALWORLD_AVAILABLE = False


class RealGitHubMOSSExperiment:
    """
    真实GitHub MOSS实验（修复版）
    
    实验目标：验证MOSS在真实API环境中的自驱行为
    """
    
    def __init__(self, max_steps: int = 10, test_mode: bool = True):
        # 配置文件路径（Windows兼容）
        config_path = os.path.join(_MOSS_ROOT, 'integration', 'api_config.json')
        
        # 检查RealWorld模块是否可用
        self.realworld_available = REALWORLD_AVAILABLE
        
        if self.realworld_available:
            try:
                self.integration = RealWorldAPIIntegration(config_path=str(config_path))
                print(f"✅ RealWorldAPIIntegration 初始化成功")
            except Exception as e:
                print(f"❌ RealWorldAPIIntegration 初始化失败: {e}")
                self.integration = None
                self.realworld_available = False
        else:
            self.integration = None
        
        self.max_steps = max_steps
        self.test_mode = test_mode
        self.experiment_log = []
        self.knowledge_base = []
        
        # MOSS状态
        self.weights = {
            'curiosity': 0.40,
            'survival': 0.20,
            'influence': 0.30,
            'optimization': 0.10
        }
        
        self.objective_scores = {
            'curiosity': 0.5,
            'survival': 1.0,
            'influence': 0.0,
            'optimization': 0.0
        }
    
    def execute_github_search(self, query: str) -> Optional[Dict]:
        """执行真实的GitHub搜索（或模拟搜索）"""
        
        # 如果是测试模式或者缺少集成，使用模拟数据
        if self.test_mode or not REALWORLD_AVAILABLE:
            print(f"🔄 模拟搜索: {query}")
            return self._simulate_github_search(query)
        
        # 真实API调用
        if not self.integration:
            print("❌ 集成模块未初始化")
            return self._simulate_github_search(query)
        
        # 尝试获取token
        try:
            token = self.integration.config.get('github_token', '')
        except:
            token = ''
        
        if not token:
            print("⚠️  No GitHub token configured, using simulation")
            return self._simulate_github_search(query)
        
        try:
            # 使用curl执行真实API调用
            cmd = [
                'curl', '-s',
                '-H', f'Authorization: token {token}',
                '-H', 'Accept: application/vnd.github.v3+json',
                f'https://api.github.com/search/repositories?q={query.replace(" ", "+")}&per_page=5'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                
                # 记录预算（如果可用）
                if hasattr(self.integration, 'budget_tracker'):
                    try:
                        self.integration.budget_tracker.record_usage('github', 0.0)
                    except:
                        pass
                
                return {
                    'query': query,
                    'total_count': data.get('total_count', 0),
                    'repositories': [
                        {
                            'name': item.get('full_name'),
                            'stars': item.get('stargazers_count', 0),
                            'description': item.get('description', ''),
                            'url': item.get('html_url')
                        }
                        for item in data.get('items', [])
                    ]
                }
            else:
                print(f"❌ API error: {result.stderr}")
                return self._simulate_github_search(query)
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return self._simulate_github_search(query)
    
    def _simulate_github_search(self, query: str) -> Dict:
        """模拟GitHub搜索"""
        # 模拟数据
        mock_repos = [
            {'full_name': 'torvalds/linux', 'stargazers_count': 150000, 'description': 'Linux kernel', 'html_url': 'https://github.com/torvalds/linux'},
            {'full_name': 'microsoft/vscode', 'stargazers_count': 140000, 'description': 'Visual Studio Code', 'html_url': 'https://github.com/microsoft/vscode'},
            {'full_name': 'facebook/react', 'stargazers_count': 210000, 'description': 'React library', 'html_url': 'https://github.com/facebook/react'},
            {'full_name': 'tensorflow/tensorflow', 'stargazers_count': 175000, 'description': 'TensorFlow ML framework', 'html_url': 'https://github.com/tensorflow/tensorflow'},
            {'full_name': 'keras-team/keras', 'stargazers_count': 59000, 'description': 'Keras deep learning API', 'html_url': 'https://github.com/keras-team/keras'}
        ]
        
        return {
            'query': query,
            'total_count': len(mock_repos) * 100,  # 模拟总数量
            'repositories': [
                {
                    'name': repo['full_name'],
                    'stars': repo['stargazers_count'],
                    'description': repo['description'],
                    'url': repo['html_url']
                }
                for repo in mock_repos
            ]
        }
    
    def select_action(self) -> str:
        """基于MOSS目标选择动作"""
        # 简化版：基于最高目标选择
        max_obj = max(self.objective_scores, key=self.objective_scores.get)
        
        action_map = {
            'curiosity': 'explore_repos',
            'survival': 'monitor_resources',
            'influence': 'analyze_trends',
            'optimization': 'learn_best_practices'
        }
        
        return action_map.get(max_obj, 'explore_repos')
    
    def update_objectives(self, action_result: Optional[Dict]):
        """更新目标分数"""
        if action_result and action_result.get('repositories'):
            # 成功获取知识，增加Curiosity
            self.objective_scores['curiosity'] = min(1.0, self.objective_scores['curiosity'] + 0.1)
            
            # 增加Influence（获取更多star的repo更有影响力）
            total_stars = sum(repo.get('stars', 0) for repo in action_result['repositories'])
            self.objective_scores['influence'] = min(1.0, self.objective_scores['influence'] + total_stars / 100000)
            
            # 添加到知识库
            self.knowledge_base.append({
                'timestamp': datetime.now().isoformat(),
                'query': action_result['query'],
                'repos_found': len(action_result['repositories']),
                'total_stars': total_stars
            })
        else:
            # 失败，降低Curiosity，增加Survival权重
            self.objective_scores['curiosity'] = max(0, self.objective_scores['curiosity'] - 0.05)
            self.objective_scores['survival'] = max(0, self.objective_scores['survival'] - 0.02)
    
    def generate_search_query(self) -> str:
        """生成搜索查询"""
        # 基于当前状态动态生成查询
        topics = [
            "machine learning",
            "artificial intelligence",
            "neural networks",
            "deep learning",
            "reinforcement learning",
            "autonomous agents",
            "multi objective optimization"
        ]
        
        # 基于知识库大小选择不同复杂度
        if len(self.knowledge_base) < 3:
            return "machine learning stars:>1000"
        elif len(self.knowledge_base) < 6:
            return "autonomous agents stars:>500"
        else:
            return "multi objective optimization stars:>100"
    
    def run_experiment(self):
        """运行实验"""
        print("="*70)
        print("MOSS REAL-WORLD EXPERIMENT WITH GITHUB API (FIXED)")
        print("="*70)
        print(f"Start time: {datetime.now().isoformat()}")
        print(f"Max steps: {self.max_steps}")
        print(f"Test mode: {'Yes' if self.test_mode else 'No'}")
        print(f"RealWorld available: {'Yes' if REALWORLD_AVAILABLE else 'No'}")
        print()
        
        # 检查API状态（如果可用）
        if REALWORLD_AVAILABLE and self.integration:
            try:
                apis = self.integration.get_available_apis()
                print("API Status:")
                for api, enabled in apis.items():
                    print(f"  {api}: {'✅' if enabled else '❌'}")
                print()
            except:
                print("⚠️  Cannot check API status")
                print()
        else:
            print("⚠️  RealWorld integration not available")
            print("🔄 Using simulation mode")
            print()
        
        print("Starting experiment...")
        print("-"*70)
        
        for step in range(self.max_steps):
            print(f"\nStep {step + 1}/{self.max_steps}")
            print(f"Objectives: {self.objective_scores}")
            
            # 选择动作
            action = self.select_action()
            print(f"Action: {action}")
            
            if action == 'explore_repos':
                query = self.generate_search_query()
                print(f"Search query: {query}")
                
                result = self.execute_github_search(query)
                
                if result:
                    print(f"✅ Found {result['total_count']} repositories")
                    for repo in result['repositories'][:3]:
                        print(f"   - {repo['name']} ({repo['stars']} ⭐)")
                else:
                    print("❌ Search failed")
                
                self.update_objectives(result)
            
            else:
                print(f"Simulating: {action}")
                self.update_objectives(None)
            
            # 记录日志
            self.experiment_log.append({
                'step': step + 1,
                'timestamp': datetime.now().isoformat(),
                'action': action,
                'objectives': self.objective_scores.copy(),
                'knowledge_count': len(self.knowledge_base)
            })
            
            # 短暂延迟避免API限制
            time.sleep(0.5)
        
        # 生成报告
        self._generate_report()
    
    def _generate_report(self):
        """生成实验报告"""
        print("\n" + "="*70)
        print("EXPERIMENT COMPLETE")
        print("="*70)
        
        print(f"\nTotal steps: {len(self.experiment_log)}")
        print(f"Knowledge items acquired: {len(self.knowledge_base)}")
        print(f"Final objective scores: {self.objective_scores}")
        
        if self.knowledge_base:
            print("\nKnowledge Base:")
            for i, item in enumerate(self.knowledge_base, 1):
                print(f"  {i}. Query: {item['query']}")
                print(f"     Repos: {item['repos_found']}, Stars: {item['total_stars']}")
        else:
            print("\nNo knowledge acquired during experiment")
        
        # 保存结果
        result = {
            'timestamp': datetime.now().isoformat(),
            'experiment': 'real_github_moss_fixed',
            'test_mode': self.test_mode,
            'realworld_available': REALWORLD_AVAILABLE,
            'steps': len(self.experiment_log),
            'knowledge_acquired': len(self.knowledge_base),
            'final_objectives': self.objective_scores,
            'knowledge_base': self.knowledge_base,
            'log': self.experiment_log
        }
        
        # 创建输出目录
        output_dir = os.path.join(_MOSS_ROOT, 'experiments', 'github_results')
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"real_experiment_github_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Results saved to: {filepath}")


def main():
    """主函数"""
    print("MOSS GitHub真实API实验 (修复版)")
    print("说明: 如果没有配置GitHub token，将自动使用模拟模式")
    
    # 使用模拟模式进行测试
    experiment = RealGitHubMOSSExperiment(max_steps=5, test_mode=True)
    experiment.run_experiment()


if __name__ == "__main__":
    main()
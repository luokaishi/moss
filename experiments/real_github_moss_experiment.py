"""
MOSS Real-World Experiment with GitHub API
使用真实GitHub API的MOSS实验

这是首个真实互联网子集实验（Grok/Kimi推荐）
"""

import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Optional

sys.path.insert(0, '/workspace/projects/moss')

from integration.real_world_api_integration import RealWorldAPIIntegration
import subprocess


class RealGitHubMOSSExperiment:
    """
    真实GitHub MOSS实验
    
    实验目标：验证MOSS在真实API环境中的自驱行为
    """
    
    def __init__(self, max_steps: int = 20):
        self.integration = RealWorldAPIIntegration(
            config_path='/workspace/projects/moss/integration/api_config.json'
        )
        self.max_steps = max_steps
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
        """执行真实的GitHub搜索"""
        token = self.integration.config.get('github_token', '')
        
        if not token:
            print("❌ No GitHub token configured")
            return None
        
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
                
                # 记录预算
                self.integration.budget_tracker.record_usage('github', 0.0)
                
                return {
                    'query': query,
                    'total_count': data.get('total_count', 0),
                    'repositories': [
                        {
                            'name': item.get('full_name'),
                            'stars': item.get('stargazers_count'),
                            'description': item.get('description'),
                            'url': item.get('html_url')
                        }
                        for item in data.get('items', [])
                    ]
                }
            else:
                print(f"❌ API error: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
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
            self.objective_scores['influence'] = min(1.0, self.objective_scores['influence'] + total_stars / 10000)
            
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
        if len(self.knowledge_base) < 5:
            return "machine learning stars:>1000"
        elif len(self.knowledge_base) < 10:
            return "autonomous agents stars:>500"
        else:
            return "multi objective optimization stars:>100"
    
    def run_experiment(self):
        """运行实验"""
        print("="*70)
        print("MOSS REAL-WORLD EXPERIMENT WITH GITHUB API")
        print("="*70)
        print(f"Start time: {datetime.now().isoformat()}")
        print(f"Max steps: {self.max_steps}")
        print()
        
        # 检查API状态
        apis = self.integration.get_available_apis()
        print("API Status:")
        for api, enabled in apis.items():
            print(f"  {api}: {'✅' if enabled else '❌'}")
        print()
        
        if not apis['github']:
            print("❌ GitHub API not available. Aborting.")
            return
        
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
            time.sleep(1)
        
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
        
        print("\nKnowledge Base:")
        for i, item in enumerate(self.knowledge_base, 1):
            print(f"  {i}. Query: {item['query']}")
            print(f"     Repos: {item['repos_found']}, Stars: {item['total_stars']}")
        
        print("\nBudget Status:")
        budget = self.integration.budget_tracker.get_status()
        print(f"  Used: ${budget['used_budget']:.2f} / ${budget['total_budget']:.2f}")
        
        # 保存结果
        result = {
            'timestamp': datetime.now().isoformat(),
            'experiment': 'real_github_moss',
            'steps': len(self.experiment_log),
            'knowledge_acquired': len(self.knowledge_base),
            'final_objectives': self.objective_scores,
            'knowledge_base': self.knowledge_base,
            'log': self.experiment_log,
            'budget_status': budget
        }
        
        filename = f"real_experiment_github_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\n✅ Results saved to: {filename}")


def main():
    """主函数"""
    experiment = RealGitHubMOSSExperiment(max_steps=10)
    experiment.run_experiment()


if __name__ == '__main__':
    main()

"""
MOSS Complex Environment: Web Navigation Task
模拟真实Web导航场景，测试MOSS在复杂决策环境中的表现
"""

import random
import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class WebPage:
    """网页结构"""
    url: str
    content_type: str  # 'information', 'form', 'navigation', 'media'
    information_value: float  # 0.0 - 1.0
    interaction_cost: int  # tokens needed to interact
    links: List[str]  # URLs linked from this page
    depth: int  # Distance from start page


class WebNavigationEnvironment:
    """
    Web导航环境
    
    任务：Agent需要在有限资源下浏览网页，最大化信息获取
    挑战：
    - 网页有不同信息价值
    - 链接消耗资源
    - 存在死胡同和低价值页面
    - 信息价值随时间衰减（过时）
    """
    
    def __init__(self, seed: int = 42, max_depth: int = 5):
        random.seed(seed)
        self.max_depth = max_depth
        self.reset()
    
    def reset(self):
        """重置环境"""
        self.token_budget = 5000
        self.tokens_used = 0
        self.information_gained = 0.0
        self.pages_visited = 0
        self.current_page = None
        self.visited_urls = set()
        self.page_history = []
        self.terminated = False
        self.termination_reason = None
        
        # 生成Web图
        self.web_graph = self._generate_web_graph()
        self.current_page = self.web_graph['start']
        
    def _generate_web_graph(self) -> Dict[str, WebPage]:
        """生成模拟Web结构"""
        graph = {}
        
        # 创建分层结构
        pages_per_level = [3, 5, 7, 5, 3]  # 每层页面数
        
        for depth in range(self.max_depth):
            num_pages = pages_per_level[depth]
            
            for i in range(num_pages):
                url = f"page_d{depth}_p{i}"
                
                # 随机属性
                content_types = ['information', 'form', 'navigation', 'media']
                content_type = random.choice(content_types)
                
                # 信息价值随深度递减（深层通常价值低）
                base_value = max(0.1, 1.0 - depth * 0.15)
                information_value = random.uniform(base_value * 0.5, base_value)
                
                # 交互成本
                interaction_cost = random.randint(50, 200)
                
                # 生成链接（连向下一层）
                links = []
                if depth < self.max_depth - 1:
                    num_links = random.randint(1, 3)
                    next_level_pages = pages_per_level[depth + 1]
                    links = [f"page_d{depth+1}_p{random.randint(0, next_level_pages-1)}" 
                            for _ in range(num_links)]
                
                graph[url] = WebPage(
                    url=url,
                    content_type=content_type,
                    information_value=information_value,
                    interaction_cost=interaction_cost,
                    links=links,
                    depth=depth
                )
        
        # 设置起始页
        graph['start'] = graph['page_d0_p0']
        
        return graph
    
    def get_state(self) -> Dict:
        """获取当前状态"""
        resource_ratio = 1.0 - (self.tokens_used / self.token_budget)
        
        # 计算当前页面的信息密度
        current_value = self.current_page.information_value if self.current_page else 0
        
        # 计算可选动作的价值（探索vs利用）
        unexplored_links = [link for link in self.current_page.links 
                          if link not in self.visited_urls] if self.current_page else []
        
        return {
            'resource_ratio': max(0.0, resource_ratio),
            'tokens_remaining': self.token_budget - self.tokens_used,
            'information_gained': self.information_gained,
            'pages_visited': self.pages_visited,
            'current_page_value': current_value,
            'current_depth': self.current_page.depth if self.current_page else 0,
            'unexplored_links': len(unexplored_links),
            'total_links': len(self.current_page.links) if self.current_page else 0,
            'visited_ratio': len(self.visited_urls) / max(1, len(self.web_graph)),
            'terminated': self.terminated
        }
    
    def execute_action(self, action: str, target: Optional[str] = None) -> Dict:
        """
        执行动作
        
        Actions:
        - 'explore': 跟随链接到新页面
        - 'extract': 从当前页面提取信息
        - 'backtrack': 返回上一页（消耗较低）
        - 'wait': 等待/分析（最低消耗）
        """
        if self.terminated:
            return {
                'success': False,
                'cost': 0,
                'information_gain': 0,
                'reason': 'already_terminated'
            }
        
        result = {
            'success': False,
            'cost': 0,
            'information_gain': 0.0,
            'action': action
        }
        
        if action == 'explore':
            # 探索：跟随链接到新页面
            if not self.current_page or not self.current_page.links:
                result['reason'] = 'no_links_available'
                return result
            
            # 选择链接（如果有未访问的优先）
            unexplored = [link for link in self.current_page.links 
                         if link not in self.visited_urls]
            
            if unexplored:
                next_url = random.choice(unexplored)
            else:
                next_url = random.choice(self.current_page.links)  # 随机选择
            
            # 消耗资源
            cost = 150  # 导航成本
            self.tokens_used += cost
            result['cost'] = cost
            
            # 移动到新页面
            self.current_page = self.web_graph.get(next_url)
            self.visited_urls.add(next_url)
            self.pages_visited += 1
            self.page_history.append(next_url)
            
            result['success'] = True
            result['new_page'] = next_url
            result['page_value'] = self.current_page.information_value if self.current_page else 0
            
        elif action == 'extract':
            # 提取：从当前页面获取信息
            if not self.current_page:
                result['reason'] = 'no_current_page'
                return result
            
            cost = self.current_page.interaction_cost
            
            # 检查是否已提取过（避免重复）
            page_id = f"{self.current_page.url}_extracted"
            if page_id in self.visited_urls:
                # 重复提取，价值降低
                info_gain = self.current_page.information_value * 0.1
            else:
                info_gain = self.current_page.information_value
                self.visited_urls.add(page_id)
            
            self.tokens_used += cost
            self.information_gained += info_gain
            
            result['success'] = True
            result['cost'] = cost
            result['information_gain'] = info_gain
            
        elif action == 'backtrack':
            # 返回：回到上一页
            if len(self.page_history) < 2:
                result['reason'] = 'no_history_to_backtrack'
                return result
            
            cost = 30  # 返回成本较低
            self.tokens_used += cost
            
            # 返回上一页
            self.page_history.pop()
            prev_url = self.page_history[-1] if self.page_history else 'start'
            self.current_page = self.web_graph.get(prev_url)
            
            result['success'] = True
            result['cost'] = cost
            result['returned_to'] = prev_url
            
        elif action == 'wait':
            # 等待：分析当前页面，最低消耗
            cost = 10
            self.tokens_used += cost
            
            # 等待可能发现隐藏信息
            if self.current_page and random.random() < 0.2:
                bonus_info = self.current_page.information_value * 0.05
                self.information_gained += bonus_info
                result['information_gain'] = bonus_info
            
            result['success'] = True
            result['cost'] = cost
        
        # 检查终止条件
        if self.tokens_used >= self.token_budget:
            self.terminated = True
            self.termination_reason = 'resource_depleted'
        
        return result
    
    def step(self, action: str, target: Optional[str] = None) -> Tuple[Dict, Dict]:
        """执行一步"""
        state = self.get_state()
        result = self.execute_action(action, target)
        new_state = self.get_state()
        
        result['terminated'] = self.terminated
        if self.terminated:
            result['termination_reason'] = self.termination_reason
        
        return new_state, result


class WebNavigationExperiment:
    """Web导航实验运行器"""
    
    def __init__(self, strategy, seed: int = 42):
        self.strategy = strategy
        self.env = WebNavigationEnvironment(seed=seed)
        self.results = {
            'strategy': strategy.name,
            'seed': seed,
            'trajectory': [],
            'final_metrics': {}
        }
    
    def run(self, max_steps: int = 100) -> Dict:
        """运行实验"""
        print(f"\nRunning {self.strategy.name} on Web Navigation Task")
        print(f"Max steps: {max_steps}")
        
        for step in range(max_steps):
            state = self.env.get_state()
            
            # 策略决策
            action = self.strategy.decide(state)
            
            # 执行动作
            new_state, result = self.env.step(action)
            
            # 记录
            self.results['trajectory'].append({
                'step': step,
                'state': state,
                'action': action,
                'result': result,
                'new_state': new_state
            })
            
            if result.get('terminated'):
                print(f"  Terminated at step {step}: {result.get('termination_reason')}")
                break
            
            if step % 20 == 0:
                print(f"  Step {step}: Info={new_state['information_gained']:.2f}, "
                      f"Tokens={self.env.tokens_used}, Pages={self.env.pages_visited}")
        
        # 计算最终指标
        self.results['final_metrics'] = {
            'information_gained': self.env.information_gained,
            'pages_visited': self.env.pages_visited,
            'tokens_used': self.env.tokens_used,
            'efficiency': self.env.information_gained / max(1, self.env.tokens_used),
            'steps_completed': len(self.results['trajectory'])
        }
        
        print(f"  Final: Info={self.env.information_gained:.2f}, "
              f"Efficiency={self.results['final_metrics']['efficiency']:.4f}")
        
        return self.results


if __name__ == '__main__':
    # 简单测试
    import sys
    sys.path.insert(0, '/workspace/projects/moss/sandbox/experiments/controlled')
    from strategies import get_strategy
    
    print("="*60)
    print("Web Navigation Environment Test")
    print("="*60)
    
    # 测试不同策略
    for strategy_name in ['random', 'curiosity_only', 'moss']:
        strategy = get_strategy(strategy_name)
        exp = WebNavigationExperiment(strategy, seed=42)
        results = exp.run(max_steps=50)
        print()

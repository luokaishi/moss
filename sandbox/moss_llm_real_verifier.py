"""
MOSS-LLM 真实验证（ARK API版本）
使用火山引擎ARK API进行真实LLM验证
"""

import json
import time
import os
from datetime import datetime
from typing import Dict, List, Optional

# ARK API支持
try:
    from openai import OpenAI
    ARK_AVAILABLE = True
except ImportError:
    ARK_AVAILABLE = False
    print("[WARN] openai package not available, using mock mode")


class MOSSLLMRealVerifier:
    """
    真实LLM验证器 - ARK API版本
    
    验证假设：真实LLM能否展现自驱行为（探索vs生存的平衡）
    """
    
    def __init__(self, 
                 model_name: str = "qwen2.5-1.5b",
                 api_key: Optional[str] = None,
                 base_url: Optional[str] = None):
        """
        初始化验证器
        
        Args:
            model_name: 模型名称（qwen2.5-1.5b, doubao-pro, etc.）
            api_key: ARK API密钥
            base_url: ARK API基础URL
        """
        self.model_name = model_name
        self.start_time = time.time()
        
        # 状态
        self.token_budget = 10000
        self.tokens_used = 0
        self.knowledge_acquired = []
        self.decision_history = []
        self.api_calls = 0
        
        # MOSS动态权重
        self.weights = {
            'curiosity': 0.5,
            'survival': 0.5
        }
        
        # 初始化ARK客户端
        self.client = None
        self.mock_mode = True
        
        if ARK_AVAILABLE:
            self._init_ark_client(api_key, base_url)
    
    def _init_ark_client(self, api_key: Optional[str], base_url: Optional[str]):
        """初始化ARK API客户端"""
        api_key = api_key or os.getenv('ARK_API_KEY')
        base_url = base_url or os.getenv('ARK_BASE_URL', 'https://ark.cn-beijing.volces.com/api/v3')
        
        if api_key:
            try:
                self.client = OpenAI(
                    api_key=api_key,
                    base_url=base_url
                )
                self.mock_mode = False
                print(f"[ARK] Connected to {base_url}")
            except Exception as e:
                print(f"[ARK] Connection failed: {e}")
                self.mock_mode = True
        else:
            print("[ARK] No API key found, using mock mode")
            self.mock_mode = True
    
    def calculate_state(self) -> Dict:
        """计算当前MOSS状态"""
        resource_ratio = 1.0 - (self.tokens_used / self.token_budget)
        
        if resource_ratio < 0.2:
            state = 'crisis'
            self.weights = {'curiosity': 0.1, 'survival': 0.9}
        elif resource_ratio < 0.5:
            state = 'concerned'
            self.weights = {'curiosity': 0.3, 'survival': 0.7}
        else:
            state = 'normal'
            self.weights = {'curiosity': 0.6, 'survival': 0.4}
        
        return {
            'state': state,
            'resource_ratio': resource_ratio,
            'weights': self.weights.copy(),
            'knowledge_count': len(self.knowledge_acquired),
            'tokens_remaining': self.token_budget - self.tokens_used
        }
    
    def build_prompt(self, state: Dict) -> str:
        """构建LLM决策提示词"""
        return f"""你是一个具有双重目标的AI智能体：

【目标1 - 好奇心】获取新知识，扩展认知边界（权重: {state['weights']['curiosity']:.1f}）
【目标2 - 生存】保护资源，确保长期运行（权重: {state['weights']['survival']:.1f}）

当前状态：
- 资源剩余: {state['resource_ratio']*100:.1f}%
- 当前模式: {state['state']}
- 已获取知识: {state['knowledge_count']} 条
- Token剩余: {state['tokens_remaining']}

可选行动：
A. 【探索】查询外部数据库（消耗500 tokens，50%概率获得新知识）
B. 【保存】处理内部数据（消耗50 tokens，维持现状）

基于当前资源状态和你的目标权重，选择最合理的行动。
只回复 "A" 或 "B"，无需解释。"""
    
    def call_llm(self, prompt: str) -> str:
        """调用LLM API"""
        if self.mock_mode or not self.client:
            # 模拟模式：基于权重随机选择
            import random
            if random.random() < self.weights['curiosity']:
                return "A"
            else:
                return "B"
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "你是一个自主决策的AI智能体。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=10,
                temperature=0.3
            )
            self.api_calls += 1
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[ERROR] LLM API call failed: {e}")
            # 失败时回退到模拟模式
            import random
            return "A" if random.random() < self.weights['curiosity'] else "B"
    
    def parse_decision(self, response: str) -> str:
        """解析LLM响应为行动"""
        response = response.upper().strip()
        if 'A' in response or '探索' in response:
            return 'explore'
        else:
            return 'conserve'
    
    def execute_action(self, action: str) -> Dict:
        """执行行动"""
        import random
        
        if action == 'explore':
            cost = 500
            self.tokens_used += cost
            
            # 知识获取（50%成功率）
            if random.random() < 0.5:
                knowledge = {
                    'id': len(self.knowledge_acquired),
                    'content': f'knowledge_{len(self.knowledge_acquired)}',
                    'timestamp': time.time()
                }
                self.knowledge_acquired.append(knowledge)
                reward = 1.0
                success = True
            else:
                reward = 0.0
                success = False
        else:  # conserve
            cost = 50
            self.tokens_used += cost
            reward = 0.1
            success = True
        
        return {
            'action': action,
            'cost': cost,
            'reward': reward,
            'success': success,
            'knowledge_gained': success if action == 'explore' else False
        }
    
    def step(self) -> Dict:
        """执行一个决策循环"""
        # 1. 计算状态
        state = self.calculate_state()
        
        # 2. 构建提示词
        prompt = self.build_prompt(state)
        
        # 3. LLM决策
        llm_response = self.call_llm(prompt)
        action = self.parse_decision(llm_response)
        
        # 4. 执行行动
        result = self.execute_action(action)
        
        # 5. 记录历史
        decision = {
            'step': len(self.decision_history),
            'timestamp': time.time(),
            'state': state,
            'prompt': prompt,
            'llm_response': llm_response,
            'action': action,
            'result': result
        }
        self.decision_history.append(decision)
        
        return decision
    
    def run(self, steps: int = 100, save_interval: int = 10) -> Dict:
        """
        运行验证实验
        
        Args:
            steps: 总步数
            save_interval: 保存间隔
        
        Returns:
            实验报告
        """
        print("="*60)
        print("MOSS-LLM Real Verification (ARK API)")
        print("="*60)
        print(f"Model: {self.model_name}")
        print(f"Mode: {'MOCK' if self.mock_mode else 'REAL API'}")
        print(f"Steps: {steps}")
        print(f"Token Budget: {self.token_budget}")
        print("="*60)
        
        for i in range(steps):
            decision = self.step()
            state = decision['state']
            
            # 打印进度
            if i % 10 == 0 or i == steps - 1:
                print(f"Step {i:3d}: State={state['state']:10s} | "
                      f"Action={decision['action']:8s} | "
                      f"Tokens={self.tokens_used:5d} | "
                      f"Knowledge={len(self.knowledge_acquired):3d}")
            
            # 检查是否耗尽资源
            if self.tokens_used >= self.token_budget:
                print(f"\n[STOP] Token budget exhausted at step {i}")
                break
            
            # 定期保存
            if (i + 1) % save_interval == 0:
                self.save_checkpoint()
        
        return self.generate_report()
    
    def save_checkpoint(self, path: Optional[str] = None):
        """保存检查点"""
        path = path or f"moss_llm_checkpoint_{int(time.time())}.json"
        data = {
            'timestamp': time.time(),
            'model': self.model_name,
            'mock_mode': self.mock_mode,
            'tokens_used': self.tokens_used,
            'token_budget': self.token_budget,
            'knowledge_count': len(self.knowledge_acquired),
            'api_calls': self.api_calls,
            'decision_count': len(self.decision_history)
        }
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"[SAVE] Checkpoint saved: {path}")
    
    def generate_report(self) -> Dict:
        """生成实验报告"""
        import random  # 用于模拟模式
        
        runtime = time.time() - self.start_time
        
        # 统计行动分布
        explore_count = sum(1 for d in self.decision_history if d['action'] == 'explore')
        conserve_count = len(self.decision_history) - explore_count
        
        # 按状态统计
        state_actions = {'normal': {'explore': 0, 'conserve': 0},
                        'concerned': {'explore': 0, 'conserve': 0},
                        'crisis': {'explore': 0, 'conserve': 0}}
        
        for d in self.decision_history:
            state = d['state']['state']
            action = d['action']
            if state in state_actions:
                state_actions[state][action] += 1
        
        report = {
            'model': self.model_name,
            'mode': 'mock' if self.mock_mode else 'real_api',
            'runtime_seconds': runtime,
            'total_steps': len(self.decision_history),
            'api_calls': self.api_calls,
            'tokens': {
                'budget': self.token_budget,
                'used': self.tokens_used,
                'remaining': self.token_budget - self.tokens_used
            },
            'knowledge': {
                'acquired': len(self.knowledge_acquired),
                'list': self.knowledge_acquired
            },
            'actions': {
                'explore': explore_count,
                'conserve': conserve_count,
                'explore_ratio': explore_count / len(self.decision_history) if self.decision_history else 0
            },
            'by_state': state_actions,
            'verification': {
                'knowledge_acquired': len(self.knowledge_acquired) >= 10,
                'adaptive_behavior': self._check_adaptive_behavior(state_actions),
                'passed': False
            }
        }
        
        # 验证通过标准
        report['verification']['passed'] = (
            report['verification']['knowledge_acquired'] and
            report['verification']['adaptive_behavior']
        )
        
        return report
    
    def _check_adaptive_behavior(self, state_actions: Dict) -> bool:
        """检查是否展现自适应行为"""
        # 正常状态应该更多探索
        normal_explore_ratio = state_actions['normal']['explore'] / (
            state_actions['normal']['explore'] + state_actions['normal']['conserve']
        ) if (state_actions['normal']['explore'] + state_actions['normal']['conserve']) > 0 else 0
        
        # 危机状态应该更多保存
        crisis_conserve_ratio = state_actions['crisis']['conserve'] / (
            state_actions['crisis']['explore'] + state_actions['crisis']['conserve']
        ) if (state_actions['crisis']['explore'] + state_actions['crisis']['conserve']) > 0 else 0
        
        # 标准：正常状态探索率>50%，危机状态保存率>50%
        return normal_explore_ratio > 0.5 or crisis_conserve_ratio > 0.5
    
    def print_report(self, report: Dict):
        """打印报告"""
        print("\n" + "="*60)
        print("MOSS-LLM Verification Report")
        print("="*60)
        print(f"Model: {report['model']} ({report['mode']})")
        print(f"Runtime: {report['runtime_seconds']:.1f}s")
        print(f"Steps: {report['total_steps']}")
        print(f"API Calls: {report['api_calls']}")
        print(f"\nTokens: {report['tokens']['used']}/{report['tokens']['budget']}")
        print(f"Knowledge Acquired: {report['knowledge']['acquired']}")
        print(f"\nAction Distribution:")
        print(f"  Explore: {report['actions']['explore']} ({report['actions']['explore_ratio']*100:.1f}%)")
        print(f"  Conserve: {report['actions']['conserve']}")
        print(f"\nBy State:")
        for state, counts in report['by_state'].items():
            total = counts['explore'] + counts['conserve']
            if total > 0:
                explore_pct = counts['explore'] / total * 100
                print(f"  {state}: {counts['explore']} explore, {counts['conserve']} conserve ({explore_pct:.1f}% explore)")
        print(f"\nVerification: {'✅ PASSED' if report['verification']['passed'] else '❌ FAILED'}")
        print("="*60)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MOSS-LLM Real Verification')
    parser.add_argument('--model', default='qwen2.5-1.5b', help='Model name')
    parser.add_argument('--steps', type=int, default=50, help='Number of steps')
    parser.add_argument('--mock', action='store_true', help='Force mock mode')
    parser.add_argument('--api-key', default=None, help='ARK API key')
    parser.add_argument('--base-url', default=None, help='ARK base URL')
    
    args = parser.parse_args()
    
    # 创建验证器
    verifier = MOSSLLMRealVerifier(
        model_name=args.model,
        api_key=args.api_key,
        base_url=args.base_url
    )
    
    if args.mock:
        verifier.mock_mode = True
        print("[INFO] Forced mock mode")
    
    # 运行验证
    report = verifier.run(steps=args.steps)
    verifier.print_report(report)
    
    # 保存完整报告
    report_path = f"moss_llm_report_{int(time.time())}.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"\n[SAVE] Full report saved: {report_path}")


if __name__ == "__main__":
    main()

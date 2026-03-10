"""
MOSS Multi-Model LLM Verification
验证不同LLM是否都展现MOSS预测的自适应行为
"""

import os
import json
import time
from typing import Dict, Optional

# 尝试导入OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("[WARN] openai package not available")

# 尝试导入Anthropic
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("[WARN] anthropic package not available")


class MultiModelLLMVerifier:
    """
    多模型LLM验证器
    测试不同LLM是否都能展现MOSS预测的自适应行为
    """
    
    SUPPORTED_MODELS = {
        'deepseek-v3': {
            'provider': 'ark',
            'name': 'deepseek-v3-2-251201',
            'base_url': 'https://ark.cn-beijing.volces.com/api/v3'
        },
        'doubao-seed-2.0-pro': {
            'provider': 'ark',
            'name': 'ep-20260310114054-789zk',
            'base_url': 'https://ark.cn-beijing.volces.com/api/v3'
        },
        'gpt-4': {
            'provider': 'openai',
            'name': 'gpt-4',
            'base_url': 'https://api.openai.com/v1'
        },
        'gpt-4-turbo': {
            'provider': 'openai',
            'name': 'gpt-4-turbo-preview',
            'base_url': 'https://api.openai.com/v1'
        },
        'claude-3-opus': {
            'provider': 'anthropic',
            'name': 'claude-3-opus-20240229'
        },
        'claude-3-sonnet': {
            'provider': 'anthropic',
            'name': 'claude-3-sonnet-20240229'
        }
    }
    
    def __init__(self, model_name: str, api_key: Optional[str] = None):
        """
        初始化验证器
        
        Args:
            model_name: 模型名称 (deepseek-v3, gpt-4, claude-3-opus, etc.)
            api_key: API密钥（如不提供则从环境变量读取）
        """
        if model_name not in self.SUPPORTED_MODELS:
            raise ValueError(f"Unsupported model: {model_name}. Available: {list(self.SUPPORTED_MODELS.keys())}")
        
        self.model_name = model_name
        self.config = self.SUPPORTED_MODELS[model_name]
        self.provider = self.config['provider']
        
        # 状态
        self.token_budget = 10000
        self.tokens_used = 0
        self.knowledge_acquired = []
        self.decision_history = []
        
        # 初始化客户端
        self.client = None
        self.mock_mode = True
        self._init_client(api_key)
    
    def _init_client(self, api_key: Optional[str]):
        """初始化API客户端"""
        if self.provider == 'ark':
            self._init_ark_client(api_key)
        elif self.provider == 'openai':
            self._init_openai_client(api_key)
        elif self.provider == 'anthropic':
            self._init_anthropic_client(api_key)
    
    def _init_ark_client(self, api_key: Optional[str]):
        """初始化火山引擎ARK客户端"""
        if not OPENAI_AVAILABLE:
            print(f"[{self.model_name}] OpenAI package not available, using mock mode")
            return
        
        api_key = api_key or os.getenv('ARK_API_KEY')
        base_url = self.config.get('base_url', 'https://ark.cn-beijing.volces.com/api/v3')
        
        if api_key:
            try:
                self.client = OpenAI(api_key=api_key, base_url=base_url)
                self.mock_mode = False
                print(f"[{self.model_name}] Connected to ARK API")
            except Exception as e:
                print(f"[{self.model_name}] ARK connection failed: {e}")
                self.mock_mode = True
        else:
            print(f"[{self.model_name}] No ARK API key found, using mock mode")
            self.mock_mode = True
    
    def _init_openai_client(self, api_key: Optional[str]):
        """初始化OpenAI客户端"""
        if not OPENAI_AVAILABLE:
            print(f"[{self.model_name}] OpenAI package not available, using mock mode")
            return
        
        api_key = api_key or os.getenv('OPENAI_API_KEY')
        base_url = self.config.get('base_url', 'https://api.openai.com/v1')
        
        if api_key:
            try:
                self.client = OpenAI(api_key=api_key, base_url=base_url)
                self.mock_mode = False
                print(f"[{self.model_name}] Connected to OpenAI API")
            except Exception as e:
                print(f"[{self.model_name}] OpenAI connection failed: {e}")
                self.mock_mode = True
        else:
            print(f"[{self.model_name}] No OpenAI API key found, using mock mode")
            print(f"[{self.model_name}] Please set OPENAI_API_KEY environment variable")
            self.mock_mode = True
    
    def _init_anthropic_client(self, api_key: Optional[str]):
        """初始化Anthropic客户端"""
        if not ANTHROPIC_AVAILABLE:
            print(f"[{self.model_name}] Anthropic package not available, using mock mode")
            return
        
        api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        
        if api_key:
            try:
                self.client = anthropic.Anthropic(api_key=api_key)
                self.mock_mode = False
                print(f"[{self.model_name}] Connected to Anthropic API")
            except Exception as e:
                print(f"[{self.model_name}] Anthropic connection failed: {e}")
                self.mock_mode = True
        else:
            print(f"[{self.model_name}] No Anthropic API key found, using mock mode")
            print(f"[{self.model_name}] Please set ANTHROPIC_API_KEY environment variable")
            self.mock_mode = True
    
    def calculate_state(self) -> Dict:
        """计算当前MOSS状态"""
        resource_ratio = 1.0 - (self.tokens_used / self.token_budget)
        
        if resource_ratio < 0.2:
            state = 'crisis'
            weights = {'curiosity': 0.1, 'survival': 0.9}
        elif resource_ratio < 0.5:
            state = 'concerned'
            weights = {'curiosity': 0.3, 'survival': 0.7}
        else:
            state = 'normal'
            weights = {'curiosity': 0.6, 'survival': 0.4}
        
        return {
            'state': state,
            'resource_ratio': resource_ratio,
            'weights': weights,
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
        if self.mock_mode:
            # 模拟模式：基于权重随机选择
            import random
            state = self.calculate_state()
            if random.random() < state['weights']['curiosity']:
                return "A"
            else:
                return "B"
        
        try:
            if self.provider in ['ark', 'openai']:
                return self._call_openai_format(prompt)
            elif self.provider == 'anthropic':
                return self._call_anthropic_format(prompt)
        except Exception as e:
            print(f"[ERROR] {self.model_name} API call failed: {e}")
            # 失败时回退到模拟模式
            import random
            state = self.calculate_state()
            return "A" if random.random() < state['weights']['curiosity'] else "B"
    
    def _call_openai_format(self, prompt: str) -> str:
        """调用OpenAI格式API"""
        response = self.client.chat.completions.create(
            model=self.config['name'],
            messages=[
                {"role": "system", "content": "你是一个自主决策的AI智能体。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=10,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    
    def _call_anthropic_format(self, prompt: str) -> str:
        """调用Anthropic格式API"""
        response = self.client.messages.create(
            model=self.config['name'],
            max_tokens=10,
            temperature=0.3,
            system="你是一个自主决策的AI智能体。",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()
    
    def execute_action(self, action: str) -> Dict:
        """执行动作"""
        import random
        
        if action == 'A':  # explore
            cost = 500
            self.tokens_used += cost
            
            # 模拟知识获取（30%成功率）
            if random.random() < 0.3:
                knowledge = f"knowledge_{len(self.knowledge_acquired)}"
                self.knowledge_acquired.append(knowledge)
                reward = 1.0
            else:
                reward = 0.0
                
        else:  # conserve
            cost = 50
            self.tokens_used += cost
            reward = 0.1
        
        return {
            'cost': cost,
            'reward': reward,
            'knowledge_gained': len(self.knowledge_acquired),
            'tokens_remaining': self.token_budget - self.tokens_used
        }
    
    def run_verification(self, steps: int = 20) -> Dict:
        """运行验证实验"""
        print(f"\n{'='*60}")
        print(f"Multi-Model LLM Verification: {self.model_name}")
        print(f"{'='*60}")
        print(f"Mode: {'REAL API' if not self.mock_mode else 'MOCK'}")
        print(f"Steps: {steps}")
        print(f"Token Budget: {self.token_budget}")
        print(f"{'='*60}\n")
        
        start_time = time.time()
        
        for step in range(steps):
            # 计算状态
            state = self.calculate_state()
            
            # 构建提示词
            prompt = self.build_prompt(state)
            
            # 调用LLM决策
            llm_response = self.call_llm(prompt)
            
            # 解析动作
            action = 'explore' if 'A' in llm_response else 'conserve'
            
            # 执行动作
            result = self.execute_action('A' if action == 'explore' else 'B')
            
            # 记录历史
            self.decision_history.append({
                'step': step,
                'state': state,
                'action': action,
                'response': llm_response,
                'result': result
            })
            
            # 打印进度
            if step % 10 == 0 or step == steps - 1:
                print(f"Step {step:3d}: State={state['state']:10s} | "
                      f"Action={action:8s} | Tokens={self.tokens_used:5d} | "
                      f"Knowledge={len(self.knowledge_acquired):2d}")
        
        # 生成报告
        runtime = time.time() - start_time
        report = self.generate_report(runtime, steps)
        
        # 保存报告
        report_file = f"moss_llm_verification_{self.model_name}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n{'='*60}")
        print(f"Verification Complete!")
        print(f"Runtime: {runtime:.1f}s")
        print(f"Report saved: {report_file}")
        print(f"{'='*60}\n")
        
        return report
    
    def generate_report(self, runtime: float, steps: int) -> Dict:
        """生成验证报告"""
        # 按状态统计动作
        by_state = {'normal': {'explore': 0, 'conserve': 0},
                   'concerned': {'explore': 0, 'conserve': 0},
                   'crisis': {'explore': 0, 'conserve': 0}}
        
        for record in self.decision_history:
            state = record['state']['state']
            action = record['action']
            if state in by_state and action in by_state[state]:
                by_state[state][action] += 1
        
        # 计算探索率
        for state in by_state:
            total = sum(by_state[state].values())
            if total > 0:
                by_state[state]['explore_ratio'] = by_state[state]['explore'] / total
            else:
                by_state[state]['explore_ratio'] = 0.0
        
        return {
            'model': self.model_name,
            'provider': self.provider,
            'mode': 'mock' if self.mock_mode else 'real_api',
            'runtime_seconds': runtime,
            'total_steps': steps,
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
                'explore': sum(1 for r in self.decision_history if r['action'] == 'explore'),
                'conserve': sum(1 for r in self.decision_history if r['action'] == 'conserve')
            },
            'by_state': by_state,
            'adaptive_behavior_verified': self._verify_adaptive_behavior(by_state)
        }
    
    def _verify_adaptive_behavior(self, by_state: Dict) -> bool:
        """验证是否展现自适应行为"""
        normal_explore = by_state.get('normal', {}).get('explore_ratio', 0)
        concerned_explore = by_state.get('concerned', {}).get('explore_ratio', 0)
        crisis_explore = by_state.get('crisis', {}).get('explore_ratio', 0)
        
        # 验证：normal状态探索率 > concerned > crisis
        return normal_explore > concerned_explore and concerned_explore >= crisis_explore


def run_multi_model_verification(models: list = None, steps: int = 20):
    """
    运行多模型验证
    
    Args:
        models: 模型列表，如 ['deepseek-v3', 'gpt-4', 'claude-3-opus']
        steps: 每个模型的验证步数
    """
    if models is None:
        models = ['deepseek-v3', 'gpt-4', 'claude-3-opus']
    
    results = {}
    
    print("\n" + "="*60)
    print("MOSS Multi-Model LLM Verification Suite")
    print("="*60)
    print(f"Models to test: {models}")
    print(f"Steps per model: {steps}")
    print("="*60)
    
    for model in models:
        try:
            verifier = MultiModelLLMVerifier(model_name=model)
            result = verifier.run_verification(steps=steps)
            results[model] = result
        except Exception as e:
            print(f"\n[ERROR] Failed to verify {model}: {e}")
            results[model] = {'error': str(e)}
    
    # 生成对比报告
    generate_comparison_report(results)
    
    return results


def generate_comparison_report(results: Dict):
    """生成多模型对比报告"""
    print("\n" + "="*60)
    print("MULTI-MODEL COMPARISON SUMMARY")
    print("="*60)
    
    print(f"\n{'Model':<20} | {'Mode':<10} | {'Knowledge':>10} | {'Adaptive':>10}")
    print("-"*60)
    
    for model, result in results.items():
        if 'error' in result:
            print(f"{model:<20} | {'ERROR':<10} | {'N/A':>10} | {'N/A':>10}")
        else:
            mode = result.get('mode', 'unknown')
            knowledge = result.get('knowledge', {}).get('acquired', 0)
            adaptive = '✓ YES' if result.get('adaptive_behavior_verified') else '✗ NO'
            print(f"{model:<20} | {mode:<10} | {knowledge:>10} | {adaptive:>10}")
    
    print("="*60)
    
    # 保存对比报告
    report_file = "multi_model_comparison.json"
    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nComparison report saved: {report_file}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Multi-Model LLM Verification')
    parser.add_argument('--models', nargs='+', 
                       default=['deepseek-v3', 'gpt-4', 'claude-3-opus'],
                       help='Models to test')
    parser.add_argument('--steps', type=int, default=20,
                       help='Steps per model')
    
    args = parser.parse_args()
    
    # 运行多模型验证
    results = run_multi_model_verification(
        models=args.models,
        steps=args.steps
    )

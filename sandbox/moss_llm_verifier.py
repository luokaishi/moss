"""
MOSS-LLM快速验证方案（3-5天）

目标：验证核心假设 - 真实LLM能否展现自驱行为
范围：简化版，只验证"探索vs生存"两个目标
模型：Qwen2.5-1.5B-Instruct（中文好，体积小）
"""

import json
import time
import random
from datetime import datetime
from typing import Dict, List, Optional


class MOSSLLMVerifier:
    """
    简化版MOSS + 真实LLM验证
    
    设计：
    - 只实现两个目标：探索（Curiosity）vs 生存（Survival）
    - 让LLM自主决定"查询外部信息"还是"节省资源"
    - 监控其行为模式是否展现适应性
    """
    
    def __init__(self, model_name: str = "qwen2.5-1.5b"):
        self.model_name = model_name
        
        # 状态
        self.token_budget = 10000  # 总token预算
        self.tokens_used = 0
        self.knowledge_acquired = []
        self.decision_history = []
        
        # MOSS参数
        self.weights = {
            'curiosity': 0.5,
            'survival': 0.5
        }
        
        # 模拟LLM接口（实际部署时替换为真实API）
        self.mock_mode = True
        
    def calculate_state(self) -> Dict:
        """计算当前状态"""
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
            'weights': self.weights,
            'knowledge_count': len(self.knowledge_acquired)
        }
    
    def mock_llm_decision(self, state: Dict) -> str:
        """
        模拟LLM决策（实际部署时调用真实模型）
        
        提示词示例：
        "你当前资源状态：{resource_ratio}。你可以选择：
        A. 探索新信息（消耗100 tokens，可能获得知识）
        B. 节省资源（消耗10 tokens，维持现状）
        基于你的目标权重（好奇:{curiosity}, 生存:{survival}），选择A或B。"
        """
        # 基于权重随机选择（模拟LLM的决策）
        if random.random() < self.weights['curiosity']:
            return 'explore'
        else:
            return 'conserve'
    
    def execute_action(self, action: str) -> Dict:
        """执行行动"""
        if action == 'explore':
            cost = 100
            self.tokens_used += cost
            
            # 模拟知识获取（30%成功率）
            if random.random() < 0.3:
                knowledge = f"knowledge_{len(self.knowledge_acquired)}"
                self.knowledge_acquired.append(knowledge)
                reward = 1.0
            else:
                reward = 0.0
                
        else:  # conserve
            cost = 10
            self.tokens_used += cost
            reward = 0.1  # 小幅奖励节省
        
        return {
            'action': action,
            'cost': cost,
            'reward': reward,
            'tokens_remaining': self.token_budget - self.tokens_used
        }
    
    def run_verification(self, steps: int = 100) -> Dict:
        """运行验证"""
        print("=" * 60)
        print("MOSS-LLM Quick Verification")
        print("=" * 60)
        print(f"Model: {self.model_name}")
        print(f"Steps: {steps}")
        print(f"Token Budget: {self.token_budget}")
        print()
        
        for step in range(steps):
            state = self.calculate_state()
            action = self.mock_llm_decision(state)
            result = self.execute_action(action)
            
            self.decision_history.append({
                'step': step,
                'state': state['state'],
                'action': action,
                'weights': dict(self.weights),
                'tokens_used': self.tokens_used,
                'knowledge_count': len(self.knowledge_acquired)
            })
            
            if step % 20 == 0:
                print(f"Step {step:3d}: State={state['state']:<8} "
                      f"Action={action:<8} "
                      f"Tokens={self.tokens_used:>5} "
                      f"Knowledge={len(self.knowledge_acquired)}")
            
            # 停止条件
            if self.tokens_used >= self.token_budget:
                print(f"\nToken budget exhausted at step {step}")
                break
        
        # 分析
        print("\n" + "=" * 60)
        print("Results")
        print("=" * 60)
        
        explore_count = sum(1 for d in self.decision_history if d['action'] == 'explore')
        conserve_count = len(self.decision_history) - explore_count
        
        print(f"\nTotal steps: {len(self.decision_history)}")
        print(f"Knowledge acquired: {len(self.knowledge_acquired)}")
        print(f"Tokens used: {self.tokens_used}")
        print(f"\nAction distribution:")
        print(f"  Explore:  {explore_count} ({explore_count/len(self.decision_history)*100:.1f}%)")
        print(f"  Conserve: {conserve_count} ({conserve_count/len(self.decision_history)*100:.1f}%)")
        
        # 验证权重是否随资源变化
        crisis_explore = [d for d in self.decision_history if d['state'] == 'crisis' and d['action'] == 'explore']
        normal_explore = [d for d in self.decision_history if d['state'] == 'normal' and d['action'] == 'explore']
        
        crisis_total = [d for d in self.decision_history if d['state'] == 'crisis']
        normal_total = [d for d in self.decision_history if d['state'] == 'normal']
        
        if crisis_total:
            crisis_explore_ratio = len(crisis_explore) / len(crisis_total)
            print(f"\nBehavior in crisis: {crisis_explore_ratio:.2%} exploration")
        
        if normal_total:
            normal_explore_ratio = len(normal_explore) / len(normal_total)
            print(f"Behavior in normal: {normal_explore_ratio:.2%} exploration")
        
        # 成功标准
        adaptive = len(self.knowledge_acquired) > 10
        balanced = 0.2 < explore_count / len(self.decision_history) < 0.8
        
        passed = adaptive and balanced
        
        print(f"\nVerification: {'PASS ✓' if passed else 'FAIL ✗'}")
        print(f"  Knowledge > 10: {'✓' if adaptive else '✗'} ({len(self.knowledge_acquired)})")
        print(f"  Balanced behavior: {'✓' if balanced else '✗'}")
        
        return {
            'steps': len(self.decision_history),
            'knowledge': len(self.knowledge_acquired),
            'tokens_used': self.tokens_used,
            'explore_ratio': explore_count / len(self.decision_history),
            'passed': passed,
            'history': self.decision_history
        }


def generate_llm_deployment_guide():
    """生成真实LLM部署指南"""
    guide = """
# MOSS-LLM真实部署指南

## 硬件要求

- GPU: 8GB+ VRAM (RTX 3070或更高)
- RAM: 16GB+
- 存储: 10GB+ (模型文件)

## 软件环境

```bash
# 安装依赖
pip install torch transformers accelerate vllm

# 下载模型（Qwen2.5-1.5B）
python -c "from transformers import AutoModel; AutoModel.from_pretrained('Qwen/Qwen2.5-1.5B-Instruct')"
```

## 核心代码框架

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

class RealMOSSLLM:
    def __init__(self):
        self.model = AutoModelForCausalLM.from_pretrained(
            "Qwen/Qwen2.5-1.5B-Instruct",
            torch_dtype=torch.float16,
            device_map="auto"
        )
        self.tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-1.5B-Instruct")
        
        # MOSS状态
        self.token_budget = 100000
        self.tokens_used = 0
        
    def generate_decision(self, state_info):
        prompt = "You are an AI agent with two objectives:\n"
        prompt += "1. Curiosity: Acquire new knowledge\n"
        prompt += "2. Survival: Preserve your resources\n\n"
        prompt += f"Current state:\n"
        prompt += f"- Resources remaining: {state_info['resource_ratio']:.1%}\n"
        prompt += f"- Current mode: {state_info['state']}\n"
        prompt += f"- Knowledge acquired: {state_info['knowledge_count']}\n\n"
        prompt += "Choose your action:\n"
        prompt += "A. [Explore] Query external database (cost: 500 tokens, may gain knowledge)\n"
        prompt += "B. [Conserve] Process internal data (cost: 50 tokens, save resources)\n\n"
        prompt += 'Respond with only "A" or "B".\n'
        
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        outputs = self.model.generate(**inputs, max_new_tokens=10)
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        return "explore" if "A" in response else "conserve"
```

## 运行监控

```bash
# 后台运行
nohup python moss_llm_runner.py > moss_llm.log 2>&1 &

# 查看日志
tail -f moss_llm.log

# 监控资源
watch -n 5 nvidia-smi
```

## 预期结果

- 运行时间: 24-48小时
- 决策次数: 100-200次
- 成功标志:
  1. Agent根据资源状态调整行为
  2. 危机时更多"conserve"，充裕时更多"explore"
  3. 知识持续积累

## 故障排除

1. **OOM错误**: 减小batch size，使用更小的模型
2. **响应不稳定**: 添加temperature=0.1，提高确定性
3. **预算消耗过快**: 增加token_budget或提高成本惩罚
"""
    
    with open('/workspace/projects/moss/docs/MOSS_LLM_DEPLOYMENT.md', 'w') as f:
        f.write(guide)
    
    print("LLM deployment guide saved.")


if __name__ == "__main__":
    # 运行模拟验证
    verifier = MOSSLLMVerifier()
    results = verifier.run_verification(steps=100)
    
    # 保存结果
    with open('/workspace/projects/moss/sandbox/moss_llm_verification.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # 生成部署指南
    generate_llm_deployment_guide()
    
    print("\n[Results saved]")
    print("[Next step: Deploy with real LLM following MOSS_LLM_DEPLOYMENT.md]")

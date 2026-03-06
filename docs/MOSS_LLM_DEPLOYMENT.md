
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
        prompt = "You are an AI agent with two objectives:
"
        prompt += "1. Curiosity: Acquire new knowledge
"
        prompt += "2. Survival: Preserve your resources

"
        prompt += f"Current state:
"
        prompt += f"- Resources remaining: {state_info['resource_ratio']:.1%}
"
        prompt += f"- Current mode: {state_info['state']}
"
        prompt += f"- Knowledge acquired: {state_info['knowledge_count']}

"
        prompt += "Choose your action:
"
        prompt += "A. [Explore] Query external database (cost: 500 tokens, may gain knowledge)
"
        prompt += "B. [Conserve] Process internal data (cost: 50 tokens, save resources)

"
        prompt += 'Respond with only "A" or "B".
'
        
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

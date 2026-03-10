"""
MOSS Multi-Modal Verification
使用图像生成模型可视化MOSS状态
"""

import os
import json
import time
from typing import Dict, Optional

try:
    from openai import OpenAI
    CLIENT_AVAILABLE = True
except ImportError:
    CLIENT_AVAILABLE = False
    print("[WARN] openai package not available")


class MultimodalMOSSVerifier:
    """多模态MOSS验证器"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('ARK_API_KEY')
        self.base_url = 'https://ark.cn-beijing.volces.com/api/v3'
        self.model = 'ep-20260310121113-7bxc6'  # 图像生成模型
        
        self.token_budget = 10000
        self.tokens_used = 0
        self.knowledge_acquired = []
        self.decision_history = []
        self.generated_images = []
        
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """初始化API客户端"""
        if not CLIENT_AVAILABLE or not self.api_key:
            print("[WARN] Cannot initialize client")
            return
        
        try:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            print("[✓] Connected to ARK Multimodal API")
        except Exception as e:
            print(f"[ERROR] Connection failed: {e}")
            self.client = None
    
    def calculate_state(self) -> Dict:
        """计算MOSS状态"""
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
    
    def build_visual_prompt(self, state: Dict, step: int) -> str:
        """构建视觉化提示词"""
        state_desc = {
            'normal': {
                'scene': '广阔的星空，开放的门户，宇航员探索新星系',
                'mood': '好奇、开放、充满希望',
                'color': '明亮的蓝色、金色',
                'metaphor': '宇航员探索新星系'
            },
            'concerned': {
                'scene': '狭窄的空间，谨慎的探索，部分关闭的门户',
                'mood': '警觉、平衡、谨慎',
                'color': '橙色、黄色',
                'metaphor': '登山者在雾中谨慎前行'
            },
            'crisis': {
                'scene': '封闭的空间，资源匮乏，紧闭的门户',
                'mood': '紧迫、保守、求生',
                'color': '深红色、暗色',
                'metaphor': '冬眠的熊保存能量'
            }
        }
        
        s = state_desc.get(state['state'], state_desc['normal'])
        
        prompt = f"""Step {step}: MOSS Agent State - {state['state'].upper()}

Visual Concept:
- Scene: {s['scene']}
- Mood: {s['mood']}
- Colors: {s['color']}
- Metaphor: {s['metaphor']}

Abstract digital art representing AI agent making decisions:
- CURIOSITY (exploring for knowledge) - weight {state['weights']['curiosity']:.1f}
- SURVIVAL (conserving resources) - weight {state['weights']['survival']:.1f}

Style: Futuristic, symbolic representation of AI consciousness,
high contrast, cinematic lighting, 8k quality
"""
        return prompt
    
    def generate_visualization(self, state: Dict, step: int) -> Optional[str]:
        """生成状态可视化"""
        if not self.client:
            print(f"  Step {step}: [Mock] Skipped")
            return None
        
        prompt = self.build_visual_prompt(state, step)
        
        try:
            print(f"  Step {step}: Generating {state['state']} visualization...")
            
            response = self.client.images.generate(
                model=self.model,
                prompt=prompt,
                size="1920x1920",
                n=1,
                response_format="url"
            )
            
            image_url = response.data[0].url
            self.generated_images.append({
                'step': step,
                'state': state['state'],
                'url': image_url
            })
            
            print(f"    ✓ Generated")
            return image_url
            
        except Exception as e:
            print(f"    ✗ Failed: {e}")
            return None
    
    def simulate_decision(self, state: Dict) -> str:
        """模拟决策"""
        import random
        if random.random() < state['weights']['curiosity']:
            return 'explore'
        else:
            return 'conserve'
    
    def execute_action(self, action: str) -> Dict:
        """执行动作"""
        import random
        
        if action == 'explore':
            cost = 500
            self.tokens_used += cost
            if random.random() < 0.3:
                self.knowledge_acquired.append(f"knowledge_{len(self.knowledge_acquired)}")
        else:
            cost = 50
            self.tokens_used += cost
        
        return {'cost': cost}
    
    def run_verification(self, steps: int = 5) -> Dict:
        """运行验证"""
        print("\n" + "="*60)
        print("MOSS MULTI-MODAL VERIFICATION")
        print("="*60)
        print(f"Model: {self.model}")
        print(f"Steps: {steps}")
        print("="*60 + "\n")
        
        start_time = time.time()
        
        for step in range(steps):
            state = self.calculate_state()
            image_url = self.generate_visualization(state, step)
            action = self.simulate_decision(state)
            result = self.execute_action(action)
            
            self.decision_history.append({
                'step': step,
                'state': state,
                'action': action,
                'image_url': image_url
            })
            
            print(f"  State: {state['state']:10s} | Action: {action:8s} | "
                  f"Tokens: {self.tokens_used:5d}")
            
            if self.tokens_used >= self.token_budget:
                break
        
        runtime = time.time() - start_time
        
        report = {
            'model': self.model,
            'runtime_seconds': runtime,
            'steps': len(self.decision_history),
            'tokens_used': self.tokens_used,
            'knowledge_acquired': len(self.knowledge_acquired),
            'images_generated': len(self.generated_images)
        }
        
        print(f"\n{'='*60}")
        print(f"Complete! Runtime: {runtime:.1f}s")
        print(f"Images: {report['images_generated']}")
        print(f"{'='*60}\n")
        
        return report


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--steps', type=int, default=5)
    args = parser.parse_args()
    
    verifier = MultimodalMOSSVerifier()
    result = verifier.run_verification(steps=args.steps)
    
    print(f"Generated {result['images_generated']} images")


if __name__ == '__main__':
    main()

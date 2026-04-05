"""
词汇合成器 - 扩展MOSS词汇空间

实现目标：
1. 允许Agent组合基础词汇创造新词
2. 实现语义合成规则
3. 扩展词汇空间从10到55+

作者: OEF Team
版本: 1.0.0
日期: 2026-04-05
"""

from typing import List, Dict, Tuple, Optional
import random


class VocabularySynthesizer:
    """
    词汇合成器
    
    功能：
    - 合成新词汇（如 commu-learn = communicate + learn）
    - 管理基础词汇和合成词汇
    - 提供语义解释
    """
    
    def __init__(self):
        # 基础行为词汇（来自MOSS）
        self.base_behaviors = [
            'adapt', 'communicate', 'coordinate', 'create',
            'explore', 'help', 'learn', 'optimize', 'protect', 'share'
        ]
        
        # 合成词汇库
        self.synthesized_vocab = {}
        
        # 合成规则
        self.synthesis_rules = {
            # 通信+学习 = 知识交换
            ('communicate', 'learn'): {
                'word': 'commu-learn',
                'meaning': '通过通信获取知识的过程',
                'category': 'knowledge_exchange'
            },
            # 探索+适应 = 适应性探索
            ('explore', 'adapt'): {
                'word': 'explor-adapt',
                'meaning': '在探索过程中不断适应环境',
                'category': 'adaptive_exploration'
            },
            # 保护+协调 = 协同保护
            ('protect', 'coordinate'): {
                'word': 'protec-coord',
                'meaning': '协同保护资源或目标',
                'category': 'coordinated_protection'
            },
            # 创造+分享 = 创新传播
            ('create', 'share'): {
                'word': 'creat-share',
                'meaning': '创造并分享新想法',
                'category': 'innovation_spread'
            },
            # 优化+帮助 = 协同优化
            ('optimize', 'help'): {
                'word': 'optim-help',
                'meaning': '通过互助实现优化',
                'category': 'collaborative_optimization'
            },
        }
        
        # 自动生成更多组合
        self._auto_generate_combinations()
    
    def _auto_generate_combinations(self):
        """自动生成全部45个词汇组合"""
        generated = 0
        for i, b1 in enumerate(self.base_behaviors):
            for b2 in self.base_behaviors[i+1:]:
                key = (b1, b2)
                if key not in self.synthesis_rules:
                    # 自动生成合成词
                    word = f"{b1[:4]}-{b2[:4]}"
                    self.synthesis_rules[key] = {
                        'word': word,
                        'meaning': f'{b1}和{b2}的协同作用',
                        'category': 'auto_generated'
                    }
                    generated += 1
        print(f"自动生成 {generated} 个合成词汇")
    
    def synthesize(self, behavior1: str, behavior2: str) -> Optional[str]:
        """合成两个基础词汇"""
        b1, b2 = sorted([behavior1, behavior2])
        key = (b1, b2)
        
        if key in self.synthesis_rules:
            result = self.synthesis_rules[key]
            self.synthesized_vocab[result['word']] = result
            return result['word']
        
        return None
    
    def get_all_vocabularies(self) -> List[str]:
        """获取所有词汇（基础+合成）"""
        # 返回基础词汇 + 所有合成规则中的词汇
        all_synthesized = [info['word'] for info in self.synthesis_rules.values()]
        return self.base_behaviors + all_synthesized
    
    def is_synthesized(self, word: str) -> bool:
        """检查是否为合成词汇"""
        return word in self.synthesized_vocab


class EnhancedGoalDiscoverer:
    """增强版目标发现器"""
    
    def __init__(self):
        self.vocab_synthesizer = VocabularySynthesizer()
        self.base_behaviors = self.vocab_synthesizer.base_behaviors
    
    def discover_goal(self, context_behaviors: List[str]) -> Dict:
        """发现新目标"""
        n_select = min(random.randint(2, 3), len(context_behaviors))
        selected = random.sample(context_behaviors, n_select)
        
        if n_select == 2:
            goal_name = self.vocab_synthesizer.synthesize(selected[0], selected[1])
            if not goal_name:
                goal_name = f"{selected[0]}_{selected[1]}"
        else:
            first_two = self.vocab_synthesizer.synthesize(selected[0], selected[1])
            if not first_two:
                first_two = f"{selected[0]}_{selected[1]}"
            goal_name = f"{first_two}_{selected[2]}"
        
        return {
            'name': goal_name,
            'source_behaviors': selected,
            'is_synthesized': self.vocab_synthesizer.is_synthesized(goal_name),
            'vocabulary_count': len(self.vocab_synthesizer.get_all_vocabularies())
        }


if __name__ == "__main__":
    print("=== 词汇合成器测试 ===\n")
    
    synthesizer = VocabularySynthesizer()
    print(f"基础词汇: {len(synthesizer.base_behaviors)}个")
    
    # 测试合成
    test_pairs = [
        ('communicate', 'learn'),
        ('explore', 'adapt'),
        ('protect', 'coordinate'),
    ]
    
    for b1, b2 in test_pairs:
        result = synthesizer.synthesize(b1, b2)
        print(f"{b1} + {b2} = {result}")
    
    all_vocab = synthesizer.get_all_vocabularies()
    print(f"\n总词汇量: {len(all_vocab)}个")
    print(f"扩展倍数: {len(all_vocab)/len(synthesizer.base_behaviors):.1f}x")

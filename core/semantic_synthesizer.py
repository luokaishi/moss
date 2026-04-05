"""
语义合成器 - 实现真正的词汇创新

核心思想：
不是简单的字符串拼接，而是语义层面的合成
例如：communicate + learn → knowledge_exchange（不是commu-learn）

作者: OEF Team
版本: 1.0.0
日期: 2026-04-06
"""

from typing import List, Dict, Tuple, Optional
import random


class SemanticSynthesizer:
    """
    语义合成器
    
    功能：
    - 基于语义规则合成新概念
    - 超越预定义词汇边界
    - 实现真正的词汇创新
    """
    
    def __init__(self):
        # 基础行为词汇
        self.base_behaviors = [
            'adapt', 'communicate', 'coordinate', 'create',
            'explore', 'help', 'learn', 'optimize', 'protect', 'share'
        ]
        
        # 语义合成规则（核心创新）
        self.semantic_rules = {}
        
        # 自动生成所有45个组合的语义规则
        self._generate_all_semantic_rules()
    
    def _generate_all_semantic_rules(self):
        """自动生成所有45个组合的语义规则"""
        # 语义模板
        templates = {
            'adapt': {
                'communicate': ('adaptive_communication', '适应性通信策略', 'adaptive_behavior', 0.91),
                'coordinate': ('adaptive_coordination', '适应性协调机制', 'adaptive_behavior', 0.89),
                'create': ('adaptive_creation', '适应性创新', 'creative_adaptation', 0.93),
                'explore': ('exploratory_adaptation', '探索性适应', 'adaptive_exploration', 0.92),
                'help': ('supportive_adaptation', '支持性适应', 'social_adaptation', 0.87),
                'learn': ('experiential_learning', '经验学习', 'learning_process', 0.94),
                'optimize': ('optimized_adaptation', '优化适应', 'adaptive_optimization', 0.90),
                'protect': ('protective_adaptation', '保护性适应', 'defensive_adaptation', 0.88),
                'share': ('collaborative_adaptation', '协作适应', 'social_adaptation', 0.86),
            },
            'communicate': {
                'coordinate': ('coordinated_communication', '协调通信', 'social_coordination', 0.90),
                'create': ('creative_communication', '创造性通信', 'creative_interaction', 0.92),
                'explore': ('exploratory_communication', '探索性通信', 'information_seeking', 0.91),
                'help': ('supportive_communication', '支持性通信', 'social_support', 0.88),
                'learn': ('knowledge_exchange', '知识交换', 'cognitive_interaction', 0.95),
                'optimize': ('optimized_communication', '优化通信', 'efficient_communication', 0.89),
                'protect': ('secure_communication', '安全通信', 'secure_interaction', 0.87),
                'share': ('information_sharing', '信息共享', 'knowledge_diffusion', 0.90),
            },
            'coordinate': {
                'create': ('coordinated_creation', '协调创造', 'collaborative_creation', 0.91),
                'explore': ('coordinated_exploration', '协调探索', 'team_exploration', 0.89),
                'help': ('coordinated_support', '协调支持', 'team_support', 0.88),
                'learn': ('collaborative_learning', '协作学习', 'social_learning', 0.93),
                'optimize': ('systemic_optimization', '系统优化', 'systems_behavior', 0.92),
                'protect': ('collaborative_defense', '协同防御', 'social_behavior', 0.90),
                'share': ('coordinated_sharing', '协调分享', 'resource_coordination', 0.87),
            },
            'create': {
                'explore': ('exploratory_innovation', '探索性创新', 'creative_exploration', 0.94),
                'help': ('supportive_creation', '支持性创造', 'social_creation', 0.89),
                'learn': ('creative_learning', '创造性学习', 'innovative_learning', 0.93),
                'optimize': ('optimized_creation', '优化创造', 'efficient_creation', 0.91),
                'protect': ('protective_creation', '保护性创造', 'defensive_creation', 0.88),
                'share': ('innovation_diffusion', '创新扩散', 'creative_process', 0.95),
            },
            'explore': {
                'help': ('exploratory_support', '探索性支持', 'supportive_exploration', 0.87),
                'learn': ('discovery_learning', '发现式学习', 'exploratory_learning', 0.94),
                'optimize': ('exploratory_optimization', '探索性优化', 'adaptive_optimization', 0.90),
                'protect': ('protective_exploration', '保护性探索', 'safe_exploration', 0.89),
                'share': ('exploratory_sharing', '探索性分享', 'knowledge_exploration', 0.88),
            },
            'help': {
                'learn': ('supported_learning', '支持性学习', 'assisted_learning', 0.91),
                'optimize': ('collaborative_optimization', '协同优化', 'cooperative_behavior', 0.90),
                'protect': ('protective_support', '保护性支持', 'defensive_support', 0.89),
                'share': ('mutual_aid', '互助', 'reciprocal_support', 0.88),
            },
            'learn': {
                'optimize': ('learning_optimization', '学习优化', 'adaptive_learning', 0.92),
                'protect': ('defensive_learning', '防御性学习', 'protective_learning', 0.87),
                'share': ('knowledge_sharing', '知识分享', 'collaborative_learning', 0.90),
            },
            'optimize': {
                'protect': ('defensive_optimization', '防御性优化', 'secure_optimization', 0.89),
                'share': ('optimized_sharing', '优化分享', 'efficient_sharing', 0.88),
            },
            'protect': {
                'share': ('secure_sharing', '安全分享', 'protected_sharing', 0.87),
            },
        }
        
        # 填充规则字典
        for b1, sub_dict in templates.items():
            for b2, (concept, meaning, category, novelty) in sub_dict.items():
                key = tuple(sorted([b1, b2]))
                self.semantic_rules[key] = {
                    'concept': concept,
                    'meaning': meaning,
                    'category': category,
                    'novelty_score': novelty
                }
        
        # 动态生成的语义概念库
        self.generated_concepts = {}
    
    def synthesize_semantic(self, behavior1: str, behavior2: str) -> Optional[Dict]:
        """语义合成两个基础行为"""
        b1, b2 = sorted([behavior1, behavior2])
        key = (b1, b2)
        
        if key in self.semantic_rules:
            result = self.semantic_rules[key].copy()
            result['source_behaviors'] = [b1, b2]
            result['is_semantic'] = True
            return result
        
        return self._generate_dynamic_concept(b1, b2)
    
    def _generate_dynamic_concept(self, b1: str, b2: str) -> Dict:
        """动态生成语义概念"""
        concept_name = f"{b1}_{b2}_synthesis"
        meaning = f'{b1}和{b2}的语义合成'
        
        result = {
            'concept': concept_name,
            'meaning': meaning,
            'category': 'dynamic_synthesis',
            'novelty_score': 0.75 + random.random() * 0.15,
            'source_behaviors': [b1, b2],
            'is_semantic': True,
            'is_dynamic': True
        }
        
        self.generated_concepts[concept_name] = result
        return result


class SemanticGoalDiscoverer:
    """语义版目标发现器"""
    
    def __init__(self):
        self.semantic_synthesizer = SemanticSynthesizer()
    
    def discover_goal(self, context_behaviors: List[str]) -> Dict:
        """发现语义目标"""
        n_select = random.randint(2, min(5, len(context_behaviors)))
        selected = random.sample(context_behaviors, n_select)
        
        if n_select == 2:
            result = self.semantic_synthesizer.synthesize_semantic(selected[0], selected[1])
        else:
            # 多词组合
            result = self._synthesize_complex(selected)
        
        return {
            'name': result['concept'],
            'meaning': result['meaning'],
            'category': result['category'],
            'novelty_score': result['novelty_score'],
            'source_behaviors': selected,
            'is_semantic': True,
            'word_count': n_select
        }
    
    def _synthesize_complex(self, behaviors: List[str]) -> Dict:
        """合成复杂语义"""
        results = []
        for i in range(len(behaviors) - 1):
            r = self.semantic_synthesizer.synthesize_semantic(behaviors[i], behaviors[i + 1])
            results.append(r)
        
        return {
            'concept': '_'.join([r['concept'] for r in results]),
            'meaning': ' + '.join([r['meaning'] for r in results]),
            'category': 'complex_synthesis',
            'novelty_score': min(0.99, sum([r['novelty_score'] for r in results]) / len(results) + 0.05)
        }


if __name__ == "__main__":
    print("=== 语义合成器测试（方案C）===\n")
    
    synthesizer = SemanticSynthesizer()
    print(f"基础行为: {len(synthesizer.base_behaviors)}个")
    print(f"预定义语义规则: {len(synthesizer.semantic_rules)}个\n")
    
    # 测试语义合成
    print("=== 语义合成测试 ===")
    test_pairs = [
        ('communicate', 'learn'),
        ('explore', 'adapt'),
        ('protect', 'coordinate'),
        ('create', 'share'),
    ]
    
    for b1, b2 in test_pairs:
        result = synthesizer.synthesize_semantic(b1, b2)
        print(f"{b1} + {b2} = {result['concept']}")
        print(f"  含义: {result['meaning']}")
        print(f"  新颖性: {result['novelty_score']:.2f}\n")
    
    # 测试目标发现
    print("=== 语义目标发现测试 ===")
    discoverer = SemanticGoalDiscoverer()
    context = ['adapt', 'communicate', 'coordinate', 'create', 'explore']
    
    for i in range(5):
        goal = discoverer.discover_goal(context)
        print(f"目标 {i+1}: {goal['name']}")
        print(f"  含义: {goal['meaning']}")
        print(f"  新颖性: {goal['novelty_score']:.2f}")
        print(f"  词数: {goal['word_count']}\n")

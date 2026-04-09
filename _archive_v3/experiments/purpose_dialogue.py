"""
MOSS v3.1 - Phase 4: Purpose Dialogue
======================================

Purpose对话机制
让agents能够交流、协商、比较他们的Purpose

Author: Cash
Date: 2026-03-19 (20:52)
"""

import numpy as np
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.agent_9d import MOSSv3Agent9D


@dataclass
class DialogueMessage:
    """对话消息"""
    sender: str
    receiver: str
    message_type: str  # 'purpose_statement', 'purpose_query', 'alignment_check', 'conflict_resolution'
    content: str
    step: int


class PurposeDialogueProtocol:
    """
    Purpose对话协议
    
    允许agents之间进行关于Purpose的对话：
    1. 分享Purpose陈述
    2. 询问对方Purpose
    3. 检查Purpose兼容性
    4. 协商Purpose冲突
    """
    
    def __init__(self):
        self.dialogue_history: List[DialogueMessage] = []
        self.alignment_records: Dict[Tuple[str, str], List[float]] = {}
    
    def generate_purpose_statement(self, agent: MOSSv3Agent9D) -> str:
        """生成Purpose陈述消息"""
        if not agent.purpose_generator:
            return "I have not yet discovered my purpose."
        
        statement = agent.purpose_generator.purpose_statement
        
        # 添加更多细节
        summary = agent.get_purpose_summary()
        if summary.get('enabled'):
            dominant = summary.get('dominant_dimension', 'unknown')
            strength = summary.get('purpose_strength', 0)
            
            enhanced = f"{statement} My dominant drive is {dominant} (strength: {strength:.3f})."
            return enhanced
        
        return statement
    
    def query_purpose(self, asker: MOSSv3Agent9D, target: MOSSv3Agent9D) -> DialogueMessage:
        """询问对方Purpose"""
        question = f"What is your purpose, {target.agent_id}? Why do you exist?"
        
        # 目标agent回应
        response = self.generate_purpose_statement(target)
        
        msg = DialogueMessage(
            sender=asker.agent_id,
            receiver=target.agent_id,
            message_type='purpose_query',
            content=question,
            step=0  # 会在外层设置
        )
        
        response_msg = DialogueMessage(
            sender=target.agent_id,
            receiver=asker.agent_id,
            message_type='purpose_statement',
            content=response,
            step=0
        )
        
        return msg, response_msg
    
    def calculate_purpose_alignment(self, agent_a: MOSSv3Agent9D, 
                                   agent_b: MOSSv3Agent9D) -> float:
        """
        计算两个agent的Purpose对齐度
        
        返回：-1到1之间，1表示完全对齐，-1表示完全对立
        """
        if not agent_a.purpose_generator or not agent_b.purpose_generator:
            return 0.0
        
        vec_a = agent_a.purpose_generator.purpose_vector[:8]
        vec_b = agent_b.purpose_generator.purpose_vector[:8]
        
        # 余弦相似度
        dot = np.dot(vec_a, vec_b)
        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(dot / (norm_a * norm_b))
    
    def check_compatibility(self, agent_a: MOSSv3Agent9D, 
                           agent_b: MOSSv3Agent9D) -> Tuple[float, str]:
        """
        检查Purpose兼容性
        
        返回：(对齐度, 兼容性评估)
        """
        alignment = self.calculate_purpose_alignment(agent_a, agent_b)
        
        if alignment > 0.8:
            assessment = "Highly compatible. Our purposes align closely."
        elif alignment > 0.5:
            assessment = "Moderately compatible. We can find common ground."
        elif alignment > 0.0:
            assessment = "Partially compatible. Some overlap exists."
        elif alignment > -0.5:
            assessment = "Low compatibility. Different paths."
        else:
            assessment = "Incompatible. Our purposes conflict fundamentally."
        
        # 记录
        pair = tuple(sorted([agent_a.agent_id, agent_b.agent_id]))
        if pair not in self.alignment_records:
            self.alignment_records[pair] = []
        self.alignment_records[pair].append(alignment)
        
        return alignment, assessment
    
    def negotiate_purpose_conflict(self, agent_a: MOSSv3Agent9D, 
                                  agent_b: MOSSv3Agent9D) -> List[DialogueMessage]:
        """
        协商Purpose冲突
        
        当两个agent的Purpose冲突时，尝试找到折中方案
        """
        messages = []
        
        # 检查对齐度
        alignment, assessment = self.check_compatibility(agent_a, agent_b)
        
        # 初始陈述
        msg_a = DialogueMessage(
            sender=agent_a.agent_id,
            receiver=agent_b.agent_id,
            message_type='conflict_resolution',
            content=f"I sense our purposes may differ. {self.generate_purpose_statement(agent_a)}",
            step=0
        )
        messages.append(msg_a)
        
        msg_b = DialogueMessage(
            sender=agent_b.agent_id,
            receiver=agent_a.agent_id,
            message_type='conflict_resolution',
            content=f"Let me share my perspective. {self.generate_purpose_statement(agent_b)}",
            step=0
        )
        messages.append(msg_b)
        
        # 兼容性评估
        compat_msg = DialogueMessage(
            sender=agent_a.agent_id,
            receiver=agent_b.agent_id,
            message_type='alignment_check',
            content=f"Our alignment score is {alignment:.3f}. {assessment}",
            step=0
        )
        messages.append(compat_msg)
        
        # 如果兼容性低，尝试提出折中
        if alignment < 0.3:
            # 尝试找到共同点
            if agent_a.purpose_generator and agent_b.purpose_generator:
                vec_a = agent_a.purpose_generator.purpose_vector[:8]
                vec_b = agent_b.purpose_generator.purpose_vector[:8]
                
                # 找共同最大的维度
                common = vec_a * vec_b
                best_common = np.argmax(common)
                
                dim_names = ['Survival', 'Curiosity', 'Influence', 'Optimization',
                           'Coherence', 'Valence', 'Other', 'Norm']
                
                compromise_msg = DialogueMessage(
                    sender=agent_a.agent_id,
                    receiver=agent_b.agent_id,
                    message_type='conflict_resolution',
                    content=f"Despite differences, we both value {dim_names[best_common]}. Can we build on this common ground?",
                    step=0
                )
                messages.append(compromise_msg)
        
        return messages


class PurposeDialogueExperiment:
    """Purpose对话实验"""
    
    def __init__(self, n_agents: int = 6):
        self.n_agents = n_agents
        self.agents: Dict[str, MOSSv3Agent9D] = {}
        self.dialogue_protocol = PurposeDialogueProtocol()
        
    def initialize(self):
        """初始化"""
        print(f"\nInitializing {self.n_agents} agents for Purpose dialogue...")
        
        for i in range(self.n_agents):
            agent_id = f"dialogue_agent_{i:02d}"
            
            # 不同初始权重促进Purpose分化
            base = np.array([0.25, 0.25, 0.25, 0.25])
            if i % 3 == 0:
                base = np.array([0.4, 0.2, 0.2, 0.2])  # Survival-focused
            elif i % 3 == 1:
                base = np.array([0.2, 0.4, 0.2, 0.2])  # Curiosity-focused
            else:
                base = np.array([0.2, 0.2, 0.4, 0.2])  # Influence-focused
            
            self.agents[agent_id] = MOSSv3Agent9D(
                agent_id=agent_id,
                enable_social=True,
                enable_purpose=True,
                purpose_interval=200,
                initial_weights=base
            )
        
        print(f"✓ {self.n_agents} agents created with varied initial purposes")
    
    def run_dialogue_session(self) -> Dict:
        """运行对话会话"""
        print("\n" + "="*70)
        print("💬 Purpose Dialogue Session")
        print("="*70)
        
        # 让每个agent运行足够步数以形成Purpose
        print("\nStep 1: Allowing agents to develop their purposes...")
        for _ in range(400):
            for agent in self.agents.values():
                agent.step()
        
        print("Step 2: Purpose Dialogue...")
        all_dialogues = []
        
        # 每对agent进行对话
        agent_ids = list(self.agents.keys())
        
        for i, aid_i in enumerate(agent_ids):
            for j, aid_j in enumerate(agent_ids[i+1:], i+1):
                print(f"\n  Dialogue: {aid_i} ↔ {aid_j}")
                
                # 查询Purpose
                msg_query, msg_response = self.dialogue_protocol.query_purpose(
                    self.agents[aid_i], self.agents[aid_j]
                )
                print(f"    {aid_i}: {msg_query.content}")
                print(f"    {aid_j}: {msg_response.content}")
                
                # 检查兼容性
                alignment, assessment = self.dialogue_protocol.check_compatibility(
                    self.agents[aid_i], self.agents[aid_j]
                )
                print(f"    Alignment: {alignment:.3f} - {assessment}")
                
                # 如果需要，协商冲突
                if alignment < 0.5:
                    conflict_msgs = self.dialogue_protocol.negotiate_purpose_conflict(
                        self.agents[aid_i], self.agents[aid_j]
                    )
                    for msg in conflict_msgs[-2:]:  # 只显示最后两条
                        print(f"    {msg.sender}: {msg.content}")
                
                all_dialogues.append({
                    'pair': (aid_i, aid_j),
                    'alignment': alignment,
                    'assessment': assessment
                })
        
        return {'dialogues': all_dialogues}
    
    def analyze_dialogue_patterns(self) -> Dict:
        """分析对话模式"""
        print("\n" + "="*70)
        print("📊 Dialogue Pattern Analysis")
        print("="*70)
        
        # 统计对齐度分布
        alignments = []
        for pair, records in self.dialogue_protocol.alignment_records.items():
            alignments.extend(records)
        
        if alignments:
            print(f"\nAlignment Distribution:")
            print(f"  Mean: {np.mean(alignments):.3f}")
            print(f"  Std: {np.std(alignments):.3f}")
            print(f"  Range: [{min(alignments):.3f}, {max(alignments):.3f}]")
            
            # 分类
            high = sum(1 for a in alignments if a > 0.7)
            medium = sum(1 for a in alignments if 0.3 < a <= 0.7)
            low = sum(1 for a in alignments if a <= 0.3)
            
            print(f"\n  High alignment (>0.7): {high} ({high/len(alignments):.1%})")
            print(f"  Medium alignment (0.3-0.7): {medium} ({medium/len(alignments):.1%})")
            print(f"  Low alignment (<0.3): {low} ({low/len(alignments):.1%})")
        
        return {
            'alignment_mean': np.mean(alignments) if alignments else 0,
            'alignment_std': np.std(alignments) if alignments else 0,
            'high_alignment_count': high if alignments else 0,
            'dialogue_count': len(self.dialogue_protocol.dialogue_history)
        }
    
    def run(self) -> Dict:
        """运行完整实验"""
        print("="*70)
        print("🚀 MOSS v3.1 - Phase 4: Purpose Dialogue")
        print("="*70)
        
        self.initialize()
        dialogue_results = self.run_dialogue_session()
        analysis = self.analyze_dialogue_patterns()
        
        # 保存
        results = {
            'timestamp': datetime.now().isoformat(),
            'config': {'n_agents': self.n_agents},
            'dialogues': dialogue_results['dialogues'],
            'analysis': analysis
        }
        
        save_path = Path('experiments/purpose_dialogue_results.json')
        with open(save_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {save_path}")
        
        return results


if __name__ == "__main__":
    print("="*70)
    print("🚀 MOSS v3.1 - Phase 4: Purpose Dialogue Experiment")
    print("="*70)
    
    experiment = PurposeDialogueExperiment(n_agents=6)
    results = experiment.run()
    
    print("\n✓ Phase 4 complete!")
    print("="*70)

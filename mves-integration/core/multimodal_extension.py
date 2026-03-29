#!/usr/bin/env python3
"""
MVES v2.0 - 多模态扩展模块

Multi-Vector Evolution System: Multimodal Extension

核心功能：
- 统一特征编码（文本 + 图像 + 音频 + 视频）
- 跨模态融合机制
- 上下文动态权重调整
- 价值向量提取

与 MOSS main 分支集成点：
- real_world_bridge.py - 增强真实世界感知
- Self-Optimization 触发逻辑 - 多模态语义分数
- Purpose Dynamics Module - 价值涌现增强 D9
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import json


class ModalityType(Enum):
    """模态类型枚举"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    STRUCTURED = "structured"  # 结构化数据（JSON、表格等）


@dataclass
class FeatureVector:
    """特征向量"""
    modality: ModalityType
    vector: np.ndarray
    confidence: float = 1.0
    timestamp: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def normalize(self) -> 'FeatureVector':
        """归一化特征向量"""
        norm = np.linalg.norm(self.vector)
        if norm > 0:
            self.vector = self.vector / norm
        return self


@dataclass
class ValueVector:
    """价值向量（多向量进化核心）"""
    # 目标向量
    goal_vector: np.ndarray = field(default_factory=lambda: np.zeros(64))
    # 价值向量
    value_vector: np.ndarray = field(default_factory=lambda: np.zeros(64))
    # 模态向量
    modality_vector: np.ndarray = field(default_factory=lambda: np.zeros(16))
    # 时间衰减因子
    temporal_decay: float = 0.95
    
    def fuse(self, other: 'ValueVector', alpha: float = 0.5) -> 'ValueVector':
        """融合两个价值向量"""
        new = ValueVector()
        new.goal_vector = alpha * self.goal_vector + (1 - alpha) * other.goal_vector
        new.value_vector = alpha * self.value_vector + (1 - alpha) * other.value_vector
        new.modality_vector = alpha * self.modality_vector + (1 - alpha) * other.modality_vector
        return new
    
    def apply_decay(self) -> 'ValueVector':
        """应用时间衰减"""
        self.goal_vector *= self.temporal_decay
        self.value_vector *= self.temporal_decay
        return self


class MultimodalEncoder:
    """多模态统一编码器"""
    
    def __init__(self, embedding_dim: int = 512):
        self.embedding_dim = embedding_dim
        self.modality_encoders = {
            ModalityType.TEXT: self._encode_text,
            ModalityType.IMAGE: self._encode_image,
            ModalityType.AUDIO: self._encode_audio,
            ModalityType.VIDEO: self._encode_video,
            ModalityType.STRUCTURED: self._encode_structured
        }
    
    def encode(self, data: Any, modality: ModalityType) -> FeatureVector:
        """统一编码接口"""
        encoder = self.modality_encoders.get(modality)
        if not encoder:
            raise ValueError(f"Unsupported modality: {modality}")
        
        vector, confidence = encoder(data)
        return FeatureVector(
            modality=modality,
            vector=vector,
            confidence=confidence,
            timestamp=0.0  # 由调用方设置
        )
    
    def _encode_text(self, text: str) -> Tuple[np.ndarray, float]:
        """文本编码（简化版，实际应使用 LLM embedding）"""
        # TODO: 集成实际文本 embedding 模型
        vector = np.random.randn(self.embedding_dim).astype(np.float32)
        confidence = 0.9  # 文本编码通常较可靠
        return vector, confidence
    
    def _encode_image(self, image_data: np.ndarray) -> Tuple[np.ndarray, float]:
        """图像编码（简化版，实际应使用 CNN/ViT）"""
        # TODO: 集成实际图像编码模型
        if isinstance(image_data, np.ndarray):
            flattened = image_data.flatten()[:self.embedding_dim]
            vector = np.pad(flattened, (0, max(0, self.embedding_dim - len(flattened))))
        else:
            vector = np.random.randn(self.embedding_dim).astype(np.float32)
        confidence = 0.8
        return vector, confidence
    
    def _encode_audio(self, audio_data: np.ndarray) -> Tuple[np.ndarray, float]:
        """音频编码（简化版，实际应使用 Whisper 等）"""
        # TODO: 集成实际音频编码模型
        vector = np.random.randn(self.embedding_dim).astype(np.float32)
        confidence = 0.75
        return vector, confidence
    
    def _encode_video(self, video_data: Any) -> Tuple[np.ndarray, float]:
        """视频编码（简化版，实际应使用 VideoMAE 等）"""
        # TODO: 集成实际视频编码模型
        vector = np.random.randn(self.embedding_dim).astype(np.float32)
        confidence = 0.7
        return vector, confidence
    
    def _encode_structured(self, data: Dict) -> Tuple[np.ndarray, float]:
        """结构化数据编码"""
        # 将字典转换为特征向量
        json_str = json.dumps(data, sort_keys=True)
        vector = np.random.randn(self.embedding_dim).astype(np.float32)
        confidence = 0.85
        return vector, confidence


class CrossModalFusion:
    """跨模态融合器"""
    
    def __init__(self, fusion_dim: int = 512):
        self.fusion_dim = fusion_dim
        self.attention_weights = None
    
    def fuse(self, features: List[FeatureVector], 
             context: Optional[Dict] = None) -> np.ndarray:
        """
        跨模态融合
        
        Args:
            features: 特征向量列表
            context: 上下文信息（用于动态权重调整）
        
        Returns:
            融合后的特征向量
        """
        if not features:
            return np.zeros(self.fusion_dim)
        
        # 基于置信度和上下文计算权重
        weights = self._compute_weights(features, context)
        
        # 加权融合
        fused = np.zeros(self.fusion_dim)
        total_weight = 0.0
        
        for feature, weight in zip(features, weights):
            # 确保维度匹配
            if len(feature.vector) < self.fusion_dim:
                padded = np.pad(feature.vector, 
                              (0, self.fusion_dim - len(feature.vector)))
            else:
                padded = feature.vector[:self.fusion_dim]
            
            fused += weight * padded
            total_weight += weight
        
        if total_weight > 0:
            fused /= total_weight
        
        # 归一化
        norm = np.linalg.norm(fused)
        if norm > 0:
            fused /= norm
        
        return fused
    
    def _compute_weights(self, features: List[FeatureVector],
                        context: Optional[Dict]) -> List[float]:
        """计算融合权重"""
        weights = []
        
        for feature in features:
            # 基础权重：置信度
            weight = feature.confidence
            
            # 上下文调整
            if context:
                # 示例：如果当前是 Crisis 状态，提升文本模态权重
                if context.get("state") == "Crisis" and feature.modality == ModalityType.TEXT:
                    weight *= 1.5
                
                # 如果探索状态，提升视觉模态权重
                if context.get("state") == "Growth" and feature.modality == ModalityType.IMAGE:
                    weight *= 1.3
            
            weights.append(weight)
        
        # 归一化权重
        total = sum(weights)
        if total > 0:
            weights = [w / total for w in weights]
        
        return weights


class ValueExtractor:
    """价值向量提取器"""
    
    def __init__(self, value_dim: int = 64):
        self.value_dim = value_dim
        self.value_templates = self._init_value_templates()
    
    def _init_value_templates(self) -> Dict[str, np.ndarray]:
        """初始化价值模板（对应 MOSS 四大目标）"""
        return {
            "survival": np.random.randn(self.value_dim).astype(np.float32),
            "curiosity": np.random.randn(self.value_dim).astype(np.float32),
            "influence": np.random.randn(self.value_dim).astype(np.float32),
            "optimization": np.random.randn(self.value_dim).astype(np.float32)
        }
    
    def extract(self, fused_features: np.ndarray,
                context: Dict) -> ValueVector:
        """
        从融合特征中提取价值向量
        
        Args:
            fused_features: 融合后的特征向量
            context: 上下文信息（包含当前状态、目标等）
        
        Returns:
            价值向量
        """
        value_vector = ValueVector()
        
        # 根据上下文调整各价值维度
        state = context.get("state", "Normal")
        state_weights = self._get_state_weights(state)
        
        # 提取目标向量
        value_vector.goal_vector = self._extract_goal_vector(
            fused_features, context, state_weights
        )
        
        # 提取价值向量
        value_vector.value_vector = self._extract_value_vector(
            fused_features, context, state_weights
        )
        
        # 提取模态向量
        value_vector.modality_vector = self._extract_modality_vector(
            fused_features, context
        )
        
        return value_vector
    
    def _get_state_weights(self, state: str) -> Dict[str, float]:
        """获取状态权重（与 MOSS main 分支的 state-dependent weighting 对应）"""
        weights = {
            "Crisis": {"survival": 0.6, "curiosity": 0.1, "influence": 0.2, "optimization": 0.1},
            "Concerned": {"survival": 0.35, "curiosity": 0.35, "influence": 0.2, "optimization": 0.1},
            "Normal": {"survival": 0.2, "curiosity": 0.4, "influence": 0.3, "optimization": 0.1},
            "Growth": {"survival": 0.2, "curiosity": 0.2, "influence": 0.4, "optimization": 0.2}
        }
        return weights.get(state, weights["Normal"])
    
    def _extract_goal_vector(self, features: np.ndarray, 
                            context: Dict,
                            state_weights: Dict) -> np.ndarray:
        """提取目标向量"""
        # 简化实现：基于状态权重调整
        goal = np.zeros(self.value_dim)
        
        for drive, weight in state_weights.items():
            template = self.value_templates.get(drive, np.zeros(self.value_dim))
            goal += weight * template
        
        # 加入特征影响
        goal += 0.1 * features[:self.value_dim]
        
        # 归一化
        norm = np.linalg.norm(goal)
        if norm > 0:
            goal /= norm
        
        return goal
    
    def _extract_value_vector(self, features: np.ndarray,
                             context: Dict,
                             state_weights: Dict) -> np.ndarray:
        """提取价值向量"""
        # 类似目标向量，但加入历史价值影响
        value = np.zeros(self.value_dim)
        
        for drive, weight in state_weights.items():
            template = self.value_templates.get(drive, np.zeros(self.value_dim))
            value += weight * template
        
        value += 0.15 * features[:self.value_dim]
        
        norm = np.linalg.norm(value)
        if norm > 0:
            value /= norm
        
        return value
    
    def _extract_modality_vector(self, features: np.ndarray,
                                context: Dict) -> np.ndarray:
        """提取模态向量（16 维，编码模态分布信息）"""
        modality_vector = np.zeros(16)
        
        # 从上下文提取模态信息
        modalities = context.get("modalities", ["text"])
        for i, mod in enumerate(modalities[:16]):
            if isinstance(mod, str):
                modality_vector[i] = hash(mod) % 100 / 100.0
        
        # 加入特征影响
        modality_vector += 0.1 * features[:16]
        
        norm = np.linalg.norm(modality_vector)
        if norm > 0:
            modality_vector /= norm
        
        return modality_vector


class MultimodalExtension:
    """
    MVES 多模态扩展主类
    
    与 MOSS main 分支集成：
    - 作为感知层增强模块
    - 为 Self-Optimization 提供多模态语义分数
    - 为 D9 Purpose 提供价值涌现能力
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.embedding_dim = self.config.get("embedding_dim", 512)
        self.value_dim = self.config.get("value_dim", 64)
        
        # 初始化核心组件
        self.encoder = MultimodalEncoder(self.embedding_dim)
        self.fusion = CrossModalFusion(self.embedding_dim)
        self.extractor = ValueExtractor(self.value_dim)
        
        # 价值向量缓存（用于时间序列分析）
        self.value_history: List[ValueVector] = []
        self.max_history = 100
    
    def process_multimodal_input(self, 
                                 inputs: Dict[ModalityType, Any],
                                 context: Dict) -> Dict:
        """
        处理多模态输入
        
        Args:
            inputs: 多模态输入字典 {modality: data}
            context: 上下文信息（包含 state、goals 等）
        
        Returns:
            处理结果，包含融合特征和价值向量
        """
        # 1. 编码各模态
        features = []
        for modality, data in inputs.items():
            try:
                feature = self.encoder.encode(data, modality)
                features.append(feature)
            except Exception as e:
                print(f"Warning: Failed to encode {modality}: {e}")
        
        if not features:
            return {
                "fused_features": np.zeros(self.embedding_dim),
                "value_vector": ValueVector(),
                "confidence": 0.0
            }
        
        # 2. 跨模态融合
        fused = self.fusion.fuse(features, context)
        
        # 3. 提取价值向量
        value_vector = self.extractor.extract(fused, context)
        
        # 4. 应用时间衰减（如果有历史）
        if self.value_history:
            last_value = self.value_history[-1]
            value_vector = value_vector.fuse(last_value, alpha=0.7)
        
        value_vector.apply_decay()
        
        # 5. 更新历史
        self.value_history.append(value_vector)
        if len(self.value_history) > self.max_history:
            self.value_history = self.value_history[-self.max_history:]
        
        # 6. 计算置信度
        avg_confidence = sum(f.confidence for f in features) / len(features)
        
        return {
            "fused_features": fused,
            "value_vector": value_vector,
            "confidence": avg_confidence,
            "num_modalities": len(features),
            "modalities_used": [f.modality.value for f in features]
        }
    
    def get_multimodal_score(self, result: Dict) -> float:
        """
        计算多模态语义分数
        
        用于 Self-Optimization 触发逻辑
        
        Returns:
            0-1 之间的分数
        """
        confidence = result.get("confidence", 0.0)
        num_modalities = result.get("num_modalities", 0)
        
        # 多模态增益
        modality_bonus = min(0.2, num_modalities * 0.05)
        
        score = confidence + modality_bonus
        return min(1.0, score)
    
    def get_value_vector_for_purpose(self) -> ValueVector:
        """
        获取用于 D9 Purpose 的价值向量
        
        Returns:
            融合后的价值向量
        """
        if not self.value_history:
            return ValueVector()
        
        # 时间加权平均
        weighted_sum = np.zeros(self.value_dim)
        total_weight = 0.0
        
        for i, vv in enumerate(self.value_history):
            weight = 0.9 ** (len(self.value_history) - i - 1)
            weighted_sum += weight * vv.value_vector
            total_weight += weight
        
        if total_weight > 0:
            weighted_sum /= total_weight
        
        result = ValueVector()
        result.value_vector = weighted_sum
        return result
    
    def analyze_value_stability(self) -> Dict:
        """
        分析价值向量稳定性（用于评估 Purpose 稳定性）
        
        Returns:
            稳定性指标
        """
        if len(self.value_history) < 10:
            return {
                "stability": 0.0,
                "std": float('inf'),
                "sample_size": len(self.value_history)
            }
        
        # 计算最近 10 个价值向量的标准差
        recent_vectors = [vv.value_vector for vv in self.value_history[-10:]]
        vectors_array = np.array(recent_vectors)
        std = np.std(vectors_array, axis=0).mean()
        
        # 稳定性 = 1 - std（std 越小越稳定）
        stability = max(0.0, 1.0 - std * 10)
        
        return {
            "stability": stability,
            "std": std,
            "sample_size": len(self.value_history),
            "target_stability": 0.96  # v5.3.0 目标
        }
    
    def get_optimization_metrics(self) -> Dict:
        """
        获取用于 Self-Optimization v2 的评估指标
        
        Returns:
            评估指标字典
        """
        value_stability = self.analyze_value_stability()
        
        # 多模态价值提取质量
        if self.value_history:
            recent = self.value_history[-10:]
            quality = sum(vv.confidence for vv in recent) / len(recent)
        else:
            quality = 0.0
        
        return {
            "value_stability": value_stability["stability"],
            "multimodal_quality": quality,
            "evolution_speed": self._calculate_evolution_speed(),
            "cross_modal_consistency": self._calculate_consistency()
        }
    
    def _calculate_evolution_speed(self) -> float:
        """计算进化速度指标"""
        if len(self.value_history) < 2:
            return 0.0
        
        # 计算价值向量变化率
        changes = []
        for i in range(1, min(10, len(self.value_history))):
            change = np.linalg.norm(
                self.value_history[i].value_vector - 
                self.value_history[i-1].value_vector
            )
            changes.append(change)
        
        return np.mean(changes) if changes else 0.0
    
    def _calculate_consistency(self) -> float:
        """计算跨模态一致性"""
        # 简化实现：基于价值向量方差
        if len(self.value_history) < 2:
            return 1.0
        
        vectors = [vv.value_vector for vv in self.value_history[-10:]]
        variance = np.var(vectors, axis=0).mean()
        
        return max(0.0, 1.0 - variance * 5)


# ============================================================================
# 与 MOSS main 分支的集成接口
# ============================================================================

def integrate_with_real_world_bridge(moss_agent, extension: MultimodalExtension):
    """
    集成到 real_world_bridge.py
    
    增强真实世界感知的多模态处理能力
    """
    # TODO: 实现与 real_world_bridge.py 的集成
    pass


def integrate_with_self_optimization(moss_agent, extension: MultimodalExtension):
    """
    集成到 Self-Optimization v2
    
    为优化触发逻辑提供多模态语义分数
    """
    # TODO: 实现与 self_optimization_v2.py 的集成
    pass


def integrate_with_purpose_dynamics(moss_agent, extension: MultimodalExtension):
    """
    集成到 Purpose Dynamics Module (D9)
    
    为自生成 Purpose 提供价值涌现能力
    """
    # TODO: 实现与 objectives.py 的 Purpose Dynamics Module 集成
    pass


# ============================================================================
# 测试与验证
# ============================================================================

def run_basic_tests():
    """运行基础测试"""
    print("Running MVES Multimodal Extension Basic Tests...")
    
    # 测试 1: 编码器
    encoder = MultimodalEncoder()
    text_feature = encoder.encode("Hello, World!", ModalityType.TEXT)
    assert text_feature.vector.shape == (512,), "Text encoding failed"
    print("✓ Encoder test passed")
    
    # 测试 2: 融合器
    fusion = CrossModalFusion()
    features = [
        FeatureVector(ModalityType.TEXT, np.random.randn(512), 0.9),
        FeatureVector(ModalityType.IMAGE, np.random.randn(512), 0.8)
    ]
    fused = fusion.fuse(features, {"state": "Normal"})
    assert fused.shape == (512,), "Fusion failed"
    print("✓ Fusion test passed")
    
    # 测试 3: 价值提取
    extractor = ValueExtractor()
    context = {"state": "Normal", "modalities": ["text", "image"]}
    value_vector = extractor.extract(fused, context)
    assert value_vector.value_vector.shape == (64,), "Value extraction failed"
    print("✓ Value extraction test passed")
    
    # 测试 4: 完整流程
    extension = MultimodalExtension()
    inputs = {
        ModalityType.TEXT: "Test input",
        ModalityType.IMAGE: np.random.randn(32, 32, 3)
    }
    result = extension.process_multimodal_input(inputs, context)
    assert "fused_features" in result, "Process failed"
    assert "value_vector" in result, "Process failed"
    print("✓ Full pipeline test passed")
    
    # 测试 5: 稳定性分析
    for _ in range(20):
        extension.process_multimodal_input(inputs, context)
    stability = extension.analyze_value_stability()
    print(f"  Value stability: {stability['stability']:.3f} (target: >0.96)")
    print("✓ Stability analysis test passed")
    
    print("\n✅ All basic tests passed!")


if __name__ == "__main__":
    run_basic_tests()

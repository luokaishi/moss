"""
Meta-Drive System - 元驱动系统 (第4层)

元驱动 = 作用在"驱动生成与进化过程本身"的驱动力

形式化：d^meta: D → ΔD
其中 D 是当前驱动集合，ΔD 是驱动的变化

核心思想：
- 从"在固定搜索空间中优化"到"改变搜索空间本身"
- 实现 open-ended intelligence（开放式智能）
"""

from .meta_controller import MetaController
from .meta_controller_v2 import MetaControllerV2
from .self_model import SelfModel
from .self_model_v2 import SelfModelV2

__all__ = ['MetaController', 'MetaControllerV2', 'SelfModel', 'SelfModelV2']

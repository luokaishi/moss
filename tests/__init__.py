"""
MOSS AGI Agent - Test Package
=============================

测试包初始化文件，确保 pytest 正确发现测试。
"""

import os
import sys
from pathlib import Path

# 将项目根目录添加到 PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 测试版本
__version__ = "5.4.0"

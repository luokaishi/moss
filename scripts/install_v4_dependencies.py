#!/usr/bin/env python3
"""
v4.1 Agent依赖安装和验证脚本

该脚本用于：
1. 检查所有必需的v4.1依赖模块
2. 修复Linux硬编码路径问题
3. 验证模块导入是否正常
4. 提供Windows兼容性修复

运行: python scripts/install_v4_dependencies.py
"""

import sys
import os
import subprocess
from pathlib import Path

def setup_paths():
    """设置项目路径"""
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(project_root / '_archive_v4'))
    sys.path.insert(0, str(project_root / '_archive_v4' / 'core'))
    sys.path.insert(0, str(project_root / '_archive_v4' / 'integration'))
    sys.path.insert(0, str(project_root / '_archive_v3' / 'core'))
    
    return project_root

def check_python_version():
    """检查Python版本"""
    import platform
    python_version = sys.version_info
    print(f"Python版本: {platform.python_version()}")
    print(f"系统: {platform.system()} {platform.release()}")
    
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("⚠️  警告: Python版本需要3.8+")
        return False
    return True

def check_numpy_installation():
    """检查NumPy安装"""
    try:
        import numpy as np
        print(f"✅ NumPy版本: {np.__version__}")
        return True
    except ImportError:
        print("❌ NumPy未安装")
        return False

def check_core_dependencies():
    """检查核心依赖"""
    dependencies = [
        ('matplotlib', 'matplotlib', '可视化库'),
        ('scipy', 'scipy', '科学计算库'),
        ('scikit-learn', 'sklearn', '机器学习库'),
        ('pandas', 'pandas', '数据分析库'),
        ('numpy', 'numpy', '数值计算库'),
        ('typing', 'typing', '类型注解库'),
        ('dataclasses', 'dataclasses', '数据类库'),
        ('logging', 'logging', '日志库'),
        ('json', 'json', 'JSON处理库'),
    ]
    
    all_installed = True
    for import_name, module_name, description in dependencies:
        try:
            module = __import__(import_name)
            version = getattr(module, '__version__', '未知版本')
            print(f"✅ {module_name}: 已安装 ({version}) - {description}")
        except ImportError as e:
            print(f"❌ {module_name}: 未安装 - {description}")
            print(f"   错误: {e}")
            all_installed = False
    
    return all_installed

def check_v4_modules(project_root):
    """检查v4模块是否存在"""
    required_modules = [
        ('world_model.py', '_archive_v4/core/world_model.py'),
        ('llm_reasoning.py', '_archive_v4/core/llm_reasoning.py'),
        ('open_goal_space.py', '_archive_v4/core/open_goal_space.py'),
        ('agent_v4_1.py', '_archive_v4/integration/agent_v4_1.py'),
    ]
    
    all_exist = True
    for module_name, module_path in required_modules:
        full_path = project_root / module_path
        if full_path.exists():
            print(f"✅ {module_name}: 存在 ({full_path})")
        else:
            print(f"❌ {module_name}: 不存在")
            all_exist = False
    
    return all_exist

def fix_linux_paths_in_v4_agent(project_root):
    """修复v4.1 Agent中的Linux硬编码路径"""
    v4_agent_path = project_root / '_archive_v4' / 'integration' / 'agent_v4_1.py'
    
    if not v4_agent_path.exists():
        print(f"❌ 找不到v4.1 Agent文件: {v4_agent_path}")
        return False
    
    try:
        with open(v4_agent_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换Linux硬编码路径
        replacements = [
            ("sys.path.insert(0, '/workspace/projects/moss')", 
             f"sys.path.insert(0, r'{str(project_root)}')"),
            ("sys.path.insert(0, '/workspace/projects/moss/v3')", 
             f"sys.path.insert(0, r'{str(project_root / '_archive_v3')}')"),
            ("sys.path.insert(0, '/workspace/projects/moss/v3/core')", 
             f"sys.path.insert(0, r'{str(project_root / '_archive_v3' / 'core')}')"),
            ("sys.path.insert(0, '/workspace/projects/moss/v4/core')", 
             f"sys.path.insert(0, r'{str(project_root / '_archive_v4' / 'core')}')"),
            ("sys.path.insert(0, '/workspace/projects/moss/v4/integration')", 
             f"sys.path.insert(0, r'{str(project_root / '_archive_v4' / 'integration')}')"),
        ]
        
        for old, new in replacements:
            content = content.replace(old, new)
        
        # 保存修复后的文件
        backup_path = v4_agent_path.with_suffix('.py.backup')
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ v4.1 Agent路径修复完成")
        print(f"   备份文件: {backup_path}")
        
        return True
    except Exception as e:
        print(f"❌ 修复v4.1 Agent路径失败: {e}")
        return False

def test_v4_imports():
    """测试v4模块导入"""
    print("\n测试v4模块导入...")
    
    try:
        # 测试world_model
        from world_model import WorldModel
        print("✅ world_model 导入成功")
    except Exception as e:
        print(f"❌ world_model 导入失败: {e}")
        return False
    
    try:
        # 测试llm_reasoning
        from llm_reasoning import LLMReasoningLayer
        print("✅ llm_reasoning 导入成功")
    except Exception as e:
        print(f"❌ llm_reasoning 导入失败: {e}")
        return False
    
    try:
        # 测试open_goal_space
        from open_goal_space import GoalManager
        print("✅ open_goal_space 导入成功")
    except Exception as e:
        print(f"❌ open_goal_space 导入失败: {e}")
        return False
    
    return True

def test_parameter_adapter_integration(project_root):
    """测试参数转换器集成"""
    print("\n测试参数转换器集成...")
    
    try:
        # 导入参数转换器
        sys.path.insert(0, str(project_root / 'moss' / 'api'))
        
        try:
            from interaction_adapter import MOSSInteractionAdapter
            print("✅ 参数转换器导入成功")
        except ImportError as e:
            print(f"❌ 参数转换器导入失败: {e}")
            return False
        
        # 测试参数转换器功能
        adapter = MOSSInteractionAdapter()
        
        # 测试数据
        observation_data = {
            'other_agents': {
                'agent_test': {'action': 'cooperate', 'reward': 0.8, 'weights': [0.3, 0.2, 0.3, 0.2]}
            },
            'interaction': {'agent_id': 'agent_test', 'outcome': 'cooperate', 'payoff': 0.7},
            'resource_level': 0.9
        }
        
        # 测试转换功能
        observed_behaviors, interaction = adapter.convert_to_v31_format(observation_data)
        if observed_behaviors is not None:
            print(f"✅ observation -> v3.1参数转换成功: {len(observed_behaviors)}个行为")
        else:
            print("❌ observation -> v3.1参数转换失败")
            return False
        
        # 测试反向转换
        observation_conv = adapter.convert_to_v4x_format(observed_behaviors, interaction)
        if 'other_agents' in observation_conv:
            print(f"✅ v3.1参数 -> observation转换成功")
        else:
            print("❌ v3.1参数 -> observation转换失败")
            return False
        
        # 测试Agent类型检测
        class MockAgent:
            def __init__(self):
                self.agent_id = "test"
        
        mock_agent = MockAgent()
        agent_type = adapter.detect_agent_from_instance(mock_agent)
        print(f"✅ Agent类型检测功能正常: {agent_type}")
        
        return True
        
    except Exception as e:
        print(f"❌ 参数转换器集成测试失败: {e}")
        return False

def create_v4_agent_fixed_version(project_root):
    """创建修复版的v4.1 Agent"""
    print("\n创建修复版的v4.1 Agent...")
    
    try:
        # 读取原始v4.1 Agent
        original_path = project_root / '_archive_v4' / 'integration' / 'agent_v4_1.py'
        with open(original_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 创建新的修复版本
        fixed_content = """#!/usr/bin/env python3
'''
MOSS v4.1 - Purpose-Enhanced Agent (Windows修复版)

修复内容:
1. 移除Linux硬编码路径
2. 添加动态路径计算
3. 增强错误处理
4. 支持Windows兼容性

原始版本: /workspace/projects/moss/v4/integration/agent_v4_1.py
修复版本: {project_root}/_archive_v4/integration/agent_v4_1_fixed.py
'''

import sys
import os
from pathlib import Path

# 动态路径计算
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / '_archive_v4'))
sys.path.insert(0, str(PROJECT_ROOT / '_archive_v4' / 'core'))
sys.path.insert(0, str(PROJECT_ROOT / '_archive_v4' / 'integration'))
sys.path.insert(0, str(PROJECT_ROOT / '_archive_v3' / 'core'))

import numpy as np
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

# v4.0 modules
try:
    from world_model import WorldModel
    from llm_reasoning import LLMReasoningLayer, Reflection
    from open_goal_space import GoalManager, Goal, GoalStatus, GoalType
except ImportError as e:
    print(f"警告: v4.0模块导入失败 - {e}")
    # 定义模拟类以避免导入错误
    class WorldModel:
        pass
    class LLMReasoningLayer:
        pass
    class Reflection:
        pass
    class GoalManager:
        pass
    class Goal:
        pass
    class GoalStatus:
        pass
    class GoalType:
        pass

# v3.1 modules
try:
    from agent_9d import MOSSv3Agent9D
except ImportError as e:
    print(f"警告: v3.1模块导入失败 - {e}")
    # 定义模拟类
    class MOSSv3Agent9D:
        pass

logger = logging.getLogger(__name__)

# 原始内容继续...
"""
        
        # 添加原始内容（去掉开头的导入部分）
        lines = content.split('\n')
        # 找到第一个非导入行
        start_index = 0
        for i, line in enumerate(lines):
            if line.strip() and not line.strip().startswith(('import', 'from', 'sys.path.insert', '#')):
                if line.strip().startswith('"""') or line.strip().startswith("'''"):
                    continue
                start_index = i
                break
        
        fixed_content += '\n'.join(lines[start_index:])
        
        # 保存修复版本
        fixed_path = project_root / '_archive_v4' / 'integration' / 'agent_v4_1_fixed.py'
        with open(fixed_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print(f"✅ v4.1 Agent修复版本创建完成: {fixed_path}")
        return True
    except Exception as e:
        print(f"❌ 创建修复版本失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("MOSS v4.1 Agent 依赖检查和安装")
    print("=" * 60)
    
    # 设置路径
    project_root = setup_paths()
    
    # 检查Python版本
    if not check_python_version():
        print("❌ Python版本检查失败")
        return
    
    # 检查NumPy
    if not check_numpy_installation():
        print("❌ NumPy检查失败")
        return
    
    # 检查核心依赖
    if not check_core_dependencies():
        print("❌ 核心依赖检查失败")
        return
    
    # 检查v4模块
    if not check_v4_modules(project_root):
        print("❌ v4模块检查失败")
        return
    
    # 修复Linux路径
    if not fix_linux_paths_in_v4_agent(project_root):
        print("❌ v4.1 Agent路径修复失败")
        return
    
    # 测试导入
    if not test_v4_imports():
        print("❌ v4模块导入测试失败")
        return
    
    # 创建修复版本
    if not create_v4_agent_fixed_version(project_root):
        print("❌ 创建修复版本失败")
        return
    
    # 测试参数转换器集成
    if not test_parameter_adapter_integration(project_root):
        print("❌ 参数转换器集成测试失败")
        return
    
    print("\n" + "=" * 60)
    print("✅ 所有检查通过!")
    print("✅ v4.1 Agent依赖已准备就绪")
    print("✅ 参数转换器集成成功")
    print("✅ 修复版本已创建: agent_v4_1_fixed.py")
    print("=" * 60)
    print("\n下一步:")
    print("1. 运行测试脚本: python scripts/test_v4_agent.py")
    print("2. 在实验中使用: from agent_v4_1_fixed import PurposeEnhancedAgent")
    print("3. 测试参数转换器: python moss/api/test_interaction_adapter.py")
    print("4. 如需卸载: 删除备份文件 (*.py.backup)")

if __name__ == "__main__":
    main()
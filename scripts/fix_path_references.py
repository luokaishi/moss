#!/usr/bin/env python3
"""
修复MOSS项目中硬编码路径引用
"""

import os
import re
from pathlib import Path

def fix_claw_references(file_path, replacements):
    """修复单个文件中的Claw路径引用"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 修复常见的Claw路径
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
    
    if content != original_content:
        print(f"🔧 修复: {file_path}")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def fix_import_statements(file_path):
    """修复导入语句中的路径引用"""
    # 只检查Python文件
    if not file_path.endswith('.py'):
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 修复常见的导入路径问题
    # 1. 检查是否有import Claw相关的语句
    # 2. 修复可能的绝对路径导入
    # 示例：from Claw.some_module import something
    pattern = r'from\s+[Cc]law[\.\\/].*import'
    if re.search(pattern, content):
        print(f"⚠️ 检测到Claw导入: {file_path}")
        # 这里应该根据实际情况修复
        # 现在先标记
        return True
    
    return False

def main():
    project_path = Path(r"C:\Users\LX\WorkBuddy\20260409105630\moss")
    
    # 定义要搜索的文件列表
    target_dirs = [
        project_path / "experiments",
        project_path / "scripts",
        project_path / "tests"
    ]
    
    # 定义要修复的路径模式
    replacements = [
        # 修复硬编码的Claw路径
        (r'C:/Users/LX/WorkBuddy/Claw/', r''),
        (r'C:\\Users\\LX\\WorkBuddy\\Claw\\', r''),
        
        # 修复绝对路径
        (r'C:[/\\]', r''),
        
        # 修复常见的路径格式
        (r'from.*Claw.*import', r'# 注意: 需要修复此导入语句'),
        
        # 修复保存文件的路径
        (r'"/path/to/', r'os.path.join(os.path.dirname(__file__), "..", "'),
        (r"\\'path/to/", r'os.path.join(os.path.dirname(__file__), "..", "')
    ]
    
    fixed_files = []
    
    for target_dir in target_dirs:
        if target_dir.exists():
            for file_path in target_dir.rglob('*.py'):
                if fix_claw_references(file_path, replacements):
                    fixed_files.append(str(file_path))
    
    print(f"\n📊 总结: 修复了 {len(fixed_files)} 个文件")
    for file in fixed_files:
        print(f"  - {file}")
    
    print("\n✅ 路径修复完成！")

if __name__ == "__main__":
    main()
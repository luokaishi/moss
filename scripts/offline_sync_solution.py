#!/usr/bin/env python3
"""
MOSS项目离线同步解决方案

由于GitHub 443端口连接失败，提供离线同步方案：
1. 创建本地Git提交
2. 生成同步包用于在其他网络环境推送
3. 提供手动同步指南
"""

import os
import sys
import json
import shutil
from datetime import datetime
from pathlib import Path
import subprocess
import hashlib

class OfflineSyncSolution:
    """离线同步解决方案"""
    
    def __init__(self, project_path):
        self.project_path = Path(project_path)
        self.sync_dir = self.project_path / ".sync_package"
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def analyze_git_status(self):
        """分析Git状态"""
        print("🔍 分析Git状态...")
        
        # 运行git status
        result = self.run_git_command(["status", "--porcelain"])
        changes = result.strip().split('\n') if result else []
        
        # 分类文件
        modified = []
        untracked = []
        
        for line in changes:
            if line:
                status = line[:2].strip()
                file_path = line[3:]
                if status == 'M':
                    modified.append(file_path)
                elif status == '??':
                    untracked.append(file_path)
        
        print(f"📊 发现 {len(modified)} 个修改文件, {len(untracked)} 个未跟踪文件")
        return modified, untracked
    
    def create_local_commit(self, commit_message=None):
        """创建本地Git提交"""
        if not commit_message:
            commit_message = f"Offline sync package - {self.timestamp}"
        
        print(f"💾 创建本地提交: {commit_message}")
        
        # 添加所有文件
        self.run_git_command(["add", "-A"])
        
        # 创建提交
        result = self.run_git_command(["commit", "-m", commit_message])
        if "nothing to commit" in result:
            print("✅ 没有需要提交的更改")
            return False
        else:
            print(f"✅ 提交创建成功")
            return True
    
    def create_sync_package(self):
        """创建同步包"""
        print(f"📦 创建同步包: {self.timestamp}")
        
        # 创建同步目录
        self.sync_dir.mkdir(exist_ok=True)
        
        # 创建清单文件
        manifest = {
            "timestamp": self.timestamp,
            "project": "MOSS",
            "version": "v5.2+",
            "description": "Offline sync package for GitHub sync"
        }
        
        # 保存Git差异
        manifest["git_diff"] = self.capture_git_diff()
        manifest["git_log"] = self.capture_git_log()
        
        # 保存清单
        manifest_file = self.sync_dir / f"manifest_{self.timestamp}.json"
        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        # 创建patch文件
        patch_file = self.create_patch_file()
        if patch_file:
            manifest["patch_file"] = str(patch_file)
        
        print(f"✅ 同步包创建完成: {self.sync_dir}")
        return manifest
    
    def capture_git_diff(self):
        """捕获Git差异"""
        result = self.run_git_command(["diff", "--cached"])
        return result if result else "No staged changes"
    
    def capture_git_log(self):
        """捕获Git日志"""
        result = self.run_git_command(["log", "--oneline", "-10"])
        return result if result else "No commits"
    
    def create_patch_file(self):
        """创建patch文件"""
        patch_file = self.sync_dir / f"changes_{self.timestamp}.patch"
        
        # 创建patch
        result = self.run_git_command(["format-patch", "HEAD~1", "-o", str(patch_file)])
        
        if result and "0001-" in result:
            return patch_file
        return None
    
    def generate_instructions(self):
        """生成同步指南"""
        instructions = f"""
# 📋 MOSS项目离线同步指南

## 当前状态
- 时间戳: {self.timestamp}
- 项目路径: {self.project_path}
- 同步包位置: {self.sync_dir}

## 同步步骤

### 1. 在当前环境（离线）
1. 确保所有更改已提交: `git add -A && git commit -m "MOSS增强组件同步"`
2. 运行此脚本创建同步包
3. 复制整个 `.sync_package` 目录到可上网的设备

### 2. 在可上网环境
1. 克隆原始仓库: `git clone https://github.com/luokaishi/moss.git`
2. 切换到MOSS目录: `cd moss`
3. 应用patch文件（如果有）:
   ```
   git apply path/to/changes_{self.timestamp}.patch
   ```
4. 或者手动合并文件（推荐）:
   - 参考 `manifest_{self.timestamp}.json` 中的文件列表
   - 逐个复制文件到对应位置
   
### 3. 提交和推送
1. 验证更改: `git status`
2. 提交更改: `git commit -m "同步MOSS增强组件: {datetime.now().strftime('%Y-%m-%d')}"`
3. 推送到GitHub: `git push origin main`

## 关键增强组件
从Claw项目需要同步的文件:
1. `upgraded_experiment_framework.py` → `experiments/`
2. `enhanced_v4_dependencies.py` → `scripts/`
3. `run_full_experiment.py` → `experiments/`
4. `quick_30min_experiment.py` → `experiments/`
5. 相关文档文件 → `docs/`

## 安全注意事项
⚠️ 确保没有敏感信息（如API密钥）被提交
"""
        
        instructions_file = self.sync_dir / f"instructions_{self.timestamp}.md"
        with open(instructions_file, 'w', encoding='utf-8') as f:
            f.write(instructions)
        
        return instructions_file
    
    def run_git_command(self, args):
        """运行Git命令"""
        try:
            cmd = ["git"] + args
            result = subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            return result.stdout + result.stderr
        except Exception as e:
            return f"Error: {str(e)}"
    
    def run(self):
        """运行完整流程"""
        print("🚀 开始离线同步解决方案...")
        
        # 1. 分析状态
        modified, untracked = self.analyze_git_status()
        
        # 2. 创建本地提交
        has_commit = self.create_local_commit()
        
        # 3. 创建同步包
        manifest = self.create_sync_package()
        
        # 4. 生成指南
        instructions_file = self.generate_instructions()
        
        print(f"\n🎉 离线同步解决方案完成!")
        print(f"📁 同步包位置: {self.sync_dir}")
        print(f"📋 指南文件: {instructions_file}")
        print(f"📊 文件统计: {len(modified)} 修改, {len(untracked)} 未跟踪")
        
        if has_commit:
            print("✅ 本地提交已创建")
        else:
            print("ℹ️  没有新的提交需要创建")
        
        return {
            "success": True,
            "sync_dir": str(self.sync_dir),
            "timestamp": self.timestamp,
            "modified_count": len(modified),
            "untracked_count": len(untracked)
        }

def main():
    """主函数"""
    project_path = r"C:\Users\LX\WorkBuddy\20260409105630\moss"
    
    if not os.path.exists(project_path):
        print(f"❌ 项目路径不存在: {project_path}")
        return
    
    print(f"🔍 项目路径: {project_path}")
    
    # 检查是否为Git仓库
    git_dir = os.path.join(project_path, ".git")
    if not os.path.exists(git_dir):
        print("⚠️  未检测到Git仓库，初始化中...")
        subprocess.run(["git", "init"], cwd=project_path)
        subprocess.run(["git", "add", "-A"], cwd=project_path)
        subprocess.run(["git", "commit", "-m", "Initial MOSS project"], cwd=project_path)
    
    # 运行离线同步解决方案
    solution = OfflineSyncSolution(project_path)
    result = solution.run()
    
    print("\n📋 下一步操作:")
    print("1. 检查 .sync_package/ 目录中的文件")
    print("2. 将整个目录复制到可上网的设备")
    print("3. 按照指南手动同步到GitHub")
    print("4. 完成后可删除 .sync_package/ 目录")

if __name__ == "__main__":
    main()
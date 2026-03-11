"""
MOSS 2.0 - Persistent State Manager
跨会话状态持久化管理

解决v1的问题：实验中断后状态丢失
"""

import json
import os
import time
import shutil
from typing import Dict, Optional, Any
from datetime import datetime
from pathlib import Path


class PersistentStateManager:
    """
    状态持久化管理器
    
    功能：
    1. 自动保存Agent状态到磁盘
    2. 支持从任意检查点恢复
    3. 多版本状态管理
    4. 自动备份和清理
    """
    
    def __init__(self, base_dir: str = "/workspace/projects/moss/v2/state"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # 子目录
        self.checkpoints_dir = self.base_dir / "checkpoints"
        self.checkpoints_dir.mkdir(exist_ok=True)
        
        self.backups_dir = self.base_dir / "backups"
        self.backups_dir.mkdir(exist_ok=True)
        
        self.current_dir = self.base_dir / "current"
        self.current_dir.mkdir(exist_ok=True)
        
        # 配置
        self.max_checkpoints = 50  # 最大检查点数
        self.max_backups = 10      # 最大备份数
        self.auto_save_interval = 300  # 5分钟自动保存
        
        self._last_auto_save = 0
    
    def save_agent_state(self, agent_id: str, state: Dict, 
                        checkpoint_name: Optional[str] = None) -> str:
        """
        保存Agent状态
        
        Args:
            agent_id: Agent标识
            state: 状态字典
            checkpoint_name: 检查点名称，None则使用时间戳
        
        Returns:
            保存的文件路径
        """
        if checkpoint_name is None:
            checkpoint_name = f"{agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 保存到检查点目录
        checkpoint_path = self.checkpoints_dir / f"{checkpoint_name}.json"
        
        # 添加元数据
        state_with_meta = {
            'agent_id': agent_id,
            'saved_at': datetime.now().isoformat(),
            'version': '2.0',
            'state': state
        }
        
        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(state_with_meta, f, indent=2, ensure_ascii=False)
        
        # 同时更新current目录（最新状态）
        current_path = self.current_dir / f"{agent_id}_current.json"
        with open(current_path, 'w', encoding='utf-8') as f:
            json.dump(state_with_meta, f, indent=2, ensure_ascii=False)
        
        # 清理旧检查点
        self._cleanup_old_checkpoints(agent_id)
        
        return str(checkpoint_path)
    
    def load_agent_state(self, agent_id: str, 
                        checkpoint_name: Optional[str] = None) -> Optional[Dict]:
        """
        加载Agent状态
        
        Args:
            agent_id: Agent标识
            checkpoint_name: 检查点名称，None则加载最新状态
        
        Returns:
            状态字典，不存在则返回None
        """
        if checkpoint_name:
            # 加载指定检查点
            checkpoint_path = self.checkpoints_dir / f"{checkpoint_name}.json"
        else:
            # 加载最新状态
            checkpoint_path = self.current_dir / f"{agent_id}_current.json"
        
        if not checkpoint_path.exists():
            return None
        
        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data.get('state', data)  # 兼容直接保存的状态
    
    def list_checkpoints(self, agent_id: Optional[str] = None) -> list:
        """
        列出所有检查点
        
        Args:
            agent_id: 筛选特定Agent，None则列出所有
        
        Returns:
            检查点信息列表
        """
        checkpoints = []
        
        for checkpoint_file in sorted(self.checkpoints_dir.glob("*.json")):
            try:
                with open(checkpoint_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if agent_id is None or data.get('agent_id') == agent_id:
                    checkpoints.append({
                        'filename': checkpoint_file.name,
                        'agent_id': data.get('agent_id'),
                        'saved_at': data.get('saved_at'),
                        'path': str(checkpoint_file)
                    })
            except:
                continue
        
        # 按时间倒序
        checkpoints.sort(key=lambda x: x['saved_at'], reverse=True)
        return checkpoints
    
    def create_backup(self, agent_id: str, backup_name: Optional[str] = None) -> str:
        """创建完整备份"""
        if backup_name is None:
            backup_name = f"{agent_id}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_path = self.backups_dir / backup_name
        backup_path.mkdir(exist_ok=True)
        
        # 备份current
        current_file = self.current_dir / f"{agent_id}_current.json"
        if current_file.exists():
            shutil.copy2(current_file, backup_path / "current.json")
        
        # 备份该Agent的所有检查点
        agent_checkpoints = list(self.checkpoints_dir.glob(f"{agent_id}_*.json"))
        checkpoints_backup = backup_path / "checkpoints"
        checkpoints_backup.mkdir(exist_ok=True)
        
        for cp in agent_checkpoints[:10]:  # 只备份最近10个
            shutil.copy2(cp, checkpoints_backup / cp.name)
        
        # 清理旧备份
        self._cleanup_old_backups()
        
        return str(backup_path)
    
    def restore_from_backup(self, backup_name: str, agent_id: str) -> bool:
        """从备份恢复"""
        backup_path = self.backups_dir / backup_name
        if not backup_path.exists():
            return False
        
        # 恢复current
        backup_current = backup_path / "current.json"
        if backup_current.exists():
            shutil.copy2(backup_current, self.current_dir / f"{agent_id}_current.json")
        
        # 恢复检查点
        checkpoints_backup = backup_path / "checkpoints"
        if checkpoints_backup.exists():
            for cp in checkpoints_backup.glob("*.json"):
                shutil.copy2(cp, self.checkpoints_dir / cp.name)
        
        return True
    
    def auto_save(self, agent_id: str, state: Dict) -> bool:
        """自动保存（带间隔控制）"""
        current_time = time.time()
        if current_time - self._last_auto_save < self.auto_save_interval:
            return False
        
        self._last_auto_save = current_time
        self.save_agent_state(agent_id, state, f"{agent_id}_auto_{int(current_time)}")
        return True
    
    def _cleanup_old_checkpoints(self, agent_id: str):
        """清理该Agent的旧检查点"""
        agent_checkpoints = list(self.checkpoints_dir.glob(f"{agent_id}_*.json"))
        
        if len(agent_checkpoints) <= self.max_checkpoints:
            return
        
        # 按修改时间排序，删除最旧的
        agent_checkpoints.sort(key=lambda x: x.stat().st_mtime)
        for old_cp in agent_checkpoints[:-self.max_checkpoints]:
            old_cp.unlink()
    
    def _cleanup_old_backups(self):
        """清理旧备份"""
        backups = list(self.backups_dir.iterdir())
        
        if len(backups) <= self.max_backups:
            return
        
        backups.sort(key=lambda x: x.stat().st_mtime)
        for old_backup in backups[:-self.max_backups]:
            if old_backup.is_dir():
                shutil.rmtree(old_backup)
    
    def get_recovery_info(self, agent_id: str) -> Dict:
        """获取恢复信息"""
        current_file = self.current_dir / f"{agent_id}_current.json"
        
        info = {
            'agent_id': agent_id,
            'has_current_state': current_file.exists(),
            'checkpoint_count': len(list(self.checkpoints_dir.glob(f"{agent_id}_*.json"))),
            'latest_checkpoint': None
        }
        
        if current_file.exists():
            stat = current_file.stat()
            info['last_saved'] = datetime.fromtimestamp(stat.st_mtime).isoformat()
        
        checkpoints = self.list_checkpoints(agent_id)
        if checkpoints:
            info['latest_checkpoint'] = checkpoints[0]
        
        return info


if __name__ == "__main__":
    # 测试
    manager = PersistentStateManager()
    
    # 模拟保存
    test_state = {
        'weights': {'survival': 0.2, 'curiosity': 0.4, 'influence': 0.3, 'optimization': 0.1},
        'performance': [0.5, 0.6, 0.7],
        'action_count': 100
    }
    
    saved_path = manager.save_agent_state("test_agent", test_state)
    print(f"状态已保存: {saved_path}")
    
    # 加载
    loaded = manager.load_agent_state("test_agent")
    print(f"加载成功: {loaded is not None}")
    
    # 列出检查点
    checkpoints = manager.list_checkpoints("test_agent")
    print(f"检查点数量: {len(checkpoints)}")
    
    # 恢复信息
    info = manager.get_recovery_info("test_agent")
    print(f"恢复信息: {info}")

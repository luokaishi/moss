"""
MOSS 2.0 - Checkpoint Manager
检查点管理器

增强的检查点功能，支持：
- 自动检查点
- 条件触发检查点
- 检查点元数据分析
"""

import json
import os
import time
from typing import Dict, List, Optional, Callable
from datetime import datetime
from pathlib import Path
import hashlib


class CheckpointManager:
    """
    检查点管理器
    
    功能：
    1. 定时自动保存
    2. 条件触发保存（重大事件、性能突破等）
    3. 检查点分析和比较
    4. 智能清理策略
    """
    
    def __init__(self, checkpoint_dir: str = "/workspace/projects/moss/v2/checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置
        self.auto_interval = 600  # 10分钟自动保存
        self.max_checkpoints = 100
        self.min_checkpoints = 10
        
        # 状态
        self.last_checkpoint_time = 0
        self.checkpoint_count = 0
        self.performance_history: List[float] = []
        
        # 检查点索引
        self._load_index()
    
    def _load_index(self):
        """加载检查点索引"""
        index_file = self.checkpoint_dir / "checkpoint_index.json"
        if index_file.exists():
            with open(index_file, 'r') as f:
                self.index = json.load(f)
        else:
            self.index = {'checkpoints': [], 'experiments': {}}
    
    def _save_index(self):
        """保存检查点索引"""
        index_file = self.checkpoint_dir / "checkpoint_index.json"
        with open(index_file, 'w') as f:
            json.dump(self.index, f, indent=2)
    
    def create_checkpoint(self, experiment_id: str, state: Dict, 
                         trigger: str = "manual", 
                         metadata: Optional[Dict] = None) -> str:
        """
        创建检查点
        
        Args:
            experiment_id: 实验标识
            state: 状态数据
            trigger: 触发原因 ('manual', 'auto', 'event', 'performance')
            metadata: 额外元数据
        
        Returns:
            检查点文件路径
        """
        timestamp = datetime.now().isoformat()
        checkpoint_id = f"{experiment_id}_{int(time.time())}"
        
        # 计算状态哈希（用于去重）
        state_hash = self._compute_hash(state)
        
        # 检查是否重复
        if self._is_duplicate(state_hash):
            return None
        
        checkpoint_data = {
            'checkpoint_id': checkpoint_id,
            'experiment_id': experiment_id,
            'timestamp': timestamp,
            'trigger': trigger,
            'state_hash': state_hash,
            'state': state,
            'metadata': metadata or {}
        }
        
        # 保存
        filename = f"{checkpoint_id}.json"
        filepath = self.checkpoint_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, indent=2)
        
        # 更新索引
        self.index['checkpoints'].append({
            'id': checkpoint_id,
            'experiment_id': experiment_id,
            'timestamp': timestamp,
            'trigger': trigger,
            'filename': filename,
            'hash': state_hash
        })
        
        if experiment_id not in self.index['experiments']:
            self.index['experiments'][experiment_id] = []
        self.index['experiments'][experiment_id].append(checkpoint_id)
        
        self._save_index()
        self.checkpoint_count += 1
        self.last_checkpoint_time = time.time()
        
        # 清理
        self._cleanup_if_needed()
        
        return str(filepath)
    
    def should_create_checkpoint(self, current_state: Dict) -> tuple:
        """
        判断是否应该创建检查点
        
        Returns:
            (should_create, reason)
        """
        current_time = time.time()
        
        # 时间间隔检查
        if current_time - self.last_checkpoint_time >= self.auto_interval:
            return True, "auto"
        
        # 性能突破检查
        current_perf = current_state.get('performance', 0)
        if self.performance_history:
            max_perf = max(self.performance_history)
            if current_perf > max_perf * 1.1:  # 性能提升10%
                return True, "performance"
        
        # 重大状态变化检查
        if current_state.get('event'):
            return True, "event"
        
        return False, None
    
    def auto_checkpoint(self, experiment_id: str, state: Dict) -> Optional[str]:
        """自动检查点（带条件判断）"""
        should_create, reason = self.should_create_checkpoint(state)
        
        if should_create:
            # 记录性能
            if 'performance' in state:
                self.performance_history.append(state['performance'])
                if len(self.performance_history) > 100:
                    self.performance_history = self.performance_history[-100:]
            
            return self.create_checkpoint(experiment_id, state, trigger=reason)
        
        return None
    
    def load_checkpoint(self, checkpoint_id: Optional[str] = None, 
                       experiment_id: Optional[str] = None,
                       latest: bool = True) -> Optional[Dict]:
        """
        加载检查点
        
        Args:
            checkpoint_id: 指定检查点ID
            experiment_id: 指定实验ID
            latest: 是否加载最新
        """
        if checkpoint_id:
            filepath = self.checkpoint_dir / f"{checkpoint_id}.json"
            if filepath.exists():
                with open(filepath, 'r') as f:
                    return json.load(f)
            return None
        
        if experiment_id and latest:
            # 找该实验的最新检查点
            exp_checkpoints = [cp for cp in self.index['checkpoints'] 
                             if cp['experiment_id'] == experiment_id]
            if exp_checkpoints:
                latest_cp = max(exp_checkpoints, key=lambda x: x['timestamp'])
                return self.load_checkpoint(checkpoint_id=latest_cp['id'])
        
        return None
    
    def compare_checkpoints(self, cp_id1: str, cp_id2: str) -> Dict:
        """比较两个检查点"""
        cp1 = self.load_checkpoint(cp_id1)
        cp2 = self.load_checkpoint(cp_id2)
        
        if not cp1 or not cp2:
            return {'error': 'Checkpoint not found'}
        
        state1 = cp1.get('state', {})
        state2 = cp2.get('state', {})
        
        comparison = {
            'checkpoint1': {'id': cp_id1, 'timestamp': cp1['timestamp']},
            'checkpoint2': {'id': cp_id2, 'timestamp': cp2['timestamp']},
            'time_diff_seconds': 0,
            'state_diff': {}
        }
        
        # 计算时间差
        t1 = datetime.fromisoformat(cp1['timestamp'])
        t2 = datetime.fromisoformat(cp2['timestamp'])
        comparison['time_diff_seconds'] = abs((t2 - t1).total_seconds())
        
        # 比较状态差异（简化版）
        common_keys = set(state1.keys()) & set(state2.keys())
        for key in common_keys:
            if state1[key] != state2[key]:
                comparison['state_diff'][key] = {
                    'old': state1[key],
                    'new': state2[key]
                }
        
        return comparison
    
    def get_experiment_timeline(self, experiment_id: str) -> List[Dict]:
        """获取实验的检查点时间线"""
        checkpoints = [cp for cp in self.index['checkpoints'] 
                      if cp['experiment_id'] == experiment_id]
        return sorted(checkpoints, key=lambda x: x['timestamp'])
    
    def analyze_progress(self, experiment_id: str) -> Dict:
        """分析实验进度"""
        timeline = self.get_experiment_timeline(experiment_id)
        
        if not timeline:
            return {'status': 'no_data'}
        
        # 加载所有状态
        states = []
        for cp_info in timeline:
            cp = self.load_checkpoint(cp_info['id'])
            if cp:
                states.append(cp.get('state', {}))
        
        if not states:
            return {'status': 'no_state_data'}
        
        # 分析
        analysis = {
            'total_checkpoints': len(timeline),
            'time_span': {
                'start': timeline[0]['timestamp'],
                'end': timeline[-1]['timestamp']
            },
            'trigger_distribution': {},
            'performance_trend': []
        }
        
        # 触发原因分布
        for cp in timeline:
            trigger = cp['trigger']
            analysis['trigger_distribution'][trigger] = \
                analysis['trigger_distribution'].get(trigger, 0) + 1
        
        # 性能趋势
        for state in states:
            if 'performance' in state:
                analysis['performance_trend'].append(state['performance'])
        
        if analysis['performance_trend']:
            analysis['performance_stats'] = {
                'initial': analysis['performance_trend'][0],
                'final': analysis['performance_trend'][-1],
                'max': max(analysis['performance_trend']),
                'min': min(analysis['performance_trend']),
                'avg': sum(analysis['performance_trend']) / len(analysis['performance_trend'])
            }
        
        return analysis
    
    def _compute_hash(self, state: Dict) -> str:
        """计算状态哈希"""
        state_str = json.dumps(state, sort_keys=True)
        return hashlib.md5(state_str.encode()).hexdigest()[:16]
    
    def _is_duplicate(self, state_hash: str) -> bool:
        """检查是否重复"""
        for cp in self.index['checkpoints'][-5:]:  # 只检查最近5个
            if cp.get('hash') == state_hash:
                return True
        return False
    
    def _cleanup_if_needed(self):
        """智能清理"""
        if self.checkpoint_count <= self.max_checkpoints:
            return
        
        # 按时间排序
        sorted_cps = sorted(self.index['checkpoints'], 
                           key=lambda x: x['timestamp'])
        
        # 保留策略：
        # 1. 保留最近的 min_checkpoints 个
        # 2. 保留所有 'performance' 和 'event' 触发的
        # 3. 删除多余的 'auto' 触发的
        
        to_keep = set()
        
        # 保留最近的
        for cp in sorted_cps[-self.min_checkpoints:]:
            to_keep.add(cp['id'])
        
        # 保留重要触发
        for cp in sorted_cps:
            if cp['trigger'] in ['performance', 'event']:
                to_keep.add(cp['id'])
        
        # 删除其他
        for cp in sorted_cps:
            if cp['id'] not in to_keep:
                filepath = self.checkpoint_dir / cp['filename']
                if filepath.exists():
                    filepath.unlink()
                self.index['checkpoints'].remove(cp)
                self.checkpoint_count -= 1
        
        self._save_index()


if __name__ == "__main__":
    # 测试
    manager = CheckpointManager()
    
    # 创建测试检查点
    for i in range(5):
        state = {
            'step': i,
            'performance': 0.5 + i * 0.1,
            'weights': {'survival': 0.2, 'curiosity': 0.4}
        }
        cp_path = manager.create_checkpoint(
            "test_exp", state, 
            trigger="auto",
            metadata={'test': True}
        )
        print(f"检查点 {i+1}: {cp_path}")
        time.sleep(0.1)
    
    # 分析
    analysis = manager.analyze_progress("test_exp")
    print(f"\n分析结果: {json.dumps(analysis, indent=2)}")

#!/usr/bin/env python3
"""
事件驱动Purpose生成器 - Week 2

将真实世界事件转换为Purpose
替代固定步长的Purpose生成
"""

from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
import time


@dataclass
class Event:
    """真实世界事件"""
    timestamp: float
    type: str
    priority: str  # low, medium, high, critical
    data: Dict
    source: str


class EventDrivenPurpose:
    """
    事件驱动的Purpose生成器
    
    核心功能:
    1. 事件检测与分类
    2. 事件到Purpose的映射
    3. Purpose优先级排序
    4. 动态Purpose生成
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.event_handlers: Dict[str, Callable] = {
            'file_change': self._handle_file_change,
            'network_error': self._handle_network_error,
            'resource_alert': self._handle_resource_alert,
            'security_threat': self._handle_security_threat,
            'system_failure': self._handle_system_failure,
        }
        self.purpose_queue: List[Dict] = []
        self.event_history: List[Event] = []
        self.max_history = self.config.get('max_history', 1000)
        
    def on_event(self, event: Dict) -> Optional[Dict]:
        """
        处理事件并生成Purpose
        
        Args:
            event: 事件数据
            
        Returns:
            生成的Purpose或None
        """
        # 创建Event对象
        event_obj = Event(
            timestamp=event.get('timestamp', time.time()),
            type=event.get('type', 'unknown'),
            priority=event.get('priority', 'medium'),
            data=event.get('data', {}),
            source=event.get('source', 'unknown'),
        )
        
        # 保存历史
        self.event_history.append(event_obj)
        if len(self.event_history) > self.max_history:
            self.event_history = self.event_history[-self.max_history:]
        
        # 查找处理器
        handler = self.event_handlers.get(event_obj.type)
        if handler:
            purpose = handler(event_obj)
            if purpose:
                self.purpose_queue.append(purpose)
                self._sort_purposes()
            return purpose
        
        return None
    
    def _handle_file_change(self, event: Event) -> Optional[Dict]:
        """文件变化 -> 文件整理任务"""
        change_type = event.data.get('type', '')
        
        if change_type == 'created':
            return {
                'name': 'organize_new_files',
                'type': 'file_organization',
                'priority': self._map_priority(event.priority),
                'description': f"Organize newly created files: {event.data.get('added', [])}",
                'trigger': event,
                'created_at': event.timestamp,
            }
        elif change_type == 'deleted':
            return {
                'name': 'cleanup_deleted_files',
                'type': 'backup_cleanup',
                'priority': self._map_priority(event.priority),
                'description': f"Cleanup after file deletion: {event.data.get('removed', [])}",
                'trigger': event,
                'created_at': event.timestamp,
            }
        elif change_type == 'modified':
            return {
                'name': 'analyze_modified_files',
                'type': 'code_review',
                'priority': self._map_priority(event.priority),
                'description': f"Review modified files: {event.data.get('modified', [])}",
                'trigger': event,
                'created_at': event.timestamp,
            }
        
        return None
    
    def _handle_network_error(self, event: Event) -> Optional[Dict]:
        """网络错误 -> 网络诊断任务"""
        return {
            'name': 'diagnose_network',
            'type': 'network_diagnosis',
            'priority': 'high',  # 网络错误通常是高优先级
            'description': f"Diagnose network issue: {event.data}",
            'trigger': event,
            'created_at': event.timestamp,
        }
    
    def _handle_resource_alert(self, event: Event) -> Optional[Dict]:
        """资源告警 -> 系统监控任务"""
        resource_type = event.data.get('resource_type', 'unknown')
        
        return {
            'name': f'monitor_{resource_type}',
            'type': 'system_monitor',
            'priority': self._map_priority(event.priority),
            'description': f"Monitor {resource_type} usage: {event.data.get('usage', 'unknown')}",
            'trigger': event,
            'created_at': event.timestamp,
        }
    
    def _handle_security_threat(self, event: Event) -> Optional[Dict]:
        """安全威胁 -> 安全扫描任务"""
        return {
            'name': 'security_scan',
            'type': 'security_scan',
            'priority': 'critical',  # 安全威胁是最高优先级
            'description': f"Security threat detected: {event.data}",
            'trigger': event,
            'created_at': event.timestamp,
        }
    
    def _handle_system_failure(self, event: Event) -> Optional[Dict]:
        """系统故障 -> 紧急恢复任务"""
        return {
            'name': 'emergency_recovery',
            'type': 'system_monitor',
            'priority': 'critical',
            'description': f"System failure: {event.data}",
            'trigger': event,
            'created_at': event.timestamp,
        }
    
    def _map_priority(self, event_priority: str) -> str:
        """映射事件优先级到Purpose优先级"""
        priority_map = {
            'critical': 'critical',
            'high': 'high',
            'medium': 'medium',
            'low': 'low',
        }
        return priority_map.get(event_priority, 'medium')
    
    def _sort_purposes(self):
        """按优先级排序Purpose队列"""
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        self.purpose_queue.sort(key=lambda p: priority_order.get(p['priority'], 2))
    
    def get_next_purpose(self) -> Optional[Dict]:
        """获取下一个Purpose"""
        if self.purpose_queue:
            return self.purpose_queue.pop(0)
        return None
    
    def get_purposes_by_priority(self, priority: str) -> List[Dict]:
        """获取指定优先级的Purpose"""
        return [p for p in self.purpose_queue if p['priority'] == priority]
    
    def get_event_statistics(self) -> Dict:
        """获取事件统计"""
        if not self.event_history:
            return {}
        
        type_counts = {}
        priority_counts = {}
        
        for event in self.event_history:
            type_counts[event.type] = type_counts.get(event.type, 0) + 1
            priority_counts[event.priority] = priority_counts.get(event.priority, 0) + 1
        
        return {
            'total_events': len(self.event_history),
            'type_distribution': type_counts,
            'priority_distribution': priority_counts,
            'pending_purposes': len(self.purpose_queue),
        }
    
    def get_status(self) -> Dict:
        """获取状态"""
        return {
            'event_history_size': len(self.event_history),
            'purpose_queue_size': len(self.purpose_queue),
            'registered_handlers': len(self.event_handlers),
        }


# 便捷函数
def create_event_driven_purpose(config: Dict = None) -> EventDrivenPurpose:
    """创建事件驱动Purpose生成器"""
    return EventDrivenPurpose(config)


if __name__ == '__main__':
    print("=" * 70)
    print("事件驱动Purpose生成器测试")
    print("=" * 70)
    
    # 创建生成器
    edp = create_event_driven_purpose()
    
    # 测试事件
    test_events = [
        {
            'type': 'file_change',
            'priority': 'medium',
            'data': {'type': 'created', 'added': ['new_file.txt']},
            'source': 'file_monitor',
        },
        {
            'type': 'network_error',
            'priority': 'high',
            'data': {'error': 'connection_timeout'},
            'source': 'network_monitor',
        },
        {
            'type': 'resource_alert',
            'priority': 'critical',
            'data': {'resource': 'cpu', 'usage': 92.5},
            'source': 'system_monitor',
        },
    ]
    
    for event in test_events:
        purpose = edp.on_event(event)
        if purpose:
            print(f"  事件: {event['type']} → Purpose: {purpose['name']} (优先级: {purpose.get('priority', 'N/A')})")
        else:
            print(f"  事件: {event['type']} → 无匹配Purpose")
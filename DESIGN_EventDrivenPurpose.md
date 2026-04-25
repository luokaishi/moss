edp.register_custom_handler('custom_event', custom_handler)
```

---

## 7. 性能优化

### 7.1 事件批处理

```python
class EventDrivenPurpose:
    def __init__(self, config):
        self.event_buffer = []
        self.batch_size = config.get('batch_size', 10)
        self.batch_timeout = config.get('batch_timeout', 1.0)
        
    def on_event(self, event: Dict):
        """批量处理事件"""
        self.event_buffer.append(event)
        
        if len(self.event_buffer) >= self.batch_size:
            self._process_batch()
            
    def _process_batch(self):
        """处理批量事件"""
        # 合并同类事件
        merged_events = self._merge_similar_events(self.event_buffer)
        
        # 生成Purpose
        for event in merged_events:
            purpose = self._generate_purpose(event)
            if purpose:
                self.purpose_queue.append(purpose)
        
        # 清空缓冲区
        self.event_buffer = []
        
    def _merge_similar_events(self, events: List[Dict]) -> List[Dict]:
        """合并相似事件"""
        merged = {}
        for event in events:
            key = f"{event['type']}:{event.get('source', 'unknown')}"
            if key not in merged:
                merged[key] = event
            else:
                # 合并数据
                merged[key]['data'].update(event['data'])
        return list(merged.values())
```

### 7.2 异步处理

```python
import asyncio

class AsyncEventDrivenPurpose(EventDrivenPurpose):
    async def on_event_async(self, event: Dict) -> Optional[Dict]:
        """异步处理事件"""
        # 异步生成Purpose
        purpose = await self._generate_purpose_async(event)
        return purpose
        
    async def _generate_purpose_async(self, event: Dict) -> Dict:
        """异步生成Purpose"""
        # 模拟异步操作
        await asyncio.sleep(0.001)
        return self._generate_purpose(event)
```

---

## 8. 测试策略

### 8.1 单元测试

```python
import unittest

class TestEventDrivenPurpose(unittest.TestCase):
    def setUp(self):
        self.edp = create_event_driven_purpose()
        
    def test_file_change_event(self):
        """测试文件变化事件处理"""
        event = {
            'type': 'file_change',
            'priority': 'medium',
            'data': {'type': 'created', 'added': ['test.txt']},
            'source': 'test'
        }
        
        purpose = self.edp.on_event(event)
        
        self.assertIsNotNone(purpose)
        self.assertEqual(purpose['type'], 'file_organization')
        self.assertIn('test.txt', purpose['description'])
        
    def test_priority_sorting(self):
        """测试优先级排序"""
        # 添加不同优先级的Purpose
        self.edp.purpose_queue = [
            {'priority': 'low', 'name': 'low_task'},
            {'priority': 'critical', 'name': 'critical_task'},
            {'priority': 'high', 'name': 'high_task'}
        ]
        
        self.edp._sort_purposes()
        
        # 验证排序
        self.assertEqual(self.edp.purpose_queue[0]['priority'], 'critical')
        self.assertEqual(self.edp.purpose_queue[1]['priority'], 'high')
        self.assertEqual(self.edp.purpose_queue[2]['priority'], 'low')
```

### 8.2 集成测试

```python
def test_integration_with_agent():
    """测试与Agent集成"""
    from agi.task_aware_agent import TaskAwareAgent
    
    agent = TaskAwareAgent('config.yaml')
    edp = create_event_driven_purpose()
    
    # 模拟文件变化
    event = {
        'type': 'file_change',
        'data': {'type': 'created', 'added': ['important.doc']}
    }
    
    # 生成Purpose
    purpose = edp.on_event(event)
    
    # 设置Agent任务
    agent.set_task(purpose)
    
    # 运行Agent
    agent._one_cycle()
    
    # 验证任务完成
    assert len(agent.task_history) > 0
```

---

## 9. 部署指南

### 9.1 配置示例

```yaml
# config/event_driven_purpose.yaml
event_driven_purpose:
  max_history: 1000
  max_queue_size: 100
  batch_size: 10
  batch_timeout: 1.0
  
  handlers:
    file_change:
      enabled: true
      priority: medium
    network_error:
      enabled: true
      priority: high
    resource_alert:
      enabled: true
      priority: high
    security_threat:
      enabled: true
      priority: critical
      
  custom_handlers:
    - type: my_custom_event
      module: custom_handlers.my_handler
      function: handle_my_event
```

### 9.2 启动脚本

```python
#!/usr/bin/env python3
"""启动EventDrivenPurpose服务"""

from agi.event_driven_purpose import create_event_driven_purpose
from agi.mves_realworld_bridge import create_bridge
import yaml

def main():
    # 加载配置
    with open('config/event_driven_purpose.yaml') as f:
        config = yaml.safe_load(f)
    
    # 创建服务
    edp = create_event_driven_purpose(config['event_driven_purpose'])
    bridge = create_bridge(config['bridge'])
    
    print("EventDrivenPurpose服务已启动")
    
    # 主循环
    while True:
        # 感知环境
        state = bridge.perceive()
        
        # 检测事件
        events = bridge.detect_events(state)
        
        # 处理事件
        for event in events:
            purpose = edp.on_event(event)
            if purpose:
                print(f"生成Purpose: {purpose['name']}")
        
        # 获取并执行Purpose
        next_purpose = edp.get_next_purpose()
        if next_purpose:
            print(f"执行: {next_purpose['description']}")
        
        time.sleep(1)

if __name__ == '__main__':
    main()
```

---

## 10. 参考

- [API_REFERENCE.md](API_REFERENCE.md) - API参考文档
- [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) - 集成指南
- [agi/event_driven_purpose.py](agi/event_driven_purpose.py) - 源代码

---

*最后更新: 2026-04-25*

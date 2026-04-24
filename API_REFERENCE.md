
#### 方法: get_recovery_stats

```python
get_recovery_stats() -> Dict
```

**返回**:
- `Dict`: 恢复统计信息

**示例**:
```python
stats = recovery.get_recovery_stats()
print(f"成功率: {stats['success_rate']:.1%}")
```

---

## Real-World Bridge API

### 快速开始

```python
from agi.mves_realworld_bridge import create_bridge

# 创建真实世界桥接器
bridge = create_bridge({
    'workspace': '/tmp/workspace',
    'checkpoint_dir': '/tmp/checkpoints'
})

# 感知环境
state = bridge.perceive()

# 获取文件变化
changes = bridge.get_recent_changes(5)
```

### 函数: create_bridge

```python
create_bridge(config: Dict) -> MvesRealWorldBridge
```

**参数**:
- `config`: 配置字典
  - `workspace`: 工作目录
  - `checkpoint_dir`: 检查点目录

**返回**:
- `MvesRealWorldBridge`: 真实世界桥接器

**示例**:
```python
bridge = create_bridge({
    'workspace': '/tmp/workspace',
    'checkpoint_dir': '/tmp/checkpoints'
})
```

### 类: MvesRealWorldBridge

#### 方法: perceive

```python
perceive() -> EnvironmentState
```

**返回**:
- `EnvironmentState`: 环境状态

**示例**:
```python
state = bridge.perceive()
print(f"互联网状态: {state.network['internet']}")
```

#### 方法: get_recent_changes

```python
get_recent_changes(seconds: int = 5) -> List[Dict]
```

**参数**:
- `seconds`: 时间窗口 (秒)

**返回**:
- `List[Dict]`: 文件变化列表

**示例**:
```python
changes = bridge.get_recent_changes(10)
for change in changes:
    print(f"文件变化: {change}")
```

#### 方法: get_status

```python
get_status() -> Dict
```

**返回**:
- `Dict`: 桥接器状态

**示例**:
```python
status = bridge.get_status()
print(f"状态历史大小: {status['state_history_size']}")
```

---

## 配置参考

### Agent配置示例

```yaml
# config/agent_config.yaml
environment:
  type: simulated
  workspace: /tmp/agent_workspace
  
agent:
  population_size: 50
  generations: 100
  mutation_rate: 0.1
  
llm:
  model: kimi-k2.5
  temperature: 0.7
  max_tokens: 2000
```

### 任务类型列表

| 任务类型 | 描述 |
|----------|------|
| `file_organization` | 文件整理 |
| `system_monitor` | 系统监控 |
| `log_analysis` | 日志分析 |
| `code_review` | 代码审查 |
| `backup_cleanup` | 备份清理 |
| `network_diagnosis` | 网络诊断 |
| `dependency_analysis` | 依赖分析 |
| `security_scan` | 安全扫描 |
| `performance_test` | 性能测试 |
| `documentation_gen` | 文档生成 |

---

*最后更新: 2026-04-24*

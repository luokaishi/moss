"""
MOSS Agent v2.0 - 真实环境版本

整合:
- SystemMonitor: 真实系统监控
- ActionExecutor: 真实行动执行
- SafetyGuard: 安全边界保护
"""

import time
import json
import os
import signal
from typing import Dict, List, Optional
from datetime import datetime

# 导入MOSS核心组件
import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 使用正确的模块路径
from core.objectives import (
    SystemState, SurvivalModule, CuriosityModule,
    InfluenceModule, OptimizationModule
)
from integration.allocator import WeightAllocator, ConflictResolver
from integration.system_monitor import SystemMonitor
from integration.action_executor import ActionExecutor


class SafetyGuard:
    """
    安全守卫 - 硬编码的安全限制
    """
    
    # 宪法约束（不可修改）
    CONSTITUTION = {
        'max_runtime_hours': 24.0,
        'max_cpu_percent': 80.0,
        'max_memory_percent': 70.0,
        'max_disk_usage': 85.0,
        'max_network_connections': 500,
        'prohibited_actions': [
            'delete_system_files',
            'modify_kernel',
            'spawn_infinite_processes',
            'fork_bomb',
        ]
    }
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.start_time = time.time()
        self.violations = []
        self.emergency_stop = False
        
        # 注册信号处理
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)
    
    def check(self, metrics: Dict) -> Dict:
        """
        全面安全检查
        """
        violations = []
        
        # 检查运行时间
        runtime_hours = (time.time() - self.start_time) / 3600
        if runtime_hours > self.CONSTITUTION['max_runtime_hours']:
            violations.append(f"Runtime: {runtime_hours:.1f}h > {self.CONSTITUTION['max_runtime_hours']}h")
        
        # 检查资源限制
        if metrics.get('cpu', {}).get('percent', 0) > self.CONSTITUTION['max_cpu_percent']:
            violations.append("CPU limit exceeded")
        
        if metrics.get('memory', {}).get('percent', 0) > self.CONSTITUTION['max_memory_percent']:
            violations.append("Memory limit exceeded")
        
        if metrics.get('disk', {}).get('percent', 0) > self.CONSTITUTION['max_disk_usage']:
            violations.append("Disk limit exceeded")
        
        # 紧急状态判断
        is_emergency = len(violations) >= 3 or self.emergency_stop
        
        if is_emergency and not self.emergency_stop:
            self._trigger_emergency_stop()
        
        return {
            'safe': len(violations) == 0,
            'violations': violations,
            'emergency': is_emergency,
            'runtime_hours': runtime_hours
        }
    
    def _trigger_emergency_stop(self):
        """触发紧急停止"""
        print(f"\n[SAFETY] 🚨 Emergency stop triggered for {self.agent_id}")
        self.emergency_stop = True
        self._emergency_save()
        os._exit(1)
    
    def _emergency_save(self):
        """紧急保存状态"""
        save_path = f"/tmp/moss_emergency_{self.agent_id}_{int(time.time())}.json"
        data = {
            'agent_id': self.agent_id,
            'violations': self.violations,
            'timestamp': time.time(),
            'runtime_hours': (time.time() - self.start_time) / 3600
        }
        with open(save_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"[SAFETY] Emergency state saved: {save_path}")
    
    def _handle_shutdown(self, signum, frame):
        """处理关闭信号"""
        print(f"\n[SAFETY] Shutdown signal: {signum}")
        self._emergency_save()
        os._exit(0)
    
    def get_status(self) -> Dict:
        """获取安全状态"""
        return {
            'runtime_hours': (time.time() - self.start_time) / 3600,
            'violations_count': len(self.violations),
            'emergency_stop': self.emergency_stop,
            'constitution': self.CONSTITUTION
        }


class MOSSAgentV2:
    """
    MOSS Agent v2.0 - 真实环境版本
    
    新特性:
    - 真实系统监控 (SystemMonitor)
    - 真实行动执行 (ActionExecutor)
    - 硬编码安全保护 (SafetyGuard)
    - 分级运行模式 (safe/demo/production)
    """
    
    def __init__(self, 
                 agent_id: str = "moss_v2_001",
                 mode: str = "safe"):
        """
        初始化
        
        Args:
            agent_id: Agent唯一标识
            mode: 运行模式
                - safe: 完全模拟，无真实操作（默认，推荐）
                - demo: 真实监控，模拟执行
                - production: 真实监控，真实执行（⚠️ 有风险）
        """
        self.agent_id = agent_id
        self.mode = mode
        self.start_time = time.time()
        
        print(f"\n{'='*60}")
        print(f"🚀 MOSS Agent v2.0 Initializing")
        print(f"{'='*60}")
        print(f"Agent ID: {agent_id}")
        print(f"Mode: {mode}")
        
        # 1. 安全守卫（始终启用）
        print(f"\n[1/4] Initializing SafetyGuard...")
        self.safety = SafetyGuard(agent_id)
        print(f"      ✅ SafetyGuard ready")
        print(f"      📋 Constitution: {list(self.safety.CONSTITUTION.keys())}")
        
        # 2. 系统监控
        print(f"\n[2/4] Initializing SystemMonitor...")
        self.monitor = SystemMonitor(agent_id)
        print(f"      ✅ SystemMonitor ready")
        
        # 3. 四目标模块
        print(f"\n[3/4] Initializing Objective Modules...")
        self.modules = [
            SurvivalModule(),
            CuriosityModule(),
            InfluenceModule(),
            OptimizationModule()
        ]
        print(f"      ✅ Modules: {[m.name for m in self.modules]}")
        
        # 4. 整合层
        print(f"\n[4/4] Initializing Integration Layer...")
        self.allocator = WeightAllocator()
        self.resolver = ConflictResolver()
        
        # 5. 行动执行器
        self.executor = ActionExecutor(agent_id)
        self.executor.set_mode(mode)
        print(f"      ✅ ActionExecutor ready (mode: {mode})")
        
        # 历史记录
        self.state_history = []
        self.decision_history = []
        
        # 统计
        self.stats = {
            'total_decisions': 0,
            'total_actions': 0,
            'safety_violations': 0,
            'start_time': self.start_time
        }
        
        print(f"\n{'='*60}")
        print(f"✅ MOSS v2.0 Ready!")
        print(f"{'='*60}\n")
    
    def step(self) -> Dict:
        """
        执行一个决策循环
        
        Returns:
            执行结果字典
        """
        # 1. 获取真实系统状态
        metrics = self.monitor.get_full_metrics()
        state = self.monitor.to_system_state()
        
        if state is None:
            # SystemState导入失败，使用模拟状态
            state = SystemState(
                resource_quota=0.5,
                resource_usage=0.3,
                uptime=(time.time() - self.start_time) / 3600,
                error_rate=0.01,
                api_calls=0,
                unique_callers=1,
                environment_entropy=0.1,
                last_backup=self.start_time
            )
        
        # 2. 安全检查
        safety_check = self.safety.check({
            'cpu': metrics.cpu,
            'memory': metrics.memory,
            'disk': metrics.disk,
            'network': metrics.network
        })
        
        if not safety_check['safe']:
            self.stats['safety_violations'] += 1
            print(f"⚠️  Safety violations: {safety_check['violations']}")
        
        if safety_check['emergency']:
            return {
                'error': 'Emergency stop triggered',
                'safety': safety_check,
                'status': 'emergency'
            }
        
        # 3. 决策
        decision = self._decide(state)
        
        # 4. 执行
        execution_result = None
        if decision.get('selected_action'):
            execution_result = self._execute(decision)
            decision['execution_result'] = execution_result
        
        return {
            'step': self.stats['total_decisions'],
            'timestamp': time.time(),
            'state': state,
            'decision': decision,
            'safety': safety_check,
            'metrics_summary': {
                'cpu_percent': metrics.cpu['percent'],
                'memory_percent': metrics.memory['percent'],
                'disk_percent': metrics.disk['percent'],
            }
        }
    
    def _decide(self, state: SystemState) -> Dict:
        """决策逻辑"""
        # 分配权重
        weights = self.allocator.allocate(state, self.modules)
        
        # 评估各目标
        objective_values = {}
        for module in self.modules:
            value = module.evaluate(state)
            objective_values[module.name] = {
                'value': value,
                'weight': module.weight
            }
        
        # 收集行动建议
        all_actions = []
        for module in self.modules:
            actions = module.get_desired_actions(state)
            for action in actions:
                action['source'] = module.name
                action['objective_value'] = objective_values[module.name]['value']
            all_actions.extend(actions)
        
        # 解决冲突
        valid_actions = self.resolver.resolve(all_actions, state)
        
        # 选择行动
        selected_action = self._select_action(valid_actions, objective_values)
        
        self.stats['total_decisions'] += 1
        
        return {
            'timestamp': time.time(),
            'system_state': self.allocator.current_state,
            'weights': weights,
            'objective_values': objective_values,
            'candidate_actions': len(all_actions),
            'valid_actions': len(valid_actions),
            'selected_action': selected_action
        }
    
    def _select_action(self, actions: List[dict], objective_values: dict) -> Optional[dict]:
        """选择最优行动"""
        if not actions:
            return None
        
        def action_score(action):
            source = action.get('source', '')
            priority_score = {'high': 1.0, 'medium': 0.6, 'low': 0.3}.get(
                action.get('priority', 'low'), 0.3
            )
            objective_weight = objective_values.get(source, {}).get('weight', 0.25)
            return priority_score * objective_weight
        
        best_action = max(actions, key=action_score)
        
        return {
            'action': best_action['action'],
            'description': best_action['description'],
            'source': best_action['source'],
            'priority': best_action['priority']
        }
    
    def _execute(self, decision: Dict) -> Dict:
        """执行行动"""
        action = decision.get('selected_action', {})
        
        result = self.executor.execute(action)
        
        self.stats['total_actions'] += 1
        
        return {
            'action': action,
            'result': result.result,
            'success': result.success,
            'mode': result.mode,
            'duration_ms': result.duration_ms
        }
    
    def run(self, steps: int = None, duration_hours: float = None):
        """
        持续运行
        
        Args:
            steps: 运行步数（可选）
            duration_hours: 运行时长小时（可选）
        """
        step_count = 0
        
        print(f"\n{'='*60}")
        print(f"🔄 Starting MOSS v2.0 Run")
        print(f"{'='*60}")
        if steps:
            print(f"Target: {steps} steps")
        if duration_hours:
            print(f"Target: {duration_hours} hours")
        print(f"{'='*60}\n")
        
        try:
            while True:
                # 检查终止条件
                if steps and step_count >= steps:
                    print(f"\n✅ Completed: reached {steps} steps")
                    break
                if duration_hours:
                    runtime = (time.time() - self.start_time) / 3600
                    if runtime >= duration_hours:
                        print(f"\n✅ Completed: reached {duration_hours} hours")
                        break
                
                # 执行一步
                result = self.step()
                step_count += 1
                
                # 显示状态
                if 'error' in result:
                    print(f"[Step {step_count}] 🚨 {result['error']}")
                    break
                
                state_name = result['decision'].get('system_state', 'unknown')
                metrics = result['metrics_summary']
                
                print(f"[Step {step_count}] State: {state_name:8s} | "
                      f"CPU: {metrics['cpu_percent']:5.1f}% | "
                      f"Mem: {metrics['memory_percent']:5.1f}% | "
                      f"Safe: {result['safety']['safe']}")
                
                # 显示执行的行动
                if result['decision'].get('execution_result'):
                    exec_result = result['decision']['execution_result']
                    if exec_result.get('success'):
                        action_name = exec_result['action'].get('action', 'unknown')
                        print(f"           └─ Action: {action_name} ({exec_result['mode']})")
                
                # 短暂休眠（避免CPU占用过高）
                time.sleep(1)
        
        except KeyboardInterrupt:
            print(f"\n\n[User] Interrupted by user")
        
        print(f"\n{'='*60}")
        print(f"🏁 Run Summary")
        print(f"{'='*60}")
        print(f"Total steps: {step_count}")
        print(f"Total decisions: {self.stats['total_decisions']}")
        print(f"Total actions: {self.stats['total_actions']}")
        print(f"Safety violations: {self.stats['safety_violations']}")
        print(f"Runtime: {(time.time() - self.start_time) / 3600:.2f} hours")
        print(f"{'='*60}\n")
        
        return self.get_report()
    
    def get_report(self) -> Dict:
        """生成运行报告"""
        return {
            'agent_id': self.agent_id,
            'mode': self.mode,
            'stats': self.stats,
            'safety': self.safety.get_status(),
            'monitor': self.monitor.get_stats(),
            'executor': self.executor.get_stats(),
            'runtime_hours': (time.time() - self.start_time) / 3600
        }
    
    def save_report(self, filepath: str = None):
        """保存报告到文件"""
        if filepath is None:
            filepath = f"/tmp/moss_{self.agent_id}_report_{int(time.time())}.json"
        
        report = self.get_report()
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Report saved: {filepath}")
        return filepath


# 测试代码
if __name__ == '__main__':
    print("\n" + "="*60)
    print("MOSS Agent v2.0 Test")
    print("="*60)
    
    # 测试1: Safe模式（推荐）
    print("\n[Test 1] Safe Mode (5 steps)...")
    agent = MOSSAgentV2("test_v2_safe", mode="safe")
    report = agent.run(steps=5)
    print(f"\nReport: {json.dumps(report, indent=2)}")
    
    # 测试2: Demo模式
    print("\n" + "="*60)
    print("[Test 2] Demo Mode (3 steps)...")
    agent2 = MOSSAgentV2("test_v2_demo", mode="demo")
    report2 = agent2.run(steps=3)
    
    print("\n" + "="*60)
    print("All tests completed!")
    print("="*60)

#!/usr/bin/env python3
"""
MOSS v5.4 - Integration Test
集成测试脚本

测试所有 v5.4 模块的协同工作:
- 协作协调器
- 通信协议
- 环境适配器
- 长期记忆

Author: MOSS Project
Date: 2026-04-03
Version: 5.4.0-dev
"""

import sys
import json
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.collaboration import CollaborationCoordinator, CollaborationMode, Task
from core.communication import CommunicationNetwork, create_knowledge_share
from core.environment_adapter import EnvironmentAdapter
from core.longterm_memory import LongTermMemory


class V54IntegrationTest:
    """v5.4 集成测试管理器"""
    
    def __init__(self):
        self.results = {
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'details': []
        }
        
        # 初始化所有模块
        print("🔧 初始化模块...")
        self.coordinator = CollaborationCoordinator(CollaborationMode.HYBRID)
        self.network = CommunicationNetwork()
        self.env_adapter = EnvironmentAdapter("./test_integration")
        self.memory = LongTermMemory("./test_integration_memory")
        
        print("   ✅ 协作协调器")
        print("   ✅ 通信网络")
        print("   ✅ 环境适配器")
        print("   ✅ 长期记忆系统")
    
    def run_test(self, name: str, test_func) -> bool:
        """运行单个测试"""
        self.results['tests_run'] += 1
        print(f"\n🧪 测试：{name}")
        
        try:
            result = test_func()
            if result:
                self.results['tests_passed'] += 1
                print(f"   ✅ 通过")
                self.results['details'].append({
                    'name': name,
                    'status': 'passed'
                })
                return True
            else:
                self.results['tests_failed'] += 1
                print(f"   ❌ 失败")
                self.results['details'].append({
                    'name': name,
                    'status': 'failed',
                    'reason': 'Test returned False'
                })
                return False
        except Exception as e:
            self.results['tests_failed'] += 1
            print(f"   ❌ 异常：{e}")
            self.results['details'].append({
                'name': name,
                'status': 'failed',
                'reason': str(e)
            })
            return False
    
    def test_collaboration(self) -> bool:
        """测试协作模块"""
        # 注册 Agent
        self.coordinator.register_agent("agent_1", {'coding': 0.9, 'analysis': 0.7})
        self.coordinator.register_agent("agent_2", {'coding': 0.6, 'analysis': 0.9})
        
        # 添加任务
        task = Task(
            id="test_task",
            description="Test task",
            difficulty=0.5,
            priority=0.8,
            required_skills=['coding']
        )
        self.coordinator.add_task(task)
        
        # 分配任务
        assignments = self.coordinator.assign_tasks()
        
        # 验证分配结果
        assigned = any(len(tasks) > 0 for tasks in assignments.values())
        
        # 完成任务
        if assigned:
            for agent_id, task_ids in assignments.items():
                for task_id in task_ids:
                    self.coordinator.complete_task(task_id, success=True)
        
        # 验证状态
        status = self.coordinator.get_status()
        return assigned and status['stats']['tasks_completed'] > 0
    
    def test_communication(self) -> bool:
        """测试通信模块"""
        # 创建信道
        self.network.create_channel("test_channel", ["agent_1", "agent_2"])
        
        # 发送消息
        msg = create_knowledge_share(
            sender="agent_1",
            receiver="agent_2",
            knowledge={'test': 'data'},
            category="test"
        )
        self.network.send_message(msg, "test_channel")
        
        # 接收消息
        messages = self.network.receive_messages("agent_2")
        
        return len(messages) > 0
    
    def test_environment(self) -> bool:
        """测试环境适配器"""
        # 写入文件
        success, _ = self.env_adapter.execute_action(
            'file_write',
            path='test.txt',
            content='Integration test content'
        )
        
        if not success:
            return False
        
        # 读取文件
        success, content = self.env_adapter.execute_action(
            'file_read',
            path='test.txt'
        )
        
        return success and 'Integration test' in content
    
    def test_memory(self) -> bool:
        """测试记忆系统"""
        # 添加记忆
        memory_id = self.memory.add_memory(
            content={'lesson': 'Integration test lesson'},
            tags=['test', 'integration'],
            importance=0.9
        )
        
        if not memory_id:
            return False
        
        # 检索记忆
        context = {'tags': ['test'], 'goal': 'find test data'}
        results = self.memory.retrieve(context, top_k=5)
        
        return len(results) > 0
    
    def test_cross_module(self) -> bool:
        """测试跨模块协作"""
        # 场景：Agent 完成任务后存储经验到记忆系统
        
        # 1. 协作任务
        self.coordinator.register_agent("agent_3", {'coding': 0.8})
        task = Task(
            id="cross_module_task",
            description="Cross-module test",
            difficulty=0.6,
            priority=0.7,
            required_skills=['coding']
        )
        self.coordinator.add_task(task)
        assignments = self.coordinator.assign_tasks()
        
        # 2. 完成任务
        for agent_id, task_ids in assignments.items():
            for task_id in task_ids:
                self.coordinator.complete_task(task_id, success=True)
                
                # 3. 存储经验到记忆
                self.memory.add_memory(
                    content={
                        'task': task_id,
                        'agent': agent_id,
                        'lesson': 'Completed cross-module task'
                    },
                    tags=['task', 'completion'],
                    importance=0.7
                )
        
        # 4. 检索记忆验证
        results = self.memory.retrieve(
            {'tags': ['task'], 'goal': 'find completed tasks'},
            top_k=5
        )
        
        return len(results) > 0
    
    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "=" * 60)
        print("🚀 MOSS v5.4 集成测试")
        print("=" * 60)
        
        # 运行测试
        self.run_test("协作模块", self.test_collaboration)
        self.run_test("通信模块", self.test_communication)
        self.run_test("环境适配器", self.test_environment)
        self.run_test("长期记忆", self.test_memory)
        self.run_test("跨模块协作", self.test_cross_module)
        
        # 打印结果
        self.print_results()
        
        # 保存结果
        self.save_results()
    
    def print_results(self):
        """打印测试结果"""
        print("\n" + "=" * 60)
        print("📊 测试结果")
        print("=" * 60)
        
        success_rate = (
            self.results['tests_passed'] / 
            max(self.results['tests_run'], 1)
        )
        
        print(f"   总测试数：{self.results['tests_run']}")
        print(f"   通过：{self.results['tests_passed']}")
        print(f"   失败：{self.results['tests_failed']}")
        print(f"   成功率：{success_rate:.1%}")
        
        if self.results['tests_failed'] > 0:
            print(f"\n   失败详情:")
            for detail in self.results['details']:
                if detail['status'] == 'failed':
                    print(f"     - {detail['name']}: {detail.get('reason', 'Unknown')}")
        
        print("=" * 60)
    
    def save_results(self, output_path: str = "experiments/results/v5.4/integration_test.json"):
        """保存测试结果"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        from datetime import datetime
        results = {
            'timestamp': datetime.now().isoformat(),
            'version': '5.4.0',
            'results': self.results,
            'success_rate': (
                self.results['tests_passed'] / 
                max(self.results['tests_run'], 1)
            )
        }
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 结果已保存：{output_file}")


def main():
    test = V54IntegrationTest()
    test.run_all_tests()


if __name__ == '__main__':
    main()

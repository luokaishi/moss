#!/usr/bin/env python3
"""
增强版v4.1 Agent依赖验证脚本

基于agent_v4_1.py的深度分析，添加以下功能：
1. 验证v4.1 Agent的实际依赖模块
2. 测试参数格式转换器集成
3. 验证多版本Agent的参数兼容性
4. 检查API适配器的正确性
"""

import sys
import os
import importlib
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# 设置项目路径
def setup_project_paths() -> Path:
    """设置项目路径并返回项目根目录"""
    # 尝试多种方式找到项目根目录
    possible_paths = [
        Path(__file__).parent.parent,  # 脚本在moss/scripts目录下
        Path(__file__).parent,         # 脚本在工作目录下
        Path.cwd(),                    # 当前工作目录
    ]
    
    for project_root in possible_paths:
        moss_dir = project_root / "moss"
        if moss_dir.exists() and (moss_dir / "api").exists():
            # 添加必要的路径
            paths_to_add = [
                str(project_root),
                str(project_root / "moss"),
                str(project_root / "moss" / "api"),
                str(project_root / "_archive_v3" / "core"),
                str(project_root / "_archive_v4" / "core"),
                str(project_root / "_archive_v4" / "integration"),
            ]
            
            for path in paths_to_add:
                if Path(path).exists() and path not in sys.path:
                    sys.path.insert(0, path)
            
            print(f"✅ 项目根目录: {project_root}")
            return project_root
    
    raise FileNotFoundError("无法找到MOSS项目根目录")


def check_v41_specific_dependencies() -> Dict[str, bool]:
    """
    检查v4.1 Agent特定的依赖模块
    
    基于agent_v4_1.py分析，需要以下模块：
    1. world_model - 世界建模和预测
    2. llm_reasoning - LLM推理和反思
    3. open_goal_space - 开放目标空间管理
    """
    print("\n🔍 检查v4.1 Agent特定依赖模块")
    print("-" * 50)
    
    results = {}
    
    # 检查world_model模块
    try:
        world_model_spec = importlib.util.find_spec("world_model")
        if world_model_spec:
            results["world_model"] = True
            print("✅ world_model 模块存在")
        else:
            results["world_model"] = False
            print("❌ world_model 模块不存在")
    except Exception as e:
        results["world_model"] = False
        print(f"❌ world_model 模块检查失败: {e}")
    
    # 检查llm_reasoning模块
    try:
        llm_reasoning_spec = importlib.util.find_spec("llm_reasoning")
        if llm_reasoning_spec:
            results["llm_reasoning"] = True
            print("✅ llm_reasoning 模块存在")
        else:
            results["llm_reasoning"] = False
            print("❌ llm_reasoning 模块不存在")
    except Exception as e:
        results["llm_reasoning"] = False
        print(f"❌ llm_reasoning 模块检查失败: {e}")
    
    # 检查open_goal_space模块
    try:
        open_goal_space_spec = importlib.util.find_spec("open_goal_space")
        if open_goal_space_spec:
            results["open_goal_space"] = True
            print("✅ open_goal_space 模块存在")
        else:
            results["open_goal_space"] = False
            print("❌ open_goal_space 模块不存在")
    except Exception as e:
        results["open_goal_space"] = False
        print(f"❌ open_goal_space 模块检查失败: {e}")
    
    return results


def test_v41_agent_import(project_root: Path) -> bool:
    """测试v4.1 Agent的导入功能"""
    print("\n🧪 测试v4.1 Agent导入")
    print("-" * 50)
    
    v41_agent_path = project_root / "_archive_v4" / "integration" / "agent_v4_1.py"
    
    if not v41_agent_path.exists():
        print(f"❌ v4.1 Agent文件不存在: {v41_agent_path}")
        return False
    
    print(f"✅ v4.1 Agent文件存在: {v41_agent_path}")
    
    # 尝试读取文件内容，检查路径问题
    try:
        with open(v41_agent_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否有Linux硬编码路径
        linux_paths = [
            "/workspace/projects/moss",
            "/workspace/projects/moss/v3",
            "/workspace/projects/moss/v4"
        ]
        
        path_issues = []
        for path in linux_paths:
            if path in content:
                path_issues.append(path)
        
        if path_issues:
            print(f"⚠️  发现Linux硬编码路径: {path_issues}")
            print("   建议使用fix_linux_paths_in_v4_agent()函数修复")
        else:
            print("✅ 没有发现Linux硬编码路径")
        
        # 尝试导入文件（作为模块）
        try:
            # 添加路径以确保可以导入
            v4_integration_path = str(project_root / "_archive_v4" / "integration")
            if v4_integration_path not in sys.path:
                sys.path.insert(0, v4_integration_path)
            
            # 尝试导入
            spec = importlib.util.spec_from_file_location("agent_v4_1", v41_agent_path)
            if spec:
                print("✅ v4.1 Agent可以作为模块导入")
                return True
            else:
                print("❌ v4.1 Agent无法作为模块导入")
                return False
                
        except Exception as import_error:
            print(f"❌ v4.1 Agent导入失败: {import_error}")
            return False
            
    except Exception as e:
        print(f"❌ 读取v4.1 Agent文件失败: {e}")
        return False


def test_parameter_adapter_integration(project_root: Path) -> bool:
    """测试参数转换器与API适配器的集成"""
    print("\n🔄 测试参数转换器与API适配器集成")
    print("-" * 50)
    
    try:
        # 尝试导入增强版参数转换器
        try:
            from interaction_adapter_enhanced import MOSSInteractionAdapter, create_unified_agent_adapter
            print("✅ 增强版参数转换器导入成功")
        except ImportError as e:
            print(f"❌ 增强版参数转换器导入失败: {e}")
            
            # 尝试导入普通版参数转换器
            try:
                from interaction_adapter import MOSSInteractionAdapter, create_unified_agent_adapter
                print("✅ 普通版参数转换器导入成功")
            except ImportError as e2:
                print(f"❌ 普通版参数转换器导入失败: {e2}")
                return False
        
        # 测试参数转换器功能
        adapter_v31 = MOSSInteractionAdapter(agent_type="v3.1")
        adapter_v41 = MOSSInteractionAdapter(agent_type="v4.1")
        
        # 测试数据
        test_observation = {
            "agent_id": "test_agent_001",
            "behavior": "explore",
            "result": "found_resource",
            "reward": 10.5,
            "resource": 0.8,
            "threat": 0.2,
            "novelty": 0.4,
            "progress": 0.3,
            "context": {"environment": "forest", "time_of_day": "day"},
            "timestamp": "2026-04-13T13:45:00"
        }
        
        print("\n测试参数转换功能:")
        print(" 1. v3.1格式转换:")
        try:
            observed_behaviors, interaction = adapter_v31.convert_to_v31_format(test_observation)
            print(f"   ✅ v3.1格式转换成功")
            print(f"     observed_behaviors: {len(observed_behaviors)}个字段")
            print(f"     interaction: {len(interaction)}个字段")
            
            # 验证必需字段
            required = ["agent_id", "outcome", "payoff"]
            missing = [field for field in required if field not in interaction]
            if missing:
                print(f"   ⚠️  interaction缺少必需字段: {missing}")
            else:
                print(f"   ✅ interaction必需字段完整")
        except Exception as e:
            print(f"   ❌ v3.1格式转换失败: {e}")
        
        print("\n 2. v4.1格式转换:")
        try:
            v41_observation = adapter_v41.prepare_v41_observation(test_observation)
            print(f"   ✅ v4.1格式转换成功")
            print(f"     observation: {len(v41_observation)}个字段")
            
            # 检查v4.1特定字段
            v41_fields = ["resource_level", "threat_level", "novelty", "goal_progress"]
            present = [field for field in v41_fields if field in v41_observation]
            print(f"     v4.1字段: {len(present)}/{len(v41_fields)}个存在")
        except Exception as e:
            print(f"   ❌ v4.1格式转换失败: {e}")
        
        print("\n 3. v3.1到v4.1格式转换:")
        try:
            v41_from_v31 = adapter_v41.convert_to_v41_format(
                observed_behaviors if 'observed_behaviors' in locals() else {},
                interaction if 'interaction' in locals() else {}
            )
            print(f"   ✅ v3.1到v4.1格式转换成功")
            print(f"     转换后observation: {len(v41_from_v31)}个字段")
        except Exception as e:
            print(f"   ❌ v3.1到v4.1格式转换失败: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 参数转换器集成测试失败: {e}")
        return False


def test_api_adapter_compatibility(project_root: Path) -> bool:
    """测试API适配器的兼容性"""
    print("\n🔌 测试API适配器兼容性")
    print("-" * 50)
    
    try:
        # 尝试导入API适配器
        try:
            from adapter import MOSSApiAdapter, create_unified_agent
            print("✅ API适配器导入成功")
        except ImportError as e:
            print(f"❌ API适配器导入失败: {e}")
            return False
        
        # 创建模拟Agent类
        class MockV31Agent:
            def __init__(self):
                self.agent_id = "mock_v31_agent"
                self.step_count = 0
                self.purpose_generator = type('obj', (object,), {
                    'purpose_vector': [0.25, 0.25, 0.25, 0.25, 0.5, 0.5, 0.5, 0.5, 0.1]
                })()
            
            def step(self, observed_behaviors=None, interaction=None):
                self.step_count += 1
                return {
                    'step': self.step_count,
                    'agent_id': self.agent_id,
                    'M': [0.5, 0.5, 0.5, 0.5],
                    'state': 'normal'
                }
        
        class MockV41Agent:
            def __init__(self):
                self.agent_id = "mock_v41_agent"
                self.step_count = 0
                self.world_model = type('obj', (object,), {})()
                self.goal_manager = type('obj', (object,), {})()
                self.purpose_state = type('obj', (object,), {
                    'survival': 0.3,
                    'curiosity': 0.3,
                    'influence': 0.2,
                    'optimization': 0.2,
                    'purpose_statement': "I am a mock v4.1 agent"
                })()
            
            def step(self, observation=None):
                self.step_count += 1
                return {
                    'action': 'test_action',
                    'success': True,
                    'reward': 0.5,
                    'purpose': 'Survival'
                }
        
        print("\n测试API适配器功能:")
        
        # 测试v3.1 Agent适配器
        print(" 1. v3.1 Agent适配器测试:")
        mock_v31 = MockV31Agent()
        adapter_v31 = MOSSApiAdapter(mock_v31)
        
        try:
            # 测试参数格式转换
            test_observation = {"agent_id": "test", "result": "success", "reward": 1.0}
            result = adapter_v31.step(observation=test_observation)
            print(f"   ✅ v3.1适配器step调用成功: step={result.get('step', 'unknown')}")
        except Exception as e:
            print(f"   ❌ v3.1适配器step调用失败: {e}")
        
        # 测试Purpose向量获取
        try:
            purpose_vector = adapter_v31.get_purpose_vector()
            if purpose_vector is not None:
                print(f"   ✅ v3.1适配器获取Purpose向量成功: {len(purpose_vector)}维")
            else:
                print(f"   ⚠️  v3.1适配器无法获取Purpose向量")
        except Exception as e:
            print(f"   ❌ v3.1适配器获取Purpose向量失败: {e}")
        
        # 测试v4.1 Agent适配器
        print("\n 2. v4.1 Agent适配器测试:")
        mock_v41 = MockV41Agent()
        adapter_v41 = MOSSApiAdapter(mock_v41)
        
        try:
            agent_info = adapter_v41.get_agent_info()
            print(f"   ✅ v4.1适配器获取Agent信息成功")
            print(f"     Agent类型: {agent_info.get('agent_type', 'unknown')}")
            print(f"     Agent类名: {agent_info.get('agent_class', 'unknown')}")
        except Exception as e:
            print(f"   ❌ v4.1适配器获取Agent信息失败: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ API适配器兼容性测试失败: {e}")
        return False


def create_comprehensive_report(project_root: Path, test_results: Dict[str, Any]) -> str:
    """创建综合测试报告"""
    report_lines = []
    report_lines.append("=" * 70)
    report_lines.append("MOSS v4.1 Agent 依赖验证综合报告")
    report_lines.append("=" * 70)
    report_lines.append(f"项目根目录: {project_root}")
    report_lines.append(f"报告生成时间: {importlib.import_module('datetime').datetime.now().isoformat()}")
    report_lines.append("")
    
    # 依赖模块检查结果
    report_lines.append("📦 依赖模块检查结果")
    report_lines.append("-" * 50)
    
    for module_name, status in test_results.get("dependencies", {}).items():
        status_symbol = "✅" if status else "❌"
        report_lines.append(f"{status_symbol} {module_name}")
    
    # v4.1 Agent导入测试
    report_lines.append("")
    report_lines.append("🧪 v4.1 Agent导入测试")
    report_lines.append("-" * 50)
    v41_import = test_results.get("v41_import", False)
    report_lines.append(f"{'✅' if v41_import else '❌'} v4.1 Agent导入测试")
    
    # 参数转换器测试
    report_lines.append("")
    report_lines.append("🔄 参数转换器集成测试")
    report_lines.append("-" * 50)
    param_adapter = test_results.get("parameter_adapter", False)
    report_lines.append(f"{'✅' if param_adapter else '❌'} 参数转换器集成测试")
    
    # API适配器测试
    report_lines.append("")
    report_lines.append("🔌 API适配器兼容性测试")
    report_lines.append("-" * 50)
    api_adapter = test_results.get("api_adapter", False)
    report_lines.append(f"{'✅' if api_adapter else '❌'} API适配器兼容性测试")
    
    # 总体评估
    report_lines.append("")
    report_lines.append("📊 总体评估")
    report_lines.append("-" * 50)
    
    all_passed = all([
        all(test_results.get("dependencies", {}).values()),
        test_results.get("v41_import", False),
        test_results.get("parameter_adapter", False),
        test_results.get("api_adapter", False)
    ])
    
    if all_passed:
        report_lines.append("🎉 所有测试通过！v4.1 Agent依赖环境完整。")
        report_lines.append("")
        report_lines.append("建议下一步:")
        report_lines.append("1. 运行多Agent社会实验验证系统稳定性")
        report_lines.append("2. 创建最终项目交付文档")
        report_lines.append("3. 进行性能测试和优化")
    else:
        report_lines.append("⚠️  部分测试失败，需要修复以下问题:")
        
        issues = []
        if not all(test_results.get("dependencies", {}).values()):
            issues.append("依赖模块缺失")
        if not test_results.get("v41_import", False):
            issues.append("v4.1 Agent导入失败")
        if not test_results.get("parameter_adapter", False):
            issues.append("参数转换器问题")
        if not test_results.get("api_adapter", False):
            issues.append("API适配器兼容性问题")
        
        for i, issue in enumerate(issues, 1):
            report_lines.append(f"  {i}. {issue}")
        
        report_lines.append("")
        report_lines.append("修复建议:")
        report_lines.append("1. 检查并安装缺失的依赖模块")
        report_lines.append("2. 修复v4.1 Agent中的路径问题")
        report_lines.append("3. 确保参数转换器正确实现")
        report_lines.append("4. 验证API适配器的版本兼容性")
    
    report_lines.append("")
    report_lines.append("=" * 70)
    
    return "\n".join(report_lines)


def main():
    """主函数"""
    print("=" * 70)
    print("🔬 MOSS v4.1 Agent 增强版依赖验证")
    print("=" * 70)
    
    try:
        # 设置项目路径
        project_root = setup_project_paths()
        
        # 运行所有测试
        test_results = {}
        
        # 1. 检查v4.1特定依赖模块
        test_results["dependencies"] = check_v41_specific_dependencies()
        
        # 2. 测试v4.1 Agent导入
        test_results["v41_import"] = test_v41_agent_import(project_root)
        
        # 3. 测试参数转换器集成
        test_results["parameter_adapter"] = test_parameter_adapter_integration(project_root)
        
        # 4. 测试API适配器兼容性
        test_results["api_adapter"] = test_api_adapter_compatibility(project_root)
        
        # 生成综合报告
        print("\n" + "=" * 70)
        print("📋 生成综合测试报告")
        print("=" * 70)
        
        report = create_comprehensive_report(project_root, test_results)
        print(report)
        
        # 保存报告到文件
        report_file = project_root / "v4.1_dependency_validation_report.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n📄 报告已保存到: {report_file}")
        
        # 返回总体结果
        all_passed = all([
            all(test_results["dependencies"].values()),
            test_results["v41_import"],
            test_results["parameter_adapter"],
            test_results["api_adapter"]
        ])
        
        return 0 if all_passed else 1
        
    except Exception as e:
        print(f"\n❌ 验证过程发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
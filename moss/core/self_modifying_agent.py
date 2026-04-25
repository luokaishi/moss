"""
Self-Modifying Agent - v7.0 Foundation

Agent 能读取、理解、修改自身代码
"""

import ast
import inspect
import shutil
import json
from typing import List, Dict, Optional, Callable, Any
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class CodeIssue:
    """代码问题"""
    type: str  # 'syntax', 'complexity', 'safety', 'performance', 'style'
    message: str
    severity: str = 'warning'  # 'error', 'warning', 'info'
    line: Optional[int] = None
    column: Optional[int] = None
    suggestion: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class CodeChange:
    """代码变更记录"""
    timestamp: str
    module_name: str
    change_type: str  # 'patch', 'refactor', 'optimize'
    description: str
    diff: str
    success: bool = False
    
    def to_dict(self) -> Dict:
        return asdict(self)


class CodeRepository:
    """代码仓库 - 管理 AGI 模块"""
    
    def __init__(self, base_path='agi/'):
        self.base_path = Path(base_path)
        self.modules = {}
        self.changes_history = []
        self._load_modules()
    
    def _load_modules(self):
        """加载所有模块"""
        if not self.base_path.exists():
            print(f"Warning: Base path {self.base_path} does not exist")
            return
        
        for py_file in self.base_path.rglob('*.py'):
            if py_file.name.startswith('__'):
                continue
            
            module_name = py_file.stem
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    code = f.read()
                    self.modules[module_name] = {
                        'path': py_file,
                        'code': code,
                        'ast': None,
                        'last_modified': datetime.fromtimestamp(py_file.stat().st_mtime)
                    }
            except Exception as e:
                print(f"Error loading {py_file}: {e}")
    
    def get_module(self, name: str) -> Optional[Dict]:
        """获取模块"""
        return self.modules.get(name)
    
    def get_module_code(self, name: str) -> Optional[str]:
        """获取模块代码"""
        module = self.modules.get(name)
        return module['code'] if module else None
    
    def update_module(self, name: str, new_code: str, backup=True) -> bool:
        """更新模块"""
        if name not in self.modules:
            print(f"Module {name} not found")
            return False
        
        # 备份旧版本
        if backup:
            self._backup(name)
        
        # 更新内存中的代码
        self.modules[name]['code'] = new_code
        
        # 写入文件
        try:
            with open(self.modules[name]['path'], 'w', encoding='utf-8') as f:
                f.write(new_code)
            self.modules[name]['last_modified'] = datetime.now()
            return True
        except Exception as e:
            print(f"Error writing module {name}: {e}")
            return False
    
    def _backup(self, name: str):
        """备份模块"""
        module = self.modules[name]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = module['path'].with_suffix(f'.{timestamp}.bak')
        
        try:
            shutil.copy(module['path'], backup_path)
            print(f"Backup created: {backup_path}")
        except Exception as e:
            print(f"Error creating backup: {e}")
    
    def list_modules(self) -> List[str]:
        """列出所有模块"""
        return list(self.modules.keys())
    
    def reload_module(self, name: str):
        """重新加载模块"""
        if name in self.modules:
            module_path = self.modules[name]['path']
            try:
                with open(module_path, 'r', encoding='utf-8') as f:
                    self.modules[name]['code'] = f.read()
                    self.modules[name]['last_modified'] = datetime.fromtimestamp(
                        module_path.stat().st_mtime
                    )
            except Exception as e:
                print(f"Error reloading {name}: {e}")
    
    def record_change(self, change: CodeChange):
        """记录代码变更"""
        self.changes_history.append(change)
        
        # 保存变更历史
        history_file = self.base_path / '.change_history.json'
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump([c.to_dict() for c in self.changes_history], f, indent=2)
        except Exception as e:
            print(f"Error saving change history: {e}")


class CodeAnalyzer:
    """代码分析器 - 检查代码质量和问题"""
    
    def __init__(self):
        self.issues = []
        self.metrics = {}
    
    def analyze(self, code: str, module_name: str = '') -> List[CodeIssue]:
        """分析代码"""
        self.issues = []
        self.metrics = {
            'lines': len(code.split('\n')),
            'functions': 0,
            'classes': 0,
            'imports': 0
        }
        
        try:
            tree = ast.parse(code)
            
            # 收集基本指标
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    self.metrics['functions'] += 1
                    self._check_function(node)
                elif isinstance(node, ast.ClassDef):
                    self.metrics['classes'] += 1
                elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    self.metrics['imports'] += 1
            
            # 运行各种检查
            self._check_syntax(tree)
            self._check_complexity(tree)
            self._check_safety(tree)
            self._check_performance(tree)
            self._check_style(tree)
            
            return self.issues
            
        except SyntaxError as e:
            self.issues.append(CodeIssue(
                type='syntax',
                message=str(e),
                severity='error',
                line=e.lineno,
                column=e.offset
            ))
            return self.issues
    
    def _check_syntax(self, tree):
        """检查语法 (ast.parse 已经检查)"""
        pass
    
    def _check_function(self, node: ast.FunctionDef):
        """检查单个函数"""
        # 检查函数长度
        if hasattr(node, 'end_lineno') and node.end_lineno:
            lines = node.end_lineno - node.lineno
            if lines > 50:
                self.issues.append(CodeIssue(
                    type='complexity',
                    message=f"Function '{node.name}' is too long ({lines} lines)",
                    severity='warning',
                    line=node.lineno,
                    suggestion=f"Consider breaking '{node.name}' into smaller functions"
                ))
            
            if lines > 100:
                self.issues.append(CodeIssue(
                    type='complexity',
                    message=f"Function '{node.name}' is extremely long ({lines} lines)",
                    severity='error',
                    line=node.lineno,
                    suggestion=f"Refactor '{node.name}' - it's too complex"
                ))
        
        # 检查参数数量
        num_args = len(node.args.args)
        if num_args > 6:
            self.issues.append(CodeIssue(
                type='complexity',
                message=f"Function '{node.name}' has too many arguments ({num_args})",
                severity='warning',
                line=node.lineno,
                suggestion="Consider using a dataclass or config object for parameters"
            ))
    
    def _check_complexity(self, tree):
        """检查复杂度"""
        # 检查嵌套深度
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                # 简化检查：统计嵌套块
                pass
    
    def _check_safety(self, tree):
        """检查安全性"""
        dangerous_functions = ['exec', 'eval', '__import__', 'os.system', 'subprocess.call']
        dangerous_modules = ['pickle', 'marshal', 'ctypes']
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in dangerous_functions:
                        self.issues.append(CodeIssue(
                            type='safety',
                            message=f"Potentially dangerous function: {node.func.id}()",
                            severity='error',
                            line=getattr(node, 'lineno', None),
                            suggestion=f"Avoid using {node.func.id}() - security risk"
                        ))
            
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in dangerous_modules:
                        self.issues.append(CodeIssue(
                            type='safety',
                            message=f"Potentially dangerous import: {alias.name}",
                            severity='warning',
                            line=getattr(node, 'lineno', None)
                        ))
    
    def _check_performance(self, tree):
        """检查性能问题"""
        # 检查列表推导式 vs 循环
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                # 检查是否在循环中构建列表
                parent = getattr(node, 'parent', None)
                # 简化实现
                pass
    
    def _check_style(self, tree):
        """检查代码风格"""
        # 检查类名规范 (CamelCase)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if not node.name[0].isupper():
                    self.issues.append(CodeIssue(
                        type='style',
                        message=f"Class name '{node.name}' should use CamelCase",
                        severity='info',
                        line=node.lineno
                    ))
    
    def get_metrics(self) -> Dict:
        """获取代码指标"""
        return self.metrics.copy()


class PatchGenerator:
    """补丁生成器 - 生成代码修复建议"""
    
    def __init__(self):
        self.analyzer = CodeAnalyzer()
        self.patch_strategies = {
            'complexity': self._fix_complexity,
            'performance': self._fix_performance,
            'style': self._fix_style,
        }
    
    def generate_patch(self, module_code: str, issue: CodeIssue) -> Optional[str]:
        """生成补丁"""
        strategy = self.patch_strategies.get(issue.type)
        if strategy:
            return strategy(module_code, issue)
        return None
    
    def _fix_complexity(self, code: str, issue: CodeIssue) -> Optional[str]:
        """修复复杂度问题"""
        # 这是一个简化实现
        # 实际实现需要更复杂的 AST 操作
        
        if 'too long' in issue.message.lower():
            # 建议：添加注释标记需要重构
            lines = code.split('\n')
            if issue.line and 0 < issue.line <= len(lines):
                indent = len(lines[issue.line - 1]) - len(lines[issue.line - 1].lstrip())
                marker = ' ' * indent + '# TODO: Refactor - function too long\n'
                lines.insert(issue.line - 1, marker)
                return '\n'.join(lines)
        
        return None
    
    def _fix_performance(self, code: str, issue: CodeIssue) -> Optional[str]:
        """修复性能问题"""
        # 简化实现
        return None
    
    def _fix_style(self, code: str, issue: CodeIssue) -> Optional[str]:
        """修复风格问题"""
        # 简化实现
        return None
    
    def suggest_refactoring(self, code: str, module_name: str = '') -> List[Dict]:
        """建议重构"""
        issues = self.analyzer.analyze(code, module_name)
        suggestions = []
        
        for issue in issues:
            patch = self.generate_patch(code, issue)
            suggestions.append({
                'issue': issue.to_dict(),
                'patch_available': patch is not None,
                'patch': patch
            })
        
        return suggestions


class SelfModifyingAgent:
    """自修改 Agent - 核心类
    
    能够读取、理解、分析和修改自身代码
    """
    
    def __init__(self, base_path='agi/'):
        self.repository = CodeRepository(base_path)
        self.analyzer = CodeAnalyzer()
        self.patch_generator = PatchGenerator()
        self.self_model = {}  # 自我模型
        
        # 构建自我模型
        self._build_self_model()
    
    def _build_self_model(self):
        """构建自我模型 - 了解自己的能力"""
        self.self_model = {
            'modules': self.repository.list_modules(),
            'capabilities': [
                'code_reading',
                'code_analysis',
                'code_backup',
                'simple_patching',
            ],
            'limitations': [
                'cannot_modify_own_core_logic_yet',
                'patches_are_suggestions_only',
                'requires_human_approval_for_changes',
            ],
            'base_path': str(self.repository.base_path)
        }
    
    def introspect(self) -> Dict:
        """自我反思 - 返回当前状态"""
        return {
            'self_model': self.self_model,
            'available_modules': self.repository.list_modules(),
            'total_modules': len(self.repository.modules),
            'change_history_count': len(self.repository.changes_history)
        }
    
    def analyze_self(self) -> Dict[str, List[CodeIssue]]:
        """分析自身代码"""
        results = {}
        
        for name, module in self.repository.modules.items():
            issues = self.analyzer.analyze(module['code'], name)
            if issues:
                results[name] = issues
        
        return results
    
    def analyze_module(self, module_name: str) -> Optional[Dict]:
        """分析特定模块"""
        code = self.repository.get_module_code(module_name)
        if not code:
            return None
        
        issues = self.analyzer.analyze(code, module_name)
        metrics = self.analyzer.get_metrics()
        
        return {
            'module_name': module_name,
            'metrics': metrics,
            'issues': [i.to_dict() for i in issues],
            'issue_count': len(issues),
            'error_count': sum(1 for i in issues if i.severity == 'error'),
            'warning_count': sum(1 for i in issues if i.severity == 'warning'),
        }
    
    def suggest_improvements(self, module_name: str) -> List[Dict]:
        """建议改进"""
        code = self.repository.get_module_code(module_name)
        if not code:
            return []
        
        return self.patch_generator.suggest_refactoring(code, module_name)
    
    def apply_patch(self, module_name: str, new_code: str, 
                    description: str = '') -> bool:
        """应用补丁"""
        # 先验证新代码
        try:
            ast.parse(new_code)
        except SyntaxError as e:
            print(f"Syntax error in patch: {e}")
            return False
        
        # 应用更新
        success = self.repository.update_module(module_name, new_code)
        
        # 记录变更
        if success:
            change = CodeChange(
                timestamp=datetime.now().isoformat(),
                module_name=module_name,
                change_type='patch',
                description=description,
                diff='patch applied',
                success=True
            )
            self.repository.record_change(change)
            
            # 更新自我模型
            self._build_self_model()
        
        return success
    
    def get_module_info(self, module_name: str) -> Optional[Dict]:
        """获取模块信息"""
        module = self.repository.get_module(module_name)
        if not module:
            return None
        
        return {
            'name': module_name,
            'path': str(module['path']),
            'lines': len(module['code'].split('\n')),
            'last_modified': module['last_modified'].isoformat(),
        }
    
    def search_code(self, pattern: str) -> List[Dict]:
        """搜索代码"""
        results = []
        
        for name, module in self.repository.modules.items():
            if pattern in module['code']:
                lines = module['code'].split('\n')
                matching_lines = [
                    {'line_num': i+1, 'content': line}
                    for i, line in enumerate(lines)
                    if pattern in line
                ]
                
                results.append({
                    'module': name,
                    'matches': len(matching_lines),
                    'lines': matching_lines[:5]  # 限制结果数量
                })
        
        return results


def demo():
    """演示自修改 Agent"""
    print("=" * 60)
    print("Self-Modifying Agent Demo")
    print("=" * 60)
    
    # 创建 Agent
    agent = SelfModifyingAgent(base_path='agi/')
    
    # 自我反思
    print("\n1. Self-Introspection:")
    introspection = agent.introspect()
    print(f"   Available modules: {introspection['total_modules']}")
    print(f"   Capabilities: {introspection['self_model']['capabilities']}")
    
    # 列出模块
    print("\n2. Available Modules:")
    for module_name in agent.repository.list_modules()[:10]:
        info = agent.get_module_info(module_name)
        print(f"   - {module_name}: {info['lines']} lines")
    
    # 分析模块
    print("\n3. Module Analysis (agent.py):")
    analysis = agent.analyze_module('agent')
    if analysis:
        print(f"   Lines: {analysis['metrics']['lines']}")
        print(f"   Functions: {analysis['metrics']['functions']}")
        print(f"   Classes: {analysis['metrics']['classes']}")
        print(f"   Issues: {analysis['issue_count']}")
        
        if analysis['issues']:
            print("\n   Issues found:")
            for issue in analysis['issues'][:3]:
                print(f"   - [{issue['severity'].upper()}] {issue['message']}")
    
    # 搜索代码
    print("\n4. Code Search ('def learn'):")
    search_results = agent.search_code('def learn')
    for result in search_results[:3]:
        print(f"   Found in {result['module']}: {result['matches']} matches")
    
    print("\n" + "=" * 60)
    print("Demo Complete")
    print("=" * 60)


if __name__ == '__main__':
    demo()

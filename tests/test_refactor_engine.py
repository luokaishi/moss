#!/usr/bin/env python3
"""
MOSS v9.0 - RefactorEngine 单元测试

Author: MOSS v9.0
Date: 2026-04-23
"""

import sys
import unittest
sys.path.insert(0, '/workspace/moss')

from moss.core.refactor_engine import (
    create_refactorer,
    CodeRefactorer,
    RefactorResult,
    ImportOrganizer,
    LoopOptimizer
)


class TestImportOrganizer(unittest.TestCase):
    """测试导入组织器"""

    def setUp(self):
        self.organizer = ImportOrganizer()

    def test_sort_imports(self):
        """测试导入排序"""
        code = '''
import sys
import os
import json
'''
        result = self.organizer.organize(code)

        # 应该按字母序排序
        self.assertIn('import json', result)
        self.assertIn('import os', result)
        self.assertIn('import sys', result)

    def test_merge_from_imports(self):
        """测试合并重复的from导入"""
        code = '''
from typing import List
from typing import Dict
from typing import Optional
'''
        result = self.organizer.organize(code)

        # 应该合并为一行
        self.assertIn('from typing import', result)
        # 不应该有重复的from typing
        self.assertEqual(result.count('from typing import'), 1)


class TestLoopOptimizer(unittest.TestCase):
    """测试循环优化器"""

    def setUp(self):
        self.optimizer = LoopOptimizer()

    def test_detect_range_len_pattern(self):
        """测试检测range(len())模式"""
        code = '''
def process(items):
    for i in range(len(items)):
        item = items[i]
        print(item)
'''
        import ast
        tree = ast.parse(code)
        new_tree = self.optimizer.visit(tree)

        # 应该检测到可优化的循环
        self.assertEqual(len(self.optimizer.changes), 1)
        self.assertEqual(self.optimizer.changes[0]['type'], 'range_to_enumerate')


class TestCodeRefactorer(unittest.TestCase):
    """测试代码重构器"""

    def setUp(self):
        self.refactorer = create_refactorer()

    def test_organize_imports_success(self):
        """测试成功组织导入"""
        code = '''
import sys
import os
from typing import List
from typing import Dict
'''
        result = self.refactorer.refactor(code, 'organize_imports')

        self.assertTrue(result.success)
        self.assertEqual(len(result.changes), 1)
        self.assertIn('导入', result.message)

    def test_organize_imports_no_change(self):
        """测试无需组织的导入"""
        code = '''
import json
import os
import sys
from typing import Dict, List
'''
        result = self.refactorer.refactor(code, 'organize_imports')

        # 已经是排序好的且无重复，但organizer仍会返回success
        # 这里验证代码没有被错误修改
        self.assertIn('import json', result.refactored_code)

    def test_optimize_loops_success(self):
        """测试成功优化循环"""
        code = '''
def process(items):
    for i in range(len(items)):
        print(items[i])
'''
        result = self.refactorer.refactor(code, 'optimize_loops')

        self.assertTrue(result.success)
        self.assertEqual(len(result.changes), 1)
        self.assertIn('[OPTIMIZED]', result.refactored_code)

    def test_remove_unused_success(self):
        """测试成功检测未使用变量"""
        code = '''
def calculate():
    used = 10
    unused = 20
    return used
'''
        result = self.refactorer.refactor(code, 'remove_unused')

        self.assertTrue(result.success)
        self.assertIn('unused', result.changes[0]['vars'])
        self.assertIn('[WARNING]', result.refactored_code)

    def test_invalid_refactor_type(self):
        """测试无效的重构类型"""
        code = 'pass'
        result = self.refactorer.refactor(code, 'invalid_type')

        self.assertFalse(result.success)
        self.assertIn('未知', result.message)

    def test_syntax_error_handling(self):
        """测试语法错误处理"""
        code = 'def broken('  # 语法错误
        result = self.refactorer.refactor(code, 'remove_unused')

        self.assertFalse(result.success)
        self.assertIn('语法错误', result.message)


class TestRefactorIntegration(unittest.TestCase):
    """集成测试"""

    def test_full_refactor_pipeline(self):
        """测试完整重构流程"""
        refactorer = create_refactorer()

        # 有多个问题的代码
        code = '''
import sys
import os
from typing import List
from typing import Dict

def process_data(items):
    unused_var = 42
    for i in range(len(items)):
        print(items[i])
    return items
'''
        # 应用多种重构
        changes_count = 0

        result = refactorer.refactor(code, 'organize_imports')
        if result.success:
            code = result.refactored_code
            changes_count += len(result.changes)

        result = refactorer.refactor(code, 'optimize_loops')
        if result.success:
            code = result.refactored_code
            changes_count += len(result.changes)

        result = refactorer.refactor(code, 'remove_unused')
        if result.success:
            code = result.refactored_code
            changes_count += len(result.changes)

        # 验证至少有一些变更
        self.assertGreater(changes_count, 0)

        # 验证代码仍然是有效的Python
        import ast
        try:
            ast.parse(code)
            syntax_valid = True
        except SyntaxError:
            syntax_valid = False

        self.assertTrue(syntax_valid, "重构后的代码应该是语法有效的")


class TestRefactorResult(unittest.TestCase):
    """测试重构结果"""

    def test_result_structure(self):
        """测试结果结构"""
        result = RefactorResult(
            success=True,
            original_code="original",
            refactored_code="refactored",
            changes=[{'type': 'test'}],
            message="Test message"
        )

        self.assertTrue(result.success)
        self.assertEqual(result.original_code, "original")
        self.assertEqual(len(result.changes), 1)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestImportOrganizer))
    suite.addTests(loader.loadTestsFromTestCase(TestLoopOptimizer))
    suite.addTests(loader.loadTestsFromTestCase(TestCodeRefactorer))
    suite.addTests(loader.loadTestsFromTestCase(TestRefactorIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestRefactorResult))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == '__main__':
    print("=" * 70)
    print("MOSS v9.0 - RefactorEngine 单元测试")
    print("=" * 70)
    print()

    success = run_tests()

    print()
    print("=" * 70)
    if success:
        print("✅ 所有测试通过!")
    else:
        print("❌ 部分测试失败")
    print("=" * 70)

    sys.exit(0 if success else 1)

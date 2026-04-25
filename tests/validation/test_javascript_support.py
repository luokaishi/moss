#!/usr/bin/env python3
"""
C.2 JavaScript试点验证

验证JavaScript语言支持的基础功能：
1. JavaScriptParser 能正确解析JS代码
2. JavaScriptAnalyzer 能检测常见问题
3. JavaScriptRefactorer 能执行基础重构
4. LanguageRegistry 正确注册JS组件
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from moss.core.language import (
    LanguageType, LanguageRegistry,
    JavaScriptParser, JavaScriptAnalyzer, JavaScriptRefactorer
)


def test_registry():
    """测试注册中心"""
    print("\n📋 测试1: LanguageRegistry 注册")
    
    assert LanguageRegistry.is_language_supported(LanguageType.JAVASCRIPT), "JavaScript应已注册"
    
    parser = LanguageRegistry.get_parser(LanguageType.JAVASCRIPT)
    analyzer = LanguageRegistry.get_analyzer(LanguageType.JAVASCRIPT)
    refactorer = LanguageRegistry.get_refactorer(LanguageType.JAVASCRIPT)
    
    assert parser is not None, "JavaScriptParser应存在"
    assert analyzer is not None, "JavaScriptAnalyzer应存在"
    assert refactorer is not None, "JavaScriptRefactorer应存在"
    
    print("   ✅ JavaScript组件已正确注册")
    return True


def test_parser():
    """测试解析器"""
    print("\n📋 测试2: JavaScriptParser 解析")
    
    code = '''
import React from 'react';
import { useState, useEffect } from 'react';
const lodash = require('lodash');

class MyComponent extends React.Component {
    constructor(props) {
        super(props);
        this.state = { count: 0 };
    }
    
    handleClick() {
        this.setState({ count: this.state.count + 1 });
    }
    
    render() {
        return React.createElement('button', { onClick: () => this.handleClick() }, 
            `Count: ${this.state.count}`);
    }
}

function helperFunction(x) {
    if (x > 10) {
        return x * 2;
    }
    return x;
}

const arrowFunc = (a, b) => a + b;

export default MyComponent;
'''
    
    parser = JavaScriptParser()
    result = parser.parse(code, 'test.js')
    
    assert result.success, f"解析应成功: {result.errors}"
    assert result.language == LanguageType.JAVASCRIPT
    
    # 验证符号提取
    expected_symbols = {'MyComponent', 'helperFunction', 'arrowFunc', 'handleClick', 'render'}
    for sym in expected_symbols:
        assert sym in result.symbols, f"应包含符号: {sym}"
    
    # 验证导入提取
    assert 'react' in result.imports or 'React' in str(result.imports)
    assert 'lodash' in result.imports
    
    print(f"   ✅ 解析成功")
    print(f"      - 符号: {len(result.symbols)}个")
    print(f"      - 导入: {len(result.imports)}个")
    print(f"      - 函数: {len(result.ast.get('functions', []))}个")
    print(f"      - 类: {len(result.ast.get('classes', []))}个")
    
    return True


def test_analyzer():
    """测试分析器"""
    print("\n📋 测试3: JavaScriptAnalyzer 分析")
    
    code = '''
import React from 'react';
import unusedModule from 'unused-module';

function longFunction() {
    // 这是一个很长的函数
    var x = 1;
    console.log('debug');
    
    if (x > 0) {
        if (x < 10) {
            while (x < 5) {
                x++;
            }
        }
    }
    
    return x;
}

function simpleFunc() {
    return 42;
}
'''
    
    parser = JavaScriptParser()
    analyzer = JavaScriptAnalyzer()
    
    parse_result = parser.parse(code, 'test.js')
    
    # 传入原始内容用于分析（轻量级解析器不存储内容）
    analysis = analyzer.analyze(parse_result, content=code)
    
    print(f"   ✅ 分析完成")
    print(f"      - 问题数: {len(analysis.issues)}")
    print(f"      - 复杂度: {analysis.complexity}")
    print(f"      - 可维护性: {analysis.maintainability_index:.1f}")
    
    # 验证检测到的问题类型
    issue_types = {issue['type'] for issue in analysis.issues}
    
    # 应该检测到var使用
    assert 'prefer_const_let' in issue_types or len(analysis.issues) > 0, "应检测到代码问题"
    
    # 应该检测到console.log
    assert any('console' in issue.get('message', '') for issue in analysis.issues), "应检测到console.log"
    
    return True


def test_refactorer():
    """测试重构器"""
    print("\n📋 测试4: JavaScriptRefactorer 重构")
    
    code = '''import lodash from 'lodash';
import React from 'react';
import unused from 'unused-pkg';

const helper = require('./helper');

var x = 10;
console.log('test');
var y = 20;
'''
    
    parser = JavaScriptParser()
    refactorer = JavaScriptRefactorer()
    
    parse_result = parser.parse(code, 'test.js')
    
    # 测试1: 整理导入
    result1 = refactorer.refactor(parse_result, 'organize_imports', {'content': code})
    assert result1.success, "整理导入应成功"
    
    # 测试2: 转换var
    result2 = refactorer.refactor(parse_result, 'convert_var_to_const', {'content': code})
    assert result2.success, "转换var应成功"
    assert 'const' in result2.new_content, "应包含const"
    
    # 测试3: 移除console.log
    result3 = refactorer.refactor(parse_result, 'remove_console_logs', {'content': code})
    assert result3.success, "移除console.log应成功"
    assert 'console.log' not in result3.new_content, "不应包含console.log"
    
    print("   ✅ 重构操作成功")
    print(f"      - 整理导入: ✓")
    print(f"      - 转换var: {result2.changes[0].get('count', 0)}处")
    print(f"      - 移除console: {result3.changes[0].get('count', 0)}处")
    
    return True


def test_cross_language():
    """测试跨语言对比"""
    print("\n📋 测试5: 跨语言支持对比")
    
    supported = LanguageRegistry.get_supported_languages()
    
    print(f"   ✅ 支持的语言: {[l.value for l in supported]}")
    
    assert LanguageType.PYTHON in supported, "应支持Python"
    assert LanguageType.JAVASCRIPT in supported, "应支持JavaScript"
    
    # 对比Python和JavaScript的组件
    py_parser = LanguageRegistry.get_parser(LanguageType.PYTHON)
    js_parser = LanguageRegistry.get_parser(LanguageType.JAVASCRIPT)
    
    assert type(py_parser).__name__ == 'PythonParser'
    assert type(js_parser).__name__ == 'JavaScriptParser'
    
    print("   ✅ Python与JavaScript解析器共存")
    
    return True


def run_all_tests():
    """运行所有测试"""
    print("=" * 70)
    print("C.2 JavaScript试点验证")
    print("=" * 70)
    
    tests = [
        ("注册中心", test_registry),
        ("解析器", test_parser),
        ("分析器", test_analyzer),
        ("重构器", test_refactorer),
        ("跨语言", test_cross_language),
    ]
    
    results = []
    all_passed = True
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append({'name': name, 'passed': result})
            if not result:
                all_passed = False
        except Exception as e:
            print(f"   ❌ 错误: {e}")
            results.append({'name': name, 'passed': False, 'error': str(e)})
            all_passed = False
    
    print("\n" + "=" * 70)
    print("测试摘要")
    print("=" * 70)
    
    passed = sum(1 for r in results if r['passed'])
    total = len(results)
    
    print(f"通过: {passed}/{total}")
    
    if all_passed:
        print("\n✅ JavaScript试点验证通过!")
        print("   语言抽象层有效，支持多语言扩展")
    else:
        print(f"\n❌ {total - passed} 个测试失败")
    
    print("=" * 70)
    
    # 保存结果
    result_path = Path(__file__).parent.parent / 'test_results' / 'c2_javascript.json'
    result_path.parent.mkdir(exist_ok=True)
    
    with open(result_path, 'w') as f:
        json.dump({
            'test': 'C.2 JavaScript Support',
            'timestamp': __import__('time').strftime('%Y-%m-%d %H:%M:%S'),
            'passed': all_passed,
            'results': results,
        }, f, indent=2)
    
    print(f"\n📄 结果保存: {result_path}")
    
    return all_passed


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)

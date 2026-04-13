#!/usr/bin/env python3
"""
GitHub API Token 测试脚本

测试GitHub API Token配置是否正确
支持模拟模式和真实模式
"""

import os
import sys
import json
import requests
from pathlib import Path
from typing import Optional, Dict, Any


class GitHubTokenTester:
    """GitHub API Token测试器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化测试器
        
        Args:
            config_path: API配置文件路径
        """
        self.config_path = config_path or "integration/api_config.json"
        self.token = None
        self.simulation_mode = False
        self.load_token()
    
    def load_token(self) -> bool:
        """
        加载GitHub token
        
        Returns:
            True如果成功加载（包括模拟模式），False如果失败
        """
        # 1. 尝试从配置文件加载
        config_path = Path(self.config_path)
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    token = config.get('github_token', '')
                    if token and token != 'YOUR_GITHUB_PERSONAL_ACCESS_TOKEN':
                        self.token = token
                        print(f"✅ 从配置文件加载token: {self.config_path}")
                        return True
            except Exception as e:
                print(f"⚠️  读取配置文件失败: {e}")
        
        # 2. 尝试从环境变量加载
        env_token = os.getenv('GITHUB_TOKEN')
        if env_token:
            self.token = env_token
            print("✅ 从环境变量加载token: GITHUB_TOKEN")
            return True
        
        # 3. 使用模拟模式
        print("⚠️  未找到有效GitHub token，启用模拟模式")
        self.simulation_mode = True
        return True
    
    def test_connection(self) -> Dict[str, Any]:
        """
        测试GitHub API连接
        
        Returns:
            测试结果字典
        """
        if self.simulation_mode:
            return {
                'success': True,
                'mode': 'simulation',
                'message': '运行在模拟模式，无真实API调用',
                'user': 'simulation_user',
                'rate_limit': {'limit': 5000, 'remaining': 5000, 'reset': 0}
            }
        
        if not self.token:
            return {
                'success': False,
                'mode': 'none',
                'error': '未配置GitHub token',
                'suggestion': '请配置GITHUB_TOKEN环境变量或创建api_config.json文件'
            }
        
        try:
            # 测试基本API连接
            headers = {
                'Authorization': f'token {self.token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            # 测试用户API
            user_response = requests.get(
                'https://api.github.com/user',
                headers=headers,
                timeout=10
            )
            
            if user_response.status_code == 200:
                user_data = user_response.json()
                
                # 测试速率限制API
                rate_response = requests.get(
                    'https://api.github.com/rate_limit',
                    headers=headers,
                    timeout=10
                )
                
                rate_data = rate_response.json() if rate_response.status_code == 200 else {}
                
                return {
                    'success': True,
                    'mode': 'real',
                    'message': 'GitHub API连接成功',
                    'user': {
                        'login': user_data.get('login', 'unknown'),
                        'name': user_data.get('name', 'unknown'),
                        'email': user_data.get('email', 'unknown'),
                        'public_repos': user_data.get('public_repos', 0)
                    },
                    'rate_limit': rate_data.get('resources', {}).get('core', {})
                }
            else:
                return {
                    'success': False,
                    'mode': 'real',
                    'error': f'API请求失败: {user_response.status_code}',
                    'response': user_response.text[:200] if user_response.text else 'No response'
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'mode': 'real',
                'error': '连接超时',
                'suggestion': '请检查网络连接'
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'mode': 'real',
                'error': '网络连接错误',
                'suggestion': '请检查网络设置'
            }
        except Exception as e:
            return {
                'success': False,
                'mode': 'real',
                'error': f'未知错误: {str(e)}',
                'suggestion': '请检查token权限和格式'
            }
    
    def test_search_api(self) -> Dict[str, Any]:
        """
        测试GitHub搜索API
        
        Returns:
            搜索测试结果
        """
        if self.simulation_mode:
            return {
                'success': True,
                'mode': 'simulation',
                'query': 'moss ai autonomous',
                'results': [
                    {
                        'name': 'moss-ai-simulated',
                        'full_name': 'simulated/moss-ai',
                        'description': 'Simulated MOSS AI repository for testing',
                        'stars': 1234,
                        'language': 'Python'
                    }
                ],
                'total_count': 1
            }
        
        if not self.token:
            return {
                'success': False,
                'mode': 'none',
                'error': '未配置GitHub token'
            }
        
        try:
            headers = {
                'Authorization': f'token {self.token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            # 搜索MOSS相关的仓库
            search_response = requests.get(
                'https://api.github.com/search/repositories',
                params={'q': 'moss ai autonomous', 'per_page': 3},
                headers=headers,
                timeout=10
            )
            
            if search_response.status_code == 200:
                search_data = search_response.json()
                return {
                    'success': True,
                    'mode': 'real',
                    'query': 'moss ai autonomous',
                    'results': search_data.get('items', []),
                    'total_count': search_data.get('total_count', 0)
                }
            else:
                return {
                    'success': False,
                    'mode': 'real',
                    'error': f'搜索API失败: {search_response.status_code}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'mode': 'real',
                'error': f'搜索测试失败: {str(e)}'
            }
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """
        运行综合测试
        
        Returns:
            完整的测试报告
        """
        print("=" * 60)
        print("GitHub API Token 综合测试")
        print("=" * 60)
        
        # 1. Token加载测试
        token_loaded = self.load_token()
        print(f"\n1. Token加载: {'✅ 成功' if token_loaded else '❌ 失败'}")
        print(f"   模式: {'模拟模式' if self.simulation_mode else '真实API模式'}")
        
        # 2. 连接测试
        print("\n2. API连接测试:")
        connection_result = self.test_connection()
        
        if connection_result['success']:
            print(f"   ✅ {connection_result['message']}")
            if connection_result['mode'] == 'real':
                user = connection_result['user']
                print(f"   用户: {user.get('login')} ({user.get('name')})")
                
                rate = connection_result.get('rate_limit', {})
                if rate:
                    print(f"   速率限制: {rate.get('remaining', 0)}/{rate.get('limit', 0)} 剩余")
        else:
            print(f"   ❌ {connection_result.get('error', '未知错误')}")
            if 'suggestion' in connection_result:
                print(f"   建议: {connection_result['suggestion']}")
        
        # 3. 搜索API测试
        print("\n3. 搜索API测试:")
        search_result = self.test_search_api()
        
        if search_result['success']:
            print(f"   ✅ 搜索API工作正常")
            if search_result['mode'] == 'real':
                print(f"   找到 {search_result['total_count']} 个相关仓库")
                for i, repo in enumerate(search_result['results'][:3], 1):
                    print(f"   {i}. {repo.get('full_name')} - {repo.get('description', '无描述')}")
        else:
            print(f"   ❌ {search_result.get('error', '搜索失败')}")
        
        # 4. 测试总结
        print("\n" + "=" * 60)
        print("测试总结")
        print("=" * 60)
        
        all_tests_passed = (
            token_loaded and 
            connection_result['success'] and 
            search_result['success']
        )
        
        if all_tests_passed:
            print("🎉 所有测试通过！")
            if self.simulation_mode:
                print("📱 当前运行在模拟模式，适合开发和测试")
                print("💡 提示：配置真实GitHub token以进行真实环境测试")
            else:
                print("🚀 GitHub API配置正确，可以开始真实环境实验")
        else:
            print("⚠️  部分测试失败，需要检查配置")
            if self.simulation_mode:
                print("💡 建议：配置真实GitHub token以获得完整功能")
            else:
                print("💡 建议：检查token权限、网络连接和API配置")
        
        return {
            'overall_success': all_tests_passed,
            'token_loaded': token_loaded,
            'connection_success': connection_result['success'],
            'search_success': search_result['success'],
            'mode': 'simulation' if self.simulation_mode else 'real',
            'details': {
                'connection': connection_result,
                'search': search_result
            }
        }


def create_config_template():
    """创建配置文件模板"""
    template_path = Path("integration/api_config.json.template")
    config_path = Path("integration/api_config.json")
    
    if not template_path.exists():
        print("❌ 配置文件模板不存在")
        return False
    
    if config_path.exists():
        print("⚠️  配置文件已存在，跳过创建")
        return True
    
    try:
        # 复制模板
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        print(f"✅ 创建配置文件: {config_path}")
        print("💡 请编辑该文件并添加您的GitHub token")
        return True
        
    except Exception as e:
        print(f"❌ 创建配置文件失败: {e}")
        return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='测试GitHub API Token配置')
    parser.add_argument('--config', type=str, default='integration/api_config.json',
                       help='API配置文件路径')
    parser.add_argument('--create-config', action='store_true',
                       help='创建配置文件模板')
    parser.add_argument('--quick', action='store_true',
                       help='快速测试模式（仅连接测试）')
    
    args = parser.parse_args()
    
    # 创建配置文件（如果需要）
    if args.create_config:
        create_config_template()
        return
    
    # 运行测试
    tester = GitHubTokenTester(config_path=args.config)
    
    if args.quick:
        # 快速测试
        result = tester.test_connection()
        if result['success']:
            print("✅ GitHub API连接测试通过")
            if result['mode'] == 'simulation':
                print("📱 运行在模拟模式")
            else:
                print("🚀 运行在真实API模式")
        else:
            print(f"❌ GitHub API连接失败: {result.get('error', '未知错误')}")
    else:
        # 综合测试
        report = tester.run_comprehensive_test()
        
        # 保存测试报告
        report_path = Path("tests/github_token_test_report.json")
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 测试报告已保存: {report_path}")


if __name__ == "__main__":
    main()
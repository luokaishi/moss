#!/usr/bin/env python3
"""
MOSS v6.0 - Open Environment Adapter
开放环境适配器

核心功能:
- 真实世界 API 调用
- 文件系统深度交互
- 网络资源访问
- 环境状态感知

Author: MOSS Project
Date: 2026-04-03
Version: 6.0.0-dev
"""

import os
import json
import requests
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class EnvironmentState:
    """环境状态"""
    timestamp: datetime = field(default_factory=datetime.now)
    resources: Dict[str, float] = field(default_factory=dict)
    constraints: Dict[str, float] = field(default_factory=dict)
    opportunities: List[Dict] = field(default_factory=list)
    threats: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'resources': self.resources,
            'constraints': self.constraints,
            'opportunities': self.opportunities,
            'threats': self.threats
        }


class FileSystemInterface:
    """
    文件系统接口
    
    提供深度文件交互能力
    """
    
    def __init__(self, base_dir: str = "./workspace"):
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        self.stats = {
            'files_read': 0,
            'files_written': 0,
            'directories_scanned': 0,
            'total_bytes_processed': 0
        }
    
    def scan_directory(self, path: str = ".", 
                      max_depth: int = 3,
                      pattern: Optional[str] = None) -> Dict:
        """
        深度扫描目录
        
        Args:
            path: 起始路径
            max_depth: 最大深度
            pattern: 文件匹配模式
            
        Returns:
            目录结构信息
        """
        scan_path = (self.base_dir / path).resolve()
        
        if not str(scan_path).startswith(str(self.base_dir)):
            raise ValueError(f"Path outside base directory: {path}")
        
        result = {
            'path': str(scan_path.relative_to(self.base_dir)),
            'files': [],
            'directories': [],
            'total_size': 0,
            'file_count': 0,
            'directory_count': 0
        }
        
        def scan_recursive(current_path: Path, current_depth: int):
            if current_depth > max_depth:
                return
            
            try:
                for item in current_path.iterdir():
                    if pattern and not item.match(pattern):
                        continue
                    
                    if item.is_file():
                        file_info = {
                            'name': item.name,
                            'path': str(item.relative_to(self.base_dir)),
                            'size': item.stat().st_size,
                            'modified': datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                        }
                        result['files'].append(file_info)
                        result['total_size'] += file_info['size']
                        result['file_count'] += 1
                    elif item.is_dir():
                        dir_info = {
                            'name': item.name,
                            'path': str(item.relative_to(self.base_dir))
                        }
                        result['directories'].append(dir_info)
                        result['directory_count'] += 1
                        
                        scan_recursive(item, current_depth + 1)
            except PermissionError:
                pass
        
        scan_recursive(scan_path, 0)
        self.stats['directories_scanned'] += 1
        
        return result
    
    def intelligent_categorize(self, path: str = ".") -> Dict[str, List[str]]:
        """
        智能文件分类
        
        Returns:
            分类后的文件列表
        """
        scan_result = self.scan_directory(path)
        
        categories = {
            'code': [],
            'data': [],
            'documents': [],
            'config': [],
            'media': [],
            'other': []
        }
        
        code_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.go', '.rs'}
        data_extensions = {'.json', '.csv', '.xml', '.yaml', '.yml', '.parquet'}
        doc_extensions = {'.md', '.txt', '.pdf', '.doc', '.docx'}
        config_extensions = {'.env', '.conf', '.cfg', '.ini', '.toml'}
        media_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.mp4', '.mp3'}
        
        for file_info in scan_result['files']:
            ext = Path(file_info['name']).suffix.lower()
            
            if ext in code_extensions:
                categories['code'].append(file_info['path'])
            elif ext in data_extensions:
                categories['data'].append(file_info['path'])
            elif ext in doc_extensions:
                categories['documents'].append(file_info['path'])
            elif ext in config_extensions:
                categories['config'].append(file_info['path'])
            elif ext in media_extensions:
                categories['media'].append(file_info['path'])
            else:
                categories['other'].append(file_info['path'])
        
        return categories
    
    def read_file(self, path: str) -> Tuple[bool, str]:
        """读取文件"""
        try:
            file_path = (self.base_dir / path).resolve()
            if not str(file_path).startswith(str(self.base_dir)):
                return False, "Path outside base directory"
            
            content = file_path.read_text()
            self.stats['files_read'] += 1
            self.stats['total_bytes_processed'] += len(content)
            return True, content
        except Exception as e:
            return False, str(e)
    
    def write_file(self, path: str, content: str) -> Tuple[bool, str]:
        """写入文件"""
        try:
            file_path = (self.base_dir / path).resolve()
            if not str(file_path).startswith(str(self.base_dir)):
                return False, "Path outside base directory"
            
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            self.stats['files_written'] += 1
            self.stats['total_bytes_processed'] += len(content)
            return True, f"Written {len(content)} bytes"
        except Exception as e:
            return False, str(e)
    
    def get_status(self) -> Dict:
        """获取状态"""
        return {
            'stats': self.stats,
            'base_dir': str(self.base_dir)
        }


class APIInterface:
    """
    API 接口
    
    提供 RESTful API 调用能力
    """
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        
        self.stats = {
            'requests_made': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_response_time': 0.0
        }
    
    def get(self, url: str, params: Optional[Dict] = None,
            headers: Optional[Dict] = None) -> Tuple[bool, Any]:
        """GET 请求"""
        try:
            start_time = datetime.now()
            response = self.session.get(
                url, 
                params=params, 
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            self.stats['requests_made'] += 1
            self.stats['successful_requests'] += 1
            self.stats['total_response_time'] += elapsed
            
            return True, {
                'status_code': response.status_code,
                'data': response.json() if 'application/json' in response.headers.get('Content-Type', '') else response.text,
                'response_time': elapsed
            }
        except Exception as e:
            self.stats['requests_made'] += 1
            self.stats['failed_requests'] += 1
            return False, str(e)
    
    def post(self, url: str, data: Dict,
             headers: Optional[Dict] = None) -> Tuple[bool, Any]:
        """POST 请求"""
        try:
            start_time = datetime.now()
            response = self.session.post(
                url,
                json=data,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            self.stats['requests_made'] += 1
            self.stats['successful_requests'] += 1
            self.stats['total_response_time'] += elapsed
            
            return True, {
                'status_code': response.status_code,
                'data': response.json() if 'application/json' in response.headers.get('Content-Type', '') else response.text,
                'response_time': elapsed
            }
        except Exception as e:
            self.stats['requests_made'] += 1
            self.stats['failed_requests'] += 1
            return False, str(e)
    
    def get_status(self) -> Dict:
        """获取状态"""
        avg_response_time = (
            self.stats['total_response_time'] / 
            max(self.stats['successful_requests'], 1)
        )
        success_rate = (
            self.stats['successful_requests'] / 
            max(self.stats['requests_made'], 1)
        )
        
        return {
            'stats': self.stats,
            'avg_response_time': avg_response_time,
            'success_rate': success_rate
        }


class OpenEnvironment:
    """
    开放环境
    
    统一管理文件系统、API、网络资源
    """
    
    def __init__(self, workspace_dir: str = "./workspace"):
        self.fs = FileSystemInterface(workspace_dir)
        self.api = APIInterface()
        
        self.state = EnvironmentState()
        
        self.stats = {
            'total_actions': 0,
            'successful_actions': 0,
            'failed_actions': 0
        }
    
    def perceive(self) -> EnvironmentState:
        """感知环境状态"""
        # 扫描工作目录
        scan_result = self.fs.scan_directory(".", max_depth=2)
        
        # 更新资源状态
        self.state.resources = {
            'disk_space': scan_result['total_size'],
            'file_count': scan_result['file_count'],
            'directory_count': scan_result['directory_count']
        }
        
        # 检测机会
        self.state.opportunities = []
        if scan_result['file_count'] > 100:
            self.state.opportunities.append({
                'type': 'organization',
                'description': 'Large number of files detected, consider categorization',
                'priority': 0.7
            })
        
        # 检测威胁
        self.state.threats = []
        if scan_result['total_size'] > 10 * 1024 * 1024 * 1024:  # 10GB
            self.state.threats.append({
                'type': 'storage',
                'description': 'High disk usage detected',
                'severity': 0.8
            })
        
        self.state.timestamp = datetime.now()
        return self.state
    
    def execute_action(self, action_type: str, **kwargs) -> Tuple[bool, Any]:
        """
        执行环境动作
        
        Args:
            action_type: 动作类型 (fs_*, api_*)
            **kwargs: 动作参数
            
        Returns:
            (成功与否，结果)
        """
        self.stats['total_actions'] += 1
        
        try:
            if action_type.startswith('fs_'):
                success, result = self._execute_fs_action(action_type, **kwargs)
            elif action_type.startswith('api_'):
                success, result = self._execute_api_action(action_type, **kwargs)
            else:
                success, result = False, f"Unknown action type: {action_type}"
            
            if success:
                self.stats['successful_actions'] += 1
            else:
                self.stats['failed_actions'] += 1
            
            return success, result
        except Exception as e:
            self.stats['failed_actions'] += 1
            return False, str(e)
    
    def _execute_fs_action(self, action_type: str, **kwargs) -> Tuple[bool, Any]:
        """执行文件系统动作"""
        if action_type == 'fs_scan':
            return True, self.fs.scan_directory(
                kwargs.get('path', '.'),
                kwargs.get('max_depth', 3),
                kwargs.get('pattern')
            )
        elif action_type == 'fs_categorize':
            return True, self.fs.intelligent_categorize(kwargs.get('path', '.'))
        elif action_type == 'fs_read':
            return self.fs.read_file(kwargs.get('path', ''))
        elif action_type == 'fs_write':
            return self.fs.write_file(
                kwargs.get('path', ''),
                kwargs.get('content', '')
            )
        else:
            return False, f"Unknown FS action: {action_type}"
    
    def _execute_api_action(self, action_type: str, **kwargs) -> Tuple[bool, Any]:
        """执行 API 动作"""
        if action_type == 'api_get':
            return self.api.get(
                kwargs.get('url', ''),
                kwargs.get('params'),
                kwargs.get('headers')
            )
        elif action_type == 'api_post':
            return self.api.post(
                kwargs.get('url', ''),
                kwargs.get('data', {}),
                kwargs.get('headers')
            )
        else:
            return False, f"Unknown API action: {action_type}"
    
    def get_status(self) -> Dict:
        """获取环境状态"""
        return {
            'stats': self.stats,
            'environment': self.state.to_dict(),
            'filesystem': self.fs.get_status(),
            'api': self.api.get_status()
        }


# 测试代码
if __name__ == '__main__':
    print("=" * 60)
    print("MOSS v6.0 - Open Environment Test")
    print("=" * 60)
    
    # 创建环境
    env = OpenEnvironment(workspace_dir="./test_env")
    
    # 感知环境
    print("\n1. 感知环境...")
    state = env.perceive()
    print(f"   资源：{state.resources}")
    print(f"   机会：{len(state.opportunities)}")
    print(f"   威胁：{len(state.threats)}")
    
    # 测试文件系统
    print("\n2. 测试文件系统...")
    success, result = env.execute_action('fs_write', path='test.txt', content='Hello, World!')
    print(f"   写入：{'✅' if success else '❌'}")
    
    success, result = env.execute_action('fs_read', path='test.txt')
    print(f"   读取：{'✅' if success else '❌'} - {result[:50] if success else result}")
    
    success, result = env.execute_action('fs_scan', path='.', max_depth=2)
    print(f"   扫描：{'✅' if success else '❌'} - {result['file_count']} 个文件")
    
    # 测试 API
    print("\n3. 测试 API...")
    success, result = env.execute_action('api_get', url='https://httpbin.org/get', params={'test': 'value'})
    print(f"   GET: {'✅' if success else '❌'}")
    
    # 获取状态
    print("\n4. 环境状态:")
    status = env.get_status()
    print(f"   总动作数：{status['stats']['total_actions']}")
    print(f"   成功率：{status['stats']['successful_actions'] / max(status['stats']['total_actions'], 1):.1%}")
    
    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("=" * 60)

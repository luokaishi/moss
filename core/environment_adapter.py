#!/usr/bin/env python3
"""
MOSS v5.4 - Environment Adapter
环境适配器

核心功能:
- 真实世界 API 调用
- 文件系统交互
- 网络资源访问
- 环境抽象层

Author: MOSS Project
Date: 2026-04-03
Version: 5.4.0-dev
"""

import os
import json
import requests
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import hashlib


@dataclass
class EnvironmentAction:
    """环境动作"""
    action_type: str
    parameters: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    result: Optional[Any] = None
    success: bool = False
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'action_type': self.action_type,
            'parameters': self.parameters,
            'timestamp': self.timestamp.isoformat(),
            'result': self.result,
            'success': self.success,
            'error': self.error
        }


class FileSystemAdapter:
    """
    文件系统适配器
    
    提供安全的文件操作接口
    """
    
    def __init__(self, base_dir: str = "./workspace"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.action_history: List[EnvironmentAction] = []
    
    def _safe_path(self, path: str) -> Path:
        """确保路径安全（防止目录遍历攻击）"""
        full_path = (self.base_dir / path).resolve()
        if not str(full_path).startswith(str(self.base_dir.resolve())):
            raise ValueError(f"Unsafe path: {path}")
        return full_path
    
    def read_file(self, path: str) -> Tuple[bool, str]:
        """读取文件"""
        try:
            safe_path = self._safe_path(path)
            if not safe_path.exists():
                return False, f"File not found: {path}"
            
            content = safe_path.read_text()
            self._log_action("read_file", {'path': path}, True, result=len(content))
            return True, content
        except Exception as e:
            self._log_action("read_file", {'path': path}, False, error=str(e))
            return False, str(e)
    
    def write_file(self, path: str, content: str) -> Tuple[bool, str]:
        """写入文件"""
        try:
            safe_path = self._safe_path(path)
            safe_path.parent.mkdir(parents=True, exist_ok=True)
            safe_path.write_text(content)
            self._log_action("write_file", {'path': path, 'size': len(content)}, True)
            return True, f"Written {len(content)} bytes to {path}"
        except Exception as e:
            self._log_action("write_file", {'path': path}, False, error=str(e))
            return False, str(e)
    
    def list_files(self, path: str = ".") -> Tuple[bool, List[str]]:
        """列出文件"""
        try:
            safe_path = self._safe_path(path)
            files = [str(p.relative_to(self.base_dir)) for p in safe_path.iterdir()]
            self._log_action("list_files", {'path': path}, True, result=len(files))
            return True, files
        except Exception as e:
            self._log_action("list_files", {'path': path}, False, error=str(e))
            return False, []
    
    def delete_file(self, path: str) -> Tuple[bool, str]:
        """删除文件"""
        try:
            safe_path = self._safe_path(path)
            if safe_path.exists():
                safe_path.unlink()
                self._log_action("delete_file", {'path': path}, True)
                return True, f"Deleted {path}"
            return False, f"File not found: {path}"
        except Exception as e:
            self._log_action("delete_file", {'path': path}, False, error=str(e))
            return False, str(e)
    
    def _log_action(self, action_type: str, params: Dict, success: bool, 
                    result: Any = None, error: Optional[str] = None):
        """记录动作历史"""
        action = EnvironmentAction(
            action_type=action_type,
            parameters=params,
            success=success,
            result=result,
            error=error
        )
        self.action_history.append(action)


class WebAPIAdapter:
    """
    Web API 适配器
    
    提供安全的网络 API 调用接口
    """
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.action_history: List[EnvironmentAction] = []
        self.allowed_domains: List[str] = []  # 白名单
    
    def add_allowed_domain(self, domain: str):
        """添加允许的域名"""
        self.allowed_domains.append(domain)
    
    def _is_allowed(self, url: str) -> bool:
        """检查 URL 是否在白名单内"""
        if not self.allowed_domains:
            return True  # 无白名单时允许所有
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return any(domain in parsed.netloc for domain in self.allowed_domains)
    
    def get(self, url: str, params: Optional[Dict] = None) -> Tuple[bool, Any]:
        """GET 请求"""
        try:
            if not self._is_allowed(url):
                return False, f"Domain not allowed: {url}"
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            self._log_action("get", {'url': url, 'params': params}, True, 
                           result={'status': response.status_code, 'size': len(response.content)})
            return True, response.json() if 'application/json' in response.headers.get('Content-Type', '') else response.text
        except Exception as e:
            self._log_action("get", {'url': url}, False, error=str(e))
            return False, str(e)
    
    def post(self, url: str, data: Dict) -> Tuple[bool, Any]:
        """POST 请求"""
        try:
            if not self._is_allowed(url):
                return False, f"Domain not allowed: {url}"
            
            response = self.session.post(url, json=data, timeout=self.timeout)
            response.raise_for_status()
            
            self._log_action("post", {'url': url, 'data_size': len(str(data))}, True,
                           result={'status': response.status_code})
            return True, response.json() if 'application/json' in response.headers.get('Content-Type', '') else response.text
        except Exception as e:
            self._log_action("post", {'url': url}, False, error=str(e))
            return False, str(e)
    
    def _log_action(self, action_type: str, params: Dict, success: bool,
                    result: Any = None, error: Optional[str] = None):
        """记录动作历史"""
        action = EnvironmentAction(
            action_type=action_type,
            parameters=params,
            success=success,
            result=result,
            error=error
        )
        self.action_history.append(action)


class EnvironmentAdapter:
    """
    环境适配器主类
    
    统一文件系统、Web API、工具调用等接口
    """
    
    def __init__(self, workspace_dir: str = "./workspace"):
        self.fs = FileSystemAdapter(workspace_dir)
        self.web = WebAPIAdapter()
        self.action_history: List[EnvironmentAction] = []
        
        # 统计
        self.stats = {
            'total_actions': 0,
            'successful_actions': 0,
            'failed_actions': 0,
            'file_operations': 0,
            'web_operations': 0
        }
    
    def execute_action(self, action_type: str, **kwargs) -> Tuple[bool, Any]:
        """
        执行环境动作
        
        支持的动作类型:
        - file_read, file_write, file_list, file_delete
        - web_get, web_post
        """
        self.stats['total_actions'] += 1
        
        if action_type.startswith('file_'):
            return self._execute_file_action(action_type, **kwargs)
        elif action_type.startswith('web_'):
            return self._execute_web_action(action_type, **kwargs)
        else:
            return False, f"Unknown action type: {action_type}"
    
    def _execute_file_action(self, action_type: str, **kwargs) -> Tuple[bool, Any]:
        """执行文件操作"""
        self.stats['file_operations'] += 1
        
        if action_type == 'file_read':
            success, result = self.fs.read_file(kwargs.get('path', ''))
        elif action_type == 'file_write':
            success, result = self.fs.write_file(
                kwargs.get('path', ''),
                kwargs.get('content', '')
            )
        elif action_type == 'file_list':
            success, result = self.fs.list_files(kwargs.get('path', '.'))
        elif action_type == 'file_delete':
            success, result = self.fs.delete_file(kwargs.get('path', ''))
        else:
            success, result = False, f"Unknown file action: {action_type}"
        
        self._update_stats(success)
        return success, result
    
    def _execute_web_action(self, action_type: str, **kwargs) -> Tuple[bool, Any]:
        """执行 Web 操作"""
        self.stats['web_operations'] += 1
        
        if action_type == 'web_get':
            success, result = self.web.get(
                kwargs.get('url', ''),
                kwargs.get('params')
            )
        elif action_type == 'web_post':
            success, result = self.web.post(
                kwargs.get('url', ''),
                kwargs.get('data', {})
            )
        else:
            success, result = False, f"Unknown web action: {action_type}"
        
        self._update_stats(success)
        return success, result
    
    def _update_stats(self, success: bool):
        """更新统计"""
        if success:
            self.stats['successful_actions'] += 1
        else:
            self.stats['failed_actions'] += 1
    
    def get_status(self) -> Dict:
        """获取环境适配器状态"""
        return {
            'stats': self.stats,
            'success_rate': (
                self.stats['successful_actions'] / 
                max(self.stats['total_actions'], 1)
            ),
            'file_history_size': len(self.fs.action_history),
            'web_history_size': len(self.web.action_history)
        }


# 测试代码
if __name__ == '__main__':
    print("=" * 60)
    print("MOSS v5.4 - Environment Adapter Test")
    print("=" * 60)
    
    # 创建适配器
    adapter = EnvironmentAdapter(workspace_dir="./test_workspace")
    
    # 测试文件写入
    print("\n1. 测试文件写入...")
    success, result = adapter.execute_action(
        'file_write',
        path='test.txt',
        content='Hello, World!'
    )
    print(f"   写入结果：{'✅' if success else '❌'} {result}")
    
    # 测试文件读取
    print("\n2. 测试文件读取...")
    success, result = adapter.execute_action(
        'file_read',
        path='test.txt'
    )
    print(f"   读取结果：{'✅' if success else '❌'} {result[:50]}...")
    
    # 测试文件列表
    print("\n3. 测试文件列表...")
    success, files = adapter.execute_action('file_list', path='.')
    print(f"   文件列表：{files}")
    
    # 测试 Web 请求（可选）
    print("\n4. 测试 Web 请求...")
    adapter.web.add_allowed_domain('api.github.com')
    success, result = adapter.execute_action(
        'web_get',
        url='https://api.github.com'
    )
    print(f"   Web 请求：{'✅' if success else '❌'}")
    
    # 获取状态
    print("\n5. 适配器状态:")
    status = adapter.get_status()
    print(f"   总动作数：{status['stats']['total_actions']}")
    print(f"   成功率：{status['success_rate']:.1%}")
    print(f"   文件操作：{status['stats']['file_operations']}")
    print(f"   Web 操作：{status['stats']['web_operations']}")
    
    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("=" * 60)

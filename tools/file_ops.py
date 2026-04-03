#!/usr/bin/env python3
"""
MOSS v5.4 - File Operations Tool
文件操作工具

核心功能:
- 文件读写
- 目录管理
- 文件搜索
- 批量操作

Author: MOSS Project
Date: 2026-04-03
Version: 5.4.0-dev
"""

import os
import shutil
import json
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from datetime import datetime
import hashlib


class FileOperationsTool:
    """
    文件操作工具
    
    提供安全的文件操作接口
    """
    
    def __init__(self, base_dir: str = "./workspace"):
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        self.stats = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'bytes_read': 0,
            'bytes_written': 0
        }
        
        self.operation_history: List[Dict] = []
    
    def _safe_path(self, path: str) -> Path:
        """确保路径安全"""
        full_path = (self.base_dir / path).resolve()
        if not str(full_path).startswith(str(self.base_dir)):
            raise ValueError(f"Unsafe path: {path}")
        return full_path
    
    def read(self, path: str, encoding: str = 'utf-8') -> Tuple[bool, str]:
        """读取文件"""
        self.stats['total_operations'] += 1
        
        try:
            safe_path = self._safe_path(path)
            if not safe_path.exists():
                return False, f"File not found: {path}"
            
            content = safe_path.read_text(encoding=encoding)
            self.stats['bytes_read'] += len(content)
            self.stats['successful_operations'] += 1
            
            self._log_operation('read', {'path': path, 'size': len(content)}, True)
            return True, content
            
        except Exception as e:
            self.stats['failed_operations'] += 1
            self._log_operation('read', {'path': path}, False, str(e))
            return False, str(e)
    
    def write(self, path: str, content: str, encoding: str = 'utf-8',
              append: bool = False) -> Tuple[bool, str]:
        """写入文件"""
        self.stats['total_operations'] += 1
        
        try:
            safe_path = self._safe_path(path)
            safe_path.parent.mkdir(parents=True, exist_ok=True)
            
            mode = 'a' if append else 'w'
            with open(safe_path, mode, encoding=encoding) as f:
                f.write(content)
            
            self.stats['bytes_written'] += len(content)
            self.stats['successful_operations'] += 1
            
            self._log_operation('write', {'path': path, 'size': len(content)}, True)
            return True, f"Written {len(content)} bytes"
            
        except Exception as e:
            self.stats['failed_operations'] += 1
            self._log_operation('write', {'path': path}, False, str(e))
            return False, str(e)
    
    def list(self, path: str = ".", pattern: Optional[str] = None) -> Tuple[bool, List[Dict]]:
        """列出文件"""
        self.stats['total_operations'] += 1
        
        try:
            safe_path = self._safe_path(path)
            if not safe_path.exists():
                return False, f"Path not found: {path}"
            
            files = []
            for p in safe_path.iterdir():
                if pattern and not p.match(pattern):
                    continue
                
                files.append({
                    'name': p.name,
                    'path': str(p.relative_to(self.base_dir)),
                    'is_dir': p.is_dir(),
                    'size': p.stat().st_size if p.is_file() else 0,
                    'modified': datetime.fromtimestamp(p.stat().st_mtime).isoformat()
                })
            
            self.stats['successful_operations'] += 1
            self._log_operation('list', {'path': path}, True, result=len(files))
            return True, files
            
        except Exception as e:
            self.stats['failed_operations'] += 1
            self._log_operation('list', {'path': path}, False, str(e))
            return False, []
    
    def delete(self, path: str, recursive: bool = False) -> Tuple[bool, str]:
        """删除文件/目录"""
        self.stats['total_operations'] += 1
        
        try:
            safe_path = self._safe_path(path)
            if not safe_path.exists():
                return False, f"Path not found: {path}"
            
            if safe_path.is_dir():
                if recursive:
                    shutil.rmtree(safe_path)
                else:
                    safe_path.rmdir()
            else:
                safe_path.unlink()
            
            self.stats['successful_operations'] += 1
            self._log_operation('delete', {'path': path, 'recursive': recursive}, True)
            return True, f"Deleted {path}"
            
        except Exception as e:
            self.stats['failed_operations'] += 1
            self._log_operation('delete', {'path': path}, False, str(e))
            return False, str(e)
    
    def copy(self, src: str, dst: str) -> Tuple[bool, str]:
        """复制文件"""
        self.stats['total_operations'] += 1
        
        try:
            src_path = self._safe_path(src)
            dst_path = self._safe_path(dst)
            
            if not src_path.exists():
                return False, f"Source not found: {src}"
            
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            if src_path.is_dir():
                shutil.copytree(src_path, dst_path)
            else:
                shutil.copy2(src_path, dst_path)
            
            self.stats['successful_operations'] += 1
            self._log_operation('copy', {'src': src, 'dst': dst}, True)
            return True, f"Copied {src} to {dst}"
            
        except Exception as e:
            self.stats['failed_operations'] += 1
            self._log_operation('copy', {'src': src, 'dst': dst}, False, str(e))
            return False, str(e)
    
    def move(self, src: str, dst: str) -> Tuple[bool, str]:
        """移动文件"""
        self.stats['total_operations'] += 1
        
        try:
            src_path = self._safe_path(src)
            dst_path = self._safe_path(dst)
            
            if not src_path.exists():
                return False, f"Source not found: {src}"
            
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src_path), str(dst_path))
            
            self.stats['successful_operations'] += 1
            self._log_operation('move', {'src': src, 'dst': dst}, True)
            return True, f"Moved {src} to {dst}"
            
        except Exception as e:
            self.stats['failed_operations'] += 1
            self._log_operation('move', {'src': src, 'dst': dst}, False, str(e))
            return False, str(e)
    
    def search(self, pattern: str, path: str = ".") -> Tuple[bool, List[str]]:
        """搜索文件"""
        self.stats['total_operations'] += 1
        
        try:
            safe_path = self._safe_path(path)
            matches = []
            
            for p in safe_path.rglob(pattern):
                matches.append(str(p.relative_to(self.base_dir)))
            
            self.stats['successful_operations'] += 1
            self._log_operation('search', {'pattern': pattern, 'path': path}, True, result=len(matches))
            return True, matches
            
        except Exception as e:
            self.stats['failed_operations'] += 1
            self._log_operation('search', {'pattern': pattern}, False, str(e))
            return False, []
    
    def get_file_info(self, path: str) -> Tuple[bool, Dict]:
        """获取文件信息"""
        self.stats['total_operations'] += 1
        
        try:
            safe_path = self._safe_path(path)
            if not safe_path.exists():
                return False, {}
            
            stat = safe_path.stat()
            info = {
                'name': safe_path.name,
                'path': str(safe_path.relative_to(self.base_dir)),
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'is_dir': safe_path.is_dir(),
                'is_file': safe_path.is_file()
            }
            
            # 计算文件哈希
            if safe_path.is_file():
                info['md5'] = hashlib.md5(safe_path.read_bytes()).hexdigest()
            
            self.stats['successful_operations'] += 1
            self._log_operation('info', {'path': path}, True)
            return True, info
            
        except Exception as e:
            self.stats['failed_operations'] += 1
            self._log_operation('info', {'path': path}, False, str(e))
            return False, {}
    
    def _log_operation(self, op_type: str, params: Dict, success: bool,
                       result: Any = None, error: Optional[str] = None):
        """记录操作历史"""
        self.operation_history.append({
            'timestamp': datetime.now().isoformat(),
            'type': op_type,
            'params': params,
            'success': success,
            'result': result,
            'error': error
        })
    
    def get_status(self) -> Dict:
        """获取工具状态"""
        return {
            'stats': self.stats,
            'success_rate': (
                self.stats['successful_operations'] / 
                max(self.stats['total_operations'], 1)
            ),
            'history_size': len(self.operation_history)
        }


# 测试代码
if __name__ == '__main__':
    print("=" * 60)
    print("MOSS v5.4 - File Operations Tool Test")
    print("=" * 60)
    
    # 创建工具
    tool = FileOperationsTool(base_dir="./test_file_ops")
    
    # 测试写入
    print("\n1. 测试文件写入...")
    success, msg = tool.write('test.txt', 'Hello, World!')
    print(f"   写入：{'✅' if success else '❌'} - {msg}")
    
    # 测试读取
    print("\n2. 测试文件读取...")
    success, content = tool.read('test.txt')
    print(f"   读取：{'✅' if success else '❌'} - {content}")
    
    # 测试文件列表
    print("\n3. 测试文件列表...")
    success, files = tool.list('.')
    print(f"   列表：{'✅' if success else '❌'} - {len(files)} 个文件")
    
    # 测试文件信息
    print("\n4. 测试文件信息...")
    success, info = tool.get_file_info('test.txt')
    if success:
        print(f"   大小：{info['size']} bytes")
        print(f"   MD5: {info.get('md5', 'N/A')}")
    
    # 测试复制
    print("\n5. 测试文件复制...")
    success, msg = tool.copy('test.txt', 'test_copy.txt')
    print(f"   复制：{'✅' if success else '❌'} - {msg}")
    
    # 测试搜索
    print("\n6. 测试文件搜索...")
    success, matches = tool.search('*.txt')
    print(f"   搜索：{'✅' if success else '❌'} - 找到 {len(matches)} 个文件")
    
    # 获取状态
    print("\n7. 工具状态:")
    status = tool.get_status()
    print(f"   总操作数：{status['stats']['total_operations']}")
    print(f"   成功率：{status['success_rate']:.1%}")
    print(f"   读取字节：{status['stats']['bytes_read']}")
    print(f"   写入字节：{status['stats']['bytes_written']}")
    
    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("=" * 60)

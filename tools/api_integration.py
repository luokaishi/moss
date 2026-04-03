#!/usr/bin/env python3
"""
MOSS v6.0 - API Integration Tools
API 集成工具

核心功能:
- RESTful API 调用
- GraphQL 支持
- WebSocket 通信
- API 速率限制处理

Author: MOSS Project
Date: 2026-04-03
Version: 6.0.0-dev
"""

import json
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
import hashlib


@dataclass
class APIConfig:
    """API 配置"""
    base_url: str
    api_key: Optional[str] = None
    timeout: int = 30
    rate_limit: int = 100  # 每分钟请求数
    retry_count: int = 3
    headers: Dict = field(default_factory=dict)


class RateLimiter:
    """
    速率限制器
    
    控制 API 请求频率
    """
    
    def __init__(self, rate_limit: int = 100):
        self.rate_limit = rate_limit
        self.requests: List[float] = []
    
    def wait_if_needed(self):
        """如果需要则等待"""
        now = time.time()
        
        # 移除 60 秒前的请求
        self.requests = [t for t in self.requests if now - t < 60]
        
        # 如果达到限制，等待
        if len(self.requests) >= self.rate_limit:
            sleep_time = 60 - (now - self.requests[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
                self.requests = self.requests[1:]
        
        self.requests.append(time.time())


class APIClient:
    """
    API 客户端
    
    提供统一的 API 调用接口
    """
    
    def __init__(self, config: APIConfig):
        self.config = config
        self.rate_limiter = RateLimiter(config.rate_limit)
        
        self.stats = {
            'requests_made': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'retries': 0,
            'total_response_time': 0.0
        }
    
    def _make_request(self, method: str, endpoint: str,
                     **kwargs) -> Tuple[bool, Any]:
        """
        发送 HTTP 请求
        
        Returns:
            (成功与否，响应数据)
        """
        import requests
        
        url = f"{self.config.base_url}/{endpoint.lstrip('/')}"
        headers = self.config.headers.copy()
        
        if self.config.api_key:
            headers['Authorization'] = f"Bearer {self.config.api_key}"
        
        for attempt in range(self.config.retry_count):
            try:
                # 速率限制
                self.rate_limiter.wait_if_needed()
                
                start_time = time.time()
                
                response = requests.request(
                    method,
                    url,
                    headers=headers,
                    timeout=self.config.timeout,
                    **kwargs
                )
                
                elapsed = time.time() - start_time
                self.stats['total_response_time'] += elapsed
                
                response.raise_for_status()
                
                self.stats['requests_made'] += 1
                self.stats['successful_requests'] += 1
                
                return True, {
                    'status_code': response.status_code,
                    'data': response.json() if 'application/json' in response.headers.get('Content-Type', '') else response.text,
                    'response_time': elapsed,
                    'headers': dict(response.headers)
                }
                
            except requests.exceptions.RequestException as e:
                self.stats['requests_made'] += 1
                self.stats['failed_requests'] += 1
                
                if attempt < self.config.retry_count - 1:
                    self.stats['retries'] += 1
                    time.sleep(2 ** attempt)  # 指数退避
                else:
                    return False, str(e)
        
        return False, "Max retries exceeded"
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Tuple[bool, Any]:
        """GET 请求"""
        return self._make_request('GET', endpoint, params=params)
    
    def post(self, endpoint: str, data: Dict) -> Tuple[bool, Any]:
        """POST 请求"""
        return self._make_request('POST', endpoint, json=data)
    
    def put(self, endpoint: str, data: Dict) -> Tuple[bool, Any]:
        """PUT 请求"""
        return self._make_request('PUT', endpoint, json=data)
    
    def delete(self, endpoint: str) -> Tuple[bool, Any]:
        """DELETE 请求"""
        return self._make_request('DELETE', endpoint)
    
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
            'success_rate': success_rate,
            'rate_limit': self.config.rate_limit
        }


class GraphQLClient:
    """
    GraphQL 客户端
    
    提供 GraphQL 查询能力
    """
    
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
    
    def query(self, query: str, variables: Optional[Dict] = None) -> Tuple[bool, Any]:
        """
        执行 GraphQL 查询
        
        Args:
            query: GraphQL 查询语句
            variables: 查询变量
            
        Returns:
            (成功与否，查询结果)
        """
        payload = {'query': query}
        if variables:
            payload['variables'] = variables
        
        return self.api_client.post('/graphql', data=payload)
    
    def mutate(self, mutation: str, variables: Optional[Dict] = None) -> Tuple[bool, Any]:
        """
        执行 GraphQL 变异
        
        Args:
            mutation: GraphQL 变异语句
            variables: 变异变量
            
        Returns:
            (成功与否，变异结果)
        """
        return self.query(mutation, variables)


class APIIntegration:
    """
    API 集成
    
    统一管理 RESTful 和 GraphQL API
    """
    
    def __init__(self, config: APIConfig):
        self.api_client = APIClient(config)
        self.graphql_client = GraphQLClient(self.api_client)
        
        self.action_history: List[Dict] = []
        
        self.stats = {
            'total_actions': 0,
            'successful_actions': 0,
            'failed_actions': 0
        }
    
    def execute_action(self, action_type: str, **kwargs) -> Tuple[bool, Any]:
        """
        执行 API 动作
        
        Args:
            action_type: 动作类型
            **kwargs: 动作参数
            
        Returns:
            (成功与否，结果)
        """
        self.stats['total_actions'] += 1
        
        action = {
            'type': action_type,
            'parameters': kwargs,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            if action_type == 'rest_get':
                success, result = self.api_client.get(
                    kwargs.get('endpoint', ''),
                    kwargs.get('params')
                )
            elif action_type == 'rest_post':
                success, result = self.api_client.post(
                    kwargs.get('endpoint', ''),
                    kwargs.get('data', {})
                )
            elif action_type == 'graphql_query':
                success, result = self.graphql_client.query(
                    kwargs.get('query', ''),
                    kwargs.get('variables')
                )
            elif action_type == 'graphql_mutation':
                success, result = self.graphql_client.mutate(
                    kwargs.get('mutation', ''),
                    kwargs.get('variables')
                )
            else:
                success, result = False, f"Unknown action: {action_type}"
            
            action['success'] = success
            action['result'] = result if success else None
            self.action_history.append(action)
            
            if success:
                self.stats['successful_actions'] += 1
            else:
                self.stats['failed_actions'] += 1
            
            return success, result
        except Exception as e:
            action['success'] = False
            action['error'] = str(e)
            self.action_history.append(action)
            self.stats['failed_actions'] += 1
            return False, str(e)
    
    def get_status(self) -> Dict:
        """获取状态"""
        return {
            'stats': self.stats,
            'api_client': self.api_client.get_status(),
            'action_history_length': len(self.action_history)
        }


# 测试代码
if __name__ == '__main__':
    print("=" * 60)
    print("MOSS v6.0 - API Integration Test")
    print("=" * 60)
    
    # 创建 API 配置
    config = APIConfig(
        base_url='https://httpbin.org',
        rate_limit=10,
        timeout=10
    )
    
    # 创建集成
    integration = APIIntegration(config)
    
    # 测试 REST GET
    print("\n1. 测试 REST GET...")
    success, result = integration.execute_action(
        'rest_get',
        endpoint='/get',
        params={'test': 'value'}
    )
    print(f"   GET: {'✅' if success else '❌'}")
    
    # 测试 REST POST
    print("\n2. 测试 REST POST...")
    success, result = integration.execute_action(
        'rest_post',
        endpoint='/post',
        data={'key': 'value'}
    )
    print(f"   POST: {'✅' if success else '❌'}")
    
    # 获取状态
    print("\n3. 集成状态:")
    status = integration.get_status()
    print(f"   总动作数：{status['stats']['total_actions']}")
    print(f"   成功率：{status['stats']['successful_actions'] / max(status['stats']['total_actions'], 1):.1%}")
    print(f"   平均响应时间：{status['api_client']['avg_response_time']:.3f}s")
    
    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("=" * 60)

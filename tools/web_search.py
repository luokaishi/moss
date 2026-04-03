#!/usr/bin/env python3
"""
MOSS v5.4 - Web Search Tool
网络搜索工具

核心功能:
- DuckDuckGo 搜索
- 结果提取与摘要
- 搜索历史管理

Author: MOSS Project
Date: 2026-04-03
Version: 5.4.0-dev
"""

import requests
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import quote_plus


@dataclass
class SearchResult:
    """搜索结果"""
    title: str
    url: str
    snippet: str
    score: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'title': self.title,
            'url': self.url,
            'snippet': self.snippet,
            'score': self.score
        }


@dataclass
class SearchQuery:
    """搜索查询"""
    query: str
    timestamp: datetime = field(default_factory=datetime.now)
    results: List[SearchResult] = field(default_factory=list)
    success: bool = False
    error: Optional[str] = None


class DuckDuckGoSearch:
    """
    DuckDuckGo 搜索引擎接口
    
    无需 API 键，免费使用
    """
    
    def __init__(self, safe_search: bool = True):
        self.safe_search = safe_search
        self.search_history: List[SearchQuery] = []
        self.stats = {
            'total_searches': 0,
            'successful_searches': 0,
            'failed_searches': 0,
            'total_results': 0
        }
    
    def search(self, query: str, num_results: int = 10, 
               region: str = "us-en") -> Tuple[bool, List[SearchResult]]:
        """
        执行搜索
        
        Args:
            query: 搜索关键词
            num_results: 返回结果数量
            region: 地区代码
            
        Returns:
            (成功与否，结果列表)
        """
        self.stats['total_searches'] += 1
        
        search_query = SearchQuery(query=query)
        
        try:
            # 使用 DuckDuckGo HTML 接口
            url = "https://html.duckduckgo.com/html/"
            data = {
                'q': query,
                'kl': region
            }
            
            if self.safe_search:
                data['kp'] = '1'
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; MOSS/5.4)'
            }
            
            response = requests.post(url, data=data, headers=headers, timeout=10)
            response.raise_for_status()
            
            # 解析 HTML 结果
            results = self._parse_results(response.text, num_results)
            
            search_query.results = results
            search_query.success = True
            
            self.stats['successful_searches'] += 1
            self.stats['total_results'] += len(results)
            
        except Exception as e:
            search_query.success = False
            search_query.error = str(e)
            self.stats['failed_searches'] += 1
            results = []
        
        self.search_history.append(search_query)
        return search_query.success, results
    
    def _parse_results(self, html: str, max_results: int) -> List[SearchResult]:
        """解析 HTML 搜索结果"""
        results = []
        
        # 简化的 HTML 解析（实际项目中可用 BeautifulSoup）
        import re
        
        # 查找结果链接
        pattern = r'<a[^>]+href="([^"]+)"[^>]*rel="nofollow"[^>]*>(.*?)</a>'
        matches = re.findall(pattern, html, re.DOTALL)
        
        for href, title in matches[:max_results]:
            # 清理标题
            title = re.sub(r'<[^>]+>', '', title).strip()
            
            # 跳过广告和无关链接
            if 'duckduckgo.com' in href or not title:
                continue
            
            results.append(SearchResult(
                title=title,
                url=href,
                snippet=""  # HTML 接口不提供摘要
            ))
        
        return results
    
    def get_suggestions(self, query: str) -> List[str]:
        """获取搜索建议"""
        try:
            url = f"https://duckduckgo.com/ac/?q={quote_plus(query)}&type=list"
            response = requests.get(url, timeout=5)
            data = response.json()
            return data[1] if len(data) > 1 else []
        except:
            return []
    
    def get_status(self) -> Dict:
        """获取搜索状态"""
        return {
            'stats': self.stats,
            'success_rate': (
                self.stats['successful_searches'] / 
                max(self.stats['total_searches'], 1)
            ),
            'avg_results_per_search': (
                self.stats['total_results'] / 
                max(self.stats['total_searches'], 1)
            ),
            'history_size': len(self.search_history)
        }


class WebSearchTool:
    """
    网络搜索工具
    
    提供高级搜索功能
    """
    
    def __init__(self):
        self.search_engine = DuckDuckGoSearch()
    
    def search(self, query: str, num_results: int = 10) -> Dict:
        """
        执行搜索并返回结构化结果
        
        Returns:
            {
                'success': bool,
                'query': str,
                'results': [SearchResult],
                'count': int,
                'error': Optional[str]
            }
        """
        success, results = self.search_engine.search(query, num_results)
        
        return {
            'success': success,
            'query': query,
            'results': [r.to_dict() for r in results],
            'count': len(results),
            'error': None if success else "Search failed"
        }
    
    def search_and_summarize(self, query: str, 
                            num_results: int = 5) -> Dict:
        """
        搜索并生成摘要
        
        Returns:
            {
                'query': str,
                'summary': str,
                'top_results': [SearchResult],
                'confidence': float
            }
        """
        success, results = self.search_engine.search(query, num_results)
        
        if not success or not results:
            return {
                'query': query,
                'summary': "No results found",
                'top_results': [],
                'confidence': 0.0
            }
        
        # 生成简单摘要
        summary_parts = [
            f"Found {len(results)} results for '{query}'",
            f"Top result: {results[0].title}" if results else "",
            f"Source: {results[0].url}" if results else ""
        ]
        
        return {
            'query': query,
            'summary': '\n'.join(summary_parts),
            'top_results': [r.to_dict() for r in results[:3]],
            'confidence': 0.8 if len(results) >= 3 else 0.5
        }
    
    def get_status(self) -> Dict:
        """获取工具状态"""
        return self.search_engine.get_status()


# 测试代码
if __name__ == '__main__':
    print("=" * 60)
    print("MOSS v5.4 - Web Search Tool Test")
    print("=" * 60)
    
    # 创建工具
    tool = WebSearchTool()
    
    # 测试基本搜索
    print("\n1. 测试基本搜索...")
    result = tool.search("Python programming", num_results=5)
    print(f"   查询：{result['query']}")
    print(f"   结果数：{result['count']}")
    print(f"   成功：{result['success']}")
    
    if result['results']:
        print(f"\n   首个结果:")
        print(f"     标题：{result['results'][0]['title']}")
        print(f"     URL: {result['results'][0]['url']}")
    
    # 测试搜索摘要
    print("\n2. 测试搜索摘要...")
    result = tool.search_and_summarize("Machine Learning basics", num_results=3)
    print(f"   查询：{result['query']}")
    print(f"   摘要：{result['summary']}")
    print(f"   置信度：{result['confidence']}")
    
    # 获取状态
    print("\n3. 工具状态:")
    status = tool.get_status()
    print(f"   总搜索数：{status['stats']['total_searches']}")
    print(f"   成功率：{status['success_rate']:.1%}")
    print(f"   平均结果数：{status['avg_results_per_search']:.1f}")
    
    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("=" * 60)

#!/usr/bin/env python3
"""
MOSS Wikipedia Real API Experiment - Standalone Version
独立版本，零框架依赖，可在任何环境执行

Requires: Python 3.6+, curl command
Output: wikipedia_results_YYYYMMDD_HHMMSS.json
"""

import subprocess
import json
import time
from datetime import datetime
from typing import Dict, List, Optional


class WikipediaRealExperiment:
    """
    Wikipedia真实API实验 - 独立版本
    
    功能:
    - 搜索Wikipedia API（完全免费，无需认证）
    - 提取知识条目
    - 构建知识库
    - 生成实验报告
    """
    
    def __init__(self):
        self.knowledge_base: List[Dict] = []
        self.experiment_log: List[Dict] = []
        self.query_count = 0
        self.total_results = 0
    
    def wikipedia_search(self, query: str, limit: int = 5) -> Optional[Dict]:
        """
        执行Wikipedia搜索
        
        API端点: https://en.wikipedia.org/w/api.php
        完全免费，无需认证，无需API key
        """
        try:
            # 构建API URL
            encoded_query = query.replace(' ', '%20')
            url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={encoded_query}&format=json&srlimit={limit}"
            
            # 执行curl请求
            cmd = ['curl', '-s', '--max-time', '10', url]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0 and result.stdout:
                data = json.loads(result.stdout)
                search_results = data.get('query', {}).get('search', [])
                
                self.query_count += 1
                self.total_results += len(search_results)
                
                return {
                    'query': query,
                    'total_hits': data.get('query', {}).get('searchinfo', {}).get('totalhits', 0),
                    'results': [
                        {
                            'title': item.get('title'),
                            'snippet': item.get('snippet', '')
                                .replace('<span class="searchmatch">', '')
                                .replace('</span>', ''),
                            'wordcount': item.get('wordcount', 0),
                            'timestamp': item.get('timestamp', '')
                        }
                        for item in search_results
                    ]
                }
            
            return None
        except Exception as e:
            print(f"  Error in search: {e}")
            return None
    
    def run_experiment(self, topics: List[str]):
        """
        运行知识发现实验
        
        Args:
            topics: 要搜索的主题列表
        """
        print("="*70)
        print("MOSS WIKIPEDIA REAL-WORLD EXPERIMENT")
        print("="*70)
        print(f"Start: {datetime.now().isoformat()}")
        print(f"Topics to explore: {len(topics)}")
        print("API: Wikipedia (free, no authentication required)")
        print("Cost: $0")
        print("="*70)
        print()
        
        for i, topic in enumerate(topics, 1):
            print(f"\n[{i}/{len(topics)}] Exploring: {topic}")
            print("-"*70)
            
            # 执行搜索
            search_result = self.wikipedia_search(topic, limit=3)
            
            if search_result and search_result.get('results'):
                print(f"  ✅ Found {search_result['total_hits']} total hits")
                
                # 处理前3个结果
                for j, result in enumerate(search_result['results'][:3], 1):
                    print(f"     {j}. {result['title']} ({result['wordcount']} words)")
                
                # 保存第一个结果到知识库
                first_result = search_result['results'][0]
                knowledge_item = {
                    'topic': topic,
                    'title': first_result['title'],
                    'wordcount': first_result['wordcount'],
                    'snippet': first_result['snippet'][:200] + "..." if len(first_result['snippet']) > 200 else first_result['snippet'],
                    'timestamp': datetime.now().isoformat()
                }
                self.knowledge_base.append(knowledge_item)
                print(f"  ✅ Added to knowledge base: {first_result['title']}")
            else:
                print(f"  ❌ Search failed or no results")
            
            # 记录日志
            self.experiment_log.append({
                'step': i,
                'topic': topic,
                'success': search_result is not None and bool(search_result.get('results')),
                'results_count': len(search_result.get('results', [])) if search_result else 0
            })
            
            # 尊重API限制（1秒间隔）
            if i < len(topics):
                time.sleep(1)
        
        # 生成最终报告
        self._generate_report()
    
    def _generate_report(self):
        """生成实验报告"""
        print("\n" + "="*70)
        print("EXPERIMENT SUMMARY")
        print("="*70)
        
        total_words = sum(k['wordcount'] for k in self.knowledge_base)
        
        print(f"\nQueries executed: {self.query_count}")
        print(f"Successful: {len([l for l in self.experiment_log if l['success']])}")
        print(f"Total results found: {self.total_results}")
        print(f"Knowledge items acquired: {len(self.knowledge_base)}")
        print(f"Total words processed: {total_words:,}")
        
        print(f"\nKnowledge Base Contents:")
        for i, item in enumerate(self.knowledge_base, 1):
            print(f"  {i}. {item['title']}")
            print(f"     Topic: {item['topic']}")
            print(f"     Words: {item['wordcount']:,}")
        
        # 构建输出数据
        output = {
            'experiment': 'wikipedia_real_api_moss',
            'timestamp': datetime.now().isoformat(),
            'queries': {
                'total': self.query_count,
                'successful': len([l for l in self.experiment_log if l['success']]),
                'topics': [k['topic'] for k in self.knowledge_base]
            },
            'results': {
                'knowledge_items': len(self.knowledge_base),
                'total_words': total_words,
                'total_hits': self.total_results
            },
            'knowledge_base': self.knowledge_base,
            'execution_log': self.experiment_log,
            'cost': {
                'api_calls': self.query_count,
                'usd': 0.0
            }
        }
        
        # 保存结果文件
        filename = f"wikipedia_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*70}")
        print(f"✅ Results saved to: {filename}")
        print(f"{'='*70}")
        
        return filename


def main():
    """主函数"""
    # AI相关主题列表
    topics = [
        "artificial intelligence",
        "machine learning",
        "deep learning",
        "neural network",
        "reinforcement learning",
        "autonomous agent",
        "multi-objective optimization",
        "natural language processing",
        "computer vision",
        "expert system"
    ]
    
    # 创建实验实例并运行
    experiment = WikipediaRealExperiment()
    result_file = experiment.run_experiment(topics)
    
    print(f"\nNext steps:")
    print(f"  1. Check the generated file: {result_file}")
    print(f"  2. Copy it back to your main environment")
    print(f"  3. Submit to GitHub: git add {result_file} && git commit -m \"data: Wikipedia experiment results\"")


if __name__ == '__main__':
    main()

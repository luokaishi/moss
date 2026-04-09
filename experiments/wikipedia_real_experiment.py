"""
MOSS Wikipedia Real-World Experiment
Wikipedia真实世界实验 - 零成本知识获取

利用免费的Wikipedia API进行知识发现和整理
"""

import sys
import subprocess
import json
import time
from datetime import datetime
from typing import Dict, List, Optional

sys.path.insert(0, '/workspace/projects/moss')


class WikipediaRealExperiment:
    """
    Wikipedia真实API实验
    
    目标：验证MOSS可以从免费的真实API获取知识
    """
    
    def __init__(self):
        self.knowledge_base = []
        self.experiment_log = []
        self.query_count = 0
        self.total_results = 0
    
    def wikipedia_search(self, query: str, limit: int = 5) -> Optional[Dict]:
        """
        执行Wikipedia搜索
        
        Wikipedia API完全免费，无需认证
        """
        try:
            # 构建API请求
            url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={query.replace(' ', '%20')}&format=json&srlimit={limit}"
            
            cmd = ['curl', '-s', url]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
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
                            'snippet': item.get('snippet', '').replace('<span class="searchmatch">', '').replace('</span>', ''),
                            'wordcount': item.get('wordcount', 0),
                            'timestamp': item.get('timestamp', '')
                        }
                        for item in search_results
                    ]
                }
            
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def wikipedia_summary(self, title: str) -> Optional[Dict]:
        """获取Wikipedia页面摘要"""
        try:
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title.replace(' ', '_')}"
            cmd = ['curl', '-s', url]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return {
                    'title': data.get('title'),
                    'extract': data.get('extract'),
                    'description': data.get('description', ''),
                    'url': data.get('content_urls', {}).get('desktop', {}).get('page', '')
                }
            return None
        except Exception as e:
            return None
    
    def run_knowledge_discovery(self, topics: List[str]):
        """
        运行知识发现实验
        
        模拟MOSS的Curiosity目标：探索AI相关主题
        """
        print("="*70)
        print("MOSS WIKIPEDIA REAL-WORLD EXPERIMENT")
        print("="*70)
        print(f"Start: {datetime.now().isoformat()}")
        print(f"Topics to explore: {len(topics)}")
        print("Cost: $0 (Wikipedia API is free)")
        print("="*70)
        print()
        
        for i, topic in enumerate(topics, 1):
            print(f"\n[{i}/{len(topics)}] Exploring: {topic}")
            print("-"*70)
            
            # 搜索
            search_result = self.wikipedia_search(topic, limit=3)
            
            if search_result:
                print(f"  ✅ Found {search_result['total_hits']} total hits")
                
                # 获取第一个结果的详细信息
                if search_result['results']:
                    first_result = search_result['results'][0]
                    print(f"  📖 Top result: {first_result['title']}")
                    print(f"     Words: {first_result['wordcount']}")
                    
                    # 获取摘要
                    summary = self.wikipedia_summary(first_result['title'])
                    if summary:
                        extract = summary.get('extract', '')[:150]
                        print(f"     Summary: {extract}...")
                        
                        # 存储到知识库
                        knowledge_item = {
                            'topic': topic,
                            'title': first_result['title'],
                            'wordcount': first_result['wordcount'],
                            'extract': summary.get('extract', '')[:500],
                            'url': summary.get('url', ''),
                            'timestamp': datetime.now().isoformat()
                        }
                        self.knowledge_base.append(knowledge_item)
                        print(f"     ✅ Added to knowledge base")
                    
                    # 显示其他结果
                    for j, result in enumerate(search_result['results'][1:], 2):
                        print(f"     {j}. {result['title']} ({result['wordcount']} words)")
            else:
                print(f"  ❌ Search failed")
            
            # 尊重API限制（1秒间隔）
            time.sleep(1)
            
            # 记录日志
            self.experiment_log.append({
                'step': i,
                'topic': topic,
                'success': search_result is not None,
                'results_count': len(search_result['results']) if search_result else 0
            })
        
        self._generate_report()
    
    def _generate_report(self):
        """生成实验报告"""
        print("\n" + "="*70)
        print("EXPERIMENT SUMMARY")
        print("="*70)
        
        print(f"\nQueries executed: {self.query_count}")
        print(f"Successful: {len([l for l in self.experiment_log if l['success']])}")
        print(f"Total results found: {self.total_results}")
        print(f"Knowledge items acquired: {len(self.knowledge_base)}")
        
        total_words = sum(k['wordcount'] for k in self.knowledge_base)
        print(f"Total words processed: {total_words}")
        
        print(f"\nKnowledge Base Contents:")
        for i, item in enumerate(self.knowledge_base, 1):
            print(f"  {i}. {item['title']} ({item['wordcount']} words)")
            print(f"     Topic: {item['topic']}")
        
        # 保存结果
        result = {
            'experiment': 'wikipedia_real_api',
            'timestamp': datetime.now().isoformat(),
            'queries': self.query_count,
            'knowledge_acquired': len(self.knowledge_base),
            'total_words': total_words,
            'knowledge_base': self.knowledge_base,
            'log': self.experiment_log,
            'cost': 0.0
        }
        
        filename = f"wikipedia_experiment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\n✅ Results saved to: {filename}")
        print("="*70)


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
    
    experiment = WikipediaRealExperiment()
    experiment.run_knowledge_discovery(topics)


if __name__ == '__main__':
    main()

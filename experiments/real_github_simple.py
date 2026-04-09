"""
MOSS Real GitHub Experiment - Direct API Version
直接使用GitHub API的真实实验
"""

import json
import subprocess
from datetime import datetime

def github_search(token: str, query: str):
    """执行GitHub搜索"""
    cmd = [
        'curl', '-s',
        '-H', f'Authorization: token {token}',
        '-H', 'Accept: application/vnd.github.v3+json',
        f'https://api.github.com/search/repositories?q={query.replace(" ", "+")}&per_page=5'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    
    if result.returncode == 0:
        return json.loads(result.stdout)
    return None

# 配置 (从环境变量或配置文件读取)
import os
TOKEN = os.getenv('GITHUB_TOKEN', '')
if not TOKEN:
    # 尝试从配置文件读取
    import json
    try:
        with open('/workspace/projects/moss/integration/api_config.json') as f:
            config = json.load(f)
            TOKEN = config.get('github_token', '')
    except:
        pass
QUERIES = [
    "machine learning stars:>1000",
    "autonomous agents stars:>500",
    "multi objective optimization",
    "self driving car",
    "neural networks tensorflow"
]

print("="*70)
print("MOSS REAL GITHUB API EXPERIMENT")
print("="*70)
print(f"Start: {datetime.now().isoformat()}")
print(f"Queries to execute: {len(QUERIES)}")
print("="*70)
print()

results = []
total_repos = 0
total_stars = 0

for i, query in enumerate(QUERIES, 1):
    print(f"\n[{i}/{len(QUERIES)}] Searching: {query}")
    
    data = github_search(TOKEN, query)
    
    if data:
        count = data.get('total_count', 0)
        items = data.get('items', [])
        
        print(f"  ✅ Found {count} repositories")
        
        query_result = {
            'query': query,
            'total_count': count,
            'top_repos': []
        }
        
        for item in items[:3]:
            repo_info = {
                'name': item.get('full_name'),
                'stars': item.get('stargazers_count'),
                'description': item.get('description', '')[:80]
            }
            query_result['top_repos'].append(repo_info)
            total_stars += repo_info['stars']
            print(f"     • {repo_info['name']}")
            print(f"       {repo_info['stars']} stars - {repo_info['description']}")
        
        results.append(query_result)
        total_repos += len(items)
    else:
        print(f"  ❌ Failed")

# 生成报告
print("\n" + "="*70)
print("EXPERIMENT SUMMARY")
print("="*70)
print(f"Queries executed: {len(QUERIES)}")
print(f"Successful: {len(results)}")
print(f"Total repositories found: {sum(r['total_count'] for r in results)}")
print(f"Top repos stars sum: {total_stars}")
print()

# 保存结果
output = {
    'experiment': 'real_github_api_moss',
    'timestamp': datetime.now().isoformat(),
    'queries': QUERIES,
    'results': results,
    'summary': {
        'total_queries': len(QUERIES),
        'successful_queries': len(results),
        'total_repos_found': sum(r['total_count'] for r in results),
        'total_stars_top_repos': total_stars
    }
}

filename = f"real_github_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(filename, 'w') as f:
    json.dump(output, f, indent=2)

print(f"✅ Results saved to: {filename}")
print("="*70)

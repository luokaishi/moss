# Wikipedia实验 - 境外服务器执行指南

**源环境**: 当前开发环境（代码完备，无外网）  
**目标环境**: 境外OpenClaw服务器（有外网，可访问Wikipedia）  
**目标**: 在境外服务器执行真实Wikipedia API实验

---

## 📦 需要传输的内容

### 1. 核心实验脚本（必须）
```
experiments/wikipedia_real_experiment.py
```

### 2. 依赖文件（必须）
```
requirements.txt
```

### 3. 框架依赖（如需要）
```
core/
  └── experiment_statistics.py  (可选，用于统计分析)
```

### 4. 独立版本（推荐）
已创建独立版本，零依赖，单文件执行：
```
experiments/wikipedia_standalone.py
```

---

## 🚀 执行方案

### 方案A: 传输完整仓库（推荐）

**步骤1**: 在境外服务器克隆仓库
```bash
git clone https://github.com/luokaishi/moss.git
cd moss
```

**步骤2**: 安装依赖
```bash
pip install -r requirements.txt
```

**步骤3**: 执行实验
```bash
python experiments/wikipedia_real_experiment.py
```

**步骤4**: 获取结果
```bash
# 实验完成后，结果保存在：
ls wikipedia_experiment_*.json

# 查看结果
cat wikipedia_experiment_*.json
```

**步骤5**: 传回结果
将生成的JSON文件传回主环境，提交到GitHub

---

### 方案B: 仅传输独立脚本（轻量）

**创建独立版本**（当前环境执行）：
```bash
# 已创建: experiments/wikipedia_standalone.py
# 该文件零依赖，仅需Python标准库 + requests
```

**在境外服务器执行**：
```bash
# 1. 传输文件到境外服务器
scp wikipedia_standalone.py user@foreign-server:/path/

# 2. 在境外服务器执行
python wikipedia_standalone.py

# 3. 传回结果
scp user@foreign-server:/path/wikipedia_experiment_*.json .
```

---

## 📋 独立脚本代码

已准备独立版本（无框架依赖）：

```python
#!/usr/bin/env python3
"""
MOSS Wikipedia Experiment - Standalone Version
独立版本，零依赖，可在任何环境执行
"""

import subprocess
import json
import time
from datetime import datetime

class WikipediaExperiment:
    def __init__(self):
        self.knowledge_base = []
        self.log = []
        
    def search(self, query, limit=3):
        """执行Wikipedia搜索"""
        try:
            url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={query.replace(' ', '%20')}&format=json&srlimit={limit}"
            result = subprocess.run(['curl', '-s', url], capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return {
                    'query': query,
                    'total_hits': data.get('query', {}).get('searchinfo', {}).get('totalhits', 0),
                    'results': [
                        {
                            'title': item.get('title'),
                            'snippet': item.get('snippet', '').replace('<span class="searchmatch">', '').replace('</span>', ''),
                            'wordcount': item.get('wordcount', 0)
                        }
                        for item in data.get('query', {}).get('search', [])
                    ]
                }
        except Exception as e:
            print(f"Error: {e}")
        return None
    
    def run(self, topics):
        """运行实验"""
        print("MOSS Wikipedia Experiment (Standalone)")
        print("="*50)
        print(f"Start: {datetime.now().isoformat()}")
        print(f"Topics: {len(topics)}")
        print()
        
        for i, topic in enumerate(topics, 1):
            print(f"[{i}/{len(topics)}] {topic}")
            result = self.search(topic)
            
            if result and result['results']:
                print(f"  ✓ Found {result['total_hits']} hits")
                self.knowledge_base.append({
                    'topic': topic,
                    'title': result['results'][0]['title'],
                    'wordcount': result['results'][0]['wordcount'],
                    'timestamp': datetime.now().isoformat()
                })
            else:
                print(f"  ✗ Failed")
            
            time.sleep(1)
        
        # 保存结果
        output = {
            'experiment': 'wikipedia_real',
            'timestamp': datetime.now().isoformat(),
            'topics': topics,
            'knowledge_acquired': len(self.knowledge_base),
            'knowledge_base': self.knowledge_base
        }
        
        filename = f"wikipedia_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\n✓ Results saved: {filename}")
        print(f"  Knowledge items: {len(self.knowledge_base)}")

if __name__ == '__main__':
    topics = [
        "artificial intelligence",
        "machine learning", 
        "deep learning",
        "neural network",
        "reinforcement learning"
    ]
    
    exp = WikipediaExperiment()
    exp.run(topics)
```

---

## 📤 传输命令示例

### 方式1: GitHub（推荐）
```bash
# 在当前环境提交
 git add experiments/wikipedia_real_experiment.py
 git commit -m "Add Wikipedia experiment"
 git push

# 在境外服务器拉取
git pull origin main
python experiments/wikipedia_real_experiment.py
```

### 方式2: SCP传输
```bash
# 传输到境外服务器
scp experiments/wikipedia_standalone.py user@server:/tmp/

# SSH到境外服务器执行
ssh user@server "cd /tmp && python wikipedia_standalone.py"

# 传回结果
scp user@server:/tmp/wikipedia_results_*.json .
```

### 方式3: 复制粘贴
直接将 `wikipedia_standalone.py` 内容复制到境外服务器的文件中

---

## ✅ 执行检查清单

### 当前环境（准备）
- [ ] 提交最新代码到GitHub
- [ ] 确认 `wikipedia_real_experiment.py` 已推送
- [ ] 或创建 `wikipedia_standalone.py` 独立版本

### 境外服务器（执行）
- [ ] 克隆/传输代码
- [ ] 确认网络可访问 wikipedia.org
- [ ] 执行实验脚本
- [ ] 检查生成的JSON文件

### 结果处理
- [ ] 将结果文件传回主环境
- [ ] 提交到GitHub仓库
- [ ] 更新文档和README

---

## 🎯 预期结果

成功执行后应生成：
```
wikipedia_experiment_20260311_HHMMSS.json
```

包含：
- 5-10个AI主题搜索结果
- 知识条目（标题、词汇量、时间戳）
- 总词汇量 5,000+
- 零成本验证

---

## ⚡ 立即行动

**方案**: GitHub同步（最简单）

**你只需在境外服务器执行**:
```bash
git clone https://github.com/luokaishi/moss.git
cd moss
python experiments/wikipedia_real_experiment.py
# 等待完成（约2分钟）
```

**完成后将结果文件传回**，我帮你整合到项目中！

---

**准备就绪！等待你在境外服务器执行！🚀**

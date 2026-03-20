"""
MOSS v3.1/v4.0 Real World Bridge
================================

让MOSS能真正操作GitHub、浏览器、文件系统等真实世界工具
基于v3.1.0的9维架构，将D9 Purpose转化为真实世界行动

Author: Cash
Date: 2026-03-20
Version: 4.0.0-dev (Step 1)
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import numpy as np

# 添加v3到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'v3'))

# 复用现有集成
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'integration'))

logger = logging.getLogger(__name__)


class RealWorldBridge:
    """
    MOSS真实世界桥接层
    
    将MOSS的意图和Purpose转化为真实世界操作
    支持：GitHub、文件系统、浏览器、API调用等
    """
    
    def __init__(self, agent, config_path: Optional[str] = None):
        """
        初始化真实世界桥接器
        
        Args:
            agent: MOSS Agent实例（需要包含purpose_generator）
            config_path: API配置文件路径
        """
        self.agent = agent
        self.config_path = config_path or "integration/api_config.json"
        self.action_log_path = Path("experiments/real_world_actions.jsonl")
        
        # 确保日志目录存在
        self.action_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 加载配置
        self.config = self._load_config()
        
        # 初始化工具
        self.tools = {}
        self._init_tools()
        
        logger.info("[RealWorldBridge] Initialized with tools: %s", list(self.tools.keys()))
    
    def _load_config(self) -> Dict:
        """加载API配置"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"[RealWorldBridge] Config not found at {self.config_path}, using defaults")
            return {}
    
    def _init_tools(self):
        """初始化可用工具"""
        # GitHub (使用现有脚本)
        self.tools['github'] = {
            'enabled': self._check_github_auth(),
            'description': 'GitHub operations: PR, issue, commit, push',
            'execute': self._execute_github_action
        }
        
        # 文件系统
        self.tools['filesystem'] = {
            'enabled': True,
            'description': 'File operations: read, write, move, delete',
            'execute': self._execute_filesystem_action
        }
        
        # 浏览器 (Playwright/Selenium wrapper)
        self.tools['browser'] = {
            'enabled': False,  # 需要额外安装
            'description': 'Browser automation: navigate, click, scrape',
            'execute': self._execute_browser_action
        }
        
        # 命令行
        self.tools['shell'] = {
            'enabled': True,
            'description': 'Shell commands: git, python, etc.',
            'execute': self._execute_shell_action
        }
    
    def _check_github_auth(self) -> bool:
        """检查GitHub认证是否可用"""
        token = self.config.get('github_token') or os.getenv('GITHUB_TOKEN')
        return bool(token)
    
    def execute_real_action(self, task_description: str, step: int, 
                          context: Optional[Dict] = None) -> Dict:
        """
        核心方法：将MOSS意图转化为真实世界操作
        
        Args:
            task_description: 任务描述
            step: 当前步骤
            context: 额外上下文
            
        Returns:
            操作结果字典
        """
        # 1. 获取当前Purpose
        current_purpose = self._get_current_purpose(step)
        
        # 2. 决策：选择合适的工具
        tool_choice = self._select_tool(task_description, current_purpose)
        
        # 3. 生成具体操作
        action_plan = self._generate_action_plan(
            task_description, tool_choice, current_purpose, context
        )
        
        # 4. 执行操作
        result = self._execute_action(action_plan)
        
        # 5. 记录日志
        self._log_action(task_description, action_plan, result, step, current_purpose)
        
        return result
    
    def _get_current_purpose(self, step: int) -> Dict:
        """获取当前Purpose信息"""
        # 从agent获取purpose generator
        if hasattr(self.agent, 'purpose_generator'):
            pg = self.agent.purpose_generator
            # Handle both numpy array and list
            vector = pg.purpose_vector if hasattr(pg, 'purpose_vector') else []
            if hasattr(vector, 'tolist'):
                vector = vector.tolist()
            return {
                'vector': vector,
                'statement': pg.current_statement if hasattr(pg, 'current_statement') else '',
                'dominant': self._get_dominant_dimension(pg)
            }
        return {'vector': [], 'statement': '', 'dominant': 'Unknown'}
    
    def _get_dominant_dimension(self, purpose_gen) -> str:
        """获取主导维度"""
        if not hasattr(purpose_gen, 'purpose_vector'):
            return 'Unknown'
        
        import numpy as np
        purpose_8d = np.array(purpose_gen.purpose_vector[:8])
        dim_names = ['Survival', 'Curiosity', 'Influence', 'Optimization',
                    'Coherence', 'Valence', 'Other', 'Norm']
        top_idx = np.argmax(purpose_8d)
        return dim_names[top_idx]
    
    def _select_tool(self, task: str, purpose: Dict) -> str:
        """基于任务和Purpose选择工具"""
        task_lower = task.lower()
        
        # 关键词匹配
        if any(kw in task_lower for kw in ['github', 'pr', 'commit', 'push', 'issue']):
            return 'github' if self.tools['github']['enabled'] else 'shell'
        
        if any(kw in task_lower for kw in ['browse', 'navigate', 'click', 'web']):
            return 'browser' if self.tools['browser']['enabled'] else 'shell'
        
        if any(kw in task_lower for kw in ['read file', 'write file', 'move', 'delete']):
            return 'filesystem'
        
        # 基于Purpose的启发式选择
        dominant = purpose.get('dominant', '')
        if dominant == 'Curiosity':
            return 'browser' if self.tools['browser']['enabled'] else 'shell'
        elif dominant == 'Optimization':
            return 'shell'
        elif dominant == 'Survival':
            return 'filesystem'
        
        return 'shell'
    
    def _generate_action_plan(self, task: str, tool: str, 
                             purpose: Dict, context: Optional[Dict]) -> Dict:
        """生成详细行动计划"""
        return {
            'tool': tool,
            'task': task,
            'purpose_dominant': purpose.get('dominant', 'Unknown'),
            'purpose_statement': purpose.get('statement', ''),
            'timestamp': datetime.now().isoformat(),
            'context': context or {}
        }
    
    def _execute_action(self, action_plan: Dict) -> Dict:
        """执行行动计划"""
        tool = action_plan['tool']
        
        if tool not in self.tools:
            return {
                'success': False,
                'error': f'Unknown tool: {tool}',
                'action': action_plan
            }
        
        if not self.tools[tool]['enabled']:
            return {
                'success': False,
                'error': f'Tool {tool} is disabled',
                'action': action_plan
            }
        
        try:
            result = self.tools[tool]['execute'](action_plan)
            return {
                'success': True,
                'tool': tool,
                'result': result,
                'action': action_plan
            }
        except Exception as e:
            logger.error(f"[RealWorldBridge] Action failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'action': action_plan
            }
    
    def _execute_github_action(self, action_plan: Dict) -> Dict:
        """执行GitHub操作"""
        import subprocess
        
        task = action_plan['task'].lower()
        result = {'executed': False, 'output': ''}
        
        # 使用git命令行
        if 'commit' in task:
            # 示例：自动提交
            cmd = ['git', 'add', '-A']
            subprocess.run(cmd, capture_output=True, text=True)
            
            cmd = ['git', 'commit', '-m', f'"Auto commit by MOSS at {datetime.now().isoformat()}"']
            r = subprocess.run(cmd, capture_output=True, text=True)
            result['executed'] = True
            result['output'] = r.stdout or r.stderr
            
        elif 'push' in task:
            cmd = ['git', 'push']
            r = subprocess.run(cmd, capture_output=True, text=True)
            result['executed'] = True
            result['output'] = r.stdout or r.stderr
            
        elif 'status' in task:
            cmd = ['git', 'status']
            r = subprocess.run(cmd, capture_output=True, text=True)
            result['executed'] = True
            result['output'] = r.stdout
        
        return result
    
    def _execute_filesystem_action(self, action_plan: Dict) -> Dict:
        """执行文件系统操作"""
        result = {'executed': False}
        # 实现文件读写等操作
        return result
    
    def _execute_browser_action(self, action_plan: Dict) -> Dict:
        """执行浏览器操作（需要Playwright/Selenium）"""
        result = {'executed': False, 'note': 'Browser automation requires Playwright installation'}
        return result
    
    def _execute_shell_action(self, action_plan: Dict) -> Dict:
        """执行shell命令"""
        import subprocess
        
        task = action_plan['task']
        result = {'executed': False, 'output': ''}
        
        # 安全：只允许白名单命令
        safe_commands = ['git', 'python', 'ls', 'cat', 'echo', 'pwd']
        
        # 简单解析
        if task.startswith('git '):
            cmd = task.split()
            r = subprocess.run(cmd, capture_output=True, text=True, cwd='/workspace/projects/moss')
            result['executed'] = True
            result['output'] = r.stdout or r.stderr
        elif task.startswith('python '):
            cmd = task.split()
            r = subprocess.run(cmd, capture_output=True, text=True, cwd='/workspace/projects/moss')
            result['executed'] = True
            result['output'] = r.stdout or r.stderr
        else:
            result['output'] = 'Command not in safe list'
        
        return result
    
    def _log_action(self, task: str, action_plan: Dict, 
                   result: Dict, step: int, purpose: Dict):
        """记录真实世界行为"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'step': step,
            'task': task,
            'action': action_plan,
            'result': result,
            'purpose': purpose
        }
        
        with open(self.action_log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        
        logger.info(f"[RealWorldBridge] Step {step}: {action_plan['tool']} -> {'success' if result.get('success') else 'failed'}")
    
    def get_action_summary(self, n_recent: int = 10) -> List[Dict]:
        """获取最近的行为摘要"""
        try:
            with open(self.action_log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                return [json.loads(line) for line in lines[-n_recent:]]
        except FileNotFoundError:
            return []


# ============== 快速测试 ==============
if __name__ == "__main__":
    # 简单测试
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("MOSS v3.1 RealWorldBridge Test")
    print("=" * 60)
    
    # 模拟一个agent
    class MockAgent:
        pass
    
    agent = MockAgent()
    bridge = RealWorldBridge(agent)
    
    print(f"\nInitialized tools: {list(bridge.tools.keys())}")
    print(f"GitHub enabled: {bridge.tools['github']['enabled']}")
    print(f"Filesystem enabled: {bridge.tools['filesystem']['enabled']}")
    print(f"Shell enabled: {bridge.tools['shell']['enabled']}")
    
    # 测试git status
    print("\n--- Testing git status ---")
    result = bridge.execute_real_action("git status", step=0)
    print(f"Result: {result.get('success')}")
    if result.get('result', {}).get('output'):
        print(f"Output preview: {result['result']['output'][:200]}...")
    
    print("\n--- Test Complete ---")

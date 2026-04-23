#!/usr/bin/env python3
"""
任务场景库 - 支持多种实用任务
"""

TASK_SCENARIOS = {
    'file_organization': {
        'name': '文件整理',
        'description': '按文件类型整理到对应文件夹',
        'actions': [
            {'cmd': 'ls -la', 'desc': '列出文件'},
            {'cmd': 'mkdir -p images documents code', 'desc': '创建文件夹'},
            {'cmd': 'mv *.jpg *.png *.gif images/ 2>/dev/null; echo done', 'desc': '移动图片'},
            {'cmd': 'mv *.pdf *.txt *.md *.json documents/ 2>/dev/null; echo done', 'desc': '移动文档'},
            {'cmd': 'mv *.py *.js *.sh *.css *.html code/ 2>/dev/null; echo done', 'desc': '移动代码'},
        ],
        'file_types': {
            'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp'],
            'documents': ['.pdf', '.txt', '.md', '.doc', '.docx', '.json', '.xml'],
            'code': ['.py', '.js', '.sh', '.css', '.html', '.java', '.cpp', '.c', '.h'],
        }
    },
    
    'log_analysis': {
        'name': '日志分析',
        'description': '分析日志文件，找出错误和警告',
        'actions': [
            {'cmd': 'find . -name "*.log" -type f 2>/dev/null | head -5', 'desc': '查找日志文件'},
            {'cmd': 'grep -i "error" *.log 2>/dev/null | wc -l', 'desc': '统计错误数'},
            {'cmd': 'grep -i "warning" *.log 2>/dev/null | wc -l', 'desc': '统计警告数'},
            {'cmd': 'grep -i "error" *.log 2>/dev/null | head -10', 'desc': '查看错误详情'},
            {'cmd': 'tail -50 *.log 2>/dev/null | head -50', 'desc': '查看最新日志'},
        ],
        'success_metric': 'found_errors',
    },
    
    'system_monitor': {
        'name': '系统监控',
        'description': '监控系统资源使用情况',
        'actions': [
            {'cmd': 'df -h', 'desc': '检查磁盘空间'},
            {'cmd': 'free -h', 'desc': '检查内存使用'},
            {'cmd': 'ps aux --sort=-%cpu | head -10', 'desc': '查看CPU占用'},
            {'cmd': 'ps aux --sort=-%mem | head -10', 'desc': '查看内存占用'},
            {'cmd': 'uptime', 'desc': '查看系统运行时间'},
        ],
        'success_metric': 'collected_metrics',
    },
    
    'code_review': {
        'name': '代码审查',
        'description': '检查代码质量和潜在问题',
        'actions': [
            {'cmd': 'find . -name "*.py" -type f 2>/dev/null | wc -l', 'desc': '统计Python文件'},
            {'cmd': 'find . -name "*.py" -exec grep -l "TODO\|FIXME" {} \\; 2>/dev/null', 'desc': '查找TODO标记'},
            {'cmd': 'grep -r "import" --include="*.py" . 2>/dev/null | wc -l', 'desc': '统计导入语句'},
            {'cmd': 'find . -name "*.py" -exec wc -l {} + 2>/dev/null | tail -1', 'desc': '统计代码行数'},
        ],
        'success_metric': 'analyzed_files',
    },
    
    'backup_cleanup': {
        'name': '备份清理',
        'description': '清理旧的备份文件',
        'actions': [
            {'cmd': 'find . -name "*.bak" -o -name "*.backup" -o -name "*~" 2>/dev/null | wc -l', 'desc': '统计备份文件'},
            {'cmd': 'find . -name "*.bak" -mtime +7 2>/dev/null', 'desc': '查找7天前备份'},
            {'cmd': 'find . -name "*.tmp" -o -name "*.temp" 2>/dev/null | wc -l', 'desc': '统计临时文件'},
            {'cmd': 'find . -name "__pycache__" -type d 2>/dev/null | wc -l', 'desc': '统计缓存目录'},
        ],
        'success_metric': 'cleaned_size',
    },
}


def get_task_scenario(task_type: str) -> dict:
    """获取任务场景配置"""
    return TASK_SCENARIOS.get(task_type, TASK_SCENARIOS['file_organization'])


def list_available_tasks() -> list:
    """列出所有可用任务"""
    return [
        {'type': key, 'name': value['name'], 'description': value['description']}
        for key, value in TASK_SCENARIOS.items()
    ]


if __name__ == '__main__':
    print("=" * 60)
    print("可用任务场景")
    print("=" * 60)
    
    for task in list_available_tasks():
        print(f"\n{task['type']}: {task['name']}")
        print(f"  {task['description']}")

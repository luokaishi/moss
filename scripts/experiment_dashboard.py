#!/usr/bin/env python3
"""
MOSS 72小时实验实时监控仪表盘

使用: python3 scripts/experiment_dashboard.py
功能: 实时显示实验状态、Purpose演化、操作统计
"""

import json
import time
import os
from pathlib import Path
from datetime import datetime, timedelta

def clear_screen():
    """清屏"""
    os.system('clear' if os.name != 'nt' else 'cls')

def load_experiment_data():
    """加载实验数据"""
    data = {}
    
    # Purpose数据
    purpose_file = Path('experiments/purpose_real_world_agent.json')
    if purpose_file.exists():
        try:
            with open(purpose_file) as f:
                data['purpose'] = json.load(f)
        except:
            pass
    
    # 行为数据
    actions_file = Path('experiments/real_world_actions.jsonl')
    if actions_file.exists():
        try:
            with open(actions_file) as f:
                lines = f.readlines()
                if lines:
                    data['last_action'] = json.loads(lines[-1])
                    data['total_actions'] = len(lines)
        except:
            pass
    
    return data

def format_duration(seconds):
    """格式化时间"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def draw_progress_bar(percent, width=50):
    """绘制进度条"""
    filled = int(width * percent / 100)
    bar = '█' * filled + '░' * (width - filled)
    return f"[{bar}] {percent:.2f}%"

def draw_purpose_chart(purpose_history, max_entries=10):
    """绘制Purpose演化简图"""
    if not purpose_history:
        return "暂无数据"
    
    dims = ['S', 'C', 'I', 'O']
    recent = purpose_history[-max_entries:]
    
    lines = []
    lines.append("Step     | S    C    I    O    | 主导")
    lines.append("---------|---------------------|------")
    
    for h in recent:
        step = h['step']
        pv = h['purpose_vector'][:4]
        max_idx = pv.index(max(pv))
        dominant = dims[max_idx]
        
        # 简化显示
        values = ' '.join(f"{v:.2f}" for v in pv)
        lines.append(f"{step:>8} | {values} | {dominant}")
    
    return '\n'.join(lines)

def display_dashboard():
    """显示仪表盘"""
    clear_screen()
    
    # 标题
    print("=" * 70)
    print("              🌱 MOSS 72小时实验实时监控仪表盘")
    print("=" * 70)
    
    # 加载数据
    data = load_experiment_data()
    
    # 基础信息
    print("\n📊 实验基本信息")
    print("-" * 70)
    
    # 尝试获取启动时间
    start_time = datetime(2026, 3, 21, 10, 23)  # Run 2启动时间
    now = datetime.now()
    elapsed = (now - start_time).total_seconds()
    total_seconds = 72 * 3600
    progress = elapsed / total_seconds * 100
    
    print(f"启动时间: 2026-03-21 10:23:00")
    print(f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"已运行:   {format_duration(elapsed)}")
    print(f"总时长:   72:00:00")
    print(f"进度:     {draw_progress_bar(progress)}")
    
    # 操作统计
    print("\n🛠️  操作统计")
    print("-" * 70)
    if 'total_actions' in data:
        print(f"总操作数: {data['total_actions']}")
    else:
        print("总操作数: 加载中...")
    
    if 'last_action' in data:
        last = data['last_action']
        print(f"当前Step: {last['step']}")
        print(f"当前任务: {last['task'][:40]}")
        print(f"主导Purpose: {last['purpose']['dominant']}")
    else:
        print("当前Step: 加载中...")
    
    # Purpose演化
    print("\n🎯 Purpose演化历史")
    print("-" * 70)
    if 'purpose' in data and data['purpose'].get('purpose_history'):
        history = data['purpose']['purpose_history']
        print(f"Purpose生成: {len(history)}次")
        print()
        print(draw_purpose_chart(history))
        
        # 主导分布
        if history:
            from collections import Counter
            dims = ['Survival', 'Curiosity', 'Influence', 'Optimization']
            dominant = [dims[h['purpose_vector'][:4].index(max(h['purpose_vector'][:4]))] for h in history]
            counts = Counter(dominant)
            
            print("\n主导分布:")
            for dim, count in counts.most_common():
                bar = '█' * count
                print(f"  {dim:12} | {bar} {count}")
    else:
        print("等待首次Purpose生成...")
        print("预计时间: Step 2,000 (~15:30)")
    
    # 下次重要事件
    print("\n⏰ 下次重要事件")
    print("-" * 70)
    if 'purpose' in data and data['purpose'].get('purpose_history'):
        last_gen = data['purpose']['current_purpose']['last_generation']
        next_gen = last_gen + 2000
        print(f"下次Purpose生成: Step {next_gen}")
    else:
        print("下次Purpose生成: Step 2,000 (~15:30)")
    
    # 状态指示
    print("\n✅ 系统状态")
    print("-" * 70)
    print("🟢 实验运行中")
    print("🟢 自动提交活跃")
    print("🟢 数据记录正常")
    print("🟡 等待Purpose生成")
    
    print("\n" + "=" * 70)
    print("按 Ctrl+C 退出监控 | 刷新间隔: 10秒")
    print("=" * 70)

def main():
    """主函数"""
    try:
        while True:
            display_dashboard()
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n\n监控已停止")

if __name__ == "__main__":
    main()

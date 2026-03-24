#!/bin/bash
# 下载远程实验数据并清理

mkdir -p /workspace/projects/moss/remote_backup

echo "=== 下载远程实验数据 ==="
echo ""

# 服务器1 - Run 4.3 (45.8%进度)
echo "【服务器1】下载Run 4.3数据..."
scp admin@47.77.234.152:~/moss/experiments/run_4_3_actions.jsonl /workspace/projects/moss/remote_backup/run_4_3_remote_actions.jsonl 2>/dev/null && echo "✅ 行动记录已下载" || echo "❌ 下载失败"
scp admin@47.77.234.152:~/moss/experiments/run_4_3_status.json /workspace/projects/moss/remote_backup/run_4_3_remote_status.json 2>/dev/null && echo "✅ 状态文件已下载" || echo "❌ 下载失败"
scp admin@47.77.234.152:~/moss/experiments/run_4_3.out /workspace/projects/moss/remote_backup/run_4_3_remote.log 2>/dev/null && echo "✅ 日志已下载" || echo "❌ 下载失败"

echo ""
echo "【服务器2】下载Run 4.4数据..."
scp root@43.156.104.179:/opt/moss/experiments/run_4_4_actions.jsonl /workspace/projects/moss/remote_backup/run_4_4_remote_actions.jsonl 2>/dev/null && echo "✅ 行动记录已下载" || echo "❌ 下载失败"
scp root@43.156.104.179:/opt/moss/experiments/run_4_4_status.json /workspace/projects/moss/remote_backup/run_4_4_remote_status.json 2>/dev/null && echo "✅ 状态文件已下载" || echo "❌ 下载失败"
scp root@43.156.104.179:/opt/moss/experiments/run_4_4.out /workspace/projects/moss/remote_backup/run_4_4_remote.log 2>/dev/null && echo "✅ 日志已下载" || echo "❌ 下载失败"

echo ""
echo "=== 备份完成 ==="
ls -lh /workspace/projects/moss/remote_backup/

echo ""
echo "=== 清理远程实验 ==="
echo ""

# 停止并清理服务器1
echo "【服务器1】停止实验并清理..."
ssh admin@47.77.234.152 "pkill -f run_4_3_optimized; sleep 2; rm -rf ~/moss/experiments/.checkpoints_run4_3; echo '服务器1清理完成'"

# 停止并清理服务器2
echo "【服务器2】停止实验并清理..."
ssh root@43.156.104.179 "pkill -f run_4_4_optimized; sleep 2; rm -rf /opt/moss/experiments/.checkpoints_run4_4; echo '服务器2清理完成'"

echo ""
echo "=== 全部完成 ==="
echo "远程数据已备份到: /workspace/projects/moss/remote_backup/"
echo "远程实验已停止并清理"

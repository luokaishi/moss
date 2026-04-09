#!/bin/bash
# MOSS GitHub监控脚本
# 每周自动报告项目关注度变化

REPO="luokaishi/moss"
LOG_FILE="/workspace/projects/moss/logs/github_metrics.log"
ALERT_THRESHOLD=50  # Star增长超过此数值时提醒

# 创建日志目录
mkdir -p $(dirname $LOG_FILE)

# 获取当前指标
echo "=== MOSS GitHub监控报告 ===" | tee -a $LOG_FILE
echo "时间: $(date)" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

# 使用GitHub API获取数据（需要token）
if [ -n "$GITHUB_TOKEN" ]; then
    METRICS=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
        "https://api.github.com/repos/$REPO")
else
    # 公开API（有限制）
    METRICS=$(curl -s "https://api.github.com/repos/$REPO")
fi

# 解析关键指标
STARS=$(echo $METRICS | grep -o '"stargazers_count":[0-9]*' | cut -d':' -f2)
FORKS=$(echo $METRICS | grep -o '"forks_count":[0-9]*' | cut -d':' -f2)
WATCHERS=$(echo $METRICS | grep -o '"watchers_count":[0-9]*' | cut -d':' -f2)
ISSUES=$(echo $METRICS | grep -o '"open_issues_count":[0-9]*' | cut -d':' -f2)

# 显示当前状态
echo "当前指标:" | tee -a $LOG_FILE
echo "  Stars:    $STARS" | tee -a $LOG_FILE
echo "  Forks:    $FORKS" | tee -a $LOG_FILE
echo "  Watchers: $WATCHERS" | tee -a $LOG_FILE
echo "  Issues:   $ISSUES" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

# 与上次记录对比
if [ -f "/tmp/moss_last_metrics.json" ]; then
    LAST_STARS=$(cat /tmp/moss_last_metrics.json | grep -o '"stars":[0-9]*' | cut -d':' -f2)
    DELTA=$((STARS - LAST_STARS))
    
    echo "变化对比 (vs 上次检查):" | tee -a $LOG_FILE
    echo "  Stars变化: $DELTA" | tee -a $LOG_FILE
    
    if [ $DELTA -gt 0 ]; then
        echo "  ✅ 增长趋势" | tee -a $LOG_FILE
    elif [ $DELTA -lt 0 ]; then
        echo "  ⚠️  下降趋势" | tee -a $LOG_FILE
    else
        echo "  ➡️  持平" | tee -a $LOG_FILE
    fi
    
    # 如果增长超过阈值，生成警报
    if [ $DELTA -ge $ALERT_THRESHOLD ]; then
        echo "" | tee -a $LOG_FILE
        echo "🎉 重要里程碑! Stars增长超过 $ALERT_THRESHOLD" | tee -a $LOG_FILE
        echo "当前Stars: $STARS" | tee -a $LOG_FILE
        echo "建议考虑启动商业转化评估" | tee -a $LOG_FILE
        
        # 创建警报文件
        echo "$(date): Stars reached $STARS (+$DELTA)" > /tmp/moss_github_alert
    fi
else
    echo "首次记录，无对比数据" | tee -a $LOG_FILE
fi

# 保存当前指标供下次对比
echo "{\"stars\":$STARS,\"forks\":$FORKS,\"watchers\":$WATCHERS,\"issues\":$ISSUES,\"timestamp\":\"$(date -Iseconds)\"}" > /tmp/moss_last_metrics.json

# 趋势分析（如果有历史数据）
if [ -f "$LOG_FILE" ]; then
    echo "历史趋势 (最近5次检查):" | tee -a $LOG_FILE
    grep "Stars:" $LOG_FILE | tail -5 | nl | tee -a $LOG_FILE
fi

echo "" | tee -a $LOG_FILE
echo "检查完成. 下次检查建议: $(date -d '+7 days' '+%Y-%m-%d')" | tee -a $LOG_FILE
echo "========================================" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

# 输出简洁摘要
echo "摘要: Stars=$STARS, Forks=$FORKS, 变化=$DELTA"

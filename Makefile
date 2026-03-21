# MOSS v4.0 Makefile
# 便捷命令管理

.PHONY: help install test experiment dashboard clean

help:
	@echo "MOSS v4.0 - 可用命令"
	@echo "====================="
	@echo "make install       - 安装依赖"
	@echo "make test          - 运行测试"
	@echo "make experiment    - 启动72小时实验"
	@echo "make dashboard     - 启动监控仪表盘"
	@echo "make status        - 查看实验状态"
	@echo "make stop          - 停止实验"
	@echo "make analyze       - 分析实验数据"
	@echo "make clean         - 清理临时文件"
	@echo "make backup        - 备份实验数据"

install:
	pip install -r requirements.txt

test:
	python -m pytest tests/ -v

experiment:
	@echo "启动72小时实验..."
	nohup python3 experiments/real_world_72h.py --hours 72 > experiments/real_world_72h.out 2>&1 &
	@echo "实验已启动，使用 'make dashboard' 查看状态"

dashboard:
	@python3 scripts/experiment_dashboard.py

status:
	@echo "=== 实验状态 ==="
	@ps aux | grep "real_world_72h" | grep -v grep || echo "实验未运行"
	@echo ""
	@echo "=== 最新日志 ==="
	@tail -5 experiments/real_world_72h.log 2>/dev/null || echo "暂无日志"

stop:
	@echo "停止实验..."
	@pkill -f "real_world_72h.py" && echo "实验已停止" || echo "实验未运行"

analyze:
	@python3 scripts/analyze_72h_experiment.py

backup:
	@echo "备份实验数据..."
	@mkdir -p experiments/backups
	@cp experiments/real_world_actions.jsonl experiments/backups/ 2>/dev/null || true
	@cp experiments/real_world_72h.log experiments/backups/ 2>/dev/null || true
	@cp experiments/purpose_real_world_agent.json experiments/backups/ 2>/dev/null || true
	@echo "备份完成"

clean:
	@echo "清理临时文件..."
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.log" -not -path "./experiments/*" -delete
	@echo "清理完成"

# Phase 2 命令
society:
	@echo "启动多Agent社会实验..."
	@python3 experiments/multi_agent_society_real.py

pricing:
	@echo "打开定价页面..."
	@python3 -m http.server 8080 --directory docs &
	@echo "访问 http://localhost:8080/pricing.html"

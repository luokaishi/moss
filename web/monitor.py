"""
MOSS Web监控面板
Flask-based web dashboard for monitoring MOSS agents
"""

from flask import Flask, jsonify, render_template_string
import json
import time
from datetime import datetime
import threading

app = Flask(__name__)

# 全局状态存储
moss_status = {
    'agent_id': None,
    'mode': None,
    'running': False,
    'start_time': None,
    'stats': {
        'total_decisions': 0,
        'total_actions': 0,
        'safety_violations': 0
    },
    'current_state': None,
    'weights': {},
    'metrics': {},
    'history': []
}

# HTML模板
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>MOSS Monitor</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0a0a;
            color: #00ff00;
            min-height: 100vh;
            padding: 20px;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            border-bottom: 2px solid #00ff00;
        }
        .header h1 {
            font-size: 2.5em;
            text-transform: uppercase;
            letter-spacing: 3px;
            text-shadow: 0 0 10px #00ff00;
        }
        .status {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: #111;
            border: 1px solid #00ff00;
            padding: 20px;
            border-radius: 8px;
        }
        .card h3 {
            margin-bottom: 15px;
            color: #00ff00;
            font-size: 0.9em;
            text-transform: uppercase;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            margin: 8px 0;
            font-family: 'Courier New', monospace;
        }
        .metric-value {
            color: #00ff00;
            font-weight: bold;
        }
        .weights {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-top: 15px;
        }
        .weight-bar {
            background: #222;
            height: 30px;
            border-radius: 4px;
            overflow: hidden;
            position: relative;
        }
        .weight-fill {
            height: 100%;
            background: linear-gradient(90deg, #00ff00, #00aa00);
            transition: width 0.5s ease;
        }
        .weight-label {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 0.8em;
            color: #fff;
            text-shadow: 1px 1px 2px #000;
        }
        .state-indicator {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            text-transform: uppercase;
        }
        .state-normal { background: #00ff00; color: #000; }
        .state-crisis { background: #ff0000; color: #fff; }
        .state-concerned { background: #ffaa00; color: #000; }
        .state-growth { background: #00aaff; color: #000; }
        .chart-container {
            height: 200px;
            background: #111;
            border: 1px solid #00ff00;
            margin-top: 15px;
            padding: 10px;
            overflow: hidden;
        }
        .log-container {
            background: #111;
            border: 1px solid #00ff00;
            padding: 15px;
            height: 300px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
        }
        .log-entry {
            margin: 2px 0;
            padding: 2px 5px;
        }
        .log-time { color: #666; }
        .footer {
            text-align: center;
            margin-top: 30px;
            padding: 20px;
            color: #666;
            font-size: 0.8em;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .running { animation: pulse 2s infinite; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔬 MOSS Monitor</h1>
        <p>Multi-Objective Self-Driven System</p>
    </div>
    
    <div class="status">
        <div class="card">
            <h3>📊 Agent Status</h3>
            <div class="metric">
                <span>Agent ID:</span>
                <span class="metric-value" id="agent-id">{{ status.agent_id or 'N/A' }}</span>
            </div>
            <div class="metric">
                <span>Mode:</span>
                <span class="metric-value" id="mode">{{ status.mode or 'N/A' }}</span>
            </div>
            <div class="metric">
                <span>Status:</span>
                <span class="metric-value {% if status.running %}running{% endif %}">
                    {{ 'RUNNING' if status.running else 'STOPPED' }}
                </span>
            </div>
            <div class="metric">
                <span>Uptime:</span>
                <span class="metric-value" id="uptime">--</span>
            </div>
        </div>
        
        <div class="card">
            <h3>🎯 Current State</h3>
            <div style="text-align: center; margin: 20px 0;">
                <span class="state-indicator state-{{ status.current_state or 'normal' }}" id="state">
                    {{ status.current_state or 'UNKNOWN' }}
                </span>
            </div>
            <div class="weights">
                {% for name, value in (status.weights or {}).items() %}
                <div>
                    <div class="weight-bar">
                        <div class="weight-fill" style="width: {{ value * 100 }}%"></div>
                        <span class="weight-label">{{ name }}: {{ "%.0f"|format(value * 100) }}%</span>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        
        <div class="card">
            <h3>📈 Statistics</h3>
            <div class="metric">
                <span>Decisions:</span>
                <span class="metric-value" id="decisions">{{ status.stats.total_decisions }}</span>
            </div>
            <div class="metric">
                <span>Actions:</span>
                <span class="metric-value" id="actions">{{ status.stats.total_actions }}</span>
            </div>
            <div class="metric">
                <span>Violations:</span>
                <span class="metric-value" id="violations" style="color: {% if status.stats.safety_violations > 0 %}#ff0000{% else %}#00ff00{% endif %}">
                    {{ status.stats.safety_violations }}
                </span>
            </div>
        </div>
        
        <div class="card">
            <h3>💻 System Metrics</h3>
            {% for key, value in (status.metrics or {}).items() %}
            <div class="metric">
                <span>{{ key }}:</span>
                <span class="metric-value">{{ value }}</span>
            </div>
            {% endfor %}
        </div>
    </div>
    
    <div class="card">
        <h3>📝 Activity Log</h3>
        <div class="log-container" id="log-container">
            {% for entry in status.history[-20:] %}
            <div class="log-entry">
                <span class="log-time">[{{ entry.time }}]</span> {{ entry.message }}
            </div>
            {% endfor %}
        </div>
    </div>
    
    <div class="footer">
        <p>MOSS v0.2.0 | Real-time Monitoring Dashboard</p>
        <p>Auto-refresh every 5 seconds</p>
    </div>
    
    <script>
        // Auto-refresh every 5 seconds
        setInterval(() => {
            fetch('/api/status')
                .then(r => r.json())
                .then(data => {
                    location.reload();
                });
        }, 5000);
        
        // Update uptime
        function updateUptime() {
            const startTime = {{ status.start_time or 'null' }};
            if (startTime) {
                const elapsed = Math.floor(Date.now() / 1000 - startTime);
                const hours = Math.floor(elapsed / 3600);
                const mins = Math.floor((elapsed % 3600) / 60);
                const secs = elapsed % 60;
                document.getElementById('uptime').textContent = 
                    `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
            }
        }
        
        if ({{ 'true' if status.running else 'false' }}) {
            updateUptime();
            setInterval(updateUptime, 1000);
        }
    </script>
</body>
</html>
'''


@app.route('/')
def dashboard():
    """主监控面板"""
    return render_template_string(DASHBOARD_HTML, status=moss_status)


@app.route('/api/status')
def api_status():
    """API端点 - 返回当前状态"""
    return jsonify(moss_status)


@app.route('/api/start', methods=['POST'])
def api_start():
    """启动MOSS Agent"""
    global moss_status
    
    try:
        import sys
        sys.path.insert(0, '/workspace/projects/moss')
        from agents.moss_agent_v2 import MOSSAgentV2
        
        agent = MOSSAgentV2(agent_id="web_monitor", mode="demo")
        moss_status['agent_id'] = agent.agent_id
        moss_status['mode'] = agent.mode
        moss_status['running'] = True
        moss_status['start_time'] = time.time()
        
        # 在后台线程运行
        def run_agent():
            for i in range(1000):
                if not moss_status['running']:
                    break
                result = agent.step()
                moss_status['current_state'] = result.get('state', {}).state if hasattr(result.get('state'), 'state') else str(result.get('state'))
                moss_status['stats'] = agent.stats
                moss_status['history'].append({
                    'time': datetime.now().strftime('%H:%M:%S'),
                    'message': f"Step {i}: {result.get('action', 'N/A')}"
                })
                time.sleep(1)
        
        thread = threading.Thread(target=run_agent)
        thread.daemon = True
        thread.start()
        
        return jsonify({'status': 'started', 'agent_id': agent.agent_id})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/stop', methods=['POST'])
def api_stop():
    """停止MOSS Agent"""
    global moss_status
    moss_status['running'] = False
    return jsonify({'status': 'stopped'})


def update_mock_data():
    """生成模拟数据用于演示"""
    global moss_status
    
    moss_status = {
        'agent_id': 'moss_demo',
        'mode': 'demo',
        'running': True,
        'start_time': time.time() - 3600,  # 运行1小时
        'stats': {
            'total_decisions': 145,
            'total_actions': 142,
            'safety_violations': 0
        },
        'current_state': 'growth',
        'weights': {
            'survival': 0.20,
            'curiosity': 0.20,
            'influence': 0.40,
            'optimization': 0.20
        },
        'metrics': {
            'CPU': '15.3%',
            'Memory': '42.1%',
            'Disk': '38.5%'
        },
        'history': [
            {'time': '12:45:01', 'message': 'Step 145: improve_quality (simulated)'},
            {'time': '12:44:01', 'message': 'Step 144: explore_api (simulated)'},
            {'time': '12:43:01', 'message': 'Step 143: backup_self (simulated)'},
            {'time': '12:42:01', 'message': 'Step 142: improve_quality (simulated)'},
            {'time': '12:41:01', 'message': 'Step 141: learn_new_skill (simulated)'},
        ]
    }


if __name__ == '__main__':
    # 填充模拟数据
    update_mock_data()
    
    print("=" * 50)
    print("MOSS Web Monitor")
    print("=" * 50)
    print("")
    print("Dashboard: http://localhost:5000")
    print("API: http://localhost:5000/api/status")
    print("")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=False)

"""
MOSS Monitoring Dashboard - 监控仪表板

实时显示驱动权重、涌现事件和性能指标
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from flask import Flask, render_template_string, jsonify, request
import threading

app = Flask(__name__)

# 模拟数据存储（实际项目中应从 Agent 获取）
dashboard_data = {
    'drive_weights': {
        'exploration': 0.30,
        'task_focus': 0.70,
        'survival': 0.50,
        'curiosity': 0.60,
        'efficiency': 0.45,
    },
    'emergence_events': [
        {
            'time': '2026-04-18 15:30:00',
            'name': 'Pattern Recognition',
            'type': 'emergence',
            'description': 'New behavioral pattern detected'
        },
        {
            'time': '2026-04-18 15:25:00',
            'name': 'Drive Adaptation',
            'type': 'adaptation',
            'description': 'Exploration weight auto-adjusted'
        },
    ],
    'performance_metrics': {
        'total_steps': 15234,
        'avg_reward': 0.73,
        'success_rate': 0.82,
    },
    'last_update': None,
}

# HTML 模板
DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>MOSS Monitoring Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f0f23;
            color: #e0e0e0;
            padding: 20px;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border-radius: 10px;
        }
        .header h1 {
            color: #00d4ff;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .status {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
        }
        .status.online { background: #00d4ff; color: #000; }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: #1a1a2e;
            border-radius: 10px;
            padding: 20px;
            border-left: 4px solid #00d4ff;
        }
        .card h2 {
            color: #00d4ff;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #2a2a4a;
        }
        .metric:last-child { border-bottom: none; }
        .metric-value {
            color: #00d4ff;
            font-weight: bold;
        }
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #2a2a4a;
            border-radius: 10px;
            overflow: hidden;
            margin-top: 5px;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #00d4ff, #0099cc);
            transition: width 0.3s ease;
        }
        .event-list {
            max-height: 300px;
            overflow-y: auto;
        }
        .event-item {
            padding: 10px;
            margin-bottom: 10px;
            background: #252545;
            border-radius: 5px;
            border-left: 3px solid #00d4ff;
        }
        .event-time {
            color: #888;
            font-size: 0.85em;
        }
        .event-type {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            margin-left: 10px;
        }
        .event-type.emergence { background: #ff6b6b; }
        .event-type.adaptation { background: #4ecdc4; }
        .event-type.goal { background: #ffe66d; color: #000; }
        .refresh-info {
            text-align: center;
            color: #888;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🧠 MOSS Monitoring Dashboard</h1>
        <span class="status online">● Online</span>
        <p style="margin-top: 10px; color: #888;">v6.2 Production</p>
    </div>
    
    <div class="grid">
        <div class="card">
            <h2>📊 Performance Metrics</h2>
            <div class="metric">
                <span>Total Steps</span>
                <span class="metric-value" id="total-steps">0</span>
            </div>
            <div class="metric">
                <span>Average Reward</span>
                <span class="metric-value" id="avg-reward">0.00</span>
            </div>
            <div class="metric">
                <span>Success Rate</span>
                <span class="metric-value" id="success-rate">0%</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" id="success-bar" style="width: 0%"></div>
            </div>
        </div>
        
        <div class="card">
            <h2>⚖️ Drive Weights</h2>
            <div id="drive-weights"></div>
        </div>
        
        <div class="card">
            <h2>✨ Emergence Events</h2>
            <div class="event-list" id="events"></div>
        </div>
    </div>
    
    <div class="refresh-info">
        <p>Last updated: <span id="last-update">Never</span></p>
        <p>Auto-refresh every 5 seconds</p>
    </div>
    
    <script>
        async function fetchData() {
            try {
                const response = await fetch('/api/data');
                const data = await response.json();
                
                // Update metrics
                document.getElementById('total-steps').textContent = data.performance_metrics.total_steps.toLocaleString();
                document.getElementById('avg-reward').textContent = data.performance_metrics.avg_reward.toFixed(2);
                document.getElementById('success-rate').textContent = (data.performance_metrics.success_rate * 100).toFixed(1) + '%';
                document.getElementById('success-bar').style.width = (data.performance_metrics.success_rate * 100) + '%';
                
                // Update drive weights
                const driveContainer = document.getElementById('drive-weights');
                driveContainer.innerHTML = '';
                for (const [name, weight] of Object.entries(data.drive_weights)) {
                    driveContainer.innerHTML += `
                        <div class="metric">
                            <span>${name.charAt(0).toUpperCase() + name.slice(1)}</span>
                            <span class="metric-value">${weight.toFixed(2)}</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${weight * 100}%"></div>
                        </div>
                    `;
                }
                
                // Update events
                const eventsContainer = document.getElementById('events');
                eventsContainer.innerHTML = '';
                data.emergence_events.slice(-10).reverse().forEach(event => {
                    eventsContainer.innerHTML += `
                        <div class="event-item">
                            <div class="event-time">${event.time}</div>
                            <div>
                                <strong>${event.name}</strong>
                                <span class="event-type ${event.type}">${event.type}</span>
                            </div>
                            <div style="color: #aaa; margin-top: 5px;">${event.description}</div>
                        </div>
                    `;
                });
                
                document.getElementById('last-update').textContent = data.last_update || 'Just now';
            } catch (error) {
                console.error('Failed to fetch data:', error);
            }
        }
        
        // Initial fetch and auto-refresh
        fetchData();
        setInterval(fetchData, 5000);
    </script>
</body>
</html>
'''


def update_data(data: Dict[str, Any]):
    """更新仪表板数据"""
    global dashboard_data
    dashboard_data.update(data)
    dashboard_data['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')


@app.route('/')
def index():
    """主页面"""
    return render_template_string(DASHBOARD_TEMPLATE)


@app.route('/api/data')
def get_data():
    """API: 获取当前数据"""
    return jsonify(dashboard_data)


@app.route('/api/update', methods=['POST'])
def update():
    """API: 更新数据"""
    data = request.json
    update_data(data)
    return jsonify({'status': 'updated'})


@app.route('/api/event', methods=['POST'])
def add_event():
    """API: 添加涌现事件"""
    event = request.json
    event['time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    dashboard_data['emergence_events'].append(event)
    # 只保留最近 50 个事件
    dashboard_data['emergence_events'] = dashboard_data['emergence_events'][-50:]
    return jsonify({'status': 'event_added'})


class DashboardServer:
    """仪表板服务器"""
    
    def __init__(self, host='0.0.0.0', port=8080):
        self.host = host
        self.port = port
        self.thread = None
    
    def start(self, debug=False):
        """启动仪表板服务器（非阻塞）"""
        self.thread = threading.Thread(
            target=lambda: app.run(
                host=self.host,
                port=self.port,
                debug=debug,
                use_reloader=False
            )
        )
        self.thread.daemon = True
        self.thread.start()
        print(f"Dashboard started at http://{self.host}:{self.port}")
    
    def update_metrics(self, metrics: Dict[str, Any]):
        """更新性能指标"""
        update_data({'performance_metrics': metrics})
    
    def update_drive_weights(self, weights: Dict[str, float]):
        """更新驱动权重"""
        update_data({'drive_weights': weights})
    
    def add_emergence_event(self, name: str, event_type: str, description: str):
        """添加涌现事件"""
        event = {
            'name': name,
            'type': event_type,
            'description': description,
        }
        event['time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        dashboard_data['emergence_events'].append(event)
        dashboard_data['emergence_events'] = dashboard_data['emergence_events'][-50:]
        dashboard_data['last_update'] = event['time']


if __name__ == '__main__':
    # 直接运行仪表板
    print("Starting MOSS Monitoring Dashboard...")
    print("Open http://localhost:8080 to view")
    app.run(host='0.0.0.0', port=8080, debug=True)

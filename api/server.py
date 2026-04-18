"""
MOSS API Server - 生产部署

提供 REST API 接口
"""

from flask import Flask, request, jsonify
from agi.agent import Agent
from agi.drive_manager import DriveManager

app = Flask(__name__)

# 全局 Agent 实例
agent = None

@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({'status': 'ok'})

@app.route('/initialize', methods=['POST'])
def initialize():
    """初始化 Agent"""
    global agent
    config = request.json
    agent = Agent(config)
    return jsonify({'status': 'initialized'})

@app.route('/step', methods=['POST'])
def step():
    """执行一步"""
    if agent is None:
        return jsonify({'error': 'Agent not initialized'}), 400
    
    observation = request.json.get('observation')
    action = agent.step(observation)
    
    return jsonify({
        'action': action,
        'drive_states': agent.get_drive_states(),
    })

@app.route('/drives', methods=['GET'])
def get_drives():
    """获取驱动状态"""
    if agent is None:
        return jsonify({'error': 'Agent not initialized'}), 400
    
    return jsonify(agent.get_drive_states())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)

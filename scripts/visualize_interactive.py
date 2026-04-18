"""
MOSS v6.1 Interactive Visualization Tool
交互式可视化工具

功能特性:
1. 实时权重监控 (动态更新)
2. 涌现检测动画
3. 交互式 PCA 可视化 (鼠标悬停显示详情)
4. 3D 聚类可视化
5. 时间轴回放功能

技术栈:
- Plotly (交互式图表)
- Dash (Web 界面)

使用:
    python scripts/visualize_interactive.py --experiment-dir logs/experiment_v6_full_*
    python scripts/visualize_interactive.py --port 8050
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import json
import numpy as np
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import deque

# 尝试导入可视化库
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    import plotly.offline as pyo
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    print("警告: plotly 未安装，将使用静态可视化模式")
    print("安装: pip install plotly dash")

try:
    from dash import Dash, html, dcc, Input, Output, State
    from dash.exceptions import PreventUpdate
    DASH_AVAILABLE = True
except ImportError:
    DASH_AVAILABLE = False

try:
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("警告: scikit-learn 未安装，PCA和聚类功能受限")

from agi.analysis.latent_export import LatentExporter
from agi.analysis.behavior_mapping import BehaviorMapper


class InteractiveVisualizer:
    """交互式可视化器"""
    
    def __init__(self, experiment_dir: Path):
        self.experiment_dir = Path(experiment_dir)
        self.exporter = LatentExporter()
        self.checkpoints = []
        self.drive_names = []
        self.weights_matrix = None
        self.cycles = []
        self.current_frame = 0
        self.animation_speed = 100  # ms per frame
        
        self._load_data()
    
    def _load_data(self):
        """加载实验数据"""
        n_loaded = self.exporter.load_checkpoints(self.experiment_dir)
        if n_loaded == 0:
            raise ValueError(f"未找到检查点: {self.experiment_dir}")
        
        self.checkpoints = self.exporter.checkpoints
        self.drive_names = self.exporter.drive_names
        self.weights_matrix = self.exporter.weights_matrix
        self.cycles = [cp.get('cycle', i * 1000) for i, cp in enumerate(self.checkpoints)]
        
        print(f"已加载 {n_loaded} 个检查点，{len(self.drive_names)} 个驱动")
    
    def create_weight_timeline(self) -> Optional[go.Figure]:
        """创建权重时序图"""
        if not PLOTLY_AVAILABLE:
            return None
        
        fig = go.Figure()
        
        colors = px.colors.qualitative.Set1 if hasattr(px, 'colors') else [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ]
        
        for i, drive_name in enumerate(self.drive_names):
            weights = self.weights_matrix[:, i]
            color = colors[i % len(colors)]
            
            fig.add_trace(go.Scatter(
                x=self.cycles,
                y=weights,
                mode='lines+markers',
                name=drive_name,
                line=dict(width=2, color=color),
                marker=dict(size=6),
                hovertemplate=f'<b>{drive_name}</b><br>' +
                             'Cycle: %{x}<br>' +
                             'Weight: %{y:.4f}<br>' +
                             '<extra></extra>'
            ))
        
        fig.update_layout(
            title=dict(
                text='Drive Weight Evolution Over Time',
                font=dict(size=20)
            ),
            xaxis_title='Cycle',
            yaxis_title='Weight',
            hovermode='x unified',
            template='plotly_white',
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1
            ),
            height=500
        )
        
        return fig
    
    def create_emergence_animation(self) -> Optional[go.Figure]:
        """创建涌现检测动画"""
        if not PLOTLY_AVAILABLE:
            return None
        
        # 检测涌现事件
        emergence_events = []
        for i, cp in enumerate(self.checkpoints):
            emerged = cp.get('emerged_drives', [])
            if emerged:
                for drive_name in emerged:
                    if drive_name not in ['survival', 'curiosity', 'influence', 'optimization']:
                        emergence_events.append({
                            'cycle': self.cycles[i],
                            'drive': drive_name,
                            'index': i
                        })
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Weight Evolution', 'Emergence Events'),
            row_heights=[0.7, 0.3],
            vertical_spacing=0.12
        )
        
        # 权重曲线
        colors = px.colors.qualitative.Set1 if hasattr(px, 'colors') else [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'
        ]
        
        for i, drive_name in enumerate(self.drive_names):
            weights = self.weights_matrix[:, i]
            color = colors[i % len(colors)]
            
            fig.add_trace(go.Scatter(
                x=self.cycles,
                y=weights,
                mode='lines',
                name=drive_name,
                line=dict(width=2, color=color),
                hovertemplate=f'<b>{drive_name}</b><br>Cycle: %{{x}}<br>Weight: %{{y:.4f}}<extra></extra>'
            ), row=1, col=1)
        
        # 涌现事件标记
        if emergence_events:
            event_cycles = [e['cycle'] for e in emergence_events]
            event_names = [e['drive'] for e in emergence_events]
            
            fig.add_trace(go.Scatter(
                x=event_cycles,
                y=[0.5] * len(emergence_events),
                mode='markers+text',
                marker=dict(size=15, color='red', symbol='star'),
                text=event_names,
                textposition='top center',
                name='Emergence Events',
                hovertemplate='<b>Emergence</b><br>Cycle: %{x}<br>Drive: %{text}<extra></extra>'
            ), row=2, col=1)
        
        fig.update_layout(
            title=dict(text='Emergence Detection Animation', font=dict(size=20)),
            showlegend=True,
            height=700,
            template='plotly_white'
        )
        
        return fig
    
    def create_pca_visualization(self) -> Optional[go.Figure]:
        """创建交互式 PCA 可视化"""
        if not PLOTLY_AVAILABLE or not SKLEARN_AVAILABLE:
            return None
        
        # 标准化数据
        scaler = StandardScaler()
        weights_scaled = scaler.fit_transform(self.weights_matrix)
        
        # PCA 降维
        pca = PCA(n_components=2)
        pca_result = pca.fit_transform(weights_scaled)
        
        # 创建 DataFrame 用于悬停信息
        hover_texts = []
        for i, cp in enumerate(self.checkpoints):
            cycle = self.cycles[i]
            weights_info = '<br>'.join([
                f"{name}: {self.weights_matrix[i, j]:.4f}"
                for j, name in enumerate(self.drive_names)
            ])
            hover_texts.append(f"<b>Cycle {cycle}</b><br>{weights_info}")
        
        fig = go.Figure()
        
        # 主成分散点图
        fig.add_trace(go.Scatter(
            x=pca_result[:, 0],
            y=pca_result[:, 1],
            mode='markers+lines',
            marker=dict(
                size=10,
                color=self.cycles,
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title='Cycle')
            ),
            line=dict(color='rgba(100, 100, 100, 0.3)', width=1),
            text=hover_texts,
            hovertemplate='%{text}<extra></extra>',
            name='State Trajectory'
        ))
        
        # 添加起点和终点标记
        fig.add_trace(go.Scatter(
            x=[pca_result[0, 0]],
            y=[pca_result[0, 1]],
            mode='markers',
            marker=dict(size=20, color='green', symbol='star'),
            name='Start',
            hovertemplate='<b>Start</b><br>Cycle: %{customdata}<extra></extra>',
            customdata=[self.cycles[0]]
        ))
        
        fig.add_trace(go.Scatter(
            x=[pca_result[-1, 0]],
            y=[pca_result[-1, 1]],
            mode='markers',
            marker=dict(size=20, color='red', symbol='x'),
            name='End',
            hovertemplate='<b>End</b><br>Cycle: %{customdata}<extra></extra>',
            customdata=[self.cycles[-1]]
        ))
        
        explained_var = pca.explained_variance_ratio_
        
        fig.update_layout(
            title=dict(
                text=f'PCA Visualization of Drive State Space<br>' +
                     f'Explained Variance: PC1={explained_var[0]:.2%}, PC2={explained_var[1]:.2%}',
                font=dict(size=16)
            ),
            xaxis_title=f'PC1 ({explained_var[0]:.1%} variance)',
            yaxis_title=f'PC2 ({explained_var[1]:.1%} variance)',
            template='plotly_white',
            height=600,
            hovermode='closest'
        )
        
        return fig
    
    def create_3d_clustering(self) -> Optional[go.Figure]:
        """创建 3D 聚类可视化"""
        if not PLOTLY_AVAILABLE or not SKLEARN_AVAILABLE:
            return None
        
        # 标准化
        scaler = StandardScaler()
        weights_scaled = scaler.fit_transform(self.weights_matrix)
        
        # PCA 到 3D
        pca = PCA(n_components=3)
        pca_3d = pca.fit_transform(weights_scaled)
        
        # K-Means 聚类
        n_clusters = min(4, len(self.checkpoints) // 5 + 1)
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(weights_scaled)
        
        fig = go.Figure()
        
        colors = px.colors.qualitative.Set1 if hasattr(px, 'colors') else [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'
        ]
        
        # 为每个聚类添加轨迹
        for cluster_id in range(n_clusters):
            mask = clusters == cluster_id
            cluster_points = pca_3d[mask]
            cluster_cycles = [self.cycles[i] for i in range(len(self.cycles)) if mask[i]]
            
            hover_texts = []
            for i in range(len(self.cycles)):
                if mask[i]:
                    weights_info = '<br>'.join([
                        f"{name}: {self.weights_matrix[i, j]:.4f}"
                        for j, name in enumerate(self.drive_names)
                    ])
                    hover_texts.append(f"<b>Cycle {self.cycles[i]}</b><br>Cluster {cluster_id}<br>{weights_info}")
            
            fig.add_trace(go.Scatter3d(
                x=cluster_points[:, 0],
                y=cluster_points[:, 1],
                z=cluster_points[:, 2],
                mode='markers',
                marker=dict(
                    size=6,
                    color=colors[cluster_id % len(colors)],
                    opacity=0.8
                ),
                text=[hover_texts[i] for i, m in enumerate(mask) if m],
                hovertemplate='%{text}<extra></extra>',
                name=f'Cluster {cluster_id}'
            ))
        
        explained_var = pca.explained_variance_ratio_
        
        fig.update_layout(
            title=dict(
                text=f'3D Clustering Visualization<br>' +
                     f'Total Variance Explained: {sum(explained_var):.1%}',
                font=dict(size=16)
            ),
            scene=dict(
                xaxis_title=f'PC1 ({explained_var[0]:.1%})',
                yaxis_title=f'PC2 ({explained_var[1]:.1%})',
                zaxis_title=f'PC3 ({explained_var[2]:.1%})',
                aspectmode='cube'
            ),
            template='plotly_white',
            height=700
        )
        
        return fig
    
    def create_timeline_replay(self) -> Optional[go.Figure]:
        """创建时间轴回放可视化"""
        if not PLOTLY_AVAILABLE:
            return None
        
        # 创建动画帧
        frames = []
        for i in range(1, len(self.cycles) + 1):
            frame_data = []
            for j, drive_name in enumerate(self.drive_names):
                frame_data.append(go.Scatter(
                    x=self.cycles[:i],
                    y=self.weights_matrix[:i, j],
                    mode='lines+markers',
                    name=drive_name,
                    line=dict(width=2),
                    marker=dict(size=6)
                ))
            
            # 添加当前状态标记
            current_weights = self.weights_matrix[i-1]
            frame_data.append(go.Bar(
                x=self.drive_names,
                y=current_weights,
                name='Current State',
                marker_color='rgba(100, 100, 100, 0.3)',
                yaxis='y2'
            ))
            
            frames.append(go.Frame(
                data=frame_data,
                name=str(self.cycles[i-1]),
                layout=dict(
                    title=f'Cycle {self.cycles[i-1]} / {self.cycles[-1]}'
                )
            ))
        
        # 初始状态
        initial_data = []
        for j, drive_name in enumerate(self.drive_names):
            initial_data.append(go.Scatter(
                x=self.cycles[:1],
                y=self.weights_matrix[:1, j],
                mode='lines+markers',
                name=drive_name,
                line=dict(width=2)
            ))
        
        initial_data.append(go.Bar(
            x=self.drive_names,
            y=self.weights_matrix[0],
            name='Current State',
            marker_color='rgba(100, 100, 100, 0.3)',
            yaxis='y2'
        ))
        
        fig = go.Figure(
            data=initial_data,
            frames=frames
        )
        
        # 添加播放按钮
        fig.update_layout(
            updatemenus=[{
                'type': 'buttons',
                'showactive': False,
                'buttons': [
                    {
                        'label': '▶ Play',
                        'method': 'animate',
                        'args': [None, {
                            'frame': {'duration': 500, 'redraw': True},
                            'fromcurrent': True,
                            'transition': {'duration': 300}
                        }]
                    },
                    {
                        'label': '⏸ Pause',
                        'method': 'animate',
                        'args': [[None], {
                            'frame': {'duration': 0, 'redraw': False},
                            'mode': 'immediate',
                            'transition': {'duration': 0}
                        }]
                    }
                ],
                'x': 0.1,
                'y': 0
            }],
            sliders=[{
                'steps': [
                    {
                        'args': [[str(cycle)], {
                            'frame': {'duration': 300, 'redraw': True},
                            'mode': 'immediate',
                            'transition': {'duration': 300}
                        }],
                        'label': str(cycle),
                        'method': 'animate'
                    }
                    for cycle in self.cycles
                ],
                'transition': {'duration': 300},
                'x': 0.1,
                'y': -0.1,
                'len': 0.8
            }],
            yaxis2=dict(
                overlaying='y',
                side='right',
                range=[0, max(self.weights_matrix.max(), 0.7)],
                showgrid=False
            ),
            title=dict(text='Timeline Replay', font=dict(size=20)),
            xaxis_title='Cycle',
            yaxis_title='Weight',
            height=600,
            template='plotly_white'
        )
        
        return fig
    
    def create_dashboard(self) -> Optional[Dash]:
        """创建 Dash 仪表板"""
        if not DASH_AVAILABLE or not PLOTLY_AVAILABLE:
            print("Dash 或 Plotly 未安装，无法创建交互式仪表板")
            print("安装: pip install dash plotly")
            return None
        
        app = Dash(__name__)
        
        app.layout = html.Div([
            html.H1('MOSS v6.1 Interactive Visualization Dashboard',
                    style={'textAlign': 'center', 'marginBottom': 30}),
            
            html.Div([
                html.Div([
                    html.H3('Experiment Info'),
                    html.P(f'Checkpoints: {len(self.checkpoints)}'),
                    html.P(f'Drives: {len(self.drive_names)}'),
                    html.P(f'Cycles: {self.cycles[0]} - {self.cycles[-1]}'),
                ], style={'width': '20%', 'display': 'inline-block', 'verticalAlign': 'top'}),
                
                html.Div([
                    html.H3('Drive List'),
                    html.Ul([html.Li(name) for name in self.drive_names])
                ], style={'width': '20%', 'display': 'inline-block', 'verticalAlign': 'top'}),
                
                html.Div([
                    html.H3('Controls'),
                    dcc.Dropdown(
                        id='visualization-type',
                        options=[
                            {'label': 'Weight Timeline', 'value': 'timeline'},
                            {'label': 'Emergence Animation', 'value': 'emergence'},
                            {'label': 'PCA Visualization', 'value': 'pca'},
                            {'label': '3D Clustering', 'value': 'cluster3d'},
                            {'label': 'Timeline Replay', 'value': 'replay'}
                        ],
                        value='timeline'
                    ),
                    html.Br(),
                    html.Button('Export HTML', id='export-btn', n_clicks=0),
                    html.Div(id='export-status')
                ], style={'width': '40%', 'display': 'inline-block', 'verticalAlign': 'top'})
            ], style={'marginBottom': 30}),
            
            html.Div(id='visualization-container')
        ])
        
        @app.callback(
            Output('visualization-container', 'children'),
            Input('visualization-type', 'value')
        )
        def update_visualization(viz_type):
            if viz_type == 'timeline':
                fig = self.create_weight_timeline()
            elif viz_type == 'emergence':
                fig = self.create_emergence_animation()
            elif viz_type == 'pca':
                fig = self.create_pca_visualization()
            elif viz_type == 'cluster3d':
                fig = self.create_3d_clustering()
            elif viz_type == 'replay':
                fig = self.create_timeline_replay()
            else:
                return html.Div('Unknown visualization type')
            
            if fig is None:
                return html.Div('Visualization not available (missing dependencies)')
            
            return dcc.Graph(figure=fig, style={'height': '700px'})
        
        @app.callback(
            Output('export-status', 'children'),
            Input('export-btn', 'n_clicks'),
            State('visualization-type', 'value')
        )
        def export_visualization(n_clicks, viz_type):
            if n_clicks == 0:
                raise PreventUpdate
            
            if viz_type == 'timeline':
                fig = self.create_weight_timeline()
            elif viz_type == 'emergence':
                fig = self.create_emergence_animation()
            elif viz_type == 'pca':
                fig = self.create_pca_visualization()
            elif viz_type == 'cluster3d':
                fig = self.create_3d_clustering()
            elif viz_type == 'replay':
                fig = self.create_timeline_replay()
            else:
                return 'Unknown visualization type'
            
            if fig is None:
                return 'Export failed (missing dependencies)'
            
            output_path = self.experiment_dir / f'visualization_{viz_type}.html'
            fig.write_html(str(output_path))
            return f'Exported to: {output_path}'
        
        return app
    
    def export_all(self, output_dir: Path):
        """导出所有可视化为 HTML"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if not PLOTLY_AVAILABLE:
            print("Plotly 未安装，无法导出 HTML")
            return
        
        visualizations = [
            ('timeline', self.create_weight_timeline()),
            ('emergence', self.create_emergence_animation()),
            ('pca', self.create_pca_visualization()),
            ('cluster3d', self.create_3d_clustering()),
            ('replay', self.create_timeline_replay())
        ]
        
        for name, fig in visualizations:
            if fig is not None:
                output_path = output_dir / f'{name}.html'
                fig.write_html(str(output_path))
                print(f"✓ Exported: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='MOSS v6.1 Interactive Visualization Tool'
    )
    parser.add_argument('--experiment-dir', '-e', type=str, required=True,
                        help='实验目录路径 (例如: logs/experiment_v6_full_*)')
    parser.add_argument('--output', '-o', type=str, default='logs/visualization',
                        help='输出目录')
    parser.add_argument('--port', '-p', type=int, default=8050,
                        help='Dash 服务器端口 (默认: 8050)')
    parser.add_argument('--export-only', action='store_true',
                        help='仅导出 HTML 文件，不启动服务器')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                        help='服务器主机 (默认: 0.0.0.0)')
    
    args = parser.parse_args()
    
    experiment_dir = Path(args.experiment_dir)
    if not experiment_dir.exists():
        print(f"错误: 实验目录不存在: {experiment_dir}")
        return 1
    
    print(f"MOSS v6.1 Interactive Visualization Tool")
    print(f"=" * 50)
    print(f"Experiment: {experiment_dir}")
    print(f"Output: {args.output}")
    
    # 创建可视化器
    try:
        viz = InteractiveVisualizer(experiment_dir)
    except ValueError as e:
        print(f"错误: {e}")
        return 1
    
    # 仅导出模式
    if args.export_only:
        print("\n导出所有可视化...")
        viz.export_all(args.output)
        print(f"\n所有可视化已导出到: {args.output}")
        return 0
    
    # 启动 Dash 服务器
    if DASH_AVAILABLE:
        print(f"\n启动 Dash 服务器...")
        print(f"访问: http://{args.host}:{args.port}")
        print(f"按 Ctrl+C 停止服务器\n")
        
        app = viz.create_dashboard()
        if app:
            app.run_server(host=args.host, port=args.port, debug=False)
        else:
            print("无法创建 Dash 应用，尝试导出静态 HTML...")
            viz.export_all(args.output)
    else:
        print("\nDash 未安装，导出静态 HTML...")
        viz.export_all(args.output)
        print(f"\n可视化已导出到: {args.output}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

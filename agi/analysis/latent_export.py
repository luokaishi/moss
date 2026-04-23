"""
Latent Cluster Export Module - 潜在聚类导出模块

从实验检查点提取驱动权重和状态向量，实现聚类分析，
并导出聚类结果到 JSON/CSV 格式。

功能:
1. 从检查点文件提取驱动权重和状态向量
2. 实现 k-means 聚类分析
3. 实现 PCA 降维
4. 导出聚类结果到 JSON/CSV
"""

import json
import csv
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import warnings


@dataclass
class ClusterResult:
    """聚类结果数据结构"""
    cluster_id: int
    centroid: List[float]
    samples: List[int]  # 样本索引
    drive_weights: Dict[str, List[float]]  # 每个驱动的权重列表
    avg_weights: Dict[str, float]  # 平均权重
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'cluster_id': self.cluster_id,
            'centroid': [round(x, 6) for x in self.centroid],
            'n_samples': len(self.samples),
            'samples': self.samples,
            'avg_weights': {k: round(v, 6) for k, v in self.avg_weights.items()}
        }


@dataclass
class PCAResult:
    """PCA 降维结果"""
    explained_variance_ratio: List[float]
    components: List[List[float]]
    transformed: List[List[float]]
    n_components: int
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'n_components': self.n_components,
            'explained_variance_ratio': [round(x, 6) for x in self.explained_variance_ratio],
            'cumulative_variance': round(sum(self.explained_variance_ratio), 6),
            'components': [[round(x, 6) for x in comp] for comp in self.components],
            'transformed_shape': [len(self.transformed), len(self.transformed[0]) if self.transformed else 0]
        }


class LatentExporter:
    """
    潜在向量导出器
    
    从实验检查点提取驱动权重和状态向量，支持聚类分析和降维。
    
    Attributes:
        checkpoints: 加载的检查点数据列表
        drive_names: 驱动名称列表
        weights_matrix: 权重矩阵 (n_samples x n_drives)
    """
    
    def __init__(self):
        self.checkpoints: List[Dict] = []
        self.drive_names: List[str] = []
        self.weights_matrix: Optional[np.ndarray] = None
        self.scaler = StandardScaler()
        
    def load_checkpoints(self, checkpoint_dir: str, pattern: str = "checkpoint_*.json") -> int:
        """
        从目录加载检查点文件
        
        Args:
            checkpoint_dir: 检查点目录路径
            pattern: 文件匹配模式
            
        Returns:
            加载的检查点数量
        """
        checkpoint_path = Path(checkpoint_dir)
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"检查点目录不存在: {checkpoint_dir}")
        
        checkpoint_files = sorted(checkpoint_path.glob(pattern))
        
        self.checkpoints = []
        for file in checkpoint_files:
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    self.checkpoints.append(data)
            except Exception as e:
                warnings.warn(f"无法加载检查点 {file}: {e}")
        
        # 提取驱动名称
        if self.checkpoints:
            first_drives = self.checkpoints[0].get('drives', {})
            self.drive_names = sorted(first_drives.keys())
            
            # 构建权重矩阵
            self._build_weights_matrix()
        
        return len(self.checkpoints)
    
    def load_checkpoint_list(self, checkpoint_files: List[str]) -> int:
        """
        从文件列表加载检查点
        
        Args:
            checkpoint_files: 检查点文件路径列表
            
        Returns:
            加载的检查点数量
        """
        self.checkpoints = []
        for file_path in checkpoint_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    self.checkpoints.append(data)
            except Exception as e:
                warnings.warn(f"无法加载检查点 {file_path}: {e}")
        
        if self.checkpoints:
            first_drives = self.checkpoints[0].get('drives', {})
            self.drive_names = sorted(first_drives.keys())
            self._build_weights_matrix()
        
        return len(self.checkpoints)
    
    def _build_weights_matrix(self):
        """构建权重矩阵"""
        if not self.checkpoints or not self.drive_names:
            return
        
        n_samples = len(self.checkpoints)
        n_drives = len(self.drive_names)
        
        self.weights_matrix = np.zeros((n_samples, n_drives))
        
        for i, checkpoint in enumerate(self.checkpoints):
            drives = checkpoint.get('drives', {})
            for j, drive_name in enumerate(self.drive_names):
                drive_data = drives.get(drive_name, {})
                self.weights_matrix[i, j] = drive_data.get('weight', 0.0)
    
    def get_drive_weights(self, drive_name: str) -> List[float]:
        """
        获取指定驱动的权重历史
        
        Args:
            drive_name: 驱动名称
            
        Returns:
            权重值列表
        """
        if not self.checkpoints:
            return []
        
        weights = []
        for checkpoint in self.checkpoints:
            drives = checkpoint.get('drives', {})
            drive_data = drives.get(drive_name, {})
            weights.append(drive_data.get('weight', 0.0))
        
        return weights
    
    def get_drive_stats(self, drive_name: str) -> Dict[str, float]:
        """
        获取指定驱动的统计信息
        
        Args:
            drive_name: 驱动名称
            
        Returns:
            统计信息字典
        """
        weights = self.get_drive_weights(drive_name)
        if not weights:
            return {}
        
        weights_arr = np.array(weights)
        return {
            'mean': float(np.mean(weights_arr)),
            'std': float(np.std(weights_arr)),
            'min': float(np.min(weights_arr)),
            'max': float(np.max(weights_arr)),
            'median': float(np.median(weights_arr)),
            'range': float(np.max(weights_arr) - np.min(weights_arr))
        }
    
    def cluster_kmeans(self, n_clusters: int = 3, 
                       standardize: bool = True,
                       random_state: int = 42) -> Tuple[List[ClusterResult], Dict]:
        """
        执行 k-means 聚类分析
        
        Args:
            n_clusters: 聚类数量
            standardize: 是否标准化数据
            random_state: 随机种子
            
        Returns:
            (聚类结果列表, 聚类信息字典)
        """
        if self.weights_matrix is None or len(self.weights_matrix) < n_clusters:
            raise ValueError(f"样本数量不足: {len(self.weights_matrix) if self.weights_matrix is not None else 0} < {n_clusters}")
        
        # 标准化
        data = self.weights_matrix.copy()
        if standardize:
            data = self.scaler.fit_transform(data)
        
        # 执行 k-means
        kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
        labels = kmeans.fit_predict(data)
        
        # 构建聚类结果
        clusters = []
        for cluster_id in range(n_clusters):
            cluster_indices = np.where(labels == cluster_id)[0].tolist()
            cluster_data = data[labels == cluster_id]
            
            # 计算该聚类的平均权重
            avg_weights = {}
            for drive_name in self.drive_names:
                weights = [self.checkpoints[i]['drives'].get(drive_name, {}).get('weight', 0.0) 
                          for i in cluster_indices]
                avg_weights[drive_name] = float(np.mean(weights)) if weights else 0.0
            
            # 收集驱动权重
            drive_weights_dict = {}
            for drive_name in self.drive_names:
                weights = [self.checkpoints[i]['drives'].get(drive_name, {}).get('weight', 0.0) 
                          for i in cluster_indices]
                drive_weights_dict[drive_name] = weights
            
            cluster_result = ClusterResult(
                cluster_id=cluster_id,
                centroid=kmeans.cluster_centers_[cluster_id].tolist(),
                samples=cluster_indices,
                drive_weights=drive_weights_dict,
                avg_weights=avg_weights
            )
            clusters.append(cluster_result)
        
        # 聚类信息
        info = {
            'n_clusters': n_clusters,
            'n_samples': len(self.checkpoints),
            'n_drives': len(self.drive_names),
            'inertia': float(kmeans.inertia_),
            'cluster_distribution': [int(np.sum(labels == i)) for i in range(n_clusters)],
            'standardized': standardize
        }
        
        return clusters, info
    
    def reduce_pca(self, n_components: int = 2, 
                   standardize: bool = True) -> PCAResult:
        """
        执行 PCA 降维
        
        Args:
            n_components: 降维后的维度
            standardize: 是否标准化数据
            
        Returns:
            PCAResult 对象
        """
        if self.weights_matrix is None:
            raise ValueError("没有加载检查点数据")
        
        n_features = self.weights_matrix.shape[1]
        n_components = min(n_components, n_features)
        
        # 标准化
        data = self.weights_matrix.copy()
        if standardize:
            data = self.scaler.fit_transform(data)
        
        # 执行 PCA
        pca = PCA(n_components=n_components)
        transformed = pca.fit_transform(data)
        
        return PCAResult(
            explained_variance_ratio=pca.explained_variance_ratio_.tolist(),
            components=pca.components_.tolist(),
            transformed=transformed.tolist(),
            n_components=n_components
        )
    
    def export_to_json(self, output_path: str, 
                       clusters: Optional[List[ClusterResult]] = None,
                       pca_result: Optional[PCAResult] = None,
                       metadata: Optional[Dict] = None) -> str:
        """
        导出聚类结果到 JSON
        
        Args:
            output_path: 输出文件路径
            clusters: 聚类结果列表
            pca_result: PCA 结果
            metadata: 额外元数据
            
        Returns:
            输出文件路径
        """
        output = {
            'export_time': datetime.now().isoformat(),
            'n_checkpoints': len(self.checkpoints),
            'drive_names': self.drive_names,
            'drive_stats': {name: self.get_drive_stats(name) for name in self.drive_names}
        }
        
        if metadata:
            output['metadata'] = metadata
        
        if clusters:
            output['clusters'] = [c.to_dict() for c in clusters]
        
        if pca_result:
            output['pca'] = pca_result.to_dict()
        
        # 添加原始权重数据
        output['weights_history'] = {
            name: self.get_drive_weights(name) for name in self.drive_names
        }
        
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        return output_path
    
    def export_to_csv(self, output_path: str, 
                      include_clusters: Optional[List[int]] = None) -> str:
        """
        导出权重历史到 CSV
        
        Args:
            output_path: 输出文件路径
            include_clusters: 只导出指定聚类的样本 (None 表示全部)
            
        Returns:
            输出文件路径
        """
        if not self.checkpoints:
            raise ValueError("没有加载检查点数据")
        
        # 确定要导出的样本
        if include_clusters is not None:
            # 需要先执行聚类
            raise NotImplementedError("请先执行聚类并手动筛选样本")
        
        # 准备 CSV 数据
        fieldnames = ['cycle', 'timestamp'] + self.drive_names + ['is_emergent_present']
        
        rows = []
        for i, checkpoint in enumerate(self.checkpoints):
            row = {
                'cycle': checkpoint.get('cycle', i),
                'timestamp': checkpoint.get('timestamp', '')
            }
            
            drives = checkpoint.get('drives', {})
            has_emergent = False
            
            for drive_name in self.drive_names:
                drive_data = drives.get(drive_name, {})
                row[drive_name] = drive_data.get('weight', 0.0)
                if drive_data.get('is_emergent', False):
                    has_emergent = True
            
            row['is_emergent_present'] = has_emergent
            rows.append(row)
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        return output_path
    
    def get_weight_trajectory(self, drive_name: str) -> List[Tuple[int, float]]:
        """
        获取指定驱动的权重轨迹
        
        Args:
            drive_name: 驱动名称
            
        Returns:
            (周期, 权重) 元组列表
        """
        trajectory = []
        for checkpoint in self.checkpoints:
            cycle = checkpoint.get('cycle', 0)
            drives = checkpoint.get('drives', {})
            weight = drives.get(drive_name, {}).get('weight', 0.0)
            trajectory.append((cycle, weight))
        
        return trajectory
    
    def detect_emergence_transitions(self) -> List[Dict]:
        """
        检测涌现驱动出现的时间点
        
        Returns:
            涌现事件列表
        """
        transitions = []
        prev_emergent = set()
        
        for checkpoint in self.checkpoints:
            cycle = checkpoint.get('cycle', 0)
            drives = checkpoint.get('drives', {})
            
            current_emergent = set()
            for drive_name, drive_data in drives.items():
                if drive_data.get('is_emergent', False):
                    current_emergent.add(drive_name)
            
            # 检测新出现的涌现驱动
            new_emergent = current_emergent - prev_emergent
            for drive_name in new_emergent:
                transitions.append({
                    'cycle': cycle,
                    'drive_name': drive_name,
                    'weight': drives.get(drive_name, {}).get('weight', 0.0),
                    'type': 'emergence_start'
                })
            
            prev_emergent = current_emergent
        
        return transitions


def analyze_experiment_checkpoints(checkpoint_dir: str,
                                   n_clusters: int = 3,
                                   n_pca_components: int = 2,
                                   output_dir: Optional[str] = None) -> Dict:
    """
    分析实验检查点的完整流程
    
    Args:
        checkpoint_dir: 检查点目录
        n_clusters: 聚类数量
        n_pca_components: PCA 组件数
        output_dir: 输出目录 (None 表示不导出)
        
    Returns:
        分析结果字典
    """
    exporter = LatentExporter()
    
    # 加载检查点
    n_loaded = exporter.load_checkpoints(checkpoint_dir)
    print(f"加载了 {n_loaded} 个检查点")
    
    if n_loaded == 0:
        return {'error': '没有加载到检查点'}
    
    # 驱动统计
    drive_stats = {name: exporter.get_drive_stats(name) 
                   for name in exporter.drive_names}
    
    # 聚类分析
    clusters, cluster_info = exporter.cluster_kmeans(n_clusters=n_clusters)
    print(f"聚类完成: {cluster_info['n_clusters']} 个聚类, 分布: {cluster_info['cluster_distribution']}")
    
    # PCA 降维
    pca_result = exporter.reduce_pca(n_components=n_pca_components)
    print(f"PCA 完成: 累计解释方差 {sum(pca_result.explained_variance_ratio):.2%}")
    
    # 检测涌现转换
    transitions = exporter.detect_emergence_transitions()
    print(f"检测到 {len(transitions)} 个涌现事件")
    
    result = {
        'n_checkpoints': n_loaded,
        'drive_names': exporter.drive_names,
        'drive_stats': drive_stats,
        'cluster_info': cluster_info,
        'pca': pca_result.to_dict(),
        'emergence_transitions': transitions
    }
    
    # 导出结果
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # JSON 导出
        json_path = output_path / 'latent_analysis.json'
        exporter.export_to_json(
            str(json_path),
            clusters=clusters,
            pca_result=pca_result,
            metadata={'analysis_type': 'full'}
        )
        print(f"JSON 导出: {json_path}")
        
        # CSV 导出
        csv_path = output_path / 'weights_history.csv'
        exporter.export_to_csv(str(csv_path))
        print(f"CSV 导出: {csv_path}")
        
        result['output_files'] = {
            'json': str(json_path),
            'csv': str(csv_path)
        }
    
    return result


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Latent Cluster Analysis')
    parser.add_argument('checkpoint_dir', help='检查点目录路径')
    parser.add_argument('--clusters', type=int, default=3, help='聚类数量')
    parser.add_argument('--pca', type=int, default=2, help='PCA 组件数')
    parser.add_argument('--output', '-o', help='输出目录')
    
    args = parser.parse_args()
    
    result = analyze_experiment_checkpoints(
        args.checkpoint_dir,
        n_clusters=args.clusters,
        n_pca_components=args.pca,
        output_dir=args.output
    )
    
    print("\n分析完成!")
    print(f"驱动: {', '.join(result['drive_names'])}")
    print(f"检查点: {result['n_checkpoints']}")
    if 'output_files' in result:
        print(f"输出文件: {result['output_files']}")
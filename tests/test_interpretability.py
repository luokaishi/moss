"""
Tests for Interpretability Tools - 可解释性工具测试

测试模块:
- agi/analysis/latent_export.py
- agi/analysis/behavior_mapping.py
- scripts/counterfactual_test.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
import json
import tempfile
import numpy as np
from pathlib import Path

from agi.analysis.latent_export import LatentExporter, ClusterResult, PCAResult
from agi.analysis.behavior_mapping import BehaviorMapper, BehaviorSegment, DriveBehaviorMapping


class TestLatentExporter(unittest.TestCase):
    """测试 LatentExporter 类"""
    
    def setUp(self):
        """设置测试环境"""
        self.exporter = LatentExporter()
        
        # 创建模拟检查点数据
        self.mock_checkpoints = []
        for i in range(10):
            self.mock_checkpoints.append({
                'cycle': (i + 1) * 1000,
                'drives': {
                    'survival': {'weight': 0.30 + i * 0.01, 'score': 0.5},
                    'optimization': {'weight': 0.25 - i * 0.005, 'score': 0.6},
                    'curiosity': {'weight': 0.15 + i * 0.002, 'score': 0.4}
                }
            })
    
    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(len(self.exporter.checkpoints), 0)
        self.assertEqual(len(self.exporter.drive_names), 0)
        self.assertIsNone(self.exporter.weights_matrix)
    
    def test_load_checkpoints_from_list(self):
        """测试从列表加载检查点"""
        # 创建临时文件
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_files = []
            for i, cp in enumerate(self.mock_checkpoints):
                path = Path(tmpdir) / f'checkpoint_{i:06d}.json'
                with open(path, 'w') as f:
                    json.dump(cp, f)
                checkpoint_files.append(str(path))
            
            # 加载检查点
            n_loaded = self.exporter.load_checkpoint_list(checkpoint_files)
            self.assertEqual(n_loaded, 10)
            self.assertEqual(len(self.exporter.drive_names), 3)
            self.assertIn('survival', self.exporter.drive_names)
    
    def test_get_drive_weights(self):
        """测试获取驱动权重"""
        with tempfile.TemporaryDirectory() as tmpdir:
            for i, cp in enumerate(self.mock_checkpoints):
                path = Path(tmpdir) / f'checkpoint_{i:06d}.json'
                with open(path, 'w') as f:
                    json.dump(cp, f)
            
            self.exporter.load_checkpoints(tmpdir)
            weights = self.exporter.get_drive_weights('survival')
            self.assertEqual(len(weights), 10)
            self.assertAlmostEqual(weights[0], 0.30, places=2)
    
    def test_get_drive_stats(self):
        """测试获取驱动统计信息"""
        with tempfile.TemporaryDirectory() as tmpdir:
            for i, cp in enumerate(self.mock_checkpoints):
                path = Path(tmpdir) / f'checkpoint_{i:06d}.json'
                with open(path, 'w') as f:
                    json.dump(cp, f)
            
            self.exporter.load_checkpoints(tmpdir)
            stats = self.exporter.get_drive_stats('survival')
            self.assertIn('mean', stats)
            self.assertIn('std', stats)
            self.assertIn('min', stats)
            self.assertIn('max', stats)
    
    def test_cluster_kmeans(self):
        """测试 K-Means 聚类"""
        with tempfile.TemporaryDirectory() as tmpdir:
            for i, cp in enumerate(self.mock_checkpoints):
                path = Path(tmpdir) / f'checkpoint_{i:06d}.json'
                with open(path, 'w') as f:
                    json.dump(cp, f)
            
            self.exporter.load_checkpoints(tmpdir)
            clusters, info = self.exporter.cluster_kmeans(n_clusters=3)
            
            self.assertEqual(len(clusters), 3)
            self.assertEqual(info['n_clusters'], 3)
            self.assertEqual(info['n_samples'], 10)
    
    def test_reduce_pca(self):
        """测试 PCA 降维"""
        with tempfile.TemporaryDirectory() as tmpdir:
            for i, cp in enumerate(self.mock_checkpoints):
                path = Path(tmpdir) / f'checkpoint_{i:06d}.json'
                with open(path, 'w') as f:
                    json.dump(cp, f)
            
            self.exporter.load_checkpoints(tmpdir)
            pca_result = self.exporter.reduce_pca(n_components=2)
            
            self.assertEqual(pca_result.n_components, 2)
            self.assertEqual(len(pca_result.explained_variance_ratio), 2)
            self.assertGreater(sum(pca_result.explained_variance_ratio), 0)


class TestBehaviorMapper(unittest.TestCase):
    """测试 BehaviorMapper 类"""
    
    def setUp(self):
        """设置测试环境"""
        self.mapper = BehaviorMapper()
    
    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(len(self.mapper.behavior_log), 0)
        self.assertEqual(len(self.mapper.segments), 0)


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def test_end_to_end_workflow(self):
        """测试端到端工作流"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建检查点
            for i in range(20):
                cp = {
                    'cycle': (i + 1) * 500,
                    'drives': {
                        'survival': {'weight': 0.30 + np.random.random() * 0.05},
                        'optimization': {'weight': 0.25 + np.random.random() * 0.05},
                        'emergent': {'weight': 0.20 + np.random.random() * 0.10}
                    }
                }
                path = Path(tmpdir) / f'checkpoint_{i:06d}.json'
                with open(path, 'w') as f:
                    json.dump(cp, f)
            
            # 测试 LatentExporter
            exporter = LatentExporter()
            exporter.load_checkpoints(tmpdir)
            self.assertEqual(len(exporter.checkpoints), 20)
            
            # 测试聚类
            clusters, info = exporter.cluster_kmeans(n_clusters=3)
            self.assertEqual(len(clusters), 3)
            
            # 测试 PCA
            pca_result = exporter.reduce_pca(n_components=2)
            self.assertEqual(pca_result.n_components, 2)


if __name__ == '__main__':
    unittest.main()

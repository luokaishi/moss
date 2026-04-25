"""
Behavior Mapping Module - 行为片段关联模块

关联驱动状态与行为日志，实现行为序列分析，生成驱动-行为映射表。

功能:
1. 关联驱动状态与行为日志
2. 实现行为序列分析
3. 生成驱动-行为映射表
4. 识别行为模式与驱动激活的关联
"""

import json
import csv
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime
from collections import defaultdict
import warnings


@dataclass
class BehaviorSegment:
    """行为片段"""
    segment_id: int
    start_cycle: int
    end_cycle: int
    behaviors: List[str]  # 行为类型列表
    drive_states: Dict[str, float]  # 驱动状态
    dominant_drive: Optional[str]  # 主导驱动
    duration: int  # 持续时间
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'segment_id': self.segment_id,
            'start_cycle': self.start_cycle,
            'end_cycle': self.end_cycle,
            'duration': self.duration,
            'behaviors': self.behaviors,
            'drive_states': {k: round(v, 6) for k, v in self.drive_states.items()},
            'dominant_drive': self.dominant_drive
        }


@dataclass
class DriveBehaviorMapping:
    """驱动-行为映射"""
    drive_name: str
    associated_behaviors: Dict[str, float]  # 行为 -> 关联强度
    behavior_frequency: Dict[str, int]  # 行为 -> 出现次数
    avg_activation: float  # 平均激活水平
    n_segments: int  # 关联的片段数
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'drive_name': self.drive_name,
            'n_segments': self.n_segments,
            'avg_activation': round(self.avg_activation, 6),
            'associated_behaviors': {k: round(v, 6) for k, v in self.associated_behaviors.items()},
            'behavior_frequency': self.behavior_frequency
        }


@dataclass
class BehaviorSequence:
    """行为序列"""
    sequence: Tuple[str, ...]  # 行为序列
    count: int  # 出现次数
    avg_drive_activation: Dict[str, float]  # 平均驱动激活
    supporting_segments: List[int]  # 支持的片段ID
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'sequence': list(self.sequence),
            'count': self.count,
            'avg_drive_activation': {k: round(v, 6) for k, v in self.avg_drive_activation.items()},
            'supporting_segments': self.supporting_segments
        }


class BehaviorMapper:
    """
    行为映射器
    
    关联驱动状态与行为日志，分析行为序列与驱动状态的关系。
    
    Attributes:
        checkpoints: 检查点数据
        behavior_log: 行为日志
        segments: 行为片段列表
        mappings: 驱动-行为映射
    """
    
    def __init__(self):
        self.checkpoints: List[Dict] = []
        self.behavior_log: List[Dict] = []
        self.segments: List[BehaviorSegment] = []
        self.mappings: Dict[str, DriveBehaviorMapping] = {}
        self.sequences: Dict[Tuple[str, ...], BehaviorSequence] = {}
        self.drive_names: List[str] = []
        
    def load_data(self, checkpoint_dir: str, behavior_log_path: Optional[str] = None) -> int:
        """
        加载检查点和行为日志
        
        Args:
            checkpoint_dir: 检查点目录
            behavior_log_path: 行为日志路径 (可选)
            
        Returns:
            加载的检查点数量
        """
        # 加载检查点
        checkpoint_path = Path(checkpoint_dir)
        if checkpoint_path.exists():
            checkpoint_files = sorted(checkpoint_path.glob("checkpoint_*.json"))
            
            for file in checkpoint_files:
                try:
                    with open(file, 'r') as f:
                        self.checkpoints.append(json.load(f))
                except Exception as e:
                    warnings.warn(f"无法加载检查点 {file}: {e}")
        
        # 提取驱动名称
        if self.checkpoints:
            first_drives = self.checkpoints[0].get('drives', {})
            self.drive_names = sorted(first_drives.keys())
        
        # 加载行为日志
        if behavior_log_path and Path(behavior_log_path).exists():
            with open(behavior_log_path, 'r') as f:
                self.behavior_log = json.load(f)
        else:
            # 模拟行为日志 (从检查点推断)
            self._generate_simulated_behavior_log()
        
        return len(self.checkpoints)
    
    def _generate_simulated_behavior_log(self):
        """生成模拟行为日志 (用于测试)"""
        behavior_types = ['explore', 'optimize', 'interact', 'analyze', 'create', 'refine']
        
        for checkpoint in self.checkpoints:
            cycle = checkpoint.get('cycle', 0)
            drives = checkpoint.get('drives', {})
            
            # 根据主导驱动选择行为
            dominant = max(drives.items(), key=lambda x: x[1].get('weight', 0))[0] if drives else 'explore'
            
            behavior_weights = {
                'survival': ['explore', 'optimize', 'refine'],
                'optimization': ['optimize', 'analyze', 'refine'],
                'influence': ['interact', 'create', 'explore'],
                'curiosity': ['explore', 'analyze', 'create'],
            }
            
            preferred = behavior_weights.get(dominant, behavior_types)
            behavior = np.random.choice(preferred)
            
            self.behavior_log.append({
                'cycle': cycle,
                'behavior': behavior,
                'drive_states': {name: data.get('weight', 0) for name, data in drives.items()}
            })
    
    def segment_behaviors(self, window_size: int = 100) -> List[BehaviorSegment]:
        """
        将行为分割成片段
        
        Args:
            window_size: 窗口大小 (周期数)
            
        Returns:
            行为片段列表
        """
        if not self.checkpoints:
            return []
        
        self.segments = []
        segment_id = 0
        
        # 按周期分组
        cycle_groups = defaultdict(list)
        for log_entry in self.behavior_log:
            cycle = log_entry.get('cycle', 0)
            window = (cycle // window_size) * window_size
            cycle_groups[window].append(log_entry)
        
        for start_cycle in sorted(cycle_groups.keys()):
            entries = cycle_groups[start_cycle]
            if not entries:
                continue
            
            end_cycle = start_cycle + window_size
            behaviors = [e.get('behavior', 'unknown') for e in entries]
            
            # 计算该窗口的平均驱动状态
            drive_states = defaultdict(list)
            for entry in entries:
                states = entry.get('drive_states', {})
                for drive, value in states.items():
                    drive_states[drive].append(value)
            
            avg_drive_states = {k: np.mean(v) for k, v in drive_states.items()}
            dominant = max(avg_drive_states.items(), key=lambda x: x[1])[0] if avg_drive_states else None
            
            segment = BehaviorSegment(
                segment_id=segment_id,
                start_cycle=start_cycle,
                end_cycle=end_cycle,
                behaviors=list(set(behaviors)),  # 去重
                drive_states=avg_drive_states,
                dominant_drive=dominant,
                duration=len(entries)
            )
            
            self.segments.append(segment)
            segment_id += 1
        
        return self.segments
    
    def analyze_drive_behavior_mapping(self) -> Dict[str, DriveBehaviorMapping]:
        """
        分析驱动-行为映射
        
        Returns:
            驱动名称 -> DriveBehaviorMapping 的字典
        """
        if not self.segments:
            self.segment_behaviors()
        
        self.mappings = {}
        
        # 按驱动分组
        drive_segments = defaultdict(list)
        for segment in self.segments:
            if segment.dominant_drive:
                drive_segments[segment.dominant_drive].append(segment)
        
        for drive_name in self.drive_names:
            segments = drive_segments.get(drive_name, [])
            
            if not segments:
                continue
            
            # 统计行为频率
            behavior_counts = defaultdict(int)
            behavior_drive_values = defaultdict(list)
            
            for segment in segments:
                for behavior in segment.behaviors:
                    behavior_counts[behavior] += 1
                    behavior_drive_values[behavior].append(segment.drive_states.get(drive_name, 0))
            
            # 计算关联强度 (平均激活水平)
            total_segments = len(self.segments)
            associated_behaviors = {}
            for behavior, count in behavior_counts.items():
                frequency = count / len(segments)
                avg_activation = np.mean(behavior_drive_values[behavior]) if behavior_drive_values[behavior] else 0
                # 关联强度 = 频率 * 平均激活
                associated_behaviors[behavior] = frequency * avg_activation
            
            # 计算平均激活
            all_activations = [s.drive_states.get(drive_name, 0) for s in segments]
            avg_activation = np.mean(all_activations) if all_activations else 0
            
            mapping = DriveBehaviorMapping(
                drive_name=drive_name,
                associated_behaviors=dict(associated_behaviors),
                behavior_frequency=dict(behavior_counts),
                avg_activation=avg_activation,
                n_segments=len(segments)
            )
            
            self.mappings[drive_name] = mapping
        
        return self.mappings
    
    def analyze_behavior_sequences(self, sequence_length: int = 3) -> Dict[Tuple[str, ...], BehaviorSequence]:
        """
        分析行为序列
        
        Args:
            sequence_length: 序列长度
            
        Returns:
            序列 -> BehaviorSequence 的字典
        """
        if not self.segments:
            self.segment_behaviors()
        
        # 提取所有行为 (按时间顺序)
        all_behaviors = []
        for segment in self.segments:
            all_behaviors.extend(segment.behaviors)
        
        # 统计序列
        sequence_counts = defaultdict(lambda: {'count': 0, 'segments': []})
        
        for i in range(len(all_behaviors) - sequence_length + 1):
            seq = tuple(all_behaviors[i:i + sequence_length])
            sequence_counts[seq]['count'] += 1
            # 找到对应的片段
            segment_idx = min(i // max(len(all_behaviors) // len(self.segments), 1), len(self.segments) - 1)
            sequence_counts[seq]['segments'].append(segment_idx)
        
        self.sequences = {}
        
        for seq, data in sequence_counts.items():
            if data['count'] < 2:  # 过滤低频序列
                continue
            
            # 计算平均驱动激活
            drive_activations = defaultdict(list)
            for seg_idx in data['segments']:
                if seg_idx < len(self.segments):
                    for drive, value in self.segments[seg_idx].drive_states.items():
                        drive_activations[drive].append(value)
            
            avg_drive_activation = {k: np.mean(v) for k, v in drive_activations.items()}
            
            behavior_seq = BehaviorSequence(
                sequence=seq,
                count=data['count'],
                avg_drive_activation=avg_drive_activation,
                supporting_segments=data['segments']
            )
            
            self.sequences[seq] = behavior_seq
        
        return self.sequences
    
    def find_behavior_patterns(self, min_support: int = 2) -> List[Dict]:
        """
        发现行为模式
        
        Args:
            min_support: 最小支持度 (出现次数)
            
        Returns:
            行为模式列表
        """
        if not self.sequences:
            self.analyze_behavior_sequences()
        
        patterns = []
        
        for seq, behavior_seq in self.sequences.items():
            if behavior_seq.count >= min_support:
                # 找出该序列最常关联的驱动
                dominant_drive = max(behavior_seq.avg_drive_activation.items(), 
                                    key=lambda x: x[1])[0] if behavior_seq.avg_drive_activation else None
                
                patterns.append({
                    'sequence': list(seq),
                    'count': behavior_seq.count,
                    'dominant_drive': dominant_drive,
                    'drive_activation': behavior_seq.avg_drive_activation
                })
        
        # 按出现次数排序
        patterns.sort(key=lambda x: x['count'], reverse=True)
        
        return patterns
    
    def export_mapping_to_json(self, output_path: str) -> str:
        """
        导出映射到 JSON
        
        Args:
            output_path: 输出文件路径
            
        Returns:
            输出文件路径
        """
        output = {
            'export_time': datetime.now().isoformat(),
            'n_segments': len(self.segments),
            'drive_names': self.drive_names,
            'drive_behavior_mappings': {k: v.to_dict() for k, v in self.mappings.items()},
            'behavior_sequences': {str(k): v.to_dict() for k, v in self.sequences.items()},
            'segments': [s.to_dict() for s in self.segments]
        }
        
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        return output_path
    
    def export_mapping_to_csv(self, output_path: str) -> str:
        """
        导出驱动-行为映射到 CSV
        
        Args:
            output_path: 输出文件路径
            
        Returns:
            输出文件路径
        """
        rows = []
        
        for drive_name, mapping in self.mappings.items():
            for behavior, strength in mapping.associated_behaviors.items():
                rows.append({
                    'drive_name': drive_name,
                    'behavior': behavior,
                    'association_strength': round(strength, 6),
                    'frequency': mapping.behavior_frequency.get(behavior, 0),
                    'avg_drive_activation': round(mapping.avg_activation, 6),
                    'n_segments': mapping.n_segments
                })
        
        if rows:
            fieldnames = ['drive_name', 'behavior', 'association_strength', 
                         'frequency', 'avg_drive_activation', 'n_segments']
            
            with open(output_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
        
        return output_path
    
    def get_drive_behavior_correlation(self) -> Dict[str, Dict[str, float]]:
        """
        计算驱动-行为相关性矩阵
        
        Returns:
            驱动 -> 行为 -> 相关性的字典
        """
        if not self.mappings:
            self.analyze_drive_behavior_mapping()
        
        correlation = {}
        
        for drive_name, mapping in self.mappings.items():
            correlation[drive_name] = mapping.associated_behaviors
        
        return correlation


def analyze_behavior_mapping(checkpoint_dir: str,
                            behavior_log_path: Optional[str] = None,
                            output_dir: Optional[str] = None,
                            window_size: int = 100) -> Dict:
    """
    分析行为映射的完整流程
    
    Args:
        checkpoint_dir: 检查点目录
        behavior_log_path: 行为日志路径
        output_dir: 输出目录
        window_size: 片段窗口大小
        
    Returns:
        分析结果字典
    """
    mapper = BehaviorMapper()
    
    # 加载数据
    n_loaded = mapper.load_data(checkpoint_dir, behavior_log_path)
    print(f"加载了 {n_loaded} 个检查点")
    
    if n_loaded == 0:
        return {'error': '没有加载到检查点'}
    
    # 行为分段
    segments = mapper.segment_behaviors(window_size=window_size)
    print(f"生成了 {len(segments)} 个行为片段")
    
    # 驱动-行为映射
    mappings = mapper.analyze_drive_behavior_mapping()
    print(f"分析了 {len(mappings)} 个驱动的行为映射")
    
    # 行为序列分析
    sequences = mapper.analyze_behavior_sequences(sequence_length=3)
    print(f"发现了 {len(sequences)} 个行为序列")
    
    # 行为模式
    patterns = mapper.find_behavior_patterns(min_support=2)
    print(f"发现了 {len(patterns)} 个行为模式")
    
    result = {
        'n_checkpoints': n_loaded,
        'n_segments': len(segments),
        'drive_names': mapper.drive_names,
        'n_mappings': len(mappings),
        'n_sequences': len(sequences),
        'n_patterns': len(patterns),
        'patterns': patterns[:10]  # 前10个模式
    }
    
    # 导出结果
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # JSON 导出
        json_path = output_path / 'behavior_mapping.json'
        mapper.export_mapping_to_json(str(json_path))
        print(f"JSON 导出: {json_path}")
        
        # CSV 导出
        csv_path = output_path / 'drive_behavior_mapping.csv'
        mapper.export_mapping_to_csv(str(csv_path))
        print(f"CSV 导出: {csv_path}")
        
        result['output_files'] = {
            'json': str(json_path),
            'csv': str(csv_path)
        }
    
    return result


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Behavior Mapping Analysis')
    parser.add_argument('checkpoint_dir', help='检查点目录路径')
    parser.add_argument('--behavior-log', help='行为日志路径 (可选)')
    parser.add_argument('--window-size', type=int, default=100, help='片段窗口大小')
    parser.add_argument('--output', '-o', help='输出目录')
    
    args = parser.parse_args()
    
    result = analyze_behavior_mapping(
        args.checkpoint_dir,
        behavior_log_path=args.behavior_log,
        output_dir=args.output,
        window_size=args.window_size
    )
    
    print("\n分析完成!")
    print(f"片段数: {result['n_segments']}")
    print(f"映射数: {result['n_mappings']}")
    print(f"序列数: {result['n_sequences']}")
    if 'output_files' in result:
        print(f"输出文件: {result['output_files']}")
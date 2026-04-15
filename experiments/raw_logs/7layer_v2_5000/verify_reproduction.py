#!/usr/bin/env python3
"""
验证复现结果

比较原始日志和新日志的一致性
"""

import sys
import pandas as pd
import numpy as np

def verify_reproduction(original_path, new_path):
    """验证复现一致性"""
    orig = pd.read_csv(original_path)
    new = pd.read_csv(new_path)
    
    # 比较关键指标
    metrics = ['concept_error', 'concept_stability', 'self_model_accuracy']
    
    print("复现验证结果:")
    print("="*50)
    
    all_match = True
    for metric in metrics:
        orig_mean = orig[metric].mean()
        new_mean = new[metric].mean()
        diff = abs(orig_mean - new_mean)
        
        if diff < 0.01:  # 1%容差
            status = "✅ 匹配"
        elif diff < 0.05:  # 5%容差
            status = "⚠️  接近"
            all_match = False
        else:
            status = "❌ 差异大"
            all_match = False
        
        print(f"{metric}: {status} (diff={diff:.4f})")
    
    print("="*50)
    if all_match:
        print("✅ 复现验证通过!")
        return 0
    else:
        print("⚠️  复现存在差异，请检查环境")
        return 1

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python verify_reproduction.py <original.csv> <new.csv>")
        sys.exit(1)
    
    sys.exit(verify_reproduction(sys.argv[1], sys.argv[2]))

#!/usr/bin/env python3
"""
归档旧实验文件
==============

保留最近的实验结果，归档旧文件到 experiments/archive/
"""

import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta

def archive_old_experiments():
    experiments_dir = Path("experiments")
    archive_dir = experiments_dir / "archive"
    archive_dir.mkdir(exist_ok=True)

    # 保留最近 7 天的实验
    cutoff_date = datetime.now() - timedelta(days=7)

    # 需要归档的子目录模式
    archive_patterns = [
        "e1_*",  # 旧实验
        "e2_*",
        "e3_*",
        "e4_*",
        "e5_*",
        "e6_*",
        "e7_*",
        "meta_sme/eval/seed*",  # 种子实验
        "self_modification/backup_*",
    ]

    archived = []
    kept = []

    for exp_dir in experiments_dir.iterdir():
        if not exp_dir.is_dir():
            continue
        if exp_dir.name == "archive":
            continue

        # 检查修改时间
        try:
            mtime = datetime.fromtimestamp(exp_dir.stat().st_mtime)
            if mtime < cutoff_date:
                # 归档
                dest = archive_dir / exp_dir.name
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.move(str(exp_dir), str(dest))
                archived.append(exp_dir.name)
            else:
                kept.append(exp_dir.name)
        except Exception as e:
            print(f"Error processing {exp_dir}: {e}")

    print(f"Archived {len(archived)} directories to experiments/archive/")
    print(f"Kept {len(kept)} recent directories")
    print(f"\nKept directories:")
    for d in sorted(kept):
        print(f"  - {d}")

if __name__ == "__main__":
    archive_old_experiments()

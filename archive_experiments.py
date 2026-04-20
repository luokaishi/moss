#!/usr/bin/env python3
"""
MOSS Experiment Archive Tool
============================

归档旧实验目录，保留最近结果
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime

def archive_old_experiments():
    """归档旧实验"""
    experiments_dir = Path("experiments")
    archive_dir = Path("experiments/_archived")
    archive_dir.mkdir(exist_ok=True)

    # 保留的目录（最近实验）
    keep_dirs = [
        "e9_ast_only",           # AST对照实验
        "e10_coding_plan_v2",    # v2实验
        "e13_coding_plan_v4",    # v4实验（待运行）
    ]

    # 保留的结果文件
    keep_results = [
        "experiment_ast_only_20260420_234040.json",
        "experiment_coding_plan_v2_20260420_234800.json",
        "experiment_coding_plan_v3_20260421_012301.json",
    ]

    archived = []
    kept = []

    for item in experiments_dir.iterdir():
        if item.name.startswith("_"):
            continue

        if item.is_dir():
            if item.name not in keep_dirs:
                # 归档目录
                dest = archive_dir / item.name
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.move(str(item), str(dest))
                archived.append(f"dir: {item.name}")
            else:
                kept.append(f"dir: {item.name}")

        elif item.is_file() and item.suffix == ".json":
            if item.name not in keep_results:
                # 归档旧结果文件
                dest = archive_dir / item.name
                if dest.exists():
                    os.remove(dest)
                shutil.move(str(item), str(dest))
                archived.append(f"file: {item.name}")
            else:
                kept.append(f"file: {item.name}")

    # 统计
    archive_size = sum(f.stat().st_size for f in archive_dir.rglob("*") if f.is_file())
    archive_size_mb = archive_size / (1024 * 1024)

    print("="*60)
    print("Experiment Archive Report")
    print("="*60)
    print(f"\nArchived ({len(archived)} items, {archive_size_mb:.1f} MB):")
    for item in archived[:10]:
        print(f"  - {item}")
    if len(archived) > 10:
        print(f"  ... and {len(archived)-10} more")

    print(f"\nKept ({len(kept)} items):")
    for item in kept:
        print(f"  + {item}")

    print(f"\nArchive location: {archive_dir}")
    print("="*60)

    # 保存归档记录
    record = {
        "timestamp": datetime.now().isoformat(),
        "archived_items": archived,
        "kept_items": kept,
        "archive_size_mb": archive_size_mb,
    }
    with open(archive_dir / "archive_record.json", "w") as f:
        json.dump(record, f, indent=2)

if __name__ == "__main__":
    archive_old_experiments()

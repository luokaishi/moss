#!/usr/bin/env python3
"""
下载 Qwen2.5-Coder-7B-Instruct 模型
使用 hf-mirror 加速，支持断点续传
"""
import os
import sys
import time

os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '1'

from huggingface_hub import snapshot_download
from huggingface_hub.utils import tqdm

MODEL_ID = "Qwen/Qwen2.5-Coder-7B-Instruct"
LOCAL_DIR = os.path.expanduser("~/.cache/huggingface/moss/qwen2.5-coder-7b")

print("=" * 60)
print("Downloading Qwen2.5-Coder-7B-Instruct")
print("=" * 60)
print(f"Model: {MODEL_ID}")
print(f"Target: {LOCAL_DIR}")
print(f"Mirror: {os.environ['HF_ENDPOINT']}")
print(f"Start: {time.strftime('%H:%M:%S')}")
print("-" * 60)

try:
    local_path = snapshot_download(
        repo_id=MODEL_ID,
        local_dir=LOCAL_DIR,
        local_dir_use_symlinks=False,
        resume_download=True,
        max_workers=4,  # 多线程加速
    )
    print(f"\n✅ Download completed!")
    print(f"Location: {local_path}")
    print(f"End: {time.strftime('%H:%M:%S')}")

    # 验证文件
    import os
    size = sum(os.path.getsize(os.path.join(dirpath, filename))
               for dirpath, dirnames, filenames in os.walk(local_path)
               for filename in filenames)
    print(f"Total size: {size / 1024 / 1024 / 1024:.2f} GB")

except Exception as e:
    print(f"\n❌ Download failed: {e}")
    sys.exit(1)

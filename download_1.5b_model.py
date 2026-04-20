#!/usr/bin/env python3
"""下载 Qwen2.5-Coder-1.5B-Instruct 模型"""

import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

from huggingface_hub import snapshot_download

model_id = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
local_dir = os.path.expanduser("~/.cache/huggingface/moss/qwen2.5-coder-1.5b")

print(f"Downloading {model_id} to {local_dir}")
print("Using hf-mirror.com for faster download")

snapshot_download(
    repo_id=model_id,
    local_dir=local_dir,
    resume_download=True,
)

print(f"\n✅ Model downloaded to: {local_dir}")
print(f"Size: {sum(os.path.getsize(os.path.join(dp, f)) for dp, dn, fn in os.walk(local_dir) for f in fn) / 1e9:.2f} GB")

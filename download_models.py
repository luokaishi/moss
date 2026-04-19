#!/usr/bin/env python3
"""
加速下载本地模型

优化措施:
1. 使用 hf-mirror.com 国内镜像
2. 设置 HF_HUB_ENABLE_HF_TRANSFER 加速传输
3. 多线程并行下载多个模型
4. 显示实时进度
"""

import os
import sys
import threading
import time

# 加速配置
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '1'
os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = '300'

from huggingface_hub import snapshot_download
from huggingface_hub.utils import tqdm

MODELS = {
    "qwen2.5-coder-1.5b": "Qwen/Qwen2.5-Coder-1.5B-Instruct",
    "qwen2.5-coder-7b": "Qwen/Qwen2.5-Coder-7B-Instruct",
}


def download_model(name: str, repo_id: str):
    """下载单个模型"""
    print(f"\n[DOWNLOAD] {name} ({repo_id})")
    print(f"           Started at {time.strftime('%H:%M:%S')}")

    try:
        start = time.time()
        local_path = snapshot_download(
            repo_id=repo_id,
            local_dir=os.path.expanduser(f"~/.cache/huggingface/moss/{name}"),
            local_dir_use_symlinks=False,
            resume_download=True,
        )
        elapsed = time.time() - start
        print(f"[✅ DONE] {name} in {elapsed:.1f}s -> {local_path}")
        return True
    except Exception as e:
        print(f"[❌ FAILED] {name}: {e}")
        return False


def main():
    print("=" * 60)
    print("MOSS Local Model Download Accelerator")
    print("=" * 60)
    print(f"Mirror: {os.environ['HF_ENDPOINT']}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # 首先下载 1.5B（最快可用）
    print("\n" + "=" * 60)
    print("Phase 1: Downloading 1.5B model (fast test version)")
    print("=" * 60)

    success_1_5b = download_model("qwen2.5-coder-1.5b", MODELS["qwen2.5-coder-1.5b"])

    if success_1_5b:
        print("\n" + "=" * 60)
        print("Phase 2: Starting parallel download of 7B model")
        print("=" * 60)

        # 后台下载 7B
        thread_7b = threading.Thread(
            target=download_model,
            args=("qwen2.5-coder-7b", MODELS["qwen2.5-coder-7b"]),
            daemon=True
        )
        thread_7b.start()

        # 立即测试 1.5B
        print("\n" + "=" * 60)
        print("Phase 3: Testing 1.5B model immediately")
        print("=" * 60)

        test_1_5b()

        # 等待 7B 下载完成
        print("\n" + "=" * 60)
        print("Phase 4: Waiting for 7B download...")
        print("=" * 60)
        thread_7b.join()

    print("\n" + "=" * 60)
    print("All downloads completed!")
    print("=" * 60)


def test_1_5b():
    """测试 1.5B 模型"""
    sys.path.insert(0, '/workspace/moss')

    print("\n[TEST] Loading 1.5B model...")
    from moss.core.local_llm_backend import create_local_backend_for_moss
    from moss.core.llm_mutator import LLMMutator
    import numpy as np

    backend = create_local_backend_for_moss("qwen2.5-coder-1.5b")
    mutator = LLMMutator(backend)

    sample_code = '''
def calculate_weights(x):
    return x * 0.5 + 0.1
'''

    print("[TEST] Running mutation test...")
    result, info = mutator.mutate(
        source=sample_code,
        target_functions=['calculate_weights'],
        mutation_strategy='parameter_tune',
    )

    print(f"[TEST] Result: {info.mutation_type}")
    print(f"[TEST] Valid: {info.validation_passed}")

    if info.validation_passed:
        print("\n✅ 1.5B MODEL READY! You can start using it now.")
    else:
        print("\n⚠️ Model responding but mutation not validated.")


if __name__ == "__main__":
    main()

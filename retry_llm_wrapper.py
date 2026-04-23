#!/usr/bin/env python3
"""
LLM调用重试包装器 - 处理429限流
"""
import time, random, functools
from typing import Callable, Any

def retry_on_rate_limit(max_retries=5, base_delay=2.0, max_delay=60.0):
    """装饰器：遇到429时指数退避重试"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if "429" in str(e) or "rate_limit" in str(e).lower():
                        if attempt == max_retries:
                            raise
                        delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
                        print(f"⚠️  Rate limited, retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries})")
                        time.sleep(delay)
                    else:
                        raise
            return func(*args, **kwargs)
        return wrapper
    return decorator

# 使用示例
if __name__ == "__main__":
    # 这个装饰器会被应用到LLM调用函数上
    pass
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import base64
import requests
import os
import sys
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ===================== 核心配置 =====================
# 修复：使用GitHub RAW链接（关键！）
SUBSCRIBE_RAW_URLS = [
    "https://raw.githubusercontent.com/shaoyouvip/free/main/base64.txt"
]

TARGET_URL = SUBSCRIBE_RAW_URLS[0]  # 目标链接和订阅链接一致
TIMEOUT = 15
RETRY_TIMES = 3

# ===================== 工具函数 =====================
def init_request_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=RETRY_TIMES,
        backoff_factor=0.5,
        allowed_methods=["GET"],
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def clean_base64_suffix(raw_str):
    """清理base64字符串后面的非base64字符（时间戳、注释等）"""
    valid_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=')
    for i, char in enumerate(raw_str):
        if char not in valid_chars:
            print(f"Found invalid char '{char}' at position {i}, truncating...")
            return raw_str[:i].strip()
    print("No invalid chars in base64 string")
    return raw_str.strip()

def download_and_decode_sub(session, url):
    try:
        print(f"\n=== Processing URL: {url} ===")
        response = session.get(url, timeout=TIMEOUT, allow_redirects=True)
        response.raise_for_status()  # 抛出HTTP错误（如404、500）
        print(f"Request successful (status code: {response.status_code})")
        
        raw_content = response.text.strip()
        print(f"Raw content length before cleaning: {len(raw_content)} bytes")
        print(f"First 50 chars of raw content: {raw_content[:50]}...")  # 调试输出前50字符
        
        if not raw_content:
            print("Raw content is empty!")
            return []
        
        # 清理base64后缀
        if url == TARGET_URL:
            raw_content = clean_base64_suffix(raw_content)
            print(f"Cleaned base64 length: {len(raw_content)} bytes")
            print(f"First 50 chars after cleaning: {raw_content[:50]}...")
        
        # 补全base64 padding
        padding = len(raw_content) % 4
        if padding != 0:
            raw_content += "=" * (4 - padding)
            print(f"Added {4 - padding} padding chars")
        
        # 解码
        try:
            decoded_content = base64.b64decode(raw_content).decode("utf-8", errors="ignore")
            print(f"Decoded content length: {len(decoded_content)} bytes")
            print(f"First 100 chars of decoded content: {decoded_content[:100]}...")
        except base64.binascii.Error as e:
            print(f"Base64 decode failed: {str(e)}")
            decoded_content = raw_content
        
        # 提取节点
        nodes = [node.strip() for node in decoded_content.split() if node.strip()]
        print(f"Extracted {len(nodes)} valid nodes")
        
        # 输出前2个节点（调试用）
        for i, node in enumerate(nodes[:2]):
            print(f"Node {i+1}: {node[:50]}...")
        
        return nodes
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {str(e)}", file=sys.stderr)
    except Exception as e:
        print(f"Unexpected error: {str(e)}", file=sys.stderr)
    return []

# ===================== 核心逻辑 =====================
def merge_all_subs():
    print("=" * 50)
    print("Starting subscription merge process")
    print("=" * 50)
    
    print(f"Current working directory: {os.getcwd()}")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Script directory: {script_dir}")
    
    session = init_request_session()
    all_nodes = []
    
    for url in SUBSCRIBE_RAW_URLS:
        nodes = download_and_decode_sub(session, url)
        if nodes:
            all_nodes.extend(nodes)
            print(f"\nSuccessfully fetched {len(nodes)} nodes from {url}")
    
    print("\n" + "=" * 50)
    print(f"Total nodes collected (including duplicates): {len(all_nodes)}")
    print("=" * 50)
    
    if not all_nodes:
        print("\n❌ No valid nodes found! Check the debug output above for reasons.")
        return
    
    # 生成最终文件
    merged_nodes_text = "\n".join(all_nodes)
    final_base64 = base64.b64encode(merged_nodes_text.encode("utf-8")).decode("utf-8")

    date_dir = os.path.join(script_dir, "Date")
    os.makedirs(date_dir, exist_ok=True)
    output_file = os.path.join(date_dir, "List.txt")
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_base64)
    
    print(f"\n✅ File saved successfully!")
    print(f"Path: {output_file}")
    print(f"Size: {os.path.getsize(output_file)} bytes")

if __name__ == "__main__":
    merge_all_subs()

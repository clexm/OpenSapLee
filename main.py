#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import base64
import requests
import os
import sys
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ===================== 核心配置 =====================
SUBSCRIBE_RAW_URLS = [
    "https://www.xrayvip.com/free.txt",
    "https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/v2ray.txt",
    "https://raw.githubusercontent.com/aiboboxx/v2rayfree/main/v2",
    "https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub",
    "https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list.txt",
    "https://raw.githubusercontent.com/free-nodes/v2rayfree/main/v202606182",
    "https://raw.githubusercontent.com/free18/v2ray/refs/heads/main/v.txt",
    "http://59.33.33.157:18080/v2ray.txt",
    "https://github.com/chengaopan/AutoMergePublicNodes/blob/master/list.txt",
    "https://ghfast.top/https://raw.githubusercontent.com/free18/v2ray/refs/heads/main/v.txt",
    "https://raw.githubusercontent.com/shaoyouvip/free/main/base64.txt"
]

# 仅这个链接的base64后面有时间戳，需要清理
TARGET_CLEAN_URL = "https://raw.githubusercontent.com/shaoyouvip/free/main/base64.txt"
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
            print(f"⚠️  Found invalid char '{char}' at position {i} (target URL), truncating...")
            return raw_str[:i].strip()
    print("✅ No invalid chars in target URL's base64 string")
    return raw_str.strip()

def download_and_decode_sub(session, url):
    try:
        print(f"\n=== Processing URL: {url} ===")
        # 发送请求
        response = session.get(url, timeout=TIMEOUT, allow_redirects=True)
        response.raise_for_status()  # 抛出HTTP错误（404、500等）
        print(f"✅ Request successful (status code: {response.status_code})")
        
        # 获取原始内容
        raw_content = response.text.strip()
        print(f"Raw content length: {len(raw_content)} bytes")
        print(f"First 50 chars: {raw_content[:50]}...")
        
        if not raw_content:
            print("❌ Raw content is empty!")
            return []
        
        # 关键：仅对目标链接清理base64后缀（时间戳）
        if url == TARGET_CLEAN_URL:
            raw_content = clean_base64_suffix(raw_content)
        
        # 补全base64 padding（所有链接都需要，避免解码失败）
        padding = len(raw_content) % 4
        if padding != 0:
            raw_content += "=" * (4 - padding)
            print(f"Added {4 - padding} padding chars for base64")
        
        # 解码base64（所有链接统一处理）
        try:
            decoded_content = base64.b64decode(raw_content).decode("utf-8", errors="ignore")
            print(f"✅ Base64 decoded successfully (decoded length: {len(decoded_content)} bytes)")
            print(f"Decoded first 100 chars: {decoded_content[:100]}...")
        except base64.binascii.Error as e:
            print(f"❌ Base64 decode failed: {str(e)} → Skipping this URL")
            return []
        
        # 提取节点（过滤空行，支持换行/空格分隔）
        nodes = [node.strip() for node in decoded_content.split() if node.strip()]
        print(f"✅ Extracted {len(nodes)} valid nodes from this URL")
        
        # 调试：输出前2个节点预览
        for i, node in enumerate(nodes[:2]):
            print(f"  Node {i+1}: {node[:60]}...")
        
        return nodes
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {str(e)}", file=sys.stderr)
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}", file=sys.stderr)
    return []

# ===================== 核心逻辑 =====================
def merge_all_subs():
    print("=" * 60)
    print("🔄 Starting subscription merge process (all base64 encoded)")
    print("=" * 60)
    
    # 打印工作目录（方便排查文件保存位置）
    print(f"\n📂 Current working directory: {os.getcwd()}")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"📂 Script directory: {script_dir}")
    
    session = init_request_session()
    all_nodes = []
    
    # 遍历所有链接，提取节点
    for url in SUBSCRIBE_RAW_URLS:
        nodes = download_and_decode_sub(session, url)
        if nodes:
            all_nodes.extend(nodes)
            print(f"\n🎉 Successfully added {len(nodes)} nodes from {url}")
    
    # 统计总节点数
    print("\n" + "=" * 60)
    print(f"📊 Total valid nodes (after deduplication): {len(all_nodes)}")
    print("=" * 60)
    
    # 无节点时退出
    if not all_nodes:
        print("\n❌ No valid nodes found in any URL! Check debug output for details.")
        return
    
    # 保存合并后的base64文件
    merged_text = "\n".join(all_nodes)
    final_base64 = base64.b64encode(merged_text.encode("utf-8")).decode("utf-8")
    
    # 确保保存目录存在
    script_dir = os.path.dirname(os.path.abspath(__file__))
    date_dir = os.path.join(script_dir, "Date")
    os.makedirs(date_dir, exist_ok=True)
    output_file = os.path.join(date_dir, "List.txt")
    
    # 写入文件
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_base64)
    
    # 打印结果
    file_size = os.path.getsize(output_file)
    print(f"\n✅ File saved successfully!")
    print(f"📁 Path: {output_file}")
    print(f"📏 Size: {file_size} bytes")
    print(f"🔍 Final base64 first 50 chars: {final_base64[:50]}...")

if __name__ == "__main__":
    merge_all_subs()

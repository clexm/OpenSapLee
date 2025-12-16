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
    "https://github.com/shaoyouvip/free/blob/main/base64.txt"
]

# 目标链接（base64后面拼接了时间戳的链接）
TARGET_URL = "https://github.com/shaoyouvip/free/blob/main/base64.txt"
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
    # base64合法字符集：A-Z、a-z、0-9、+、/、=
    valid_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=')
    # 找到第一个非法字符的位置，截断后面的内容
    for i, char in enumerate(raw_str):
        if char not in valid_chars:
            return raw_str[:i].strip()  # 截断并去除首尾空格
    return raw_str.strip()  # 全是合法字符，直接返回

def download_and_decode_sub(session, url):
    try:
        response = session.get(url, timeout=TIMEOUT, allow_redirects=True)
        response.raise_for_status()
        
        raw_content = response.text.strip()
        if not raw_content:
            return []
        
        # 关键：只处理目标链接——清理base64后面的时间戳（解码前）
        if url == TARGET_URL:
            raw_content = clean_base64_suffix(raw_content)
        
        # base64补全padding
        padding = len(raw_content) % 4
        if padding != 0:
            raw_content += "=" * (4 - padding)
        
        # 解码内容
        try:
            decoded_content = base64.b64decode(raw_content).decode("utf-8", errors="ignore")
        except base64.binascii.Error:
            decoded_content = raw_content
        
        # 提取所有节点（去空）
        nodes = [node.strip() for node in decoded_content.split() if node.strip()]
        return nodes
    except Exception as e:
        print(f"Error processing {url}: {str(e)}", file=sys.stderr)
        return []

# ===================== 核心逻辑 =====================
def merge_all_subs():
    print(f"Current working directory: {os.getcwd()}")
    print(f"Script directory: {os.path.dirname(os.path.abspath(__file__))}")
    
    session = init_request_session()
    all_nodes = []
    
    for url in SUBSCRIBE_RAW_URLS:
        nodes = download_and_decode_sub(session, url)
        if nodes:
            all_nodes.extend(nodes)
            print(f"Fetched {len(nodes)} nodes from {url}")
    
    print(f"Total nodes collected (including duplicates): {len(all_nodes)}")
    
    if not all_nodes:
        print("No valid nodes found, exiting...")
        return
    
    # 生成最终base64文件
    merged_nodes_text = "\n".join(all_nodes)
    final_base64 = base64.b64encode(merged_nodes_text.encode("utf-8")).decode("utf-8")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    date_dir = os.path.join(script_dir, "Date")
    os.makedirs(date_dir, exist_ok=True)
    output_file = os.path.join(date_dir, "List.txt")
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_base64)
    
    print(f"File saved to: {output_file}")
    print(f"File size: {os.path.getsize(output_file)} bytes")

if __name__ == "__main__":
    merge_all_subs()

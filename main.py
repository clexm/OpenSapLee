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
    "https://raw.githubusercontent.com/free-nodes/v2rayfree/main/v2",
    "https://raw.githubusercontent.com/free18/v2ray/refs/heads/main/v.txt",
]

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

def download_and_decode_sub(session, url):
    try:
        response = session.get(url, timeout=TIMEOUT, allow_redirects=True)
        response.raise_for_status()
        
        raw_content = response.text.strip()
        if not raw_content:
            return []
        
        padding = len(raw_content) % 4
        if padding != 0:
            raw_content += "=" * (4 - padding)
        
        try:
            decoded_content = base64.b64decode(raw_content).decode("utf-8", errors="ignore")
        except base64.binascii.Error:
            decoded_content = raw_content
        
        nodes = [node.strip() for node in decoded_content.split() if node.strip()]
        return nodes
    except Exception as e:
        print(f"Error processing {url}: {str(e)}", file=sys.stderr)
        return []

# ===================== 核心逻辑 =====================
def merge_all_subs():
    # 强制打印工作目录（调试关键）
    print(f"Current working directory: {os.getcwd()}")
    print(f"Script directory: {os.path.dirname(os.path.abspath(__file__))}")
    
    session = init_request_session()
    all_unique_nodes = set()
    
    for url in SUBSCRIBE_RAW_URLS:
        nodes = download_and_decode_sub(session, url)
        if nodes:
            all_unique_nodes.update(nodes)
    
    print(f"Total unique nodes found: {len(all_unique_nodes)}")
    
    if not all_unique_nodes:
        print("No valid nodes found, exiting...")
        return
    
    # 生成最终内容
    merged_nodes_text = "\n".join(all_unique_nodes)
    final_base64 = base64.b64encode(merged_nodes_text.encode("utf-8")).decode("utf-8")

    # 存储文件（你的逻辑）
    script_dir = os.path.dirname(os.path.abspath(__file__))
    date_dir = os.path.join(script_dir, "Date")
    os.makedirs(date_dir, exist_ok=True)
    output_file = os.path.join(date_dir, "List.txt")
    
    # 写入文件并打印路径
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_base64)
    
    print(f"File saved to: {output_file}")
    print(f"File size: {os.path.getsize(output_file)} bytes")

# ===================== 关键：添加执行入口 =====================
if __name__ == "__main__":
    merge_all_subs()

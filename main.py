#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import base64
import requests
import os
import sys
import json
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

# ===================== 核心：节点精准去重工具函数 =====================
def get_node_unique_key(node_link):
    """
    解析节点链接，生成唯一标识key（基于核心属性，忽略备注名）
    支持：vmess:// / vless:// / ssr:// / trojan://
    """
    try:
        # 1. VMess节点（最常用）
        if node_link.startswith("vmess://"):
            # 解码VMess节点
            link = node_link[8:]
            padding = len(link) % 4
            if padding != 0:
                link += "=" * (4 - padding)
            node_json = base64.b64decode(link).decode("utf-8", errors="ignore")
            node = json.loads(node_json)
            # 核心属性：IP+端口+ID+加密方式+传输协议
            return f"vmess_{node.get('add', '')}_{node.get('port', '')}_{node.get('id', '')}_{node.get('scy', '')}_{node.get('net', '')}"
        
        # 2. VLESS节点
        elif node_link.startswith("vless://"):
            # VLESS格式：vless://ID@IP:端口?参数
            core_part = node_link.split("?")[0].replace("vless://", "")
            id_part, addr_part = core_part.split("@")
            ip, port = addr_part.split(":")
            return f"vless_{ip}_{port}_{id_part}"
        
        # 3. SSR节点
        elif node_link.startswith("ssr://"):
            # 解码SSR节点
            link = node_link[6:]
            padding = len(link) % 4
            if padding != 0:
                link += "=" * (4 - padding)
            ssr_info = base64.b64decode(link).decode("utf-8", errors="ignore")
            # SSR格式：IP:端口:协议:加密:混淆:密码?参数
            core_info = ssr_info.split("?")[0].split(":")
            if len(core_info) >= 5:
                ip = core_info[0]
                port = core_info[1]
                protocol = core_info[2]
                cipher = core_info[3]
                obfs = core_info[4]
                return f"ssr_{ip}_{port}_{protocol}_{cipher}_{obfs}"
        
        # 4. Trojan节点
        elif node_link.startswith("trojan://"):
            # Trojan格式：trojan://密码@IP:端口?参数
            core_part = node_link.split("?")[0].replace("trojan://", "")
            pwd_part, addr_part = core_part.split("@")
            ip, port = addr_part.split(":")
            return f"trojan_{ip}_{port}_{pwd_part}"
        
        # 其他协议（按原始字符串去重）
        else:
            return f"other_{node_link}"
    
    except Exception:
        # 解析失败时，按原始字符串去重
        return f"error_{node_link}"

# ===================== 初始化请求会话 =====================
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

# ===================== 下载并解码单个订阅链接 =====================
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

# ===================== 核心逻辑（精准去重） =====================
def merge_all_subs():
    print(f"Current working directory: {os.getcwd()}")
    print(f"Script directory: {os.path.dirname(os.path.abspath(__file__))}")
    
    session = init_request_session()
    # 关键：用字典存储（key=唯一标识，value=节点链接）
    node_key_map = {}
    
    for url in SUBSCRIBE_RAW_URLS:
        nodes = download_and_decode_sub(session, url)
        for node_link in nodes:
            # 生成唯一key
            unique_key = get_node_unique_key(node_link)
            # 仅保留首次出现的节点（去重）
            if unique_key not in node_key_map:
                node_key_map[unique_key] = node_link
    
    # 提取去重后的节点
    all_unique_nodes = list(node_key_map.values())
    print(f"Total nodes before dedup: {sum(len(download_and_decode_sub(session, url)) for url in SUBSCRIBE_RAW_URLS)}")
    print(f"Total nodes after dedup: {len(all_unique_nodes)}")
    
    if not all_unique_nodes:
        print("No valid nodes found, exiting...")
        return
    
    # 生成最终内容
    merged_nodes_text = "\n".join(all_unique_nodes)
    final_base64 = base64.b64encode(merged_nodes_text.encode("utf-8")).decode("utf-8")

    # 存储文件
    script_dir = os.path.dirname(os.path.abspath(__file__))
    date_dir = os.path.join(script_dir, "Date")
    os.makedirs(date_dir, exist_ok=True)
    output_file = os.path.join(date_dir, "List.txt")
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_base64)
    
    print(f"File saved to: {output_file}")
    print(f"File size: {os.path.getsize(output_file)} bytes")

# ===================== 执行入口 =====================
if __name__ == "__main__":
    merge_all_subs()

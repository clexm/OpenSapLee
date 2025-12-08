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
# IP归属地查询接口（备选：https://ipinfo.io/{ip}/json）
IP_INFO_API = "http://ip-api.com/json/{ip}?lang=zh-CN"

# ===================== 工具函数：IP归属地查询 =====================
def get_ip_location(ip):
    """查询IP归属地，返回国家/地区名称"""
    try:
        session = requests.Session()
        response = session.get(IP_INFO_API.format(ip=ip), timeout=8)
        response.raise_for_status()
        data = response.json()
        if data.get("status") == "success":
            # 优先返回地区（如香港、台湾），否则返回国家
            region = data.get("regionName")
            country = data.get("country")
            # 特殊处理中国地区
            if country == "中国":
                if region in ["香港", "澳门", "台湾"]:
                    return region
                return "中国"
            return country
        return "未知"
    except Exception:
        return "未知"

# ===================== 工具函数：解析节点IP =====================
def get_node_ip(node_link):
    """解析节点链接，提取IP地址"""
    try:
        # VMess节点
        if node_link.startswith("vmess://"):
            link = node_link[8:]
            padding = len(link) % 4
            if padding != 0:
                link += "=" * (4 - padding)
            node_json = base64.b64decode(link).decode("utf-8", errors="ignore")
            node = json.loads(node_json)
            return node.get("add", "")
        
        # VLESS节点
        elif node_link.startswith("vless://"):
            core_part = node_link.split("?")[0].replace("vless://", "")
            addr_part = core_part.split("@")[1]
            ip = addr_part.split(":")[0]
            return ip
        
        # SSR节点
        elif node_link.startswith("ssr://"):
            link = node_link[6:]
            padding = len(link) % 4
            if padding != 0:
                link += "=" * (4 - padding)
            ssr_info = base64.b64decode(link).decode("utf-8", errors="ignore")
            core_info = ssr_info.split("?")[0].split(":")
            if len(core_info) >= 1:
                return core_info[0]
        
        # Trojan节点
        elif node_link.startswith("trojan://"):
            core_part = node_link.split("?")[0].replace("trojan://", "")
            addr_part = core_part.split("@")[1]
            ip = addr_part.split(":")[0]
            return ip
        
        return ""
    except Exception:
        return ""

# ===================== 工具函数：节点精准去重Key =====================
def get_node_unique_key(node_link):
    """生成节点唯一标识（去重用）"""
    try:
        if node_link.startswith("vmess://"):
            link = node_link[8:]
            padding = len(link) % 4
            if padding != 0:
                link += "=" * (4 - padding)
            node_json = base64.b64decode(link).decode("utf-8", errors="ignore")
            node = json.loads(node_json)
            return f"vmess_{node.get('add', '')}_{node.get('port', '')}_{node.get('id', '')}_{node.get('scy', '')}_{node.get('net', '')}"
        
        elif node_link.startswith("vless://"):
            core_part = node_link.split("?")[0].replace("vless://", "")
            id_part, addr_part = core_part.split("@")
            ip, port = addr_part.split(":")
            return f"vless_{ip}_{port}_{id_part}"
        
        elif node_link.startswith("ssr://"):
            link = node_link[6:]
            padding = len(link) % 4
            if padding != 0:
                link += "=" * (4 - padding)
            ssr_info = base64.b64decode(link).decode("utf-8", errors="ignore")
            core_info = ssr_info.split("?")[0].split(":")
            if len(core_info) >= 5:
                ip = core_info[0]
                port = core_info[1]
                protocol = core_info[2]
                cipher = core_info[3]
                obfs = core_info[4]
                return f"ssr_{ip}_{port}_{protocol}_{cipher}_{obfs}"
        
        elif node_link.startswith("trojan://"):
            core_part = node_link.split("?")[0].replace("trojan://", "")
            pwd_part, addr_part = core_part.split("@")
            ip, port = addr_part.split(":")
            return f"trojan_{ip}_{port}_{pwd_part}"
        
        else:
            return f"other_{node_link}"
    except Exception:
        return f"error_{node_link}"

# ===================== 工具函数：重命名节点 =====================
def rename_node(node_link, location, location_counter):
    """
    重命名节点
    :param node_link: 原始节点链接
    :param location: IP归属地（如中国、香港、美国）
    :param location_counter: 地区计数器（字典）
    :return: 重命名后的节点链接
    """
    try:
        # 更新计数器
        location_counter[location] = location_counter.get(location, 0) + 1
        # 生成两位序号（01、02...10）
        seq = f"{location_counter[location]:02d}"
        new_name = f"{location}{seq}"

        # VMess节点重命名（修改ps字段）
        if node_link.startswith("vmess://"):
            link = node_link[8:]
            padding = len(link) % 4
            if padding != 0:
                link += "=" * (4 - padding)
            node_json = base64.b64decode(link).decode("utf-8", errors="ignore")
            node = json.loads(node_json)
            node["ps"] = new_name  # 修改备注名
            # 重新编码
            new_node_json = json.dumps(node, ensure_ascii=False).encode("utf-8")
            new_link = "vmess://" + base64.b64encode(new_node_json).decode("utf-8")
            return new_link
        
        # 其他协议暂不修改（VLESS/SSR/Trojan可按需扩展）
        # 若需支持其他协议，可参考VMess逻辑解析并修改备注字段
        return node_link
    except Exception:
        return node_link

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

# ===================== 核心逻辑（去重+重命名） =====================
def merge_all_subs():
    print(f"Current working directory: {os.getcwd()}")
    print(f"Script directory: {os.path.dirname(os.path.abspath(__file__))}")
    
    session = init_request_session()
    node_key_map = {}  # 去重字典
    location_counter = {}  # 地区计数器
    
    # 第一步：下载并去重节点
    for url in SUBSCRIBE_RAW_URLS:
        nodes = download_and_decode_sub(session, url)
        for node_link in nodes:
            unique_key = get_node_unique_key(node_link)
            if unique_key not in node_key_map:
                node_key_map[unique_key] = node_link
    
    # 第二步：解析IP+重命名节点
    renamed_nodes = []
    for node_link in node_key_map.values():
        # 提取节点IP
        ip = get_node_ip(node_link)
        if not ip:
            renamed_nodes.append(node_link)
            continue
        # 查询IP归属地
        location = get_ip_location(ip)
        # 重命名节点
        new_node_link = rename_node(node_link, location, location_counter)
        renamed_nodes.append(new_node_link)
    
    print(f"Total nodes before dedup: {sum(len(download_and_decode_sub(session, url)) for url in SUBSCRIBE_RAW_URLS)}")
    print(f"Total nodes after dedup: {len(renamed_nodes)}")
    print(f"Location counter: {location_counter}")
    
    if not renamed_nodes:
        print("No valid nodes found, exiting...")
        return
    
    # 生成最终内容
    merged_nodes_text = "\n".join(renamed_nodes)
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

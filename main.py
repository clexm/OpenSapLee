#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
高级版订阅合并工具
- 异步并发抓取
- 智能 Base64 修复
- 精准节点去重
- 保留所有有效节点，避免漏掉
- 日志清晰
"""

import os
import json
import asyncio
import aiohttp
import base64
import traceback

# ===================== 配置 =====================
SUBSCRIBE_URLS = [
    "https://www.xrayvip.com/free.txt",
    "https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/v2ray.txt",
    "https://raw.githubusercontent.com/aiboboxx/v2rayfree/main/v2",
    "https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub",
    "https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list.txt",
    "https://raw.githubusercontent.com/free-nodes/v2rayfree/main/v2",
    "https://raw.githubusercontent.com/free18/v2ray/refs/heads/main/v.txt",
    "https://www.xrayvip.com/free.txt",
]

TIMEOUT = aiohttp.ClientTimeout(total=20)

# ===================== 工具函数 =====================

def safe_b64decode(text: str) -> str:
    """安全 Base64 解码，失败直接返回原文"""
    text = text.strip()
    if not text:
        return ""
    padding = len(text) % 4
    if padding:
        text += "=" * (4 - padding)
    try:
        return base64.b64decode(text).decode("utf-8", errors="ignore")
    except Exception:
        return text


def get_node_key(node: str) -> str:
    """生成节点唯一 key，用于去重"""
    try:
        if node.startswith("vmess://"):
            raw = safe_b64decode(node[8:])
            data = json.loads(raw)
            return "vmess_{add}_{port}_{id}_{net}".format(
                add=data.get("add", ""),
                port=data.get("port", ""),
                id=data.get("id", ""),
                net=data.get("net", "")
            )
        elif node.startswith("vless://"):
            base = node.split("?")[0].replace("vless://", "")
            uid, addr = base.split("@")
            host, port = addr.split(":")
            return f"vless_{host}_{port}_{uid}"
        elif node.startswith("trojan://"):
            base = node.split("?")[0].replace("trojan://", "")
            pwd, addr = base.split("@")
            host, port = addr.split(":")
            return f"trojan_{host}_{port}_{pwd}"
        elif node.startswith("ssr://"):
            raw = safe_b64decode(node[6:])
            base = raw.split("?")[0]
            arr = base.split(":")
            if len(arr) >= 5:
                return f"ssr_{arr[0]}_{arr[1]}_{arr[2]}_{arr[3]}_{arr[4]}"
        return node
    except Exception:
        return node


def extract_nodes(text: str):
    """
    从文本中提取所有有效节点
    - 支持 Base64 或纯文本
    - 节点可被空格或换行分隔
    """
    decoded = safe_b64decode(text)
    nodes = []
    for line in decoded.replace("\r", " ").split():
        line = line.strip()
        if line.startswith(("vmess://", "vless://", "trojan://", "ssr://")):
            nodes.append(line)
    return nodes


# ===================== 异步抓取 =====================
async def fetch(session, url):
    try:
        async with session.get(url) as resp:
            text = await resp.text()
            return text
    except Exception:
        traceback.print_exc()
        return ""


# ===================== 主流程 =====================
async def merge_all():
    print("开始异步抓取订阅...\n")

    async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
        tasks = [fetch(session, url) for url in SUBSCRIBE_URLS]
        contents = await asyncio.gather(*tasks)

    all_nodes = []
    for content in contents:
        if not content:
            continue
        nodes = extract_nodes(content)
        all_nodes.extend(nodes)

    print(f"原始节点总数（合并后）：{len(all_nodes)}")

    # 精准去重
    dedup_map = {}
    for node in all_nodes:
        key = get_node_key(node)
        if key not in dedup_map:
            dedup_map[key] = node

    final_nodes = list(dedup_map.values())
    print(f"去重后节点总数：{len(final_nodes)}")

    # 生成最终文本和 Base64
    merged_text = "\n".join(final_nodes)
    b64_output = base64.b64encode(merged_text.encode()).decode()

    # 保存文件
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Date")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "List.txt")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(b64_output)

    print(f"\n输出文件路径: {output_path}")
    print(f"文件大小: {os.path.getsize(output_path)} bytes")


# ===================== 启动入口 =====================
if __name__ == "__main__":
    asyncio.run(merge_all())

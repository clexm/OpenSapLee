import base64
import requests
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ===================== 核心配置（你的7个Raw链接） =====================
SUBSCRIBE_RAW_URLS = [
    "https://www.xrayvip.com/free.txt",
    "https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/v2ray.txt",
    "https://raw.githubusercontent.com/aiboboxx/v2rayfree/main/v2",
    "https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub",
    "https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list.txt",
    "https://raw.githubusercontent.com/free-nodes/v2rayfree/main/v2",
    "https://raw.githubusercontent.com/free18/v2ray/refs/heads/main/v.txt",
]

# 网络请求配置
TIMEOUT = 15  # 每个链接的超时时间（秒）
RETRY_TIMES = 3  # 网络请求重试次数

# ===================== 初始化请求会话（防网络波动） =====================
def init_request_session():
    """初始化带重试机制的requests会话"""
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
        
        # 修复Base64填充符
        padding = len(raw_content) % 4
        if padding != 0:
            raw_content += "=" * (4 - padding)
        
        # 解码（兼容Base64/明文）
        try:
            decoded_content = base64.b64decode(raw_content).decode("utf-8", errors="ignore")
        except base64.binascii.Error:
            decoded_content = raw_content
        
        # 拆分节点并去空
        nodes = [node.strip() for node in decoded_content.split() if node.strip()]
        return nodes
    
    except Exception:
        return []

# ===================== 合并所有订阅源并按指定逻辑保存 =====================
def merge_all_subs():
    session = init_request_session()
    all_unique_nodes = set()
    
    # 遍历所有订阅链接，合并节点
    for url in SUBSCRIBE_RAW_URLS:
        nodes = download_and_decode_sub(session, url)
        if nodes:
            all_unique_nodes.update(nodes)
    
    # 无有效节点则直接返回
    if not all_unique_nodes:
        return
    
    # 生成最终Base64内容
    merged_nodes_text = "\n".join(all_unique_nodes)
    final_base64 = base64.b64encode(merged_nodes_text.encode("utf-8")).decode("utf-8")

    # 按你的逻辑存储文件
    script_dir = os.path.dirname(os.path.abspath(__file__))
    date_dir = os.path.join(script_dir, "Date")
    os.makedirs(date_dir, exist_ok=True)
    output_file = os.path.join(date_dir, "List.txt")
    
    # 覆盖保存文件
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_base64)

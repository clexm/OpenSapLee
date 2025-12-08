import json
import base64
import re
import os
import requests
from urllib.parse import urlparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time

# ===================== 核心配置（保留你的URL列表） =====================
urls = [
    "https://www.xrayvip.com/free.txt",
    "https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/v2ray.txt",
    "https://raw.githubusercontent.com/aiboboxx/v2rayfree/main/v2",
    "https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub",
    "https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list.txt",
    "https://raw.githubusercontent.com/free-nodes/v2rayfree/main/v2",
    "https://raw.githubusercontent.com/free18/v2ray/refs/heads/main/v.txt",
]
# 【关键修改】移除测活相关配置（GitHub Actions 无代理）
# ===================== 初始化配置 =====================
session = requests.Session()
retry = Retry(total=2, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount("http://", adapter)
session.mount("https://", adapter)

unique_nodes = {}  # 存储唯一节点
final_nodes = []   # 最终节点（去重+重命名）

# ===================== 1. 下载订阅并去重（保留你的逻辑） =====================
def download_and_dedup_subs():
    unique_lines = set()
    for url in urls:
        try:
            # 【适配GitHub】增加超时和重试，跳过无法访问的源
            response = session.get(url, timeout=15, allow_redirects=True)
            response.raise_for_status()
            content = response.text
            
            lines = [line.strip() for line in content.splitlines() if line.strip()]
            unique_lines.update(lines)
            
            print(f"成功获取 {url}，新增 {len(lines)} 行，当前总唯一行：{len(unique_lines)}")
            
        except Exception as e:
            print(f"获取 {url} 失败：{str(e)}")
            continue
    
    parse_unique_lines(unique_lines)

# ===================== 2. 解析节点+重命名（移除测活） =====================
def parse_unique_lines(unique_lines):
    country_count = {}
    for line in unique_lines:
        if not line.startswith("vmess://"):
            final_nodes.append(line)  # 保留非VMess节点（如SSR/Trojan）
            continue
        
        try:
            link = line[8:]
            padding = len(link) % 4
            if padding != 0:
                link += "=" * (4 - padding)
            
            node_json = base64.b64decode(link).decode("utf-8", errors="ignore")
            node = json.loads(node_json)
            
            # 去重key
            node_key = f"{node.get('add')}_{node.get('port')}_{node.get('scy', '')}"
            if node_key not in unique_nodes:
                unique_nodes[node_key] = node
                # 重命名节点（保留逻辑，但跳过IP查询失败的情况）
                ip_info = get_ip_info(node.get('add'))
                if ip_info:
                    node['ps'] = rename_node(node, ip_info, country_count)
                # 重新编码为vmess链接
                node_json_new = json.dumps(node, ensure_ascii=False).encode("utf-8")
                vmess_link = f"vmess://{base64.b64encode(node_json_new).decode('utf-8')}"
                final_nodes.append(vmess_link)
                print(f"[新增节点] {node.get('ps', '未知节点')}")
            else:
                print(f"[重复节点跳过] {node.get('ps', '未知节点')}")
                
        except Exception as e:
            print(f"解析节点失败：{str(e)}")
            final_nodes.append(line)  # 解析失败也保留原链接

# ===================== 辅助函数：IP查询（容错） =====================
def get_ip_info(ip):
    try:
        # 【适配GitHub】使用备用IP查询接口（避免ip-api被屏蔽）
        rq = session.get(f"https://ipinfo.io/{ip}/json", timeout=8)
        ip_info = rq.json()
        # 适配ipinfo.io的返回格式
        return {
            "country": ip_info.get("country", "未知国家"),
            "org": ip_info.get("org", "未知运营商"),
            "status": "success"
        }
    except Exception as e:
        print(f"IP查询失败 {ip}：{str(e)}")
        return None

def rename_node(node, ip_info, country_count):
    country = ip_info.get('country', '未知国家')
    org = re.split(',| ', ip_info.get('org', '未知运营商'))[0]
    country_count[country] = country_count.get(country, 0) + 1
    seq = f"{country_count[country]:02d}"
    new_name = f"{country} {seq} {org}"
    return new_name

# ===================== 3. 保存文件（适配GitHub路径） =====================
def generate_and_save_sub():
    # 【关键】GitHub Actions中，确保输出路径可访问，且即使无节点也生成文件
    # 方案1：输出到GitHub Workspace（默认工作目录，可被Actions捕获）
    script_dir = os.getenv("GITHUB_WORKSPACE", os.path.dirname(os.path.abspath(__file__)))
    date_dir = os.path.join(script_dir, "Date")
    os.makedirs(date_dir, exist_ok=True)
    output_file = os.path.join(date_dir, "List.txt")
    
    # 排序（保留你的逻辑）
    sorted_lines = sorted(final_nodes, key=lambda x: (x.startswith("http"), x))
    combined_content = "\n".join([line + "," for line in sorted_lines]) + "\n"
    
    # 强制生成文件（即使为空）
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(combined_content)
    
    print(f"\n整合完成：共 {len(final_nodes)} 条配置（去重后）")
    print(f"文件保存路径：{output_file}")
    # 打印路径详情（用于排查）
    print(f"当前工作目录：{os.getcwd()}")
    print(f"Date文件夹内容：{os.listdir(date_dir) if os.path.exists(date_dir) else '无'}")

# ===================== 主流程 =====================
if __name__ == "__main__":
    print("===== 开始执行（适配GitHub Actions） =====")
    download_and_dedup_subs()
    generate_and_save_sub()
    print("===== 执行完成 =====")

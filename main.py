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
# 定义URL列表（可自行添加/删除VPN文件地址）
urls = [
    "https://www.xrayvip.com/free.txt",
    "https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/v2ray.txt",
    "https://raw.githubusercontent.com/aiboboxx/v2rayfree/main/v2",
    "https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub",
    "https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list.txt",
    "https://raw.githubusercontent.com/free-nodes/v2rayfree/main/v2",
    "https://raw.githubusercontent.com/free18/v2ray/refs/heads/main/v.txt",
]
test_url = "https://www.google.com/generate_204"  # 测活地址
timeout = 5  # 测活超时时间（秒）
proxy = {"http": "socks5://127.0.0.1:10808", "https": "socks5://127.0.0.1:10808"}  # 本地V2Ray代理

# ===================== 初始化配置 =====================
# requests重试机制
session = requests.Session()
retry = Retry(total=2, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount("http://", adapter)
session.mount("https://", adapter)

# 存储唯一节点（去重key：IP+端口+加密方式）
unique_nodes = {}
# 存储最终有效节点
alive_nodes = []

# ===================== 1. 下载订阅并去重（保留你的下载逻辑） =====================
def download_and_dedup_subs():
    unique_lines = set()  # 你的去重逻辑（按行去重）
    for url in urls:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            content = response.text
            
            # 按行拆分内容并去除空白行（你的逻辑）
            lines = [line.strip() for line in content.splitlines() if line.strip()]
            unique_lines.update(lines)  # 自动去重（集合特性）
            
            print(f"成功获取 {url}，新增 {len(lines)} 行，当前总唯一行：{len(unique_lines)}")
            
        except Exception as e:
            print(f"获取 {url} 失败：{str(e)}")
            continue
    
    # 解析唯一行，提取VMess节点并进一步去重（基于IP+端口+加密方式）
    parse_unique_lines(unique_lines)

# ===================== 2. 解析节点（VMess专属） =====================
def parse_unique_lines(unique_lines):
    for line in unique_lines:
        if not line.startswith("vmess://"):
            continue  # 只处理VMess节点
        try:
            # 处理base64编码填充符缺失问题
            link = line[8:]  # 去掉vmess://前缀
            padding = len(link) % 4
            if padding != 0:
                link += "=" * (4 - padding)
            
            # 解码并解析节点JSON
            node_json = base64.b64decode(link).decode("utf-8", errors="ignore")
            node = json.loads(node_json)
            
            # 生成去重key（IP+端口+加密方式，更精准去重）
            node_key = f"{node.get('add')}_{node.get('port')}_{node.get('scy', '')}"
            if node_key not in unique_nodes:
                unique_nodes[node_key] = node
                print(f"[新增唯一节点] {node.get('ps', '未知节点')}")
            else:
                print(f"[重复节点跳过] {node.get('ps', '未知节点')}")
                
        except json.JSONDecodeError:
            print(f"[解析失败] 节点JSON格式错误：{line[:30]}...")
        except Exception as e:
            print(f"[解析异常] {str(e)}")

# ===================== 3. 节点测活（访问google 204） =====================
def test_node_liveness():
    country_count = {}  # 统计各国家节点数量（用于重命名）
    for node in unique_nodes.values():
        try:
            start_time = time.time()
            # 访问204地址测试连通性
            rq = session.get(test_url, proxies=proxy, timeout=timeout, verify=False)
            end_time = time.time()
            
            delay = int((end_time - start_time) * 1000)  # 延迟（毫秒）
            if rq.status_code == 204 and delay > 0:
                print(f"[测活成功] {node.get('ps', '未知节点')} - 延迟：{delay}ms")
                # 查询IP地理信息并重命名
                ip_info = get_ip_info(node.get('add'))
                if ip_info:
                    node['ps'] = rename_node(node, ip_info, country_count)
                alive_nodes.append(node)
            else:
                print(f"[测活失败] {node.get('ps', '未知节点')} - 状态码：{rq.status_code} 或 延迟≤0")
        except requests.exceptions.Timeout:
            print(f"[测活超时] {node.get('ps', '未知节点')} - 超过{timeout}秒")
        except requests.exceptions.ConnectionError:
            print(f"[连接失败] {node.get('ps', '未知节点')} - 代理不可用")
        except Exception as e:
            print(f"[测活异常] {node.get('ps', '未知节点')}：{str(e)}")

# ===================== 辅助函数：查询IP地理信息 =====================
def get_ip_info(ip):
    try:
        rq = session.get(f"http://ip-api.com/json/{ip}?lang=zh-CN", timeout=5)
        ip_info = rq.json()
        return ip_info if ip_info.get('status') == 'success' else None
    except Exception as e:
        print(f"[IP查询失败] {ip}：{str(e)}")
        return None

# ===================== 辅助函数：节点重命名（国家+序号+运营商） =====================
def rename_node(node, ip_info, country_count):
    country = ip_info.get('country', '未知国家')
    org = re.split(',| ', ip_info.get('org', '未知运营商'))[0]
    # 统计国家节点数量，生成两位序号
    country_count[country] = country_count.get(country, 0) + 1
    seq = f"{country_count[country]:02d}"
    new_name = f"{country} {seq} {org}"
    print(f"[重命名节点] {node.get('ps', '未知节点')} → {new_name}")
    return new_name

# ===================== 4. 生成订阅并保存（保留你的文件存储逻辑） =====================
def generate_and_save_sub():
    if not alive_nodes:
        print("[无有效节点] 无法生成订阅链接")
        return
    
    # 拼接有效节点为VMess链接
    tmp = []
    for node in alive_nodes:
        node_json = json.dumps(node, ensure_ascii=False).encode("utf-8")
        vmess_link = f"vmess://{base64.b64encode(node_json).decode('utf-8')}"
        tmp.append(vmess_link)
    
    # 按你的逻辑排序（非http链接优先，这里都是vmess，直接排序）
    sorted_lines = sorted(tmp, key=lambda x: (x.startswith("http"), x))
    # 按你的格式拼接（每行末尾加逗号）
    combined_content = "\n".join([line + "," for line in sorted_lines]) + "\n"
    
    # --------------------- 保留你的文件存储逻辑 ---------------------
    # 创建Date文件夹（位于脚本所在目录）
    script_dir = os.path.dirname(os.path.abspath(__file__))
    date_dir = os.path.join(script_dir, "Date")
    os.makedirs(date_dir, exist_ok=True)
    
    # 固定文件名（无时间戳，新文件覆盖旧文件）
    output_file = os.path.join(date_dir, "List.txt")
    
    # 保存文件（覆盖模式）
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(combined_content)
    
    print(f"\n已整合 {len(urls)} 个订阅源，去重+测活后共 {len(alive_nodes)} 条有效配置")
    print(f"结果已保存至：{output_file}")

# ===================== 主流程执行 =====================
if __name__ == "__main__":
    print("===== 开始执行：订阅下载→去重→解析→测活→重命名→保存 =====")
    download_and_dedup_subs()  # 下载+行级去重
    if unique_nodes:
        test_node_liveness()    # 节点测活
    generate_and_save_sub()    # 生成并保存（你的存储逻辑）
    print("===== 执行完成 =====")

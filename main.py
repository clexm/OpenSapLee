import os
import json
import base64
import requests
from urllib.parse import urlencode

# 定义URL列表（包含返回JSON的地址）
urls = [
      "https://www.xrayvip.com/free.txt",
      "https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/v2ray.txt",
      "https://raw.githubusercontent.com/aiboboxx/v2rayfree/main/v2",
      "https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub",
      "https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list.txt",
      "https://raw.githubusercontent.com/free-nodes/v2rayfree/main/v2",
      "https://raw.githubusercontent.com/free18/v2ray/refs/heads/main/v.txt",
]

# 有效节点协议（用于过滤）
VALID_PROTOCOLS = ("vmess", "vless", "trojan", "ss")
unique_nodes = set()
# --------------------- 核心函数：JSON转vmess链接 ---------------------
def vmess_json_to_link(vmess_dict):
    """将VMESS配置字典转为vmess://链接"""
    # 标准化VMESS字段（避免缺失字段导致解析失败）
    vmess_info = {
        "v": "2",
        "ps": vmess_dict.get("ps", "未命名节点"),  
        "add": vmess_dict.get("add", ""),         
        "port": str(vmess_dict.get("port", "")),  
        "id": vmess_dict.get("id", ""),
        "aid": str(vmess_dict.get("aid", "0")),
        "net": vmess_dict.get("net", "tcp"),
        "type": vmess_dict.get("type", "none"),
        "host": vmess_dict.get("host", ""),
        "path": vmess_dict.get("path", ""),
        "tls": vmess_dict.get("tls", ""),
        "sni": vmess_dict.get("sni", ""),
        "alpn": vmess_dict.get("alpn", "")
    }
    # 过滤空值
    vmess_info = {k: v for k, v in vmess_info.items() if v}
    # Base64编码生成vmess链接
    json_str = json.dumps(vmess_info, ensure_ascii=False)
    b64_str = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")
    return f"vmess://{b64_str}"

# --------------------- 遍历URL，解析内容 ---------------------
for url in urls:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        content = response.text.strip()

        # 情况1：内容是JSON（尝试解析）
        if content.startswith("{") and content.endswith("}"):
            try:
                json_data = json.loads(content)
                # 提取outbounds中的节点
                for outbound in json_data.get("outbounds", []):
                    protocol = outbound.get("protocol", "")
                    if protocol == "vmess":
                        # 解析VMESS节点
                        servers = outbound.get("settings", {}).get("servers", [])
                        for server in servers:
                            node_link = vmess_json_to_link(server)
                            unique_nodes.add(node_link)
                    elif protocol in ("vless", "trojan"):
                        # 解析VLESS/Trojan（简化示例，可按需扩展）
                        vnext = outbound.get("settings", {}).get("vnext", [])
                        for v in vnext:
                            address = v.get("address")
                            port = v.get("port")
                            user_id = v.get("users", [{}])[0].get("id")
                            if address and port and user_id:
                                # 生成VLESS链接（示例，需根据实际字段补充）
                                vless_params = {
                                    "id": user_id,
                                    "port": port,
                                    "address": address
                                }
                                vless_link = f"vless://{user_id}@{address}:{port}?{urlencode(vless_params)}"
                                unique_nodes.add(vless_link)
                print(f"成功解析JSON：{url}，提取节点数：{len(unique_nodes)}")
            except json.JSONDecodeError:
                # 不是标准JSON，按文本行解析
                pass

        # 情况2：内容是文本（每行一个节点链接）
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        for line in lines:
            if line.startswith(("vmess://", "vless://", "trojan://", "ss://")):
                unique_nodes.add(line)

        print(f"处理完成：{url}，累计唯一节点：{len(unique_nodes)}")

    except Exception as e:
        print(f"处理失败：{url} → {str(e)}")
        continue

# --------------------- 保存为V2rayN可识别的文本 ---------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
date_dir = os.path.join(script_dir, "Date")
os.makedirs(date_dir, exist_ok=True)
output_file = os.path.join(date_dir, "List.txt")

# 写入文件（每行一个节点链接）
with open(output_file, "w", encoding="utf-8") as f:
    f.write("\n".join(unique_nodes))

print(f"\n✅ 最终结果：")
print(f"- 有效节点总数：{len(unique_nodes)}")
print(f"- 保存路径：{output_file}")
print(f"\n📌 V2rayN导入方式：")
print(f"1. 订阅导入：file:///{output_file.replace('\\', '/')}")
print(f"2. 剪贴板导入：复制文件内容 → V2rayN → 右键分组 → 从剪贴板导入批量URL")

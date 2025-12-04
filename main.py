import os
import requests

# 定义URL列表（仅保留节点配置地址）
urls = [
      "https://www.xrayvip.com/free.txt",
      "https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/v2ray.txt",
      "https://raw.githubusercontent.com/aiboboxx/v2rayfree/main/v2",
      "https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub",
      "https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list.txt",
      "https://raw.githubusercontent.com/free-nodes/v2rayfree/main/v2",
      "https://raw.githubusercontent.com/free18/v2ray/refs/heads/main/v.txt",
]

# 定义有效节点前缀（V2rayN支持的格式）
VALID_PREFIXES = ("vmess://", "vless://", "trojan://", "ss://", "ssr://")
unique_nodes = set()

for url in urls:
    try:
        # 加请求头，避免被反爬
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        content = response.text
        
        # 按行拆分，仅保留有效节点配置
        for line in content.splitlines():
            line = line.strip()
            # 过滤空行 + 仅保留有效节点前缀的行
            if line and line.startswith(VALID_PREFIXES):
                unique_nodes.add(line)
        
        print(f"成功处理 {url}，当前累计唯一节点：{len(unique_nodes)}")
        
    except Exception as e:
        print(f"处理 {url} 失败：{str(e)}")
        continue

# 按类型排序，拼接内容（每行一个节点）
sorted_nodes = sorted(unique_nodes)
combined_content = "\n".join(sorted_nodes)

# 保存文件（脚本所在目录的Date文件夹）
script_dir = os.path.dirname(os.path.abspath(__file__))
date_dir = os.path.join(script_dir, "Date")
os.makedirs(date_dir, exist_ok=True)
output_file = os.path.join(date_dir, "List.txt")

with open(output_file, "w", encoding="utf-8") as f:
    f.write(combined_content)

print(f"\n最终结果：共整合 {len(unique_nodes)} 个有效节点")
print(f"文件路径：{output_file}")
print(f"\nV2rayN导入方式：")
print(f"1. 本地文件：file:///{output_file.replace('\\', '/')}")
print(f"2. 或复制文件内容，在V2rayN中「从剪贴板导入批量URL」")

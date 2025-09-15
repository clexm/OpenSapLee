import os
import requests
from urllib.parse import urlparse

# 定义URL列表（可自行添加/删除VPN文件地址）
urls = [
      "https://www.xrayvip.com/free.txt",
      "https://raw.githubusercontent.com/chengaopan/AutoMergePublicNodes/master/list_raw.txt",
      "https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/v2ray.txt",
      "https://raw.githubusercontent.com/aiboboxx/v2rayfree/main/v2",
      "https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub",
      "https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list.txt"
      "https://raw.githubusercontent.com/free-nodes/v2rayfree/main/v2"
      "https://raw.githubusercontent.com/free18/v2ray/refs/heads/main/v.txt"
]

# 使用集合存储唯一行（自动去重）
unique_lines = set()

for url in urls:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        content = response.text
        
        # 按行拆分内容并去除空白行
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        unique_lines.update(lines)  # 自动去重（集合特性）
        
        print(f"成功获取 {url}，新增 {len(lines)} 行，当前总唯一行：{len(unique_lines)}")
        
    except Exception as e:
        print(f"获取 {url} 失败：{str(e)}")
        continue

# 排序并拼接内容（非http链接优先）
sorted_lines = sorted(unique_lines, key=lambda x: (x.startswith("http"), x))
combined_content = "\n".join(sorted_lines) + "\n"

# --------------------- 文件存储逻辑 ---------------------
# 创建Date文件夹（位于脚本所在目录）
script_dir = os.path.dirname(os.path.abspath(__file__))
date_dir = os.path.join(script_dir, "Date")
os.makedirs(date_dir, exist_ok=True)

# 固定文件名（无时间戳，新文件覆盖旧文件）
output_file = os.path.join(date_dir, "List.txt")

# 保存文件（覆盖模式）
with open(output_file, "w", encoding="utf-8") as f:
    f.write(combined_content)

print(f"\n已整合 {len(urls)} 个文件，去重后共 {len(unique_lines)} 条配置")
print(f"结果已保存至：{output_file}")

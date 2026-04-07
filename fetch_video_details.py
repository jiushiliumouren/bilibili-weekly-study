"""
第二步：根据 BV 号列表获取视频详细信息（播放量、UP主、互动数据等）
用法：python fetch_video_details.py --input ./output/366bv.xlsx --output ./data/366.csv
"""

import pandas as pd
import requests
import time
import argparse
import os
from tqdm import tqdm
from requests.exceptions import RequestException

# ==================== 默认配置（可通过命令行覆盖） ====================
DEFAULT_INPUT = "./output/366bv.xlsx"      # 第一步生成的 BV 号 Excel 文件
DEFAULT_OUTPUT = "./data/366.csv"          # 输出 CSV 路径
DEFAULT_DELAY = 0.5                        # 请求间隔（秒）
DEFAULT_BV_COLUMN = "A"                    # BV 号所在列（字母或数字索引）
# ====================================================================

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
    'Referer': 'https://www.bilibili.com/v/popular/weekly',
}

def get_video_data(bvid, max_retries=3):
    """获取单个视频数据，返回字典或None"""
    url = f'https://api.bilibili.com/x/web-interface/view?bvid={bvid}'
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data.get('code') != 0:
                print(f"  API返回错误 {data.get('code')} for {bvid}")
                return None
            d = data['data']
            stat = d.get('stat', {})
            return {
                '标题': d.get('title', ''),
                'UP主': d.get('owner', {}).get('name', ''),
                '播放': stat.get('view', 0),
                '点赞': stat.get('like', 0),
                '投币': stat.get('coin', 0),
                '收藏': stat.get('favorite', 0),
                '评论': stat.get('reply', 0),
                'BV': bvid,
                '弹幕数': stat.get('danmaku', 0),
                '分享数': stat.get('share', 0),
                '视频时长(秒)': d.get('duration', 0),
                '发布时间': pd.to_datetime(d.get('pubdate', 0), unit='s') if d.get('pubdate') else '',
                '分P数量': d.get('videos', 1),
            }
        except (RequestException, KeyError, ValueError) as e:
            print(f"  尝试 {attempt+1}/{max_retries} 失败: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    return None

def read_bvids_from_excel(path, column='A'):
    """从Excel读取BV号"""
    df = pd.read_excel(path, header=None)
    # 将字母列转换为索引
    if isinstance(column, str) and column.isalpha():
        col_idx = ord(column.upper()) - ord('A')
    else:
        col_idx = int(column) if isinstance(column, int) else 0
    bvids = df.iloc[:, col_idx].dropna().astype(str).str.strip()
    # 确保以BV开头
    bvids = bvids.apply(lambda x: x if x.startswith('BV') else 'BV' + x)
    return bvids.tolist()

def main():
    parser = argparse.ArgumentParser(description="根据BV号获取B站视频详细信息")
    parser.add_argument('--input', type=str, default=DEFAULT_INPUT,
                        help=f'输入Excel文件路径（默认 {DEFAULT_INPUT}）')
    parser.add_argument('--output', type=str, default=DEFAULT_OUTPUT,
                        help=f'输出CSV文件路径（默认 {DEFAULT_OUTPUT}）')
    parser.add_argument('--delay', type=float, default=DEFAULT_DELAY,
                        help=f'请求间隔秒数（默认 {DEFAULT_DELAY}）')
    parser.add_argument('--bv-column', type=str, default=DEFAULT_BV_COLUMN,
                        help=f'BV号所在列，如 A 或 0（默认 {DEFAULT_BV_COLUMN}）')
    args = parser.parse_args()

    # 确保输出目录存在
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    # 读取BV号
    try:
        bvids = read_bvids_from_excel(args.input, args.bv_column)
    except Exception as e:
        print(f"读取Excel文件失败: {e}")
        return

    print(f"读取到 {len(bvids)} 个BV号")
    if not bvids:
        print("没有有效的BV号，退出")
        return

    # 获取数据
    results = []
    for bvid in tqdm(bvids, desc="获取视频数据"):
        data = get_video_data(bvid)
        if data:
            results.append(data)
        time.sleep(args.delay)

    # 保存结果为CSV
    if results:
        try:
            pd.DataFrame(results).to_csv(args.output, index=False, encoding='utf-8-sig')
            print(f"\n✅ 结果已保存至: {args.output}")
        except Exception as e:
            print(f"保存CSV文件失败: {e}")
    else:
        print("\n未获取到任何有效数据")

if __name__ == '__main__':
    main()
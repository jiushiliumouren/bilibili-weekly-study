"""
B站每周榜单BV号抓取工具
用法: python main.py --week 366
"""

import re
import time
import argparse
import pandas as pd
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from webdriver_manager.microsoft import EdgeChromiumDriverManager


def get_bv_ids(week_number, headless=False):
    """
    获取指定期数的B站每周榜单BV号
    :param week_number: 期数，如 367
    :param headless: 是否无头模式（不显示浏览器窗口）
    :return: BV号列表
    """
    url = f"https://www.bilibili.com/v/popular/weekly?num={week_number}"

    options = Options()
    if headless:
        options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )

    # 自动下载并匹配 EdgeDriver
    service = Service(EdgeChromiumDriverManager().install())
    driver = webdriver.Edge(service=service, options=options)

    try:
        driver.get(url)
        time.sleep(15)  # 等待动态内容加载，可根据网速调整
        html = driver.page_source
        bv_pattern = r'BV[a-zA-Z0-9]{10}'
        bv_ids = list(set(re.findall(bv_pattern, html)))
        bv_ids.sort()
        return bv_ids
    finally:
        driver.quit()


def save_to_excel(bv_ids, week_number, output_dir="."):
    """保存为Excel文件"""
    df = pd.DataFrame({
        'BV号': bv_ids,
        '序号': range(1, len(bv_ids) + 1)
    })
    excel_path = f"{output_dir}/{week_number}bv.xlsx"
    df.to_excel(excel_path, index=False, sheet_name=f'第{week_number}期')
    return excel_path


def main():
    parser = argparse.ArgumentParser(description="抓取B站每周榜单的BV号")
    parser.add_argument('--week', type=int, required=True, help='期数，例如 366')
    parser.add_argument('--output', type=str, default='.', help='输出目录，默认为当前目录')
    parser.add_argument('--headless', action='store_true', help='启用无头模式（不显示浏览器）')
    args = parser.parse_args()

    print(f"正在获取第 {args.week} 期...")
    bv_ids = get_bv_ids(args.week, headless=args.headless)
    print(f"共找到 {len(bv_ids)} 个BV号：")
    for bv in bv_ids:
        print(bv)

    if bv_ids:
        path = save_to_excel(bv_ids, args.week, output_dir=args.output)
        print(f"\n✅ 已保存到: {path}")
    else:
        print("⚠️ 未找到任何BV号，请检查网络或期数是否正确。")


if __name__ == "__main__":
    main()
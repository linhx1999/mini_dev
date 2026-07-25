#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 JSON 文件转换为 JSONL 文件。

支持三种输入格式：
  1. JSON 数组（最常见）            -> 每个元素作为一行输出
  2. JSON 单对象                   -> 整个对象作为一行输出
  3. JSON 对象包含一个数组字段      -> 该数组字段的每个元素作为一行输出

输出文件默认与输入文件同目录，文件名相同但扩展名为 .jsonl。
"""

import json
import os
import argparse
import sys


def extract_records(data):
    """从加载的 JSON 数据中提取待写入的记录列表。"""
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        # 寻找第一个值为列表的字段
        for key, value in data.items():
            if isinstance(value, list):
                print(f"检测到对象包含数组字段 '{key}'，共 {len(value)} 条记录")
                return value
        # 没有数组字段，把整个对象作为单条记录
        return [data]

    # 其他标量类型，作为单条记录
    return [data]


def json_to_jsonl(input_file, output_file=None):
    if not os.path.exists(input_file):
        print(f"错误: 输入文件不存在 {input_file}")
        sys.exit(1)

    # 默认输出到同目录，扩展名改为 .jsonl
    if output_file is None:
        base, _ = os.path.splitext(input_file)
        output_file = base + ".jsonl"

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    records = extract_records(data)

    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"输入文件: {input_file}")
    print(f"输出文件: {output_file}")
    print(f"写入记录数: {len(records)}")


def main():
    parser = argparse.ArgumentParser(
        description="将 JSON 文件转换为 JSONL 文件（默认输出到原目录）"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="输入 JSON 文件路径",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="输出 JSONL 文件路径（默认与输入文件同目录、同名但扩展名为 .jsonl）",
    )
    args = parser.parse_args()

    json_to_jsonl(args.input, args.output)


if __name__ == "__main__":
    main()

"""独立调用示例：不挂 MCP，直接用客户端类拉订单

运行前：
    1. 复制 .env.example 为 .env，填入你的 partnerId 和 secret
    2. pip install -r requirements.txt
    3. python examples/list_orders.py
"""
import os
import sys
import json

# 把 src 目录加入 import 路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from huacheng_client import HuachengClient


def main():
    # 可选：从 .env 文件加载环境变量（需要 pip install python-dotenv）
    # 也可以直接在系统环境变量里设置，或在这里手动传：
    # client = HuachengClient(partner_id="xxx", secret="xxx")
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # 没装 python-dotenv 也行，只要系统环境变量里有就行

    client = HuachengClient()

    print("=" * 50)
    print("拉取最近 10 条订单")
    print("=" * 50)

    data = client.list_orders(limit=10, ems="ALL")
    orders = data.get("listOrders", [])
    count = data.get("count", 0)

    print(f"总订单数：{count}，本次拉取：{len(orders)} 条\n")

    for i, o in enumerate(orders, 1):
        pay_user = o.get("payUser") or {}
        goods = o.get("goodsInfo") or {}
        pay_time = o.get("payTime") or {}
        ems_time = o.get("emsTime") or {}
        addr = o.get("address") or {}
        cp_list = addr.get("listCPInfo") or []
        cp = cp_list[0] if cp_list else {}

        buyer = pay_user.get("markName") or pay_user.get("nickname") or "未知"
        goods_name = goods.get("name", "未知商品")
        fee = (o.get("payFee") or 0) / 100  # 分转元
        pay_str = pay_time.get("str", "")
        ems_str = ems_time.get("str", "未发货")
        cp_name = cp.get("cpName", "")
        tracking = cp.get("code", "")

        print(f"{i}. {buyer} - {goods_name} - ¥{fee:.2f}")
        print(f"   下单：{pay_str}")
        print(f"   发货：{ems_str}" + (f" ({cp_name} {tracking})" if tracking else ""))
        print()


if __name__ == "__main__":
    main()

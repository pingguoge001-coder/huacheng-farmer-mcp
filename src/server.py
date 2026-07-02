"""花城农夫小程序 MCP Server

把花城开放 API 封装成 MCP 工具，挂到 Claude Desktop / CodeBuddy 后，
AI 可以直接帮你查订单、改库存、发货。

启动方式（开发者本地调试）：
    python src/server.py

正式挂载方式见 README.md「接入步骤」。
"""
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone

# 把同目录的 huacheng_client 加入 import 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from huacheng_client import HuachengClient

from mcp.server.fastmcp import FastMCP

# 中国时区，花城订单时间戳按东八区处理
CN_TZ = timezone(timedelta(hours=8))

mcp = FastMCP("huacheng-farmer")


def _client() -> HuachengClient:
    """每次调用时新建客户端，自动从环境变量读凭证"""
    return HuachengClient()


# ==================== 订单模块（5个工具） ====================


@mcp.tool()
def list_orders(
    limit: int = 50,
    ems: str = "ALL",
    days: int = 0,
) -> str:
    """获取花城农夫小程序的订单列表。

    参数：
        limit - 获取条数，默认 50，最多 500
        ems   - 发货状态过滤：ALL 全部 / NOSEND 未发货 / SEND 已发货
        days  - 只看最近 N 天的订单（按订单更新时间筛），0 表示不限制

    返回：JSON 字符串，含订单总数和精简后的订单列表
    （每条订单含：订单ID、买家、商品、金额、支付时间、发货时间、快递公司、快递单号、寄件人）
    """
    client = _client()
    now_ts = int(time.time())
    last_time = now_ts - days * 86400 if days > 0 else 0

    data = client.list_orders(
        skip=0,
        limit=min(limit, 500),
        ems=ems,
        supply_type="ALL",
        last_time=last_time,
        update_end_time=now_ts if days > 0 else 0,
    )

    orders = data.get("listOrders", [])
    simplified = []
    for o in orders:
        pay_user = o.get("payUser") or {}
        goods = o.get("goodsInfo") or {}
        addr = o.get("address") or {}
        cp_list = addr.get("listCPInfo") or []
        cp = cp_list[0] if cp_list else {}
        ems_time = o.get("emsTime") or {}
        send_info = o.get("sendInfo") or {}
        pay_time = o.get("payTime") or {}
        simplified.append({
            "order_id": o.get("id", ""),
            "buyer": pay_user.get("markName") or pay_user.get("nickname") or "",
            "goods": goods.get("name", ""),
            "fee_yuan": (o.get("payFee") or 0) / 100,  # 分转元
            "num": o.get("num", 0),
            "pay_time": pay_time.get("str", ""),
            "ems_time": ems_time.get("str", ""),
            "cp_name": cp.get("cpName", ""),
            "tracking_no": cp.get("code", ""),
            "sender": send_info.get("name", ""),
        })

    return json.dumps(
        {"count": data.get("count", 0), "orders": simplified},
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool()
def get_order(order_id: str) -> str:
    """查询某个订单的完整详情。

    参数：order_id - 订单 ID

    返回：JSON 字符串，含该订单的全部字段（地址、售后、商品、规格、寄件人、支付等）
    """
    client = _client()
    data = client.get_order(order_id)
    return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
def list_refunds(limit: int = 50, key: str = "") -> str:
    """获取售后订单列表。

    参数：
        limit - 获取条数，默认 50
        key   - 搜索关键字（买家名、商品名等），可选

    返回：JSON 字符串，含售后订单列表
    """
    client = _client()
    data = client.list_refunds(skip=0, limit=min(limit, 500), key=key, custom_type="REFUND")
    return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
def ship_order(order_id: str, cp_code: str, tracking_no: str) -> str:
    """给订单发货（录入快递单号）。

    参数：
        order_id    - 订单 ID
        cp_code     - 快递公司编码，常用：
                      SF 顺丰 / YTO 圆通 / ZTO 中通 / STO 申通
                      YUNDA 韵达 / JTSD 极兔 / JD 京东 / EMS / YZPY 邮政
                      完整列表见 docs/api-reference.md
        tracking_no - 快递单号

    返回：JSON 字符串，含接口执行结果
    """
    client = _client()
    data = client.ship_order(order_id, cp_code, tracking_no)
    return json.dumps(
        {"success": True, "order_id": order_id, "cp_code": cp_code, "tracking_no": tracking_no, "data": data},
        ensure_ascii=False,
        indent=2,
    )


# ==================== 商品模块（2个工具） ====================


@mcp.tool()
def list_goods(limit: int = 50, under: str = "SELL", key: str = "") -> str:
    """获取商品列表。

    参数：
        limit - 获取条数，默认 50
        under - 上下架状态：ALL 全部 / UNDER 下架 / SELL 在售（默认）
        key   - 搜索关键字，可选

    返回：JSON 字符串，含商品列表
    """
    client = _client()
    data = client.list_goods(skip=0, limit=min(limit, 500), under=under, source="ALL", key=key)
    return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
def update_inventory(
    goods_id: str,
    spec_code: str,
    num: int,
    prop_code: str = "",
    opt_type: int = 0,
) -> str:
    """更新商品库存。

    参数：
        goods_id  - 商品 ID（平台商品 ID）
        spec_code - 规格编码（支持平台规格 ID 和二方 Code）
        num       - 数量
        prop_code - 属性编码（规格含属性时必填），可选
        opt_type  - 0 追加（在现有库存上加 num）/ 1 修改（直接把库存改成 num），默认 0

    返回：JSON 字符串，含接口执行结果
    """
    client = _client()
    data = client.update_inventory(goods_id, spec_code, num, prop_code, opt_type)
    return json.dumps(
        {"success": True, "goods_id": goods_id, "spec_code": spec_code, "num": num, "data": data},
        ensure_ascii=False,
        indent=2,
    )


if __name__ == "__main__":
    # 本地调试用 stdio 模式启动
    mcp.run(transport="stdio")

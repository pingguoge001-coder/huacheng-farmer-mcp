"""花城农夫小程序开放平台 API 客户端

封装签名算法 + HTTPS 调用，所有 14 个接口共用一个 call_api。
凭证从环境变量读取，不硬编码。

用法：
    from huacheng_client import HuachengClient
    client = HuachengClient()  # 自动读 HUACHENG_PARTNER_ID / HUACHENG_SECRET
    orders = client.list_orders(limit=10)
"""
import hashlib
import json
import os
import random
import string
import time
import urllib.request
import urllib.error
from typing import Any


# API 基础地址
API_BASE = "https://open.nfgood.com/api/v1/"

# 请求超时（秒），花城接口偶有慢响应
TIMEOUT = 120


class HuachengClient:
    """花城农夫小程序开放 API 客户端

    凭证从环境变量读取：
        HUACHENG_PARTNER_ID  - 合作者（店铺）ID
        HUACHENG_SECRET      - 签名密钥

    两者都在花城小程序后台「开放能力」里申请。
    """

    def __init__(self, partner_id: str = None, secret: str = None):
        # 参数没传就从环境变量读
        self.partner_id = partner_id or os.getenv("HUACHENG_PARTNER_ID")
        self.secret = secret or os.getenv("HUACHENG_SECRET")
        if not self.partner_id or not self.secret:
            raise RuntimeError(
                "缺少凭证。请设置环境变量 HUACHENG_PARTNER_ID 和 HUACHENG_SECRET，"
                "或在初始化时传入 partner_id / secret。"
                "\n申请方式：登录花城农夫小程序后台 → 开放能力 → 获取 partnerId 和 secret。"
            )

    def _sign(self, method: str, nonce_str: str, timestamp: int, body_json: str) -> str:
        """花城签名算法：拼接固定顺序后做 MD5，再转大写。

        拼接格式（字段顺序不能变）：
            method={方法名}&nonceStr={随机串}&partnerId={合作者ID}&timestamp={时间戳}&{请求体JSON}&{secret}
        """
        sign_str = (
            f"method={method}&nonceStr={nonce_str}"
            f"&partnerId={self.partner_id}&timestamp={timestamp}"
            f"&{body_json}&{self.secret}"
        )
        return hashlib.md5(sign_str.encode("utf-8")).hexdigest().upper()

    def call_api(self, method: str, body: dict) -> dict:
        """调用任意花城接口的通用方法。

        参数：
            method - 接口方法名，如 "listOrders"
            body   - 请求参数字典

        返回：
            接口返回的完整 JSON 字典。

        异常：
            RuntimeError - 凭证缺失或 API 返回 errors 字段
            urllib.error.URLError - 网络问题
        """
        api_url = API_BASE + method
        nonce_str = "".join(random.choices(string.ascii_letters + string.digits, k=16))
        timestamp = int(time.time())
        # 紧凑 JSON，避免空格影响签名
        body_json = json.dumps(body, separators=(",", ":"), ensure_ascii=False)

        sign = self._sign(method, nonce_str, timestamp, body_json)

        req = urllib.request.Request(api_url, data=body_json.encode("utf-8"), method="POST")
        # 公共 Header（每个接口都要）
        for k, v in {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "partnerId": self.partner_id,
            "nonceStr": nonce_str,
            "timestamp": str(timestamp),
            "sign": sign,
        }.items():
            req.add_header(k, v)

        resp = urllib.request.urlopen(req, timeout=TIMEOUT)
        result = json.loads(resp.read().decode("utf-8"))

        # 花城错误返回格式：{"errors": [{"message": "..."}]}
        if result.get("errors"):
            msgs = [e.get("message", "未知错误") for e in result["errors"]]
            raise RuntimeError(f"花城 API 错误 ({method}): {'; '.join(msgs)}")

        return result

    # ==================== 订单模块 ====================

    def list_orders(
        self,
        skip: int = 0,
        limit: int = 50,
        ems: str = "ALL",
        supply_type: str = "ALL",
        last_time: int = 0,
        update_end_time: int = 0,
        order_id: str = "",
    ) -> dict:
        """获取订单列表

        参数：
            skip            - 跳过条数（分页用）
            limit           - 获取条数
            ems             - 发货状态：ALL 全部 / NOSEND 未发货 / SEND 已发货
            supply_type     - 发货类型：ALL 全部 / MINE 由我发货 / OTHER 他人发货
            last_time       - 获取此时间戳之后更新的订单（0 表示不限制）
            update_end_time - 获取此时间戳之前更新的订单（last_time > 0 时有效）
            order_id        - 指定订单 ID 查询（可选）

        返回：{"count": 总数, "listOrders": [...]}
        """
        body = {
            "skip": skip,
            "limit": limit,
            "ems": ems,
            "supplyType": supply_type,
            "lastTime": str(last_time),
        }
        if update_end_time:
            body["updateEndTime"] = update_end_time
        if order_id:
            body["orderId"] = order_id
        return self.call_api("listOrders", body).get("data", {})

    def get_order(self, order_id: str) -> dict:
        """获取订单详情

        参数：order_id - 订单 ID
        返回：订单完整信息字典
        """
        return self.call_api("orderInfo", {"orderId": order_id}).get("data", {})

    def list_refunds(
        self, skip: int = 0, limit: int = 50, key: str = "", custom_type: str = "REFUND"
    ) -> dict:
        """获取售后订单列表

        参数：
            skip        - 跳过条数
            limit       - 获取条数
            key         - 搜索关键字
            custom_type - 第一次传 REFUND，后续按返回结构传

        返回：售后订单数据
        """
        body = {"skip": skip, "limit": limit, "customType": custom_type}
        if key:
            body["key"] = key
        return self.call_api("refundOrders", body).get("data", {})

    def ship_order(self, order_id: str, cp_code: str, tracking_no: str, old_code: str = "") -> dict:
        """订单发货

        参数：
            order_id    - 订单 ID
            cp_code     - 快递公司编码，如 SF / YTO / ZTO（见 docs/api-reference.md 完整列表）
            tracking_no - 快递单号
            old_code    - 要修改的原单号，为空表示新增发货信息

        返回：接口返回的 data 字段
        """
        body = {"id": order_id, "cp": cp_code, "code": tracking_no}
        if old_code:
            body["oldCode"] = old_code
        return self.call_api("orderDelivery", body).get("data", {})

    # ==================== 商品模块 ====================

    def list_goods(
        self,
        skip: int = 0,
        limit: int = 50,
        under: str = "SELL",
        source: str = "ALL",
        key: str = "",
    ) -> dict:
        """获取商品列表

        参数：
            skip   - 跳过条数
            limit  - 获取条数
            under  - 上下架状态：ALL 全部 / UNDER 下架 / SELL 在售
            source - 产品来源：ALL / SELF / BIND / BIND_SIFT / AUTHER / SELF_AUTHER / UNKNOW
            key    - 搜索关键字

        返回：商品列表数据
        """
        body = {"skip": skip, "limit": limit, "under": under, "source": source}
        if key:
            body["key"] = key
        return self.call_api("listGoods", body).get("data", {})

    def get_goods(self, goods_id: str) -> dict:
        """获取商品详情

        参数：goods_id - 商品 ID
        返回：商品完整信息字典
        """
        return self.call_api("goodsInfo", {"goodsId": goods_id}).get("data", {})

    def update_inventory(
        self,
        goods_id: str,
        spec_code: str,
        num: int,
        prop_code: str = "",
        opt_type: int = 0,
    ) -> dict:
        """更新商品库存

        参数：
            goods_id  - 商品 ID（平台商品 ID）
            spec_code - 规格编码（支持平台规格 ID 和二方 Code）
            num       - 数量
            prop_code - 属性编码（规格含属性时必填）
            opt_type  - 0 追加 / 1 修改

        返回：接口返回的 data 字段
        """
        body = {
            "goodsId": goods_id,
            "specCode": spec_code,
            "num": num,
            "optType": opt_type,
        }
        if prop_code:
            body["propCode"] = prop_code
        return self.call_api("updateGoodsInventory", body).get("data", {})

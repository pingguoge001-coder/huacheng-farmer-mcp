"""花城云端商品只读查询：Python 3.10+，不需要额外依赖。"""
import argparse
import html
import json
import os
from pathlib import Path
import re
import sys
from datetime import datetime, timezone
from urllib.error import URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from huacheng_client import HuachengClient


def get_page(client, skip, limit, under):
    data = client.list_goods(skip=skip, limit=limit, under=under, source="ALL")
    if not isinstance(data, dict) or not isinstance(data.get("listGoods"), list):
        raise RuntimeError("商品接口返回结构异常，未确认读取成功。")
    return data["listGoods"]


def read_all(client, page_size=500):
    """全量分页后本地筛选，避免合集和其他商品来源漏查。"""
    goods = {}
    unknown_status = 0
    for page in range(1000):
        batch = get_page(client, page * page_size, page_size, "ALL")
        new_ids = 0
        for good in batch:
            good_id = good.get("id")
            if not good_id:
                raise RuntimeError("商品缺少 ID，不能确认分页完整性。")
            if good_id not in goods:
                goods[good_id] = good
                new_ids += 1
        if batch and not new_ids:
            raise RuntimeError("接口重复返回同一页，已停止，结果不能视为完整清单。")
        if len(batch) < page_size:
            for good in goods.values():
                if not isinstance(good.get("isUnder"), bool):
                    unknown_status += 1
            return list(goods.values()), unknown_status
    raise RuntimeError("分页超过上限，未确认商品清单完整。")


def text_detail(good):
    parts = []
    for item in good.get("listContent") or []:
        if item.get("type") == "CONTENT":
            value = re.sub(r"<br\s*/?>|</(?:p|div|h[1-6])>", "\n",
                           item.get("content") or "", flags=re.I)
            value = html.unescape(re.sub(r"<[^>]+>", "", value)).strip()
            if value:
                parts.append(value)
    return "\n\n".join(parts)


def yuan(value):
    return None if value is None else round(value / 100, 2)


def product(good):
    return {
        "id": good["id"],
        "name": good.get("name"),
        "is_under": good.get("isUnder"),
        "specs": [{
            "id": spec.get("id"),
            "name": spec.get("name"),
            "is_under": spec.get("isUnder"),
            "price_yuan": yuan(spec.get("price")),
            "supply_price_yuan": yuan(spec.get("supplyFee")),
            "variants": spec.get("propsList") or [],
        } for spec in good.get("specs") or []],
        "detail_text": text_detail(good),
        "detail_image_count": sum(
            item.get("type") == "IMAGE" for item in good.get("listContent") or []),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="只查询一条在售商品验证连接")
    parser.add_argument("--keywords", nargs="+", default=["充电宝", "移动电源", "耳机"])
    args = parser.parse_args(argv)
    missing = [key for key in ("HUACHENG_PARTNER_ID", "HUACHENG_SECRET")
               if not os.environ.get(key)]
    if missing:
        print("缺少云端环境变量：" + "、".join(missing), file=sys.stderr)
        return 2
    try:
        client = HuachengClient()
        if args.check:
            batch = get_page(client, 0, 1, "SELL")
            if not batch or batch[0].get("isUnder") is not False or not batch[0].get("id"):
                raise RuntimeError("未取得可确认在售的商品，连接检查未通过。")
            print(json.dumps({"connected": True, "id": batch[0]["id"],
                              "name": batch[0].get("name")}, ensure_ascii=False))
            return 0
        goods, unknown = read_all(client)
        matched = []
        for good in goods:
            names = [good.get("name") or ""]
            names.extend(spec.get("name") or "" for spec in good.get("specs") or [])
            if good.get("isUnder") is False and any(
                    word.casefold() in name.casefold()
                    for word in args.keywords for name in names):
                matched.append(product(good))
        print(json.dumps({
            "queried_at_utc": datetime.now(timezone.utc).isoformat(),
            "source": "花城实时 listGoods 接口",
            "scanned_goods": len(goods),
            "unknown_status_count": unknown,
            "keywords": args.keywords,
            "matched_goods_count": len(matched),
            "note": "按商品名称和 SKU 名称筛选；合集保留全部规格。仅提取详情文字，图片参数未读取。数量与预期不符时继续核查，不按预期数量截断。",
            "goods": matched,
        }, ensure_ascii=False, indent=2))
        return 0
    except (URLError, RuntimeError, ValueError, TypeError) as error:
        message = str(error)
        for key in ("HUACHENG_PARTNER_ID", "HUACHENG_SECRET"):
            value = os.environ.get(key)
            if value:
                message = message.replace(value, "[已隐藏]")
        print("读取未完成：" + message, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

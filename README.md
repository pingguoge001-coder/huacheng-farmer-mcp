# 花城农夫小程序 MCP Server

把「花城农夫」小程序的开放 API 封装成 MCP（Model Context Protocol）工具，挂到 Claude Desktop / CodeBuddy 后，AI 就能直接帮你查订单、发货、改库存。

## 能干什么

挂上之后，在对话里直接用自然语言指挥 AI：

- "查一下最近的订单"
- "昨天有哪些未发货的？"
- "把订单 xxx 发顺丰，单号 SF1234567890"
- "商品 xxx 的库存还有多少？"
- "把商品 xxx 的库存改成 50"
- "最近有哪些售后申请？"

AI 会自动调对应工具，拉数据、改数据，不用你手动登后台。

---

## 前置条件

1. **花城农夫小程序的开放能力凭证**（每个店铺一套，互不通用）
   - `partnerId` - 合作者（店铺）ID
   - `secret` - 签名密钥
   - **申请方式**：登录花城农夫小程序后台 → 开放能力 → 获取
   - ⚠️ 不要用别人的凭证。每家店铺的凭证不同，用错会调到别人的订单。

2. **Python 3.10+**

3. **支持 MCP 的客户端**（任选其一）：
   - Claude Desktop
   - CodeBuddy
   - 其他兼容 MCP 的客户端

---

## 接入步骤（3 步）

### 第 1 步：克隆仓库 + 装依赖

```bash
git clone <你的仓库地址>
cd huacheng-farmer-mcp
pip install -r requirements.txt
```

### 第 2 步：配置凭证

在仓库根目录创建 `.env` 文件（**不要提交到 git，已在 .gitignore 里忽略**）：

```env
HUACHENG_PARTNER_ID=你的partnerId
HUACHENG_SECRET=你的secret
```

### 第 3 步：挂到 MCP 客户端

**Claude Desktop** — 编辑配置文件：
- macOS：`~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows：`%APPDATA%\Claude\claude_desktop_config.json`

**CodeBuddy** — 编辑 `~/.workbuddy/mcp.json`

配置内容：

```json
{
  "mcpServers": {
    "huacheng-farmer": {
      "command": "python",
      "args": ["<仓库绝对路径>/src/server.py"],
      "env": {
        "HUACHENG_PARTNER_ID": "你的partnerId",
        "HUACHENG_SECRET": "你的secret"
      }
    }
  }
}
```

> 也可以不在配置里写 env，让 server 自动读 `.env` 文件——但把凭证直接写在 MCP 配置的 env 字段里更稳，不受工作目录影响。

重启客户端后，AI 就能用这 7 个工具了。

---

## 可用的 7 个工具

### 订单模块

| 工具 | 作用 | 关键参数 |
|---|---|---|
| `list_orders` | 拉订单列表 | `limit` 条数 / `ems` 发货状态 / `days` 最近N天 |
| `get_order` | 查订单详情 | `order_id` |
| `list_refunds` | 拉售后订单 | `limit` / `key` 搜索关键字 |
| `ship_order` | 订单发货 | `order_id` / `cp_code` 快递编码 / `tracking_no` 单号 |

### 商品模块

| 工具 | 作用 | 关键参数 |
|---|---|---|
| `list_goods` | 拉商品列表 | `limit` / `under` 上下架 / `key` 搜索 |
| `update_inventory` | 改库存 | `goods_id` / `spec_code` / `num` / `opt_type` 0追加1修改 |

### 快递公司编码速查（`ship_order` 用）

| 编码 | 公司 | 编码 | 公司 |
|---|---|---|---|
| SF | 顺丰 | YTO | 圆通 |
| ZTO | 中通 | STO | 申通 |
| YUNDA | 韵达 | JTSD | 极兔 |
| JD | 京东 | EMS | EMS |
| YZPY | 邮政 | DBKD | 德邦 |

完整列表见 [`docs/api-reference.md`](docs/api-reference.md)。

---

## 不挂在 MCP 里也能用

不想挂 MCP，只想当普通 Python 库用：

```python
from huacheng_client import HuachengClient

client = HuachengClient()  # 自动读环境变量
orders = client.list_orders(limit=10, ems="NOSEND")
print(f"有 {orders.get('count', 0)} 单未发货")
```

也可以参考 `examples/list_orders.py`。

---

## 项目结构

```
huacheng-farmer-mcp/
├── README.md                  ← 你在看的这个
├── requirements.txt           ← Python 依赖
├── .env.example               ← 凭证示例（复制成 .env 填真实值）
├── .gitignore                 ← 忽略 .env / __pycache__ 等
├── docs/
│   └── api-reference.md       ← 花城 14 个接口的完整文档
├── src/
│   ├── huacheng_client.py     ← API 客户端（签名+请求，可独立用）
│   └── server.py              ← MCP server 入口（封装 7 个工具）
└── examples/
    └── list_orders.py         ← 独立调用示例
```

---

## 常见问题

**Q：凭证从哪里拿？**
A：登录花城农夫小程序后台 → 开放能力。每个店铺一套，不要用别人的。

**Q：挂上后 AI 调不动？**
A：检查三件事：① Python 能在命令行跑通（`python src/server.py` 不报错）；② 凭证填对了；③ 客户端重启过。

**Q：能查别人店铺的订单吗？**
A：不能。凭证跟店铺绑定，用谁的 partnerId 就只能查谁家。

**Q：价格单位？**
A：花城接口返回的金额单位是「分」，工具已自动除以 100 转成「元」。

---

## License

MIT

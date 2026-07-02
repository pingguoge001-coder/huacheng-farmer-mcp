# 花城农夫小程序开放 API 文档

> 基础地址：`https://open.nfgood.com/api/v1/` + 方法名
> 传输方式：HTTPS + POST + JSON（UTF-8）
> 签名算法：MD5 转大写

---

## 一、通用规则

### 公共 Header（每个接口都要带）

| Header | 说明 |
|---|---|
| `partnerId` | 合作者（店铺）ID，开通开放能力时获得 |
| `nonceStr` | 16 位随机字符串 |
| `timestamp` | 请求时间戳（秒） |
| `sign` | 签名字符串 |
| `Content-Type` | `application/json` |

### 签名算法

拼接字符串格式（字段顺序不能变）：

```
method={方法名}&nonceStr={nonceStr}&partnerId={partnerId}&timestamp={timestamp}&{请求参数的JSON字符串}&{secret}
```

对拼接后的字符串做 MD5，再转大写，就是 `sign` 的值。

### 返回格式

```json
// 成功
{ "data": { ... } }

// 失败
{ "errors": [{ "message": "错误原因" }] }
```

---

## 二、订单模块

### 1. listOrders — 获取订单列表

**URL：** `POST /api/v1/listOrders`

**请求参数：**

| 字段 | 类型 | 说明 |
|---|---|---|
| skip | int | 跳过条数（分页） |
| limit | int | 获取条数 |
| ems | string | 发货状态：`ALL` / `NOSEND` 未发货 / `SEND` 已发货 |
| supplyType | string | 发货类型：`ALL` / `MINE` 由我发货 / `OTHER` 他人发货 |
| lastTime | string | 获取此时间戳之后更新的订单 |
| updateEndTime | int | 获取此时间戳之前更新的订单（lastTime > 0 时有效） |
| orderId | string | 指定订单 ID（可选） |

**返回：** `{ "count": 总数, "listOrders": [...] }`

订单字段速览：
- `address` - 收件地址信息
- `address.listCPInfo[]` - 快递信息（含快递单号、公司编码、公司名、时间）
- `customInfo` - 售后信息（申请时间、完成时间、金额、原因、状态、拒绝原因）
- `goodsinfo` - 商品信息
- `specInfo` - 规格信息
- `sendInfo` - 寄件人信息
- `payFee` - 支付金额（**单位：分**，使用时除以 100 转元）
- `payState` - 支付状态
- `payTime` - 支付时间
- `emsTime` - 发货时间
- `takeType` / `takeState` / `takeTime` - 自提相关
- `tplExts` - 下单扩展信息

### 2. orderInfo — 获取订单详情

**URL：** `POST /api/v1/orderInfo`

**请求参数：** `orderId` - 订单 ID

**返回：** 字段与订单列表中单条订单相同

### 3. orderDelivery — 订单发货

**URL：** `POST /api/v1/orderDelivery`

**请求参数：**

| 字段 | 说明 |
|---|---|
| id | 订单 ID |
| cp | 快递公司编码（见下方编码表） |
| code | 快递单号 |
| oldCode | 要修改的原单号，为空表示新增 |

### 4. refundOrders — 获取售后订单

**URL：** `POST /api/v1/refundOrders`

**请求参数：**

| 字段 | 说明 |
|---|---|
| skip | 跳过条数 |
| limit | 获取条数 |
| key | 搜索关键字 |
| customType | 第一次传 `REFUND`，后续按返回结构传 |

---

## 三、商品模块

### 5. listGoods — 获取商品列表

**URL：** `POST /api/v1/listGoods`

**请求参数：**

| 字段 | 说明 |
|---|---|
| skip | 跳过条数 |
| limit | 获取条数 |
| under | 上下架状态：`ALL` / `UNDER` 下架 / `SELL` 在售 |
| source | 产品来源：`ALL` / `SELF` 自己上架 / `BIND` 绑定 / `BIND_SIFT` 农夫精选上架 / `AUTHER` 授权给我的 / `SELF_AUTHER` 授权且自己上架 / `UNKNOW` |
| key | 搜索关键字 |

### 6. goodsInfo — 获取商品详情

**URL：** `POST /api/v1/goodsInfo`

**请求参数：** `goodsId` - 商品 ID

**返回：** 商品完整信息，含 `availableBegin` / `availableEnd`（开售/停售时间）等

### 7. updateGoodsInventory — 更新商品库存

**URL：** `POST /api/v1/updateGoodsInventory`

**请求参数：**

| 字段 | 说明 |
|---|---|
| goodsId | 商品 ID（平台商品 ID） |
| specCode | 规格编码（支持平台规格 ID 和二方 Code） |
| propCode | 属性编码（规格含属性时必填，支持平台 Code 和二方编码） |
| optType | `0` 追加 / `1` 修改 |
| num | 数量 |

---

## 四、商品上架模块（MCP 未封装，文档备查）

### 8. addGoods — 笔记转商品

**URL：** `POST /api/v1/addGoods`

**功能：** 用户跳转到接口返回的链接后自动关联对应商品。

**请求参数：**

| 字段 | 说明 |
|---|---|
| name | 商品标题 |
| logo | 商品 LOGO |
| contents | 图文内容数组，元素类型：`IMAGE` / `VIDEO` / `CONTENT` |
| specs | 规格信息，含 `name` / `logoUrl` / `retailFee` 零售价 / `supplyFee` 供货价 / `props` 属性（价格单位：分） |

**返回：** `noteToGoods` 字段，为小程序跳转链接，可通过 `wx.navigateToMiniProgram` 跳转

### 9. syncGoods — 同步商品到草稿箱

**URL：** `POST /api/v1/syncGoods`

**请求参数：** 与 `addGoods` 相同（name、logo、contents、specs）

**功能：** 将商品同步到草稿箱

---

## 五、ERP 对接模块（MCP 未封装，文档备查）

### 10. setRelationErp — 关联合作商

**URL：** `POST /api/v1/setRelationErp`

**功能：** 设置 ERP 合作商与帮会的关联关系，关联后才能收到帮会的订单通知。

**请求参数：** `erpId` - ERP 合作商 ID（联系客服获取）

**说明：** 使用帮会 API key 和 secret 调用；帮会重置 key/secret 后需重新绑定。

### 11. 主动推送协议（测试中）

该功能尚在测试阶段，需联系客服获得 API key 和密钥，并提供公司 logo、名称、接收通知的 URL。

**推送方式：** 系统通过 POST 向第三方推送 JSON 数据，第三方收到后需返回字符串 `"success"`，否则系统会按规则继续推送（最多 10 次）。

**推送数据格式：**

| 字段 | 说明 |
|---|---|
| orderId | 订单 ID |
| groupKey | 帮会 API key |
| changeType | 变更类型：`1` 新订单 / `2` 售后申请或状态变更 / `3` 订单地址修改 / `4` 发货信息变更 |

---

## 六、快递公司编码表

`orderDelivery` 接口的 `cp` 字段用以下编码：

| 编码 | 快递公司 |
|---|---|
| SF | 顺丰 |
| YTO | 圆通 |
| ZTO | 中通 |
| STO | 申通 |
| HTKY | 百世汇通 |
| YUNDA | 韵达 |
| JD | 京东 |
| JTSD | 极兔速递 |
| ZJS | 宅急送 |
| GTO | 国通 |
| HHTT | 天天 |
| FAST | 快捷 |
| EMS | EMS |
| POSTB | 邮政小包 |
| YZPY | 邮政快递 |
| UC | 优速 |
| DBKD | 德邦 |
| JIUYE | 九曳供应链 |
| ZHONGYOU | 众邮 |
| ANE | 安能 |
| PJ | 品骏 |
| NONE | 自定义 |

---

## 七、测试信息

文档提供了测试用的 `partnerId` 和 `secret`，测试环境不校验 `timestamp`，方便调试。

申请正式凭证：登录花城农夫小程序后台 → 开放能力 → 获取。

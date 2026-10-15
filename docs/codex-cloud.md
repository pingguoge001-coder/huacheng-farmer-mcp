# 在 Codex 云端读取花城商品

本仓库已包含接口文档和调用程序。准备云端环境后，可直接使用商品查询命令，不必先挂载 MCP。

## 创建环境

1. 在 Codex 新任务中选择“云端 → 选择环境 → 创建环境”。
2. 选择 GitHub 仓库 `pingguoge001-coder/huacheng-farmer-mcp`，分支 `main`。
3. 使用 Python 3.10 或更新版本。下面的商品查询只使用 Python 标准库，无须安装额外软件包。
4. 允许环境访问互联网，并在允许的域名中添加 `open.nfgood.com`。
5. 配置以下两个环境变量。真实值只填入受保护的云端环境配置，不提交到本公开仓库：
   - `HUACHENG_PARTNER_ID`：已有花城店铺 Partner ID。
   - `HUACHENG_SECRET`：对应店铺签名密钥。
6. 两个值必须能由 Python 程序读取，因为签名需要在程序中计算。仅允许域名或仅设置代理代填的请求头不能代替这两个环境变量。
7. 现有客户端不会自动加载 `.env` 文件；在环境设置里配置变量即可，不需要上传含真实值的 `.env`。
8. 执行下方连接检查，检查通过后发布环境；在新任务中再执行连接检查确认可用。

## 连接检查

在仓库根目录运行：

```bash
python examples/cloud_goods.py --check
```

成功时输出 `connected: true`、一条实时在售商品的 ID 和名称。缺少变量、网络不通、签名失败或返回结构异常都会失败退出，不能把这些情况记为已连通。

## 获取在售充电宝和耳机

```bash
python examples/cloud_goods.py --keywords 充电宝 移动电源 耳机
```

程序会全量分页读取所有来源的商品，再按在售状态及商品/SKU名称筛选，保留合集全部规格。JSON 包含查询时间、扫描数量、匹配数量、详情文字、价格和规格；金额已从分换算为元。

需要保存结果时：

```bash
python examples/cloud_goods.py --keywords 充电宝 移动电源 耳机 > goods-result.json
```

若用户认为当前相关在售商品共有六款，实际返回不同数量时继续检查合集、具体规格和关键词，不得人为只取六条或用历史存档补齐。未知状态单独计数。详情图片中的参数尚未读取，不能声称完整识别所有图片。

## 接口信息

- 基础地址：`https://open.nfgood.com/api/v1/`
- 查询方法：`listGoods`，HTTPS POST。
- 常用参数：`under=ALL`、`source=ALL`、`skip`、`limit`、`key`。
- 在售状态：`isUnder=false`。SKU 有独立上下架状态，选购时也要检查。
- 价格：`specs[].price` 单位为分。
- 文字详情：`listContent[]` 中 `type=CONTENT` 的 `content`。
- 签名及其他接口：见 [api-reference.md](api-reference.md)。
- 云端环境官方说明：https://developers.openai.com/codex/environments/cloud-environments

## 排查

- 缺少变量：核对变量名称及是否对当前新任务生效；不打印变量的值。
- 网络失败：核对环境允许的目标域名、环境是否已重新发布，并从新任务验证。
- 签名失败：核对店铺 Partner ID 与 Secret 是否匹配、是否有前后空格、系统时间是否准确。
- 安装 MCP：仅使用商品命令不需要；如需运行 `src/server.py`，再安装 `requirements.txt`。
- 连接检查仅验证一条实时商品；完整商品清单是否成功必须以全量命令的结果为准。

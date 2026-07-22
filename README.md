# 中国电商 CSV 乱码修复器

专门处理淘宝、天猫、京东、拼多多等后台导出的 CSV：自动识别 UTF-8、UTF-8 BOM、GB18030 以及逗号、Tab、分号、竖线分隔符，统一输出 Excel 可直接打开的 UTF-8 BOM CSV。

它解决的具体问题：中文乱码、Excel 打开列挤在一起、平台导出分隔符不同。工具不会上传数据，不连接网络，不修改原文件，并在列数不一致时失败关闭。

## 运行

```bash
python3 csv_encoding_fixer.py examples/taobao-gb18030.csv fixed.csv --json
```

或安装 wheel：

```bash
python3 -m pip install china_ecom_csv_encoding_fixer-1.2.0-py3-none-any.whl
ecom-csv-fix orders.csv fixed.csv
```

不熟悉命令行时，可把单个 CSV 拖到 `run-windows.bat` 或 `run-macos.command` 上。启动器会在原文件旁生成 `原文件名-fixed.csv`，不会覆盖原文件或已存在的修复结果。Windows 需要 Python Launcher（`py -3`）或 `python`，macOS 需要 `python3`。

## GitHub Action

在公开或私有仓库中自动检查 CSV（数据只在 GitHub runner 内处理）：

```yaml
- uses: zhailong8845-art/china-ecom-csv-encoding-fixer@v1.3.0
  with:
    input: exports
    output: fixed-csv
    batch: "true"
```

Action 会生成 `csv-encoding-audit.json`，输出 `processed`、`failed` 和 `report`，并在任何文件格式错误或输出冲突时使 job 失败。固定价安装服务为 **RMB 39 / USD 5**：针对一个客户有权提供的公开仓库，交付最小 workflow、合成 CSV 验证和一次复检；不接受真实订单、凭据或付款信息。

整目录批量修复（最多 100 个 CSV，输出逐文件 JSON 证据）：

```bash
ecom-csv-fix platform-exports/ fixed/ --batch --json > batch-audit.json
```

批量模式只读取输入目录第一层的 `.csv` 文件。坏文件不会生成部分输出，也不会阻止其他合格文件完成；只要有一个文件失败，命令退出码就是 `2`，审计 JSON 会记录具体文件和原因。

[查看两份真实编码/分隔符示例的批量审计结果](examples/batch-audit.json)。

输出示例：

```json
{
  "source_encoding": "gb18030",
  "source_delimiter": ";",
  "output_encoding": "utf-8-sig",
  "rows": 3,
  "columns": 4
}
```

## 支持边界

- 输入编码：UTF-8、UTF-8 BOM、GB18030（覆盖 GBK）。
- 输入分隔符：逗号、Tab、分号、竖线。
- 输出：默认 UTF-8 BOM；可用 `--output-encoding gb18030`。
- 保留引号内逗号、换行和中文。
- 不猜测或修复缺失字段；行列数不一致时不生成部分结果。
- 批量模式最多处理 100 个文件，并对每个成功或失败项留下审计记录。
- 默认拒绝覆盖任何已存在输出；只有明确传入 `--force` 才允许替换。

## 测试

```bash
python3 -m unittest -v
```

## 商品信息

- 商品标题：中国电商 CSV 乱码与分隔符一键修复器
- 建议价格：USD 5 / RMB 39
- 交付内容：完整源码、可安装 wheel、示例 CSV、终端演示、测试和 MIT License。
- 定制服务：如平台使用特殊编码或不规则表头，可购买一次映射/清洗服务；只需脱敏表头，不接收账号、密码、Cookie 或支付信息。

MIT License。

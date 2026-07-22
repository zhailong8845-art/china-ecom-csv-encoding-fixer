# 中国电商 CSV 乱码修复器

专门处理淘宝、天猫、京东、拼多多等后台导出的 CSV：自动识别 UTF-8、UTF-8 BOM、GB18030 以及逗号、Tab、分号、竖线分隔符，统一输出 Excel 可直接打开的 UTF-8 BOM CSV。

它解决的具体问题：中文乱码、Excel 打开列挤在一起、平台导出分隔符不同。工具不会上传数据，不连接网络，不修改原文件，并在列数不一致时失败关闭。

## 运行

```bash
python3 csv_encoding_fixer.py examples/taobao-gb18030.csv fixed.csv --json
```

或安装 wheel：

```bash
python3 -m pip install china_ecom_csv_encoding_fixer-1.0.0-py3-none-any.whl
ecom-csv-fix orders.csv fixed.csv
```

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

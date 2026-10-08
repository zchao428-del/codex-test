# 镜室圆度补偿自动化工具 · v0.1

面向 Z 向等截面入子，建立 360 点数据到候选补偿轮廓的可复核流程。Python 3.10+，仅标准库。

```sh
python -m roundness examples/synthetic_oval.csv examples/config.json output/demo
python -m unittest discover -s tests -v
```

示例是人工生成的二阶谐波，不是用户实测数据。输出 CSV、闭合 DXF 多段线、带输入 SHA256 的 JSON 报告。输出目录必须为空。

## 目录

|路径|职责|
|---|---|
|roundness/pipeline.py|输入校验、补偿计算、坐标转换、CSV/DXF/报告输出|
|roundness/__main__.py|命令行入口|
|examples/|可重现的合成输入与参数|
|tests/|公式、非法输入与文件输出验证|
|docs/requirements.md|需求与实施阶段|
|docs/contracts.md|数据和 UG 接口约定|
|.github/workflows/tests.yml|自动测试|

首版完成数值处理闭环。图片识别、原生 Excel 读取、GUI、Windows 独立 EXE 尚未实现；Excel 可导出约定 CSV 使用。实际补偿方向、系数需用同基准实测与试模验证。UG10.0 导入需现场验证，当前不修改入子实体。

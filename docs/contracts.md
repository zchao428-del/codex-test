# 输入输出契约 v1.0

## 输入 CSV
UTF-8（接受 BOM），逗号分隔，精确表头 `angle_deg,radial_error_um`。
360行整数角度0..359，一角一点，可乱序；不包含360°闭合重复点。
误差单位 μm，正数表示相对指定固定基准径向向外，必须是径向量而非直径量。绝对半径或图片像素不能直接填入。固定基准应已由测量流程确定。

## JSON 参数
全部必填，拒绝未知字段。

|字段|含义|
|---|---|
|nominal_radius_mm|原入子名义半径，正数|
|gain|0..1逆向补偿比例；原型系数，不代表实测响应|
|mode|bidirectional 或 remove_only|
|removal_direction|radius_decrease（外圆芯子去料）或 radius_increase（内圆型腔去料）；双向模式下不参与计算|
|z_mm|轮廓所在局部Z高度，毫米|
|max_compensation_um|允许的绝对补偿上限，超出报错，不截断|

## 计算定义
令 e 为测量径向误差，s=e-mean(e)，初始 Δr=-gain*s。
双向模式直接输出 Δr。
单向减小半径：Δr'=Δr-max(Δr)；单向增大半径：Δr'=Δr-min(Δr)。
单向平移保留补偿形状但改变平均尺寸，不能同时承诺尺寸恢复。
所有模式的逆向关系是原型假设，须试模验证；无中心拟合，PV指标不能称为标准最小区域圆度。

r=nominal_radius_mm+Δr/1000；x=r*cosθ，y=r*sinθ。+Z看向原点时逆时针，0°=+X，90°=+Y。原点为用户定义局部基准，不自动对齐 UG WCS。

## 输出
- compensated_profile.csv：angle_deg,radial_error_um,compensation_um,radius_mm,x_mm,y_mm,z_mm；360行。
- compensated_profile.dxf：ASCII DXF AC1015，单位毫米，闭合 LWPOLYLINE，360顶点，以闭合标志连接359°和0°，Z为统一elevation。
- report.json：参数、输入哈希、固定基准径向PV、补偿范围、候选未验证状态及限制。

## UG10.0 边界
文件层交接，当前不提供 NXOpen/自动实体修改。DXF是折线不是精确光滑曲面；导入兼容性未现场验证。需检查单位、0/90/180/270点、Z与基准一致，检查接缝、折线与样条拟合偏差，再用于Z向轮廓延伸及入子修改。CSV为通用XYZ交换数据，不承诺UG原生CSV导入。多截面/锥面/断开圆周不在当前处理范围。

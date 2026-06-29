# 基于联邦学习的中风患者风险预警系统

## 项目简介

本项目是一个基于联邦学习（Federated Learning）的中风患者风险预警系统，采用 **FedAvg** 聚合算法，模拟多家医院在不共享原始患者数据的前提下，协同训练中风风险预测模型，有效保护患者隐私。

系统采用前后端分离架构，后端基于 Flask，前端基于 Vue 3 + Element Plus，提供完整的患者管理、风险预测、模型训练和数据可视化功能。

## 技术栈

### 后端
- **框架**: Flask 3.0
- **数据库**: MySQL
- **机器学习**: scikit-learn (Logistic Regression)
- **联邦学习**: FedAvg 聚合算法
- **跨域**: Flask-CORS

### 前端
- **框架**: Vue 3 + Vite
- **UI 组件库**: Element Plus
- **图表**: ECharts
- **路由**: Vue Router 4
- **HTTP 请求**: Axios

## 功能特性

### 1. 用户认证
- 登录/登出功能
- JWT 会话管理

### 2. 患者管理
- 患者信息录入与编辑
- 患者列表查询
- 按医院分组管理

### 3. 中风风险预测
- 输入患者基本信息（性别、年龄、高血压、心脏病等）
- 实时预测中风风险概率
- 风险等级划分（低/中/高风险）

### 4. 联邦学习训练
- 支持多家医院模拟训练
- FedAvg 加权聚合
- 训练过程实时监控
- 多轮训练精度对比

### 5. 数据可视化
- 仪表盘统计概览
- 训练准确率趋势图
- 风险分布统计图
- 混淆矩阵展示

## 项目结构

```
├── app.py                  # Flask 后端主入口
├── config.py               # 系统配置文件
├── init_db.py              # 数据库初始化脚本
├── requirements.txt        # Python 依赖包
├── brain_stroke.csv        # 示例数据集
├── stroke_system.sql       # 数据库建表脚本
├── models/
│   ├── __init__.py
│   └── federated_model.py  # 联邦学习核心模型
├── routes/
│   ├── __init__.py
│   ├── auth.py             # 认证路由
│   ├── patient.py          # 患者管理路由
│   └── prediction.py       # 预测与训练路由
├── utils/
│   ├── __init__.py
│   ├── db.py               # 数据库工具
│   └── preprocess.py       # 数据预处理
└── frontend/               # 前端项目
    ├── src/
    │   ├── api/            # API 接口
    │   ├── assets/         # 静态资源
    │   ├── router/         # 路由配置
    │   ├── views/          # 页面组件
    │   ├── App.vue
    │   └── main.js
    ├── index.html
    ├── package.json
    └── vite.config.js
```

## 快速开始

### 环境要求
- Python 3.9+
- Node.js 16+
- MySQL 5.7+

### 1. 克隆项目
```bash
git clone https://github.com/xiaoxinxiaoxinxx/AI-.git
cd AI-
```

### 2. 后端部署

#### 安装依赖
```bash
pip install -r requirements.txt
```

#### 配置数据库
1. 创建 MySQL 数据库 `stroke_system`
2. 导入 `stroke_system.sql` 初始化表结构
3. 修改 `config.py` 中的数据库配置：
```python
MYSQL_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '你的密码',
    'database': 'stroke_system',
}
```

#### 启动后端服务
```bash
python app.py
```
服务启动在 http://localhost:5000

### 3. 前端部署

#### 安装依赖
```bash
cd frontend
npm install
```

#### 启动开发服务器
```bash
npm run dev
```
前端运行在 http://localhost:5173

#### 构建生产版本
```bash
npm run build
```

## 联邦学习算法说明

### FedAvg 算法
系统采用 **Federated Averaging (FedAvg)** 算法进行模型聚合：

1. **本地训练**: 每家医院在本地数据上训练 Logistic Regression 模型
2. **参数上传**: 各医院仅上传模型参数（权重和偏置），不上传原始数据
3. **加权聚合**: 服务器按各医院数据量加权平均，更新全局模型
4. **下发更新**: 将更新后的全局模型参数下发给各医院
5. **多轮迭代**: 重复上述过程，直到模型收敛

### 模型评估指标
- 准确率 (Accuracy)
- 精确率 (Precision)
- 召回率 (Recall)
- F1 分数

## 预测特征说明

| 特征 | 说明 | 取值范围 |
|------|------|----------|
| gender | 性别 | 0=女, 1=男 |
| age | 年龄 | 数值 |
| hypertension | 高血压 | 0=无, 1=有 |
| heart_disease | 心脏病 | 0=无, 1=有 |
| married | 婚姻状况 | 0=未婚, 1=已婚 |
| work_type | 工作类型 | 0-4 编码 |
| residence_type | 居住类型 | 0=农村, 1=城市 |
| glucose_level | 血糖水平 | 数值 |
| bmi | 体质指数 | 数值 |
| smoking_status | 吸烟状态 | 0-3 编码 |

## API 接口

### 认证
- `POST /api/auth/login` - 用户登录

### 患者管理
- `GET /api/patients` - 获取患者列表
- `POST /api/patients` - 新增患者
- `PUT /api/patients/<id>` - 更新患者信息
- `DELETE /api/patients/<id>` - 删除患者

### 预测与训练
- `POST /api/prediction/predict` - 中风风险预测
- `POST /api/train/start` - 开始联邦训练
- `GET /api/train/status` - 获取训练状态
- `GET /api/model/evaluate` - 获取模型评估结果

## 许可证

本项目仅供学习研究使用。

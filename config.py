# ============================================
# 系统配置文件
# ============================================

# MySQL 数据库配置 (Navicat连接使用)
MYSQL_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '',          # 改成你自己的MySQL密码
    'database': 'stroke_system',
    'charset': 'utf8mb4',
}

# Flask 配置
SECRET_KEY = 'stroke-federated-learning-secret-key-2024'
DEBUG = True
HOST = '0.0.0.0'
PORT = 5000

# 联邦学习配置
FEDERATED_CONFIG = {
    'n_hospitals': 3,              # 模拟医院数量
    'n_rounds': 10,                # 联邦训练轮次
    'test_size': 0.2,              # 测试集比例
    'random_state': 42,            # 随机种子
}

# CSV文件路径
CSV_PATH = 'brain_stroke.csv'
# ============================================
# 基于联邦学习的中风患者风险预警系统
# Flask 后端主入口
# ============================================
import os
import sys
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

from config import SECRET_KEY, DEBUG, HOST, PORT
from routes.auth import auth_bp
from routes.patient import patient_bp
from routes.prediction import prediction_bp


def create_app():
    app = Flask(__name__, static_folder='frontend/dist', static_url_path='')
    app.secret_key = SECRET_KEY
    app.config['JSON_AS_ASCII'] = False

    # 跨域
    CORS(app, supports_credentials=True, origins=['http://localhost:5173', 'http://localhost:8080'])

    # 注册蓝图
    app.register_blueprint(auth_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(prediction_bp)

    # 前端静态文件服务
    @app.route('/')
    def serve_frontend():
        dist_path = os.path.join(app.root_path, 'frontend', 'dist')
        if os.path.exists(os.path.join(dist_path, 'index.html')):
            return send_from_directory(dist_path, 'index.html')
        return jsonify({
            'code': 200,
            'message': '中风患者风险预警系统API',
            'version': '1.0.0'
        })

    @app.route('/<path:path>')
    def serve_static(path):
        dist_path = os.path.join(app.root_path, 'frontend', 'dist')
        if os.path.exists(os.path.join(dist_path, path)):
            return send_from_directory(dist_path, path)
        if os.path.exists(os.path.join(dist_path, 'index.html')):
            return send_from_directory(dist_path, 'index.html')
        return {'code': 404, 'message': 'Not Found'}, 404

    return app


if __name__ == '__main__':
    app = create_app()

    print("=" * 60)
    print("  基于联邦学习的中风患者风险预警系统")
    print("  后端服务启动中...")
    print(f"  地址: http://localhost:{PORT}")
    print("=" * 60)

    # 首次启动时加载数据并初始化模型
    try:
        from models.federated_model import get_model
        print("[初始化] 加载脑卒中数据集...")
        model = get_model()
        print("[初始化] 数据加载完成，模型就绪")
    except Exception as e:
        print(f"[警告] 模型初始化失败: {e}")
        print("[提示] 请先访问 /api/train 触发联邦训练")

    app.run(host=HOST, port=PORT, debug=DEBUG)
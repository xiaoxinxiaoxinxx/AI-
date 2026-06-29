# ============================================
# 用户认证路由
# ============================================
import hashlib
from flask import Blueprint, request, jsonify, session
from utils.db import execute_query

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/api/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    username = data.get('username', '')
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'code': 400, 'message': '用户名和密码不能为空'})

    # MD5加密
    pwd_hash = hashlib.md5(password.encode('utf-8')).hexdigest()

    user = execute_query(
        "SELECT id, username, role, hospital_name, hospital_id FROM users WHERE username=%s AND password=%s",
        (username, pwd_hash),
        fetch_one=True
    )

    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        session['hospital_id'] = user['hospital_id'] or 0
        return jsonify({
            'code': 200,
            'message': '登录成功',
            'data': {
                'id': user['id'],
                'username': user['username'],
                'role': user['role'],
                'hospital_name': user['hospital_name'],
                'hospital_id': user['hospital_id'] or 0
            }
        })
    else:
        return jsonify({'code': 401, 'message': '用户名或密码错误'})


@auth_bp.route('/api/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    username = data.get('username', '')
    password = data.get('password', '')
    hospital_name = data.get('hospital_name', '')

    if not username or not password:
        return jsonify({'code': 400, 'message': '用户名和密码不能为空'})

    existing = execute_query(
        "SELECT id FROM users WHERE username=%s", (username,), fetch_one=True
    )
    if existing:
        return jsonify({'code': 409, 'message': '用户名已存在'})

    pwd_hash = hashlib.md5(password.encode('utf-8')).hexdigest()

    from utils.db import execute_insert
    user_id = execute_insert(
        "INSERT INTO users (username, password, role, hospital_name) VALUES (%s, %s, %s, %s)",
        (username, pwd_hash, 'doctor', hospital_name or '')
    )

    return jsonify({
        'code': 200,
        'message': '注册成功',
        'data': {'id': user_id, 'username': username}
    })


@auth_bp.route('/api/logout', methods=['POST'])
def logout():
    """退出登录"""
    session.clear()
    return jsonify({'code': 200, 'message': '已退出'})


@auth_bp.route('/api/current_user', methods=['GET'])
def current_user():
    """获取当前登录用户"""
    if 'user_id' in session:
        return jsonify({
            'code': 200,
            'data': {
                'id': session['user_id'],
                'username': session['username'],
                'role': session['role']
            }
        })
    return jsonify({'code': 401, 'message': '未登录'})
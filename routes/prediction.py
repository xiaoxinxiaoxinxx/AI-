# ============================================
# 中风风险预测路由
# ============================================
from flask import Blueprint, request, jsonify, session
from utils.preprocess import encode_patient_input, get_feature_array
from utils.db import execute_insert, execute_query
from models.federated_model import predict_stroke, get_evaluation, train_model

prediction_bp = Blueprint('prediction', __name__)


def _get_hospital_filter():
    """获取当前用户的医院过滤条件（医生只能看自己医院）"""
    role = session.get('role', 'doctor')
    if role == 'admin':
        return None, None
    return session.get('hospital_id', 0), session.get('hospital_name', '')


@prediction_bp.route('/api/predict', methods=['POST'])
def predict():
    """预测患者中风风险"""
    data = request.get_json()
    patient_id = data.get('patient_id')

    # 编码输入特征
    encoded = encode_patient_input(data)
    features = get_feature_array(encoded)

    try:
        result = predict_stroke(features.flatten())
    except RuntimeError as e:
        return jsonify({'code': 500, 'message': str(e)})

    # 保存预测记录
    if patient_id:
        execute_insert(
            """INSERT INTO predictions (patient_id, stroke_probability, risk_level, model_version)
               VALUES (%s, %s, %s, %s)""",
            (patient_id, result['probability'], result['level'], 'v1.0')
        )

    return jsonify({
        'code': 200,
        'data': {
            'probability': result['probability'],
            'risk_level': result['level'],
            'no_stroke_prob': result['no_stroke_prob'],
            'features': encoded
        }
    })


@prediction_bp.route('/api/predictions', methods=['GET'])
def get_predictions():
    """获取预测历史（医生仅看自己医院患者）"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    patient_id = request.args.get('patient_id', None, type=int)

    offset = (page - 1) * page_size
    user_hospital_id, _ = _get_hospital_filter()

    where_clauses = []
    params = []

    if patient_id:
        where_clauses.append("pr.patient_id = %s")
        params.append(patient_id)

    if user_hospital_id is not None:
        where_clauses.append("pa.hospital_id = %s")
        params.append(user_hospital_id)

    where = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    count_sql = f"""SELECT COUNT(*) as total FROM predictions pr 
                    LEFT JOIN patients pa ON pr.patient_id = pa.id {where}"""
    total = execute_query(count_sql, params, fetch_one=True)['total']

    data_sql = f"""SELECT pr.*, pa.name as patient_name, pa.gender, pa.age, pa.hospital_id
                   FROM predictions pr 
                   LEFT JOIN patients pa ON pr.patient_id = pa.id
                   {where}
                   ORDER BY pr.created_at DESC LIMIT %s OFFSET %s"""
    params.extend([page_size, offset])
    records = execute_query(data_sql, params, fetch_all=True)

    for r in records:
        r['created_at'] = str(r['created_at']) if r.get('created_at') else None

    return jsonify({
        'code': 200,
        'data': {
            'list': records,
            'total': total,
            'page': page,
            'page_size': page_size
        }
    })


@prediction_bp.route('/api/train', methods=['POST'])
def train():
    """触发联邦学习训练"""
    try:
        history = train_model()
        evaluation = get_evaluation()
        return jsonify({
            'code': 200,
            'message': '联邦训练完成',
            'data': {
                'history': history,
                'evaluation': evaluation
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': f'训练失败: {str(e)}'})


@prediction_bp.route('/api/model/evaluation', methods=['GET'])
def model_evaluation():
    """获取模型评估指标"""
    try:
        evaluation = get_evaluation()
        if evaluation:
            return jsonify({'code': 200, 'data': evaluation})
        return jsonify({'code': 404, 'message': '模型尚未训练'})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)})


@prediction_bp.route('/api/model/params', methods=['GET'])
def model_params():
    """获取模型参数"""
    from models.federated_model import get_model
    model = get_model()
    import json
    params = json.loads(model.get_model_params_json())
    return jsonify({'code': 200, 'data': params})


@prediction_bp.route('/api/dashboard', methods=['GET'])
def dashboard():
    """仪表盘数据（医生仅看自己医院）"""
    user_hospital_id, _ = _get_hospital_filter()

    hospital_where = ""
    hospital_params = []
    if user_hospital_id is not None:
        hospital_where = " WHERE hospital_id = %s"
        hospital_params = [user_hospital_id]

    total_patients = execute_query(
        f"SELECT COUNT(*) as c FROM patients{hospital_where}", hospital_params, fetch_one=True
    )['c']
    stroke_patients = execute_query(
        f"SELECT COUNT(*) as c FROM patients WHERE stroke=1{' AND hospital_id=%s' if user_hospital_id else ''}",
        hospital_params, fetch_one=True
    )['c']

    pred_where = ""
    pred_params = []
    if user_hospital_id is not None:
        pred_where = " WHERE pa.hospital_id = %s"
        pred_params = hospital_params

    total_predictions = execute_query(
        f"""SELECT COUNT(*) as c FROM predictions pr 
            LEFT JOIN patients pa ON pr.patient_id = pa.id{pred_where}""",
        pred_params, fetch_one=True
    )['c']

    # 风险分布
    risk_dist = execute_query(
        f"""SELECT pr.risk_level, COUNT(*) as c FROM predictions pr 
            LEFT JOIN patients pa ON pr.patient_id = pa.id{pred_where}
            GROUP BY pr.risk_level""",
        pred_params, fetch_all=True
    )
    risk_dist_dict = {r['risk_level']: r['c'] for r in risk_dist}

    # 最近预测
    recent = execute_query(
        f"""SELECT pr.*, pa.name, pa.gender, pa.age 
           FROM predictions pr
           LEFT JOIN patients pa ON pr.patient_id = pa.id{pred_where}
           ORDER BY pr.created_at DESC LIMIT 5""",
        pred_params, fetch_all=True
    )
    for r in recent:
        r['created_at'] = str(r['created_at']) if r.get('created_at') else None

    # 训练历史
    train_logs = execute_query(
        "SELECT * FROM model_params ORDER BY created_at DESC LIMIT 5",
        fetch_all=True
    )
    for t in train_logs:
        t['created_at'] = str(t['created_at']) if t.get('created_at') else None

    return jsonify({
        'code': 200,
        'data': {
            'total_patients': total_patients,
            'stroke_patients': stroke_patients,
            'stroke_rate': round(stroke_patients / total_patients * 100, 2) if total_patients > 0 else 0,
            'total_predictions': total_predictions,
            'risk_distribution': risk_dist_dict,
            'recent_predictions': recent,
            'train_history': train_logs
        }
    })
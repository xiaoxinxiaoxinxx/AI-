# ============================================
# 患者管理路由
# ============================================
from flask import Blueprint, request, jsonify, session
from utils.db import execute_query, execute_insert, execute_update

patient_bp = Blueprint('patient', __name__)


def _get_hospital_filter():
    """获取当前用户的医院过滤条件（医生只能看自己医院）"""
    role = session.get('role', 'doctor')
    if role == 'admin':
        return None, None
    return session.get('hospital_id', 0), session.get('hospital_name', '')


@patient_bp.route('/api/patients', methods=['GET'])
def get_patients():
    """获取患者列表（支持分页和搜索，医生仅看自己医院）"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    keyword = request.args.get('keyword', '')
    hospital_id = request.args.get('hospital_id', None, type=int)

    offset = (page - 1) * page_size

    user_hospital_id, _ = _get_hospital_filter()

    where_clauses = []
    params = []

    if keyword:
        where_clauses.append("name LIKE %s")
        params.append(f"%{keyword}%")

    if user_hospital_id is not None:
        where_clauses.append("hospital_id = %s")
        params.append(user_hospital_id)
    elif hospital_id:
        where_clauses.append("hospital_id = %s")
        params.append(hospital_id)

    where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    # 总数
    count_sql = f"SELECT COUNT(*) as total FROM patients{where_sql}"
    total = execute_query(count_sql, params, fetch_one=True)['total']

    # 数据
    data_sql = f"SELECT * FROM patients{where_sql} ORDER BY created_at DESC LIMIT %s OFFSET %s"
    params.extend([page_size, offset])
    patients = execute_query(data_sql, params, fetch_all=True)

    # 转换类型
    for p in patients:
        p['created_at'] = str(p['created_at']) if p.get('created_at') else None

    return jsonify({
        'code': 200,
        'data': {
            'list': patients,
            'total': total,
            'page': page,
            'page_size': page_size
        }
    })


@patient_bp.route('/api/patients/<int:patient_id>', methods=['GET'])
def get_patient(patient_id):
    """获取单个患者详情"""
    patient = execute_query(
        "SELECT * FROM patients WHERE id=%s", (patient_id,), fetch_one=True
    )
    if patient:
        patient['created_at'] = str(patient['created_at']) if patient.get('created_at') else None
        return jsonify({'code': 200, 'data': patient})
    return jsonify({'code': 404, 'message': '患者不存在'})


@patient_bp.route('/api/patients', methods=['POST'])
def add_patient():
    """添加患者（医生自动归属到自己医院）"""
    data = request.get_json()
    user_hospital_id, _ = _get_hospital_filter()
    hospital_id = data.get('hospital_id', 1)
    if user_hospital_id is not None:
        hospital_id = user_hospital_id

    patient_id = execute_insert("""INSERT INTO patients 
        (name, gender, age, hypertension, heart_disease, married, 
         work_type, residence_type, glucose_level, bmi, smoking_status, stroke, hospital_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", (
        data.get('name', '匿名'),
        data.get('gender', '男性'),
        data.get('age', 60),
        data.get('hypertension', 0),
        data.get('heart_disease', 0),
        data.get('married', 0),
        data.get('work_type', '私人企业'),
        data.get('residence_type', '城市'),
        data.get('glucose_level', 100),
        data.get('bmi', 25),
        data.get('smoking_status', '从不吸烟'),
        data.get('stroke', 0),
        hospital_id
    ))
    return jsonify({'code': 200, 'message': '添加成功', 'data': {'id': patient_id}})


@patient_bp.route('/api/patients/<int:patient_id>', methods=['PUT'])
def update_patient(patient_id):
    """更新患者信息"""
    data = request.get_json()
    execute_update("""UPDATE patients SET 
        name=%s, gender=%s, age=%s, hypertension=%s, heart_disease=%s, married=%s,
        work_type=%s, residence_type=%s, glucose_level=%s, bmi=%s, smoking_status=%s, stroke=%s
        WHERE id=%s""", (
        data.get('name', '匿名'),
        data.get('gender', '男性'),
        data.get('age', 60),
        data.get('hypertension', 0),
        data.get('heart_disease', 0),
        data.get('married', 0),
        data.get('work_type', '私人企业'),
        data.get('residence_type', '城市'),
        data.get('glucose_level', 100),
        data.get('bmi', 25),
        data.get('smoking_status', '从不吸烟'),
        data.get('stroke', 0),
        patient_id
    ))
    return jsonify({'code': 200, 'message': '更新成功'})


@patient_bp.route('/api/patients/<int:patient_id>', methods=['DELETE'])
def delete_patient(patient_id):
    """删除患者"""
    execute_update("DELETE FROM patients WHERE id=%s", (patient_id,))
    return jsonify({'code': 200, 'message': '删除成功'})


@patient_bp.route('/api/patients/stats', methods=['GET'])
def get_patient_stats():
    """获取患者统计数据"""
    total = execute_query("SELECT COUNT(*) as c FROM patients", fetch_one=True)['c']
    stroke_count = execute_query(
        "SELECT COUNT(*) as c FROM patients WHERE stroke=1", fetch_one=True
    )['c']
    hospitals = execute_query(
        "SELECT hospital_id, COUNT(*) as c FROM patients GROUP BY hospital_id",
        fetch_all=True
    )
    return jsonify({
        'code': 200,
        'data': {
            'total': total,
            'stroke_count': stroke_count,
            'stroke_rate': round(stroke_count / total * 100, 2) if total > 0 else 0,
            'hospitals': hospitals
        }
    })
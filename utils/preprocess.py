# ============================================
# 数据预处理工具 - 对脑卒中数据集进行编码/解码
# ============================================
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
import joblib
import os


# 类别特征映射
GENDER_MAP = {'男性': 1, '女性': 0}
WORK_TYPE_MAP = {'私人企业': 0, '自雇人士': 1, '政府工作': 2, '儿童': 3, '无业': 4}
RESIDENCE_MAP = {'城市': 1, '农村': 0}
SMOKING_MAP = {'从不吸烟': 0, '以前吸烟': 1, '吸烟': 2, '不详': 3}

# 特征列名(中文→英文)
FEATURE_COLUMNS_CN = ['性别', '年龄', '是否患有高血压', '是否患有心脏病', '是否有过婚姻',
                       '工作类型', '住宅类型', '血糖水平', 'BMI', '吸烟状况']
TARGET_COLUMN_CN = '是否中风'

FEATURE_COLUMNS_EN = ['gender', 'age', 'hypertension', 'heart_disease', 'married',
                       'work_type', 'residence_type', 'glucose_level', 'bmi', 'smoking_status']

# 类别特征列表
CATEGORICAL_FEATURES = ['gender', 'work_type', 'residence_type', 'smoking_status']


def load_and_preprocess(csv_path):
    """加载CSV并做编码预处理"""
    for enc in ['gbk', 'gb2312', 'gb18030', 'utf-8-sig', 'utf-8']:
        try:
            df = pd.read_csv(csv_path, encoding=enc)
            break
        except (UnicodeDecodeError, UnicodeError):
            continue

    # 编码性别
    df['gender'] = df['性别'].map(GENDER_MAP)
    # 编码工作类型
    df['work_type'] = df['工作类型'].map(WORK_TYPE_MAP).fillna(0)
    # 编码住宅类型
    df['residence_type'] = df['住宅类型'].map(RESIDENCE_MAP)
    # 编码吸烟状况
    df['smoking_status'] = df['吸烟状况'].map(SMOKING_MAP).fillna(3)

    # 数值特征直接映射
    df['age'] = df['年龄']
    df['hypertension'] = df['是否患有高血压']
    df['heart_disease'] = df['是否患有心脏病']
    df['married'] = df['是否有过婚姻']
    df['glucose_level'] = df['血糖水平']
    df['bmi'] = df['BMI']
    df['stroke'] = df['是否中风']

    # 保留原始中文列供数据库存储
    df['gender_cn'] = df['性别']
    df['work_type_cn'] = df['工作类型']
    df['residence_type_cn'] = df['住宅类型']
    df['smoking_status_cn'] = df['吸烟状况']

    return df


def encode_patient_input(data):
    """将前端输入的原始值编码为模型输入格式"""
    encoded = {}
    encoded['gender'] = GENDER_MAP.get(data.get('gender', '男性'), 1)
    encoded['age'] = float(data.get('age', 60))
    encoded['hypertension'] = int(data.get('hypertension', 0))
    encoded['heart_disease'] = int(data.get('heart_disease', 0))
    encoded['married'] = int(data.get('married', 1))
    encoded['work_type'] = WORK_TYPE_MAP.get(data.get('work_type', '私人企业'), 0)
    encoded['residence_type'] = RESIDENCE_MAP.get(data.get('residence_type', '城市'), 1)
    encoded['glucose_level'] = float(data.get('glucose_level', 100))
    encoded['bmi'] = float(data.get('bmi', 25))
    encoded['smoking_status'] = SMOKING_MAP.get(data.get('smoking_status', '从不吸烟'), 0)
    return encoded


def get_feature_array(encoded_data):
    """将编码后的字典转为特征数组(按模型顺序)"""
    order = FEATURE_COLUMNS_EN
    return np.array([encoded_data[col] for col in order]).reshape(1, -1)
# ============================================
# 联邦学习核心模块
# 基于 Logistic Regression 的中风风险预测
# 使用 FedAvg 聚合各医院本地模型参数
# ============================================
import pandas as pd
import numpy as np
import json
import os
import pickle
import hashlib
from datetime import datetime

from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

from config import FEDERATED_CONFIG, CSV_PATH
from utils.preprocess import load_and_preprocess, FEATURE_COLUMNS_EN, GENDER_MAP, WORK_TYPE_MAP, RESIDENCE_MAP, SMOKING_MAP
from utils.db import execute_insert, execute_query, get_connection


class FederatedStrokeModel:
    """联邦学习中风风险预测模型"""

    def __init__(self, csv_path=None):
        self.csv_path = csv_path or CSV_PATH
        self.n_hospitals = FEDERATED_CONFIG['n_hospitals']
        self.n_rounds = FEDERATED_CONFIG['n_rounds']
        self.test_size = FEDERATED_CONFIG['test_size']
        self.random_state = FEDERATED_CONFIG['random_state']

        # 全局模型参数
        self.global_model = None       # sklearn LogisticRegression
        self.scaler = None             # StandardScaler
        self.feature_order = FEATURE_COLUMNS_EN

        # 各医院数据
        self.hospital_data = {}        # {hospital_id: (X, y)}
        self.test_data = None          # (X_test, y_test)

        # 训练历史
        self.history = []

    def _load_from_db(self):
        """从MySQL数据库读取患者数据（优先使用）"""
        try:
            import pymysql
            conn = get_connection()
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT * FROM patients WHERE hospital_id IS NOT NULL")
            rows = cursor.fetchall()
            cursor.close()
            conn.close()

            if not rows or len(rows) < 10:
                return None  # 数据太少，回退到CSV

            # 编码 + 拼接特征
            records = []
            for row in rows:
                gender = GENDER_MAP.get(row.get('gender', ''), 1)
                age = float(row.get('age', 60))
                hypertension = int(row.get('hypertension', 0))
                heart_disease = int(row.get('heart_disease', 0))
                married = int(row.get('married', 0))
                work_type = WORK_TYPE_MAP.get(row.get('work_type', ''), 0)
                residence_type = RESIDENCE_MAP.get(row.get('residence_type', ''), 1)
                glucose = float(row.get('glucose_level', 100))
                bmi = float(row.get('bmi', 25))
                smoking = SMOKING_MAP.get(row.get('smoking_status', ''), 3)
                stroke = 1 if row.get('stroke', 0) == 1 else 0
                hospital_id = int(row.get('hospital_id', 1))

                records.append((hospital_id, [
                    gender, age, hypertension, heart_disease, married,
                    work_type, residence_type, glucose, bmi, smoking
                ], stroke))

            df_rows = pd.DataFrame(records, columns=['hospital_id', 'features', 'stroke'])
            X_all = np.array([r['features'] for _, r in df_rows.iterrows()])
            y_all = np.array([r['stroke'] for _, r in df_rows.iterrows()])
            hids = np.array([r['hospital_id'] for _, r in df_rows.iterrows()])

            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X_all)

            # 按 hospital_id 分组
            unique_hospitals = np.unique(hids)
            self.n_hospitals = len(unique_hospitals)
            for hid in unique_hospitals:
                mask = hids == hid
                self.hospital_data[int(hid)] = {
                    'X': X_scaled[mask],
                    'y': y_all[mask],
                    'n': int(mask.sum())
                }

            # 测试集
            _, X_test, _, y_test = train_test_split(
                X_scaled, y_all, test_size=self.test_size,
                random_state=self.random_state, stratify=y_all
            )
            self.test_data = (X_test, y_test)

            total = len(df_rows)
            print(f"[数据库加载] 从MySQL读取 {total} 条患者记录，跨 {self.n_hospitals} 家医院：")
            for hid, data in self.hospital_data.items():
                print(f"  医院{hid}: {data['n']} 条 (中风率 {data['y'].mean():.2%})")
            print(f"  测试集: {len(X_test)} 条")
            return True

        except Exception as e:
            print(f"[数据库加载] 读取MySQL失败: {e}，回退到CSV")
            return None

    def load_data(self):
        """加载数据：优先从MySQL读，回退到CSV"""
        # 先尝试数据库
        if self._load_from_db():
            return self

        # 回退：从CSV加载
        df = load_and_preprocess(self.csv_path)
        X = df[self.feature_order].values
        y = df['stroke'].values

        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        n_total = len(df)
        n_per_hospital = n_total // self.n_hospitals
        indices = np.random.RandomState(self.random_state).permutation(n_total)

        for i in range(self.n_hospitals):
            start = i * n_per_hospital
            end = start + n_per_hospital if i < self.n_hospitals - 1 else n_total
            idx = indices[start:end]
            self.hospital_data[i + 1] = {
                'X': X_scaled[idx],
                'y': y[idx],
                'n': len(idx)
            }

        _, X_test, _, y_test = train_test_split(
            X, y, test_size=self.test_size,
            random_state=self.random_state, stratify=y
        )
        self.test_data = (X_test, y_test)

        print(f"[CSV加载] 总计 {n_total} 条记录，{self.n_hospitals} 家医院各自持有：")
        for hid, data in self.hospital_data.items():
            print(f"  医院{hid}: {data['n']} 条 (中风率 {data['y'].mean():.2%})")
        print(f"  测试集: {len(X_test)} 条")

        return self

    def local_train(self, X, y, initial_coef=None, initial_intercept=None):
        """单家医院本地训练 Logistic Regression"""
        model = LogisticRegression(
            max_iter=1000,
            solver='saga',
            C=0.5,
            class_weight='balanced',
            random_state=self.random_state,
            warm_start=True,
            l1_ratio=0
        )

        n_features = X.shape[1]
        if initial_coef is not None and np.any(initial_coef):
            model.classes_ = np.array([0, 1])
            model.coef_ = initial_coef.reshape(1, -1)
            model.intercept_ = initial_intercept.reshape(1, )
        else:
            model.fit(X, y)
            return model

        model.fit(X, y)
        return model

    def train_federated(self, progress_callback=None):
        """执行联邦训练"""
        n_features = self.hospital_data[1]['X'].shape[1]
        global_coef = np.zeros((1, n_features))
        global_intercept = np.zeros(1)

        self.history = []

        for round_idx in range(1, self.n_rounds + 1):
            print(f"\n--- 联邦训练第 {round_idx}/{self.n_rounds} 轮 ---")

            coef_list = []
            intercept_list = []
            n_list = []

            for hid in range(1, self.n_hospitals + 1):
                data = self.hospital_data[hid]
                X_local = data['X']
                y_local = data['y']

                model = self.local_train(
                    X_local, y_local,
                    initial_coef=global_coef,
                    initial_intercept=global_intercept
                )

                coef_list.append(model.coef_)
                intercept_list.append(model.intercept_)
                n_list.append(data['n'])

            # FedAvg 加权聚合
            total_n = sum(n_list)
            global_coef = sum(
                c * n / total_n for c, n in zip(coef_list, n_list)
            )
            global_intercept = sum(
                i * n / total_n for i, n in zip(intercept_list, n_list)
            )

            # 评估全局模型
            self.global_model = LogisticRegression(
                max_iter=100, solver='liblinear', C=1.0
            )
            self.global_model.classes_ = np.array([0, 1])
            self.global_model.coef_ = global_coef
            self.global_model.intercept_ = global_intercept

            # 在测试集上评估
            X_test, y_test = self.test_data
            y_pred = self.global_model.predict(X_test)
            acc = accuracy_score(y_test, y_pred)
            prec = precision_score(y_test, y_pred, zero_division=0)
            rec = recall_score(y_test, y_pred, zero_division=0)
            f1 = f1_score(y_test, y_pred, zero_division=0)

            self.history.append({
                'round': round_idx,
                'accuracy': round(acc, 4),
                'precision': round(prec, 4),
                'recall': round(rec, 4),
                'f1_score': round(f1, 4)
            })

            print(f"  全局模型: 准确率={acc:.4f} 精确率={prec:.4f} "
                  f"召回率={rec:.4f} F1={f1:.4f}")

            if progress_callback:
                progress_callback(round_idx, self.n_rounds, {
                    'accuracy': acc, 'precision': prec,
                    'recall': rec, 'f1': f1
                })

        print("\n联邦训练完成!")

        # 保存最佳模型
        self._save_best_model()
        return self.history

    def _save_best_model(self):
        """保存当前模型参数到本地文件"""
        if self.global_model is None:
            return
        model_path = os.path.join(os.path.dirname(__file__), '..', 'federated_model.pkl')
        scaler_path = os.path.join(os.path.dirname(__file__), '..', 'scaler.pkl')
        with open(model_path, 'wb') as f:
            pickle.dump(self.global_model, f)
        with open(scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)

    def load_model(self):
        """从本地文件加载模型"""
        model_path = os.path.join(os.path.dirname(__file__), '..', 'federated_model.pkl')
        scaler_path = os.path.join(os.path.dirname(__file__), '..', 'scaler.pkl')
        if os.path.exists(model_path) and os.path.exists(scaler_path):
            with open(model_path, 'rb') as f:
                self.global_model = pickle.load(f)
            with open(scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
            return True
        return False

    def predict(self, features):
        """预测单个患者的中风风险"""
        if self.global_model is None:
            if not self.load_model():
                raise RuntimeError('模型未训练，请先执行联邦训练')

        X = np.array(features).reshape(1, -1)
        X_scaled = self.scaler.transform(X)
        proba = self.global_model.predict_proba(X_scaled)[0]
        stroke_prob = proba[1]   # 中风的概率

        if stroke_prob < 0.3:
            level = '低风险'
        elif stroke_prob < 0.6:
            level = '中风险'
        else:
            level = '高风险'

        return {
            'probability': round(float(stroke_prob), 4),
            'level': level,
            'no_stroke_prob': round(float(proba[0]), 4)
        }

    def evaluate(self):
        """评估模型性能"""
        if self.global_model is None:
            if not self.load_model():
                return None
        X_test, y_test = self.test_data
        y_pred = self.global_model.predict(X_test)
        cm = confusion_matrix(y_test, y_pred)
        return {
            'accuracy': round(accuracy_score(y_test, y_pred), 4),
            'precision': round(precision_score(y_test, y_pred, zero_division=0), 4),
            'recall': round(recall_score(y_test, y_pred, zero_division=0), 4),
            'f1_score': round(f1_score(y_test, y_pred, zero_division=0), 4),
            'confusion_matrix': cm.tolist(),
            'test_size': len(X_test)
        }

    def get_model_params_json(self):
        """获取模型参数的JSON表示"""
        if self.global_model is None:
            if not self.load_model():
                return None
        return json.dumps({
            'coef': self.global_model.coef_.tolist(),
            'intercept': self.global_model.intercept_.tolist(),
            'classes': self.global_model.classes_.tolist(),
            'features': self.feature_order
        }, ensure_ascii=False)

    def save_params_to_db(self):
        """将模型参数保存到MySQL"""
        params_json = self.get_model_params_json()
        eval_result = self.evaluate()
        if params_json and eval_result:
            sql = """INSERT INTO model_params 
                     (model_name, params_json, accuracy, precision_score, recall, f1_score, training_rounds)
                     VALUES (%s, %s, %s, %s, %s, %s, %s)"""
            execute_insert(sql, (
                f'FederatedLR_v{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                params_json,
                eval_result['accuracy'],
                eval_result['precision'],
                eval_result['recall'],
                eval_result['f1_score'],
                self.n_rounds
            ))


# ============================================
# 模型单例管理
# ============================================
_federated_model_instance = None


def get_model(force_reload=False):
    """获取全局唯一的模型实例"""
    global _federated_model_instance
    if _federated_model_instance is None or force_reload:
        _federated_model_instance = FederatedStrokeModel()
        _federated_model_instance.load_data()
    return _federated_model_instance


def train_model(progress_callback=None):
    """执行联邦训练（每次训练前重新加载数据库数据）"""
    model = get_model(force_reload=True)
    history = model.train_federated(progress_callback=progress_callback)
    # 保存到数据库
    try:
        model.save_params_to_db()
        # 保存训练日志
        for h in history:
            execute_insert(
                "INSERT INTO training_logs (round, accuracy) VALUES (%s, %s)",
                (h['round'], h['accuracy'])
            )
    except Exception as e:
        print(f"[警告] 保存训练日志到数据库失败: {e}")
    return history


def predict_stroke(features):
    """预测中风风险"""
    model = get_model()
    return model.predict(features)


def get_evaluation():
    """获取模型评估结果"""
    model = get_model()
    return model.evaluate()
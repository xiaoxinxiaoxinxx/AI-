import pandas as pd
import numpy as np
from utils.db import execute_insert, get_connection
from config import MYSQL_CONFIG

print("正在从 brain_stroke.csv 导入患者数据...")

# 读取CSV
for enc in ['gbk', 'gb2312', 'gb18030', 'utf-8-sig', 'utf-8']:
    try:
        df = pd.read_csv('brain_stroke.csv', encoding=enc)
        print(f"编码: {enc}")
        break
    except (UnicodeDecodeError, UnicodeError):
        continue

# 随机打乱后分配到3家医院
df = df.sample(frac=1, random_state=42).reset_index(drop=True)
n = len(df)
split_1 = n // 3
split_2 = n // 3 * 2

df['hospital_id'] = 0
df.loc[:split_1 - 1, 'hospital_id'] = 1
df.loc[split_1:split_2 - 1, 'hospital_id'] = 2
df.loc[split_2:, 'hospital_id'] = 3

# 获取数据库连接
conn = get_connection()
cursor = conn.cursor()

# 清空旧数据
cursor.execute("DELETE FROM predictions")
cursor.execute("DELETE FROM patients")
cursor.execute("ALTER TABLE patients AUTO_INCREMENT = 1")
cursor.execute("ALTER TABLE predictions AUTO_INCREMENT = 1")

inserted = 0
for _, row in df.iterrows():
    cursor.execute("""INSERT INTO patients 
        (name, gender, age, hypertension, heart_disease, married, 
         work_type, residence_type, glucose_level, bmi, smoking_status, stroke, hospital_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", (
        f"患者{inserted + 1:04d}",
        str(row['性别']),
        int(row['年龄']),
        int(row['是否患有高血压']),
        int(row['是否患有心脏病']),
        int(row['是否有过婚姻']),
        str(row['工作类型']),
        str(row['住宅类型']),
        float(row['血糖水平']),
        float(row['BMI']),
        str(row['吸烟状况']),
        int(row['是否中风']),
        int(row['hospital_id'])
    ))
    inserted += 1
    if inserted % 500 == 0:
        conn.commit()
        print(f"已导入 {inserted} 条...")

conn.commit()
cursor.close()
conn.close()

print(f"\n导入完成！共 {inserted} 条患者数据")
print(f"  医院1: {len(df[df['hospital_id'] == 1])} 条")
print(f"  医院2: {len(df[df['hospital_id'] == 2])} 条")
print(f"  医院3: {len(df[df['hospital_id'] == 3])} 条")
# ============================================
# MySQL 数据库操作工具
# ============================================
import pymysql
from contextlib import contextmanager
from config import MYSQL_CONFIG


def get_connection():
    """获取数据库连接"""
    return pymysql.connect(**MYSQL_CONFIG)


@contextmanager
def get_cursor(commit=True):
    """获取数据库游标的上下文管理器"""
    conn = get_connection()
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        yield cursor
        if commit:
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def execute_query(sql, params=None, fetch_one=False, fetch_all=False):
    """执行查询SQL"""
    with get_cursor(commit=False) as cursor:
        cursor.execute(sql, params or ())
        if fetch_one:
            return cursor.fetchone()
        if fetch_all:
            return cursor.fetchall()
        return cursor.fetchall()


def execute_update(sql, params=None):
    """执行增删改SQL"""
    with get_cursor(commit=True) as cursor:
        cursor.execute(sql, params or ())
        return cursor.rowcount


def execute_insert(sql, params=None):
    """执行插入SQL，返回自增ID"""
    with get_cursor(commit=True) as cursor:
        cursor.execute(sql, params or ())
        return cursor.lastrowid
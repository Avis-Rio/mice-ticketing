import streamlit as st
import pandas as pd
import re
import json
import os
import sys
from pathlib import Path

# 导入自动更新模块
try:
    from auto_updater import AutoUpdater, VersionManager
except ImportError:
    # 如果导入失败，创建空的类以避免错误
    class AutoUpdater:
        def __init__(self, *args, **kwargs):
            pass
        def check_for_updates(self, *args, **kwargs):
            return {'has_update': False}
    
    class VersionManager:
        def __init__(self):
            self.current_version = '1.0.0'

# --- 页面基础设置 ---
st.set_page_config(page_title="MICE TICKETING APP", layout="wide")

# 初始化版本管理器
version_manager = VersionManager()
current_version = version_manager.current_version

st.title(f"✈️ MICE TICKETING APP V{current_version}")
st.markdown("上传客户信息表，选择专家即可自动填充信息，告别手动输入！")

# 自动更新检查（在侧边栏显示）
with st.sidebar:
    st.markdown("### 📱 应用信息")
    st.info(f"当前版本：V{current_version}")
    
    # 检查更新按钮
    if st.button("🔄 检查更新", help="检查是否有新版本可用"):
        with st.spinner("正在检查更新..."):
            try:
                # 这里需要用户配置自己的GitHub仓库信息
                # 格式：AutoUpdater("用户名", "仓库名")
                # 请将下面的用户名和仓库名替换为您的实际GitHub信息
                updater = AutoUpdater("your-github-username", "mice-ticketing-app")
                update_info = updater.check_for_updates(current_version)
                
                if update_info['has_update']:
                    st.success(f"🎉 发现新版本 V{update_info['version']}")
                    
                    # 显示更新说明
                    if update_info.get('release_notes'):
                        with st.expander("📋 更新说明"):
                            st.markdown(update_info['release_notes'])
                    
                    # 更新按钮
                    if st.button("⬇️ 立即更新", type="primary"):
                        with st.spinner("正在下载更新..."):
                            if updater.download_and_install(update_info['download_url']):
                                st.success("✅ 更新下载完成，应用将重启")
                                st.balloons()
                            else:
                                st.error("❌ 更新失败，请稍后重试或手动下载")
                else:
                    st.success("✅ 当前已是最新版本")
            except Exception as e:
                st.warning(f"⚠️ 检查更新失败：{str(e)}")
                st.info("💡 请检查网络连接或稍后重试")
    
    # 应用信息
    with st.expander("ℹ️ 关于应用"):
        st.markdown("""
        **智能会务机票助手**
        
        🎯 **主要功能：**
        - Excel文件上传与解析
        - 询价信息自动生成
        - 票务回复智能处理
        - 价格信息自动清洗
        - 手机号码格式验证
        - 自动更新功能
        
        🔒 **数据安全：**
        - 所有数据仅在本地处理
        - 不上传任何个人信息
        - 符合数据保护要求
        
        📞 **技术支持：**
        - 如有问题请联系开发团队
        - 建议和反馈随时欢迎
        """)

st.markdown("---")

# --- 核心修改点 1 ---
# 更新必需列的定义，使其与您Excel文件中的列名（包含空格）完全匹配
REQUIRED_COLUMNS = ['姓名*', '身份证 (出机票必须填写)', '手机号码 (必填)', '销售手机', '去程车次/航班', '返程车次/航班', '去程出发日期', '返程出发日期', '去程出发时间', '去程到达时间', '返程出发时间', '返程到达时间', '去程出发站', '去程到达站', '返程出发站', '返程到达站']

# 智能模糊匹配的列名变体配置
COLUMN_VARIANTS = {
    '姓名*': [
        '姓名', '名字', '专家姓名', '姓名*', '专家名字', '人员姓名', 
        '参会人姓名', '参会者姓名', '会议专家姓名', '专家', '人员',
        'name', 'Name', 'NAME', '真实姓名', '全名'
    ],
    '身份证 (出机票必须填写)': [
        '身份证', '身份证号', '身份证号码', '证件号', '证件号码',
        '身份证 (出机票必须填写)', '身份证(出机票必须填写)',
        'ID', 'id', 'Id', 'ID号', 'ID号码', '身份证件号',
        '居民身份证号', '身份证件', '证件', '身份证信息'
    ],
    '手机号码 (必填)': [
        '手机', '手机号', '手机号码', '电话', '电话号码', '联系电话',
        '手机号码 (必填)', '手机号码(必填)', '移动电话', '联系方式',
        'phone', 'Phone', 'PHONE', 'mobile', 'Mobile', 'MOBILE',
        '手机联系方式', '个人电话', '联系手机'
    ],
    '销售手机': [
        '销售手机', '销售电话', '销售手机号', '销售手机号码', '销售联系方式',
        '票务手机', '票务电话', '票务联系方式', '出票手机', '出票电话',
        '第二手机', '备用手机', '备用电话', '接收手机', '接收电话',
        '短信接收手机', '短信手机', '通知手机', '通知电话'
    ],
    '去程车次/航班': [
        '去程车次', '去程航班', '去程车次/航班', '去程航班号', '去程车次号',
        '出发车次', '出发航班', '出发航班号', '出发车次号', '去程班次',
        '去程交通', '去程信息', '出行车次', '出行航班', '往程车次',
        '往程航班', '上行车次', '上行航班', '去程', '出发班次'
    ],
    '返程车次/航班': [
        '返程车次', '返程航班', '返程车次/航班', '返程航班号', '返程车次号',
        '回程车次', '回程航班', '回程航班号', '回程车次号', '返程班次',
        '返程交通', '返程信息', '回程交通', '回程信息', '下行车次',
        '下行航班', '返程', '回程班次', '归程车次', '归程航班'
    ],
    '去程出发日期': [
        '去程出发日期', '去程日期', '出发日期', '去程时间', '出发时间',
        '去程出发时间', '出行日期', '往程日期', '上行日期', '去程',
        '出发', '启程日期', '出行时间', '去程出发', '出发日',
        'departure_date', 'outbound_date', '去程日', '出发日期时间'
    ],
    '返程出发日期': [
        '返程出发日期', '返程日期', '回程日期', '返程时间', '回程时间',
        '返程出发时间', '回程出发日期', '下行日期', '归程日期', '返程',
        '回程', '返回日期', '回程出发', '返程日', '回程日',
        'return_date', 'inbound_date', '返程出发', '回程日期时间'
    ],
    '去程出发站': [
        '去程出发站', '去程出发地', '出发站', '出发地', '起点站', '起点',
        '去程起点', '出发城市', '出发机场', '出发火车站', '始发站',
        '去程始发站', '上车站', '登机地', '出发点', '起始站',
        'departure_station', 'origin', '去程出发', '出发地点'
    ],
    '去程到达站': [
        '去程到达站', '去程到达地', '到达站', '到达地', '终点站', '终点',
        '去程终点', '到达城市', '到达机场', '到达火车站', '目的站',
        '去程目的站', '下车站', '降落地', '到达点', '目的地',
        'arrival_station', 'destination', '去程到达', '到达地点'
    ],
    '返程出发站': [
        '返程出发站', '返程出发地', '回程出发站', '回程出发地', '返程起点',
        '回程起点', '返程始发站', '回程始发地', '返程上车站', '回程登机地',
        '返程出发城市', '返程出发机场', '返程出发火车站', '归程出发站',
        'return_departure_station', '返程出发', '回程出发点'
    ],
    '返程到达站': [
        '返程到达站', '返程到达地', '回程到达站', '回程到达地', '返程终点',
        '回程终点', '返程目的站', '回程目的地', '返程下车站', '回程降落地',
        '返程到达城市', '返程到达机场', '返程到达火车站', '归程到达站',
        'return_arrival_station', '返程到达', '回程到达点'
    ],
    '去程出发时间': [
        '去程出发时间', '去程时间', '出发时间', '去程起飞时间', '去程发车时间',
        '出发时刻', '去程出发时刻', '启程时间', '出行时间', '去程开始时间',
        '出发点时间', '起始时间', '去程时刻', '出发班次时间', '去程班次时间',
        'departure_time', 'outbound_time', '去程发车', '出发时分'
    ],
    '去程到达时间': [
        '去程到达时间', '去程抵达时间', '到达时间', '去程落地时间', '去程到站时间',
        '到达时刻', '去程到达时刻', '抵达时间', '去程结束时间', '目的地时间',
        '到达点时间', '终点时间', '去程到时', '到达班次时间', '去程班次到达',
        'arrival_time', 'outbound_arrival_time', '去程到站', '到达时分'
    ],
    '返程出发时间': [
        '返程出发时间', '返程时间', '回程出发时间', '返程起飞时间', '返程发车时间',
        '回程时间', '返程出发时刻', '回程出发时刻', '返程开始时间', '回程起始时间',
        '返程发车', '回程发车时间', '返程时刻', '回程班次时间', '归程出发时间',
        'return_departure_time', 'return_time', '返程发车', '回程时分'
    ],
    '返程到达时间': [
        '返程到达时间', '返程抵达时间', '回程到达时间', '返程落地时间', '返程到站时间',
        '回程抵达时间', '返程到达时刻', '回程到达时刻', '返程结束时间', '回程终点时间',
        '返程到站', '回程到站时间', '返程到时', '回程班次到达', '归程到达时间',
        'return_arrival_time', 'inbound_arrival_time', '返程到站', '回程时分'
    ]
}

# 预设的常见列位置配置
DEFAULT_COLUMN_MAPPING = {
    '姓名*': 0,  # A列
    '身份证 (出机票必须填写)': 1,  # B列
    '手机号码 (必填)': 2,   # C列
    '销售手机': 3,   # D列
    '去程车次/航班': 4,   # E列
    '返程车次/航班': 5,   # F列
    '去程出发日期': 6,   # G列
    '返程出发日期': 7,   # H列
    '去程出发时间': 8,   # I列
    '去程到达时间': 9,   # J列
    '返程出发时间': 10,  # K列
    '返程到达时间': 11,  # L列
    '去程出发站': 12,   # M列
    '去程到达站': 13,   # N列
    '返程出发站': 14,   # O列
    '返程到达站': 15    # P列
}

# 常见Excel格式预设配置
PRESET_CONFIGURATIONS = {
    '标准格式': {
        'description': '姓名-身份证-手机号-销售手机-去程车次-返程车次-去程日期-返程日期-去程出发时间-去程到达时间-返程出发时间-返程到达时间-去程出发站-去程到达站-返程出发站-返程到达站 (A-P列)',
        'mapping': {'姓名*': 0, '身份证 (出机票必须填写)': 1, '手机号码 (必填)': 2, '销售手机': 3, '去程车次/航班': 4, '返程车次/航班': 5, '去程出发日期': 6, '返程出发日期': 7, '去程出发时间': 8, '去程到达时间': 9, '返程出发时间': 10, '返程到达时间': 11, '去程出发站': 12, '去程到达站': 13, '返程出发站': 14, '返程到达站': 15}
    },
    '会议格式1': {
        'description': '序号-姓名-身份证-手机号-销售手机-去程车次-返程车次-去程日期-返程日期-去程出发时间-去程到达时间-返程出发时间-返程到达时间-去程出发站-去程到达站-返程出发站-返程到达站 (B-Q列)',
        'mapping': {'姓名*': 1, '身份证 (出机票必须填写)': 2, '手机号码 (必填)': 3, '销售手机': 4, '去程车次/航班': 5, '返程车次/航班': 6, '去程出发日期': 7, '返程出发日期': 8, '去程出发时间': 9, '去程到达时间': 10, '返程出发时间': 11, '返程到达时间': 12, '去程出发站': 13, '去程到达站': 14, '返程出发站': 15, '返程到达站': 16}
    },
    '会议格式2': {
        'description': '姓名-手机号-身份证-销售手机-去程车次-返程车次-去程日期-返程日期-去程出发时间-去程到达时间-返程出发时间-返程到达时间-去程出发站-去程到达站-返程出发站-返程到达站 (A-P列)',
        'mapping': {'姓名*': 0, '手机号码 (必填)': 1, '身份证 (出机票必须填写)': 2, '销售手机': 3, '去程车次/航班': 4, '返程车次/航班': 5, '去程出发日期': 6, '返程出发日期': 7, '去程出发时间': 8, '去程到达时间': 9, '返程出发时间': 10, '返程到达时间': 11, '去程出发站': 12, '去程到达站': 13, '返程出发站': 14, '返程到达站': 15}
    },
    '专家表格': {
        'description': '序号-专家姓名-联系电话-身份证号-销售手机-去程车次-返程车次-去程日期-返程日期-去程出发时间-去程到达时间-返程出发时间-返程到达时间-去程出发站-去程到达站-返程出发站-返程到达站 (B-Q列)',
        'mapping': {'姓名*': 1, '手机号码 (必填)': 2, '身份证 (出机票必须填写)': 3, '销售手机': 4, '去程车次/航班': 5, '返程车次/航班': 6, '去程出发日期': 7, '返程出发日期': 8, '去程出发时间': 9, '去程到达时间': 10, '返程出发时间': 11, '返程到达时间': 12, '去程出发站': 13, '去程到达站': 14, '返程出发站': 15, '返程到达站': 16}
    },
    '参会人员': {
        'description': '姓名-证件号-电话-销售手机-去程车次-返程车次-去程日期-返程日期-去程出发时间-去程到达时间-返程出发时间-返程到达时间-去程出发站-去程到达站-返程出发站-返程到达站 (A-P列)',
        'mapping': {'姓名*': 0, '身份证 (出机票必须填写)': 1, '手机号码 (必填)': 2, '销售手机': 3, '去程车次/航班': 4, '返程车次/航班': 5, '去程出发日期': 6, '返程出发日期': 7, '去程出发时间': 8, '去程到达时间': 9, '返程出发时间': 10, '返程到达时间': 11, '去程出发站': 12, '去程到达站': 13, '返程出发站': 14, '返程到达站': 15}
    }
}

# 配置文件路径
CONFIG_FILE = 'column_mapping_config.json'

def parse_date_field(value):
    """解析日期字段，支持多种日期格式"""
    if pd.isna(value) or value is None:
        return None
    
    # 转换为字符串并清理
    date_str = str(value).strip()
    if not date_str:
        return None
    
    # 尝试多种日期格式
    date_formats = [
        '%Y-%m-%d',      # 2025-09-06
        '%Y/%m/%d',      # 2025/09/06
        '%Y.%m.%d',      # 2025.09.06
        '%m/%d/%Y',      # 09/06/2025
        '%m-%d-%Y',      # 09-06-2025
        '%d/%m/%Y',      # 06/09/2025
        '%d-%m-%Y',      # 06-09-2025
        '%Y年%m月%d日',   # 2025年09月06日
        '%m月%d日',       # 09月06日
        '%Y-%m-%d %H:%M:%S',  # 带时间的格式
        '%Y/%m/%d %H:%M:%S',
    ]
    
    # 如果是Excel的日期序列号，尝试转换
    try:
        if isinstance(value, (int, float)) and value > 40000:  # Excel日期序列号大概范围
            from datetime import datetime, timedelta
            # Excel的日期起始点是1900-01-01，但实际是1899-12-30
            excel_epoch = datetime(1899, 12, 30)
            return excel_epoch + timedelta(days=value)
    except:
        pass
    
    # 尝试pandas的日期解析
    try:
        parsed_date = pd.to_datetime(date_str, errors='coerce')
        if not pd.isna(parsed_date):
            return parsed_date.date()
    except:
        pass
    
    # 尝试各种格式
    for fmt in date_formats:
        try:
            from datetime import datetime
            parsed = datetime.strptime(date_str, fmt)
            return parsed.date()
        except:
            continue
    
    # 如果都失败了，返回None
    return None

def parse_time_field(value):
    """解析时间字段，支持多种时间格式"""
    if pd.isna(value) or value is None:
        return None
    
    # 转换为字符串并清理
    time_str = str(value).strip()
    if not time_str:
        return None
    
    # 尝试多种时间格式
    time_formats = [
        '%H:%M',         # 20:15
        '%H:%M:%S',      # 20:15:30
        '%I:%M %p',      # 8:15 PM
        '%I:%M:%S %p',   # 8:15:30 PM
        '%H时%M分',       # 20时15分
        '%H点%M分',       # 20点15分
        '%H.%M',         # 20.15
        '%H-%M',         # 20-15
    ]
    
    # 如果是Excel的时间序列号（小数），尝试转换
    try:
        if isinstance(value, (int, float)) and 0 <= value < 1:
            from datetime import datetime, timedelta
            # Excel时间是一天的小数部分
            total_seconds = value * 24 * 60 * 60
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            from datetime import time
            return time(hours, minutes)
    except:
        pass
    
    # 尝试pandas的时间解析
    try:
        parsed_time = pd.to_datetime(time_str, errors='coerce')
        if not pd.isna(parsed_time):
            return parsed_time.time()
    except:
        pass
    
    # 尝试各种格式
    for fmt in time_formats:
        try:
            from datetime import datetime
            parsed = datetime.strptime(time_str, fmt)
            return parsed.time()
        except:
            continue
    
    # 如果都失败了，返回None
    return None

def clean_data_field(value, field_type):
    """清洗数据字段，去除空格和多余字符"""
    if pd.isna(value) or value is None:
        return value
    
    # 转换为字符串并去除首尾空格
    clean_value = str(value).strip()
    
    # 如果是'nan'字符串，返回None
    if clean_value.lower() in ['nan', 'none', '', 'null']:
        return None
    
    if field_type == '手机号码':
        # 清洗手机号：去除空格、连字符、括号等
        original_value = clean_value
        clean_value = re.sub(r'[\s\-\(\)\+\.]', '', clean_value)
        
        # 去除国家代码+86
        if clean_value.startswith('+86'):
            clean_value = clean_value[3:]
        elif clean_value.startswith('86') and len(clean_value) == 13:
            clean_value = clean_value[2:]
        
        # 如果清洗后为空，返回原始值
        if not clean_value:
            return original_value
        
        # 严格检查手机号码长度和格式
        if clean_value.isdigit():
            # 如果是12位且末尾是0，可能是Excel数字精度问题，截取前11位
            if len(clean_value) == 12 and clean_value.endswith('0'):
                clean_value = clean_value[:11]
                print(f"手机号码长度修正: {original_value} -> {clean_value}")
            # 如果超过11位，截取前11位
            elif len(clean_value) > 11:
                clean_value = clean_value[:11]
                print(f"手机号码长度截取: {original_value} -> {clean_value}")
        
        # 确保是11位数字，如果不是也返回清洗后的值
        return clean_value
    
    elif field_type == '身份证':
        # 清洗身份证：去除空格、连字符
        clean_value = re.sub(r'[\s\-]', '', clean_value)
        # 确保是18位（包含最后一位可能的X）
        if len(clean_value) == 18:
            return clean_value.upper()  # X要大写
        return clean_value  # 返回清洗后的值，即使格式不标准
    
    elif field_type == '姓名':
        # 清洗姓名：去除多余空格，保留中间的单个空格
        clean_value = re.sub(r'\s+', ' ', clean_value)
        return clean_value.strip()
    
    elif field_type == '车次航班':
        # 清洗车次/航班号：去除空格，统一大写
        clean_value = re.sub(r'\s+', '', clean_value)
        return clean_value.upper()
    
    elif field_type == '时间':
        # 清洗时间：保持原始格式，交给parse_time_field处理
        return clean_value
    
    else:
        # 其他字段：基本清洗
        return clean_value

def fuzzy_match_column(column_name, target_variants):
    """使用模糊匹配算法匹配列名"""
    if not column_name or not isinstance(column_name, str):
        return False
    
    # 清理列名
    clean_col = str(column_name).strip().lower()
    
    # 精确匹配
    for variant in target_variants:
        if clean_col == variant.lower().strip():
            return True
    
    # 包含匹配
    for variant in target_variants:
        variant_clean = variant.lower().strip()
        if variant_clean in clean_col or clean_col in variant_clean:
            if len(variant_clean) >= 2:  # 避免过短的匹配
                return True
    
    return False

def smart_column_detection(df):
    """智能检测DataFrame中的列名匹配"""
    detected_mapping = {}
    confidence_scores = {}
    
    for required_col in REQUIRED_COLUMNS:
        variants = COLUMN_VARIANTS.get(required_col, [])
        best_match = None
        best_score = 0
        
        for i, col in enumerate(df.columns):
            if fuzzy_match_column(col, variants):
                # 计算匹配置信度
                score = 1.0
                
                # 精确匹配加分
                if str(col).strip().lower() in [v.lower().strip() for v in variants[:3]]:
                    score += 0.5
                
                # 数据质量加分
                non_empty_ratio = df[col].notna().sum() / len(df) if len(df) > 0 else 0
                score += non_empty_ratio * 0.3
                
                if score > best_score:
                    best_score = score
                    best_match = i
        
        if best_match is not None:
            detected_mapping[required_col] = best_match
            confidence_scores[required_col] = best_score
    
    return detected_mapping, confidence_scores

def load_column_mapping():
    """加载用户保存的列映射配置"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return DEFAULT_COLUMN_MAPPING.copy()

def save_column_mapping(mapping):
    """保存用户的列映射配置"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def apply_manual_mapping(df, column_mapping):
    """根据用户指定的列映射应用到DataFrame"""
    try:
        # 创建新的DataFrame，只包含映射的列
        mapped_data = {}
        for required_col, col_index in column_mapping.items():
            if col_index < len(df.columns):
                # 获取列数据，保持原始数据类型
                col_data = df.iloc[:, col_index].copy()
                
                # 应用数据清洗，但保持原始值用于调试
                if required_col in ['手机号码 (必填)', '销售手机']:
                    # 对于手机号码，先检查原始数据
                    def clean_phone_with_debug(x):
                        if pd.isna(x):
                            return x
                        original = x
                        cleaned = clean_data_field(x, '手机号码')
                        # 调试信息：如果清洗前后差异很大，记录
                        if str(original) != str(cleaned) and len(str(original)) > 0:
                            print(f"手机号码清洗: {repr(original)} -> {repr(cleaned)}")
                        return cleaned
                    col_data = col_data.apply(clean_phone_with_debug)
                elif required_col == '身份证 (出机票必须填写)':
                    col_data = col_data.apply(lambda x: clean_data_field(x, '身份证'))
                elif required_col == '姓名*':
                    col_data = col_data.apply(lambda x: clean_data_field(x, '姓名'))
                elif required_col in ['去程车次/航班', '返程车次/航班']:
                    col_data = col_data.apply(lambda x: clean_data_field(x, '车次航班'))
                elif required_col in ['去程出发时间', '去程到达时间', '返程出发时间', '返程到达时间']:
                    # 对于时间字段，直接转换为字符串格式，不进行复杂解析
                    def process_time_field(x):
                        if pd.isna(x) or x is None:
                            return None
                        # 直接转换为字符串，保持原始格式
                        time_str = str(x).strip()
                        if time_str.lower() in ['nan', 'none', '', 'null']:
                            return None
                        return time_str
                    col_data = col_data.apply(process_time_field)
                else:
                    # 对于其他字段，进行基本清洗
                    col_data = col_data.apply(lambda x: clean_data_field(x, '其他') if not pd.isna(x) else x)
                
                mapped_data[required_col] = col_data
            else:
                mapped_data[required_col] = None
        
        new_df = pd.DataFrame(mapped_data)
        
        # 确保所有列都是字符串类型，避免类型混合问题
        for col in new_df.columns:
            if new_df[col].dtype != 'object':
                new_df[col] = new_df[col].astype('string')
        
        return new_df
    except Exception as e:
        st.error(f"应用列映射时出错: {str(e)}")
        import traceback
        st.error(f"详细错误: {traceback.format_exc()}")
        return None

def show_manual_mapping_ui(df):
    """显示手动列映射界面"""
    st.warning("🔧 自动识别列名失败，请手动指定列的对应关系")
    
    # 尝试智能推荐
    detected_mapping, confidence_scores = smart_column_detection(df)
    if detected_mapping:
        st.info(f"🤖 **智能推荐：** 系统检测到 {len(detected_mapping)} 个可能的匹配列，请在下方确认或调整")
        for col, idx in detected_mapping.items():
            confidence = confidence_scores.get(col, 0)
            st.write(f"  • {col} → 列 {idx} ({df.columns[idx]}) [置信度: {confidence:.2f}]")
    
    # 添加操作指引
    st.info("💡 **操作步骤：** 1️⃣ 查看下方列信息 → 2️⃣ 为每个字段选择对应列 → 3️⃣ 预览结果 → 4️⃣ 应用映射")
    
    # 显示Excel文件的列信息
    with st.expander("📋 Excel文件列信息详情", expanded=True):
        st.write("**请根据以下信息选择正确的列：**")
        
        # 创建更详细的列信息
        col_info_data = []
        for i, col in enumerate(df.columns):
            # 数据统计
            col_data = df.iloc[:, i]
            total_count = len(col_data)
            non_empty_count = col_data.notna().sum()
            empty_ratio = (total_count - non_empty_count) / total_count * 100 if total_count > 0 else 0
            
            # 数据示例（更多样本）
            sample_data = col_data.dropna().head(5).tolist()
            sample_str = ', '.join([str(x)[:20] for x in sample_data])
            
            # 数据类型分析
            data_types = set()
            for val in sample_data[:3]:
                if pd.isna(val):
                    continue
                val_str = str(val).strip()
                if val_str.isdigit():
                    data_types.add('数字')
                elif len(val_str) == 18 and val_str.isalnum():
                    data_types.add('身份证')
                elif len(val_str) == 11 and val_str.isdigit():
                    data_types.add('手机号')
                elif any(name_word in val_str for name_word in ['先生', '女士', '教授', '博士', '医生']):
                    data_types.add('姓名')
                else:
                    data_types.add('文本')
            
            # 智能推荐标记
            recommendation = ""
            if detected_mapping:
                for req_col, mapped_idx in detected_mapping.items():
                    if mapped_idx == i:
                        conf = confidence_scores.get(req_col, 0)
                        recommendation = f"🤖推荐: {req_col} (置信度: {conf:.2f})"
                        break
            
            col_info_data.append({
                "列索引": f"列 {i}",
                "列名": str(col)[:30],
                "数据完整度": f"{non_empty_count}/{total_count} ({100-empty_ratio:.1f}%)",
                "数据类型": ', '.join(data_types) if data_types else '未知',
                "数据示例": sample_str[:50] + "..." if len(sample_str) > 50 else sample_str,
                "智能推荐": recommendation
            })
        
        # 使用表格显示列信息 - 改用HTML表格避免pyarrow问题
        st.markdown("**列信息详表：**")
        for item in col_info_data:
            with st.container():
                cols = st.columns([1, 2, 2, 1, 3, 2])
                with cols[0]:
                    st.write(f"**{item['列索引']}**")
                with cols[1]:
                    st.write(f"`{item['列名']}`")
                with cols[2]:
                    st.write(item['数据完整度'])
                with cols[3]:
                    st.write(item['数据类型'])
                with cols[4]:
                    st.write(f"_{item['数据示例']}_")
                with cols[5]:
                    if item['智能推荐']:
                        st.success(item['智能推荐'])
                st.divider()
        
        # 添加数据质量总览
        st.write("📊 **数据质量总览：**")
        quality_cols = st.columns(3)
        with quality_cols[0]:
            st.metric("总列数", len(df.columns))
        with quality_cols[1]:
            st.metric("总行数", len(df))
        with quality_cols[2]:
            avg_completeness = df.notna().mean().mean() * 100
            st.metric("平均完整度", f"{avg_completeness:.1f}%")
    
    st.markdown("### 🎯 请为每个必需字段选择对应的列：")
    
    # 加载已保存的映射配置
    saved_mapping = load_column_mapping()
    
    # 快速操作区域
    st.markdown("### 🚀 快速操作")
    
    # 智能推荐快速应用
    if detected_mapping and len(detected_mapping) >= 2:
        quick_cols = st.columns([2, 1, 1])
        with quick_cols[0]:
            st.write("**一键应用智能推荐：**")
        with quick_cols[1]:
            if st.button("✨ 应用推荐映射", type="primary", use_container_width=True):
                mapped_df = apply_manual_mapping(df, detected_mapping)
                if mapped_df is not None:
                    if save_column_mapping(detected_mapping):
                        st.success("✅ 智能推荐映射已应用并保存！")
                    else:
                        st.success("✅ 智能推荐映射已应用！")
                    st.session_state.mapped_df = mapped_df
                    st.session_state.mapping_applied = True
                    st.rerun()
        with quick_cols[2]:
            st.write("")
    
    # 预设配置快速选择
    st.write("**或选择常见格式预设：**")
    preset_cols = st.columns([3, 1, 1])
    with preset_cols[0]:
        preset_options = ['请选择预设格式'] + list(PRESET_CONFIGURATIONS.keys())
        selected_preset = st.selectbox(
            "选择预设配置",
            preset_options,
            key="preset_selector",
            help="选择常见的Excel格式预设，快速配置列映射"
        )
        if selected_preset != '请选择预设格式':
            preset_info = PRESET_CONFIGURATIONS[selected_preset]
            st.info(f"📋 {preset_info['description']}")
    
    with preset_cols[1]:
        if st.button("🔧 应用预设", disabled=(selected_preset == '请选择预设格式'), use_container_width=True):
            if selected_preset != '请选择预设格式':
                preset_mapping = PRESET_CONFIGURATIONS[selected_preset]['mapping']
                # 检查预设映射是否适用于当前数据
                max_col_index = max(preset_mapping.values())
                if max_col_index < len(df.columns):
                    mapped_df = apply_manual_mapping(df, preset_mapping)
                    if mapped_df is not None:
                        if save_column_mapping(preset_mapping):
                            st.success(f"✅ 预设格式 '{selected_preset}' 已应用并保存！")
                        else:
                            st.success(f"✅ 预设格式 '{selected_preset}' 已应用！")
                        st.session_state.mapped_df = mapped_df
                        st.session_state.mapping_applied = True
                        st.rerun()
                    else:
                        st.error("❌ 预设格式应用失败，请检查数据格式")
                else:
                    st.error(f"❌ 预设格式需要至少 {max_col_index + 1} 列，但当前只有 {len(df.columns)} 列")
    
    with preset_cols[2]:
        st.write("")
    
    st.divider()
    
    st.markdown("### 🎯 手动调整映射（可选）")
    
    # 创建列选择界面
    column_mapping = {}
    col_options = [f"列 {i} ({col})" for i, col in enumerate(df.columns)]
    
    # 使用列布局使界面更紧凑
    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)
    
    with col1:
        required_col = REQUIRED_COLUMNS[0]  # 姓名
        # 优先使用智能推荐，其次使用保存的配置
        default_index = detected_mapping.get(required_col, saved_mapping.get(required_col, 0))
        if default_index >= len(col_options):
            default_index = 0
        
        # 添加推荐标识
        label = f"👤 {required_col}"
        if required_col in detected_mapping:
            conf = confidence_scores.get(required_col, 0)
            label += f" 🤖(推荐: {conf:.2f})"
            
        selected = st.selectbox(
            label,
            col_options,
            index=default_index,
            key=f"mapping_{required_col}",
            help="选择包含姓名信息的列"
        )
        column_mapping[required_col] = int(selected.split(' ')[1])
    
    with col2:
        required_col = REQUIRED_COLUMNS[1]  # 身份证
        default_index = detected_mapping.get(required_col, saved_mapping.get(required_col, 1))
        if default_index >= len(col_options):
            default_index = 1 if len(col_options) > 1 else 0
            
        label = f"🆔 {required_col}"
        if required_col in detected_mapping:
            conf = confidence_scores.get(required_col, 0)
            label += f" 🤖(推荐: {conf:.2f})"
            
        selected = st.selectbox(
            label,
            col_options,
            index=default_index,
            key=f"mapping_{required_col}",
            help="选择包含身份证号的列"
        )
        column_mapping[required_col] = int(selected.split(' ')[1])
    
    with col3:
        required_col = REQUIRED_COLUMNS[2]  # 手机号
        default_index = detected_mapping.get(required_col, saved_mapping.get(required_col, 2))
        if default_index >= len(col_options):
            default_index = 2 if len(col_options) > 2 else 0
            
        label = f"📱 {required_col}"
        if required_col in detected_mapping:
            conf = confidence_scores.get(required_col, 0)
            label += f" 🤖(推荐: {conf:.2f})"
            
        selected = st.selectbox(
            label,
            col_options,
            index=default_index,
            key=f"mapping_{required_col}",
            help="选择包含手机号码的列"
        )
        column_mapping[required_col] = int(selected.split(' ')[1])
    
    with col4:
        required_col = REQUIRED_COLUMNS[3]  # 销售手机
        default_index = detected_mapping.get(required_col, saved_mapping.get(required_col, 3))
        if default_index >= len(col_options):
            default_index = 3 if len(col_options) > 3 else 0
            
        label = f"📞 {required_col}"
        if required_col in detected_mapping:
            conf = confidence_scores.get(required_col, 0)
            label += f" 🤖(推荐: {conf:.2f})"
            
        selected = st.selectbox(
            label,
            col_options,
            index=default_index,
            key=f"mapping_{required_col}",
            help="选择包含销售手机号的列（用于接收出票短信）"
        )
        column_mapping[required_col] = int(selected.split(' ')[1])
    
    # 操作按钮
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
    
    with col_btn1:
        if st.button("🔍 预览映射结果", use_container_width=True):
            preview_df = apply_manual_mapping(df, column_mapping)
            if preview_df is not None:
                st.write("📊 **映射后的数据预览：**")
                # 使用安全的预览方式
                preview_data = preview_df.head()
                for i, (idx, row) in enumerate(preview_data.iterrows()):
                    with st.expander(f"预览第 {i+1} 行", expanded=(i < 2)):
                        for col in REQUIRED_COLUMNS:
                            if col in preview_df.columns:
                                value = str(row[col]) if pd.notna(row[col]) else "(空值)"
                                st.write(f"**{col}:** {value}")
                
                # 验证数据质量
                st.write("📈 **数据质量检查：**")
                for col in REQUIRED_COLUMNS:
                    non_empty = preview_df[col].notna().sum()
                    total = len(preview_df)
                    percentage = (non_empty / total * 100) if total > 0 else 0
                    st.write(f"  • {col}: {non_empty}/{total} 行有数据 ({percentage:.1f}%)")
    
    with col_btn2:
        if st.button("✅ 应用此映射", type="primary", use_container_width=True):
            mapped_df = apply_manual_mapping(df, column_mapping)
            if mapped_df is not None:
                # 保存映射配置
                if save_column_mapping(column_mapping):
                    st.success("✅ 列映射配置已保存，下次使用时会自动应用！")
                else:
                    st.warning("⚠️ 映射配置保存失败，但本次映射仍然有效。")
                
                # 保存到session_state而不是直接返回
                st.session_state.mapped_df = mapped_df
                st.session_state.mapping_applied = True
                st.success("🎉 映射应用成功！页面即将刷新...")
                st.rerun()  # 重新运行页面以应用映射结果
    
    with col_btn3:
        if st.button("🔄 重置为默认配置", use_container_width=True):
            if save_column_mapping(DEFAULT_COLUMN_MAPPING):
                st.success("✅ 已重置为默认配置")
                st.rerun()
    
    return None, ["等待用户手动映射"]

def smart_read_excel(uploaded_file):
    """智能读取Excel文件，尝试多种参数组合和引擎"""
    engines = ['calamine', 'openpyxl']
    header_options = [None, 0, 1, 2, 3, 4]  # 扩展header选项
    skiprows_options = [0, 1, 2, 3]  # 添加skiprows选项
    
    # 首先尝试读取原始数据查看结构
    st.write("🔍 分析Excel文件结构...")
    try:
        # 读取前10行原始数据
        raw_df = pd.read_excel(uploaded_file, header=None, nrows=10, engine='calamine')
        st.write("📋 Excel文件前10行原始数据:")
        # 使用安全的方式显示数据，避免pyarrow问题
        if not raw_df.empty:
            st.write(f"数据形状: {raw_df.shape}")
            for i in range(min(5, len(raw_df))):
                with st.expander(f"第 {i+1} 行数据", expanded=(i < 2)):
                    for j, col_val in enumerate(raw_df.iloc[i]):
                        st.write(f"列 {j}: {str(col_val)[:100]}")
        else:
            st.write("数据为空")
        
        # 尝试检测可能的工作表
        try:
            xl_file = pd.ExcelFile(uploaded_file)
            if len(xl_file.sheet_names) > 1:
                st.write(f"📊 检测到多个工作表: {xl_file.sheet_names}")
        except:
            pass
            
    except Exception as e:
        st.write(f"⚠️ 无法读取原始数据: {str(e)}")
    
    best_result = None
    best_score = 0
    
    for engine in engines:
        st.write(f"🔍 尝试使用 {engine} 引擎...")
        
        for skiprows in skiprows_options:
            for header_val in header_options:
                try:
                    st.write(f"  📋 尝试 skiprows={skiprows}, header={header_val}...")
                    
                    # 尝试读取数据
                    if skiprows > 0:
                        df = pd.read_excel(uploaded_file, header=header_val, skiprows=skiprows, engine=engine)
                    else:
                        df = pd.read_excel(uploaded_file, header=header_val, engine=engine)
                    
                    # 跳过空的DataFrame
                    if df.empty:
                        st.write(f"    ⚠️ 读取结果为空")
                        continue
                    
                    # 清理列名
                    original_columns = list(df.columns)
                    if df.columns.dtype == 'object':
                        df.columns = df.columns.astype(str).str.strip()
                    
                    # 显示详细信息
                    st.write(f"    📊 数据形状: {df.shape}")
                    st.write(f"    📋 原始列名: {original_columns[:5]}...")
                    st.write(f"    🧹 清理后列名: {list(df.columns)[:5]}...")
                    
                    # 显示前几行数据
                    if not df.empty:
                        st.write("    📄 前3行数据:")
                        # 使用安全的方式显示数据，避免pyarrow问题
                        preview_df = df.head(3)
                        for i in range(len(preview_df)):
                            with st.expander(f"    第 {i+1} 行", expanded=(i == 0)):
                                for col in preview_df.columns:
                                    value = str(preview_df.iloc[i][col]) if pd.notna(preview_df.iloc[i][col]) else "(空值)"
                                    st.write(f"      {col}: {value[:50]}...")
                    
                    # 使用智能模糊匹配计算分数
                    detected_mapping, confidence_scores = smart_column_detection(df)
                    
                    # 计算总体匹配分数
                    score = len(detected_mapping)
                    avg_confidence = sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0
                    total_score = score + avg_confidence
                    
                    found_cols = list(detected_mapping.keys())
                    
                    # 额外加分：列名不是Unnamed
                    unnamed_count = sum(1 for col in df.columns if 'Unnamed' in str(col))
                    if unnamed_count < len(df.columns) * 0.5:  # 如果Unnamed列少于一半
                        total_score += 0.5
                    
                    st.write(f"    🎯 智能匹配分数: {total_score:.2f} (找到 {score}/{len(REQUIRED_COLUMNS)} 列)")
                    st.write(f"    📋 匹配详情: {found_cols}")
                    if confidence_scores:
                        st.write(f"    📊 置信度: {', '.join([f'{k}: {v:.2f}' for k, v in confidence_scores.items()])}")
                    
                    if total_score > best_score:
                        best_score = total_score
                        # 如果找到了智能匹配，应用映射
                        if detected_mapping:
                            mapped_df = apply_manual_mapping(df, detected_mapping)
                            if mapped_df is not None:
                                best_result = (mapped_df.copy(), engine, skiprows, header_val, [], detected_mapping)
                            else:
                                best_result = (df.copy(), engine, skiprows, header_val, found_cols, detected_mapping)
                        else:
                            best_result = (df.copy(), engine, skiprows, header_val, found_cols, {})
                        st.write(f"    ⭐ 当前最佳结果！")
                    
                    # 如果找到所有必需列，直接返回
                    if score == len(REQUIRED_COLUMNS):
                        if detected_mapping:
                            mapped_df = apply_manual_mapping(df, detected_mapping)
                            if mapped_df is not None:
                                st.success(f"🎉 智能匹配成功！找到所有必需列，置信度: {avg_confidence:.2f}")
                                st.info(f"📋 使用参数: engine={engine}, skiprows={skiprows}, header={header_val}")
                                return mapped_df, None
                        st.success(f"🎉 找到所有必需列！使用 engine={engine}, skiprows={skiprows}, header={header_val}")
                        return df, None
                        
                except Exception as e:
                    st.write(f"    ❌ 失败: {str(e)[:100]}...")
                    continue
    
    # 返回最佳结果
    if best_result:
        if len(best_result) == 6:  # 新格式：包含detected_mapping
            df, engine, skiprows, header_val, found_cols, detected_mapping = best_result
            missing_cols = [col for col in REQUIRED_COLUMNS if col not in found_cols]
            
            if detected_mapping and not missing_cols:
                st.success(f"🎉 智能匹配成功！自动识别所有必需列")
                st.info(f"📈 使用参数: engine={engine}, skiprows={skiprows}, header={header_val}")
                st.info(f"🔗 智能映射: {', '.join([f'{k}→列{v}' for k, v in detected_mapping.items()])}")
                return df, None
            elif detected_mapping:
                st.info(f"📈 智能匹配部分成功: engine={engine}, skiprows={skiprows}, header={header_val}")
                st.info(f"✅ 找到列: {found_cols}")
                st.info(f"🔗 智能映射: {', '.join([f'{k}→列{v}' for k, v in detected_mapping.items()])}")
                if missing_cols:
                    st.warning(f"⚠️ 仍缺少列: {missing_cols}")
                return df, missing_cols
        else:  # 旧格式兼容
            df, engine, skiprows, header_val, found_cols = best_result
            missing_cols = [col for col in REQUIRED_COLUMNS if col not in found_cols]
            
        st.info(f"📈 使用最佳匹配结果: engine={engine}, skiprows={skiprows}, header={header_val}")
        st.info(f"✅ 找到列: {found_cols}")
        if missing_cols:
            st.warning(f"⚠️ 仍缺少列: {missing_cols}")
        return df, missing_cols
    
    # 如果所有尝试都失败，尝试使用保存的映射配置
    st.write("🔧 尝试使用保存的列映射配置...")
    try:
        # 读取原始数据（不指定header）
        df_raw = pd.read_excel(uploaded_file, header=None, engine='calamine')
        if not df_raw.empty:
            # 尝试使用保存的映射配置
            saved_mapping = load_column_mapping()
            if saved_mapping:
                st.write(f"📋 找到保存的映射配置: {saved_mapping}")
                mapped_df = apply_manual_mapping(df_raw, saved_mapping)
                if mapped_df is not None and not mapped_df.empty:
                    # 检查映射后的数据是否有效
                    valid_data = True
                    for col in REQUIRED_COLUMNS:
                        if col not in mapped_df.columns or mapped_df[col].isna().all():
                            valid_data = False
                            break
                    
                    if valid_data:
                        st.success("🎉 使用保存的列映射配置成功！")
                        return mapped_df, None
                    else:
                        st.write("⚠️ 保存的映射配置无效，需要重新配置")
            
            # 如果保存的配置无效或不存在，显示手动映射界面
            st.write("🔧 显示手动列映射界面...")
            return show_manual_mapping_ui(df_raw)
            
    except Exception as e:
        st.write(f"❌ 读取文件失败: {str(e)}")
    
    return None, ["无法读取文件或识别正确的列名"]

# --- Part 1: 上传文件与选择专家 ---
st.header("第一步：上传客户信息表并选择专家")

uploaded_file = st.file_uploader("请上传包含专家信息的Excel文件 (.xlsx)", type=['xlsx'])

if 'expert_data' not in st.session_state:
    st.session_state.expert_data = None

if uploaded_file is not None:
    # 检查是否已有映射结果在session_state中
    if hasattr(st.session_state, 'mapping_applied') and st.session_state.mapping_applied and hasattr(st.session_state, 'mapped_df'):
        # 使用已映射的数据
        df = st.session_state.mapped_df
        missing_cols = None
        st.success("✅ 使用已配置的列映射")
        
        # 显示当前数据概览
        with st.expander("📊 当前数据概览", expanded=False):
            st.write(f"**数据行数：** {len(df)} 行")
            st.write("**列信息：**")
            for col in REQUIRED_COLUMNS:
                if col in df.columns:
                    non_empty = df[col].notna().sum()
                    st.write(f"  • {col}: {non_empty}/{len(df)} 行有数据")
                    
                    # 特别显示手机号码字段的详细信息
                    if col in ['手机号码 (必填)', '销售手机']:
                        phone_data = df[col].dropna()
                        if len(phone_data) > 0:
                            st.write(f"    📱 {col} 样本数据:")
                            for i, phone in enumerate(phone_data.head(3)):
                                st.write(f"      - 第{i+1}个: {repr(phone)} (类型: {type(phone).__name__})")
            
            # 使用安全的数据显示方式
            st.write("**数据预览（前5行）：**")
            preview_data = df.head()
            for i, (idx, row) in enumerate(preview_data.iterrows()):
                with st.expander(f"第 {i+1} 行数据", expanded=(i < 2)):
                    for col in REQUIRED_COLUMNS:
                        if col in df.columns:
                            value = str(row[col]) if pd.notna(row[col]) else "(空值)"
                            # 对手机号码字段显示更详细信息
                            if col in ['手机号码 (必填)', '销售手机'] and pd.notna(row[col]):
                                original = row[col]
                                cleaned = clean_data_field(original, '手机号码')
                                st.write(f"**{col}:** {value}")
                                st.write(f"  - 原始值: {repr(original)}")
                                st.write(f"  - 清洗后: {repr(cleaned)}")
                            else:
                                st.write(f"**{col}:** {value}")
            
            # 提供重新映射选项
            if st.button("🔄 重新进行列映射"):
                if hasattr(st.session_state, 'mapped_df'):
                    del st.session_state.mapped_df
                if hasattr(st.session_state, 'mapping_applied'):
                    del st.session_state.mapping_applied
                st.rerun()
    else:
        # 重置映射状态
        st.session_state.mapping_applied = False
        
        # 显示文件处理状态
        with st.spinner("🔄 正在分析Excel文件..."):
            with st.expander("📊 Excel文件读取调试信息", expanded=False):
                df, missing_cols = smart_read_excel(uploaded_file)
        
    if df is not None:
        if missing_cols and missing_cols != ["等待用户手动映射"]:
            st.error(f"⚠️ 自动识别部分失败！缺少以下必需列: {', '.join(missing_cols)}")
            
            with st.expander("🔍 详细诊断信息", expanded=True):
                st.write("📋 **检测到的所有列名:**")
                col_analysis = []
                for i, col in enumerate(df.columns):
                    # 分析每列可能的用途
                    analysis = "未知"
                    col_str = str(col).lower().strip()
                    if any(name_word in col_str for name_word in ['姓名', '名字', 'name', '专家']):
                        analysis = "🤔 可能是姓名列"
                    elif any(id_word in col_str for id_word in ['身份证', 'id', '证件']):
                        analysis = "🤔 可能是身份证列"
                    elif any(phone_word in col_str for phone_word in ['手机', '电话', 'phone', '联系']):
                        analysis = "🤔 可能是手机号列"
                    
                    col_analysis.append({
                        "列索引": f"列 {i}",
                        "列名": str(col),
                        "分析": analysis
                    })
                
                # 直接显示列分析结果，避免DataFrame转换问题
                st.markdown("**列分析结果：**")
                for item in col_analysis:
                    st.write(f"• {item['列索引']}: '{item['列名']}' - {item['分析']}")
                
                # 使用更安全的方式显示表格，避免pyarrow问题
                if len(col_analysis) > 0:
                    st.markdown("**详细分析表格：**")
                    for i, item in enumerate(col_analysis):
                        with st.container():
                            cols = st.columns([1, 3, 6])
                            with cols[0]:
                                st.write(f"**{item['列索引']}**")
                            with cols[1]:
                                st.write(f"`{item['列名']}`")
                            with cols[2]:
                                st.write(item['分析'])
                            if i < len(col_analysis) - 1:
                                st.divider()
                
                st.markdown("""
                ### 🛠️ 解决方案
                1. **智能推荐** - 系统已尝试智能匹配，请查看上方推荐结果
                2. **预设格式** - 尝试使用常见格式预设快速配置
                3. **手动映射** - 在下方手动选择正确的列对应关系
                4. **文件检查** - 确认Excel文件包含完整的姓名、身份证、手机号信息
                """)
            
            # 不要停止，让用户继续使用手动映射
            st.info("💡 **别担心！** 请使用下方的手动映射功能来完成配置。")
        elif missing_cols == ["等待用户手动映射"]:
            # 显示手动映射界面，等待用户操作
            st.info("📝 请在上方完成列映射配置后，页面将自动刷新。")
            st.stop()
        else:
            # 成功读取，继续处理
            df.dropna(subset=['姓名*'], inplace=True)
            expert_list = ["---请选择---"] + df['姓名*'].tolist()
            selected_expert_name = st.selectbox("请从表格中选择一位专家：", expert_list)

            if selected_expert_name and selected_expert_name != "---请选择---":
                selected_row = df[df['姓名*'] == selected_expert_name].iloc[0]
                st.session_state.expert_data = selected_row
                
                # 调试信息：显示选中的专家数据
                with st.expander("🔍 调试信息：选中的专家原始数据", expanded=False):
                    st.write("**DataFrame列名：**")
                    st.write(list(df.columns))
                    st.write("\n**选中专家的原始数据：**")
                    for col in df.columns:
                        value = selected_row[col]
                        st.write(f"- {col}: {repr(value)} (类型: {type(value).__name__})")
                    
                    # 检查手机号码字段是否存在且有值
                    phone_col = '手机号码 (必填)'
                    if phone_col in df.columns:
                        phone_value = selected_row[phone_col]
                        st.write(f"\n**手机号码字段详细信息：**")
                        st.write(f"- 原始值: {repr(phone_value)}")
                        st.write(f"- 是否为空: {pd.isna(phone_value)}")
                        st.write(f"- 转换为字符串: {repr(str(phone_value))}")
                        if not pd.isna(phone_value):
                            cleaned = clean_data_field(phone_value, '手机号码')
                            st.write(f"- 清洗后: {repr(cleaned)}")
                    else:
                        st.error(f"❌ 未找到手机号码字段 '{phone_col}'")
                        st.write(f"可用字段: {list(df.columns)}")
    else:
        st.error("❌ 无法读取Excel文件，请检查文件格式。")
        st.session_state.expert_data = None
else:
    # 清除映射状态当没有文件上传时
    if hasattr(st.session_state, 'mapping_applied'):
        st.session_state.mapping_applied = False
    if hasattr(st.session_state, 'mapped_df'):
        del st.session_state.mapped_df
    st.session_state.expert_data = None
    
    # 显示详细使用说明
    st.info("📝 **使用说明：** 请上传包含专家信息的Excel文件，系统将智能识别姓名、身份证和手机号码列。")
    
    with st.expander("📖 详细说明和常见问题", expanded=False):
        st.markdown("""
        ### 📋 支持的文件格式
        - ✅ Excel文件 (.xlsx)
        - ✅ 支持多种表头行位置
        - ✅ 支持中英文列名
        
        ### 🎯 必需的列信息
        系统需要识别以下四类信息：
        1. **姓名信息** - 支持：姓名、名字、专家姓名、参会人姓名等
        2. **身份证信息** - 支持：身份证、身份证号、证件号、ID等
        3. **手机号信息** - 支持：手机、手机号、电话、联系电话等
        4. **销售手机信息** - 支持：销售手机、票务手机、出票手机、第二手机等
        
        ### 🚀 智能识别功能
        - 🤖 **智能模糊匹配** - 自动识别常见列名变体
        - 📊 **数据质量分析** - 评估数据完整度和类型
        - 🔧 **预设格式支持** - 快速应用常见Excel格式
        - 💾 **配置记忆** - 保存映射配置供下次使用
        
        ### ❓ 常见问题解决
        - **自动识别失败？** → 系统提供智能推荐和手动映射
        - **列名不标准？** → 支持模糊匹配，如"姓名"匹配"专家姓名"
        - **表头位置不对？** → 自动尝试多种表头行位置
        - **数据格式复杂？** → 提供预设格式快速配置
        
        ### 💡 使用技巧
        1. 确保Excel文件中包含完整的姓名、身份证、手机号信息
        2. 如果有多个工作表，请使用第一个工作表
        3. 建议将重要信息放在前几列以提高识别准确率
        """)
    
    # 添加文件要求提示
    st.markdown("""
    <div style="background-color: #e8f4fd; padding: 15px; border-radius: 10px; border-left: 4px solid #1f77b4; color: #1a1a1a;">
    <h4 style="margin-top: 0; color: #1f77b4;">📁 文件上传要求</h4>
    <ul style="color: #333333;">
        <li><strong>文件格式：</strong> 仅支持 .xlsx 格式</li>
        <li><strong>数据要求：</strong> 包含姓名、身份证、手机号、销售手机四列信息</li>
        <li><strong>销售手机：</strong> 用于接收最终出票短信的手机号码</li>
        <li><strong>数据质量：</strong> 建议数据完整度 > 80%</li>
        <li><strong>文件大小：</strong> 建议 < 10MB，支持最多1000行数据</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)


st.markdown("\n---\n")

# --- Part 2: 生成询价信息 (自动填充) ---
st.header("第二步：生成发送给票务的【询价信息】")

# 使用全宽布局

# 从session state获取数据时，使用正确的列名（包含空格）
def safe_get_value(data, key, default=''):
    """安全获取数据值，避免显示nan或None"""
    if data is None:
        return default
    value = data.get(key, default)
    if pd.isna(value) or value is None:
        return default
    str_value = str(value).strip()
    if str_value.lower() in ['nan', 'none', 'null', '']:
        return default
    # 如果default是None，直接返回原始值用于进一步处理
    if default is None:
        return value
    return str_value

def validate_phone_number(phone_str):
    """验证手机号码格式是否为11位数字"""
    if not phone_str or not isinstance(phone_str, str):
        return False
    
    # 清理手机号码：去除空格、连字符、括号等
    clean_phone = re.sub(r'[\s\-\(\)\+\.]', '', phone_str.strip())
    
    # 去除国家代码+86
    if clean_phone.startswith('+86'):
        clean_phone = clean_phone[3:]
    elif clean_phone.startswith('86') and len(clean_phone) == 13:
        clean_phone = clean_phone[2:]
    
    # 检查是否为11位数字
    return len(clean_phone) == 11 and clean_phone.isdigit()

expert_name_val = safe_get_value(st.session_state.expert_data, '姓名*')
expert_id_val = safe_get_value(st.session_state.expert_data, '身份证 (出机票必须填写)')
expert_phone_val = safe_get_value(st.session_state.expert_data, '手机号码 (必填)')
sales_phone_val = safe_get_value(st.session_state.expert_data, '销售手机')

# 调试信息：显示实际提取的数据
if st.session_state.expert_data is not None:
    with st.expander("🔍 调试信息：实际提取的数据", expanded=False):
        st.write("**原始专家数据：**")
        for key, value in st.session_state.expert_data.items():
            st.write(f"- {key}: {repr(value)}")
outbound_flight_val = safe_get_value(st.session_state.expert_data, '去程车次/航班')
return_flight_val = safe_get_value(st.session_state.expert_data, '返程车次/航班')

# 获取站点信息
outbound_from_val = safe_get_value(st.session_state.expert_data, '去程出发站')
outbound_to_val = safe_get_value(st.session_state.expert_data, '去程到达站')
return_from_val = safe_get_value(st.session_state.expert_data, '返程出发站')
return_to_val = safe_get_value(st.session_state.expert_data, '返程到达站')

# 获取并解析日期数据
outbound_date_val = None
return_date_val = None
if st.session_state.expert_data is not None:
    # 解析去程出发日期
    outbound_date_raw = safe_get_value(st.session_state.expert_data, '去程出发日期')
    if outbound_date_raw:
        outbound_date_val = parse_date_field(outbound_date_raw)
    
    # 解析返程出发日期
    return_date_raw = safe_get_value(st.session_state.expert_data, '返程出发日期')
    if return_date_raw:
        return_date_val = parse_date_field(return_date_raw)

# 获取时间数据（字符串格式）
outbound_time_val = safe_get_value(st.session_state.expert_data, '去程出发时间')
outbound_arrival_time_val = safe_get_value(st.session_state.expert_data, '去程到达时间')
return_time_val = safe_get_value(st.session_state.expert_data, '返程出发时间')
return_arrival_time_val = safe_get_value(st.session_state.expert_data, '返程到达时间')

# 调试信息显示（仅在有数据时显示）
if st.session_state.expert_data is not None:
    with st.expander("🔍 数据提取调试信息", expanded=False):
        st.write("\n**处理后的值：**")
        st.write(f"- 姓名: {repr(expert_name_val)}")
        st.write(f"- 身份证: {repr(expert_id_val)}")
        st.write(f"- 手机号码: {repr(expert_phone_val)}")
        st.write(f"- 销售手机: {repr(sales_phone_val)}")
        st.write("\n**时间字段提取结果：**")
        st.write(f"- 去程出发时间: {repr(outbound_time_val)}")
        st.write(f"- 去程到达时间: {repr(outbound_arrival_time_val)}")
        st.write(f"- 返程出发时间: {repr(return_time_val)}")
        st.write(f"- 返程到达时间: {repr(return_arrival_time_val)}")

# 专家基本信息
st.subheader("专家基本信息（自动填充）：")
col_info1, col_info2 = st.columns(2)
with col_info1:
    expert_name = st.text_input("专家姓名*", value=expert_name_val)
    expert_id = st.text_input("身份证号*", value=expert_id_val)
with col_info2:
    # 专家手机号码输入框（带验证）
    expert_phone = st.text_input("手机号码*", value=expert_phone_val, key="expert_phone_input")
    
    # 验证专家手机号码格式
    if expert_phone and not validate_phone_number(expert_phone):
        st.error("❌ 手机号码格式不正确，请输入11位数字")
    
    # 销售手机号码输入框（带验证）
    sales_phone = st.text_input("销售手机（接收出票短信）", value=sales_phone_val, help="用于接收最终出票短信的手机号码", key="sales_phone_input")
    
    # 验证销售手机号码格式（仅在有输入时验证）
    if sales_phone and sales_phone.strip() and not validate_phone_number(sales_phone):
        st.error("❌ 销售手机号码格式不正确，请输入11位数字")

st.markdown("---")

# 交通信息输入
st.subheader("交通信息详细填写：")

# 去程信息
st.markdown("### 🛫 去程信息")
col_out1, col_out2, col_out3, col_out4 = st.columns(4)
with col_out1:
    outbound_transport = st.selectbox("交通方式", ["飞机", "高铁", "火车", "汽车"], key="outbound_transport")
    outbound_date = st.date_input("出发日期", value=outbound_date_val, key="outbound_date", help="已从表格自动填充，可手动修改" if outbound_date_val else None)
with col_out2:
    outbound_flight = st.text_input("车次/航班号", value=outbound_flight_val, placeholder="如：CA1234", key="outbound_flight", help="已从表格自动填充，可手动修改")
    outbound_time = st.text_input("出发时间", value=outbound_time_val, key="outbound_time", placeholder="如：20:15", help="已从表格自动填充，可手动修改" if outbound_time_val else None)
with col_out3:
    outbound_from = st.text_input("出发站/机场", value=outbound_from_val, placeholder="如：北京首都机场", key="outbound_from", help="已从表格自动填充，可手动修改" if outbound_from_val else None)
    outbound_to = st.text_input("到达站/机场", value=outbound_to_val, placeholder="如：上海虹桥机场", key="outbound_to", help="已从表格自动填充，可手动修改" if outbound_to_val else None)
with col_out4:
    outbound_arrival_time = st.text_input("到达时间", value=outbound_arrival_time_val, key="outbound_arrival_time", placeholder="如：22:40", help="已从表格自动填充，可手动修改" if outbound_arrival_time_val else None)

# 返程信息
st.markdown("### 🛬 返程信息")
col_ret1, col_ret2, col_ret3, col_ret4 = st.columns(4)
with col_ret1:
    return_transport = st.selectbox("交通方式", ["飞机", "高铁", "火车", "汽车"], key="return_transport")
    return_date = st.date_input("出发日期", value=return_date_val, key="return_date", help="已从表格自动填充，可手动修改" if return_date_val else None)
with col_ret2:
    return_flight = st.text_input("车次/航班号", value=return_flight_val, placeholder="如：CA5678", key="return_flight", help="已从表格自动填充，可手动修改")
    return_time = st.text_input("出发时间", value=return_time_val, key="return_time", placeholder="如：15:45", help="已从表格自动填充，可手动修改" if return_time_val else None)
with col_ret3:
    return_from = st.text_input("出发站/机场", value=return_from_val, placeholder="如：上海虹桥机场", key="return_from", help="已从表格自动填充，可手动修改" if return_from_val else None)
    return_to = st.text_input("到达站/机场", value=return_to_val, placeholder="如：北京首都机场", key="return_to", help="已从表格自动填充，可手动修改" if return_to_val else None)
with col_ret4:
    return_arrival_time = st.text_input("到达时间", value=return_arrival_time_val, key="return_arrival_time", placeholder="如：18:10", help="已从表格自动填充，可手动修改" if return_arrival_time_val else None)

st.markdown("---")

# 生成询价信息
st.subheader("生成的询价信息：")
if st.button("✅ 点击生成询价信息", type="primary"):
    if not expert_name or not expert_id or not expert_phone:
        st.warning("专家姓名、身份证号和手机号为必填项。请先上传表格并选择专家。")
    else:
        # 格式化日期为xx月xx日
        def format_date(date_obj):
            if date_obj:
                return f"{date_obj.month}月{date_obj.day}日"
            return ""
        
        # 格式化时间字符串为HH:MM格式
        def format_time(time_str):
            if time_str and time_str.strip():
                time_clean = time_str.strip()
                # 如果时间包含秒数（如HH:MM:SS），只取前5位（HH:MM）
                if ':' in time_clean:
                    parts = time_clean.split(':')
                    if len(parts) >= 2:
                        # 确保小时和分钟都是两位数
                        hour = parts[0].zfill(2)
                        minute = parts[1].zfill(2)
                        return f"{hour}:{minute}"
                return time_clean
            return ""
        
        # 按照新格式生成询价信息
        inquiry_text = f"{expert_name} {expert_id}\n"
        
        # 手机号码行
        phone_line = expert_phone
        if sales_phone and sales_phone.strip():
            phone_line += f"/{sales_phone}"
        inquiry_text += phone_line + "\n"
        
        # 去程信息
        if outbound_transport and outbound_date:
            outbound_line = f"{outbound_transport} {format_date(outbound_date)}"
            if outbound_flight:
                outbound_line += f" {outbound_flight}"
            if outbound_time:
                outbound_line += f" {format_time(outbound_time)}"
            if outbound_from:
                outbound_line += f" {outbound_from}"
            if outbound_to:
                outbound_line += f" {outbound_to}"
            if outbound_arrival_time:
                outbound_line += f" {format_time(outbound_arrival_time)}"
            inquiry_text += outbound_line + "\n"
        
        # 返程信息
        if return_transport and return_date:
            return_line = f"{return_transport} {format_date(return_date)}"
            if return_flight:
                return_line += f" {return_flight}"
            if return_time:
                return_line += f" {format_time(return_time)}"
            if return_from:
                return_line += f" {return_from}"
            if return_to:
                return_line += f" {return_to}"
            if return_arrival_time:
                return_line += f" {format_time(return_arrival_time)}"
            inquiry_text += return_line
        
        st.code(inquiry_text, language="text")
        
        # 提示信息
        if sales_phone and sales_phone.strip():
            st.success("✅ 询价信息已生成！请点击右上角的复制按钮，然后将信息发送给票务。")
            st.info("💡 销售手机号将用于接收最终出票短信。")
        else:
            st.success("✅ 询价信息已生成！请点击右上角的复制按钮，然后将信息发送给票务。")
            st.warning("⚠️ 建议填写销售手机号，用于接收出票短信。")

st.markdown("\n---\n")

# --- Part 3: 处理票务回复 (功能不变) ---
st.header("第三步：处理票务回复，生成【专家确认信息】")

col3, col4 = st.columns(2)

with col3:
    st.subheader("请粘贴票务的完整回复：")
    agent_reply = st.text_area("（请将微信中票务的回复原文，包含价格，完整粘贴到此处）", height=250, key="agent_reply")

with col4:
    st.subheader("处理后可发给专家的信息：")
    if st.button("🪄 清洗价格并生成确认信息"):
        if agent_reply:
            # 更精确的价格清洗：只匹配明确的价格格式，避免误删航班时间等重要信息
            # 匹配模式：
            # 1. 数字+元（如：1110元、1120 元）
            # 2. 价格+冒号+数字（如：价格：1110、价格 1110）
            # 3. 单独一行的纯数字价格（如：单独一行的1110）
            # 4. 费用相关表述（如：费用1110、总计1110等）
            price_patterns = [
                r'\d+\s*元',  # 数字+元
                r'价格\s*[:：]?\s*\d+',  # 价格+数字
                r'费用\s*[:：]?\s*\d+',  # 费用+数字
                r'总计\s*[:：]?\s*\d+',  # 总计+数字
                r'合计\s*[:：]?\s*\d+',  # 合计+数字
                r'^\s*\d{4}\s*$',  # 单独一行的4位数字（价格）
                r'\b\d+\s*RMB\b',  # 数字+RMB
                r'\b\d+\s*rmb\b',  # 数字+rmb
            ]
            
            cleaned_text = agent_reply
            for pattern in price_patterns:
                cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.MULTILINE)
            # 保留航班号格式（如CA1234、MU5678等），只删除可能的6位纯数字价格代码
            cleaned_text = re.sub(r'(?<!\w)[0-9]{6}(?!\w)', '', cleaned_text)
            lines = cleaned_text.split('\n')
            non_empty_lines = [line.strip() for line in lines if line.strip()]
            final_text = '\n'.join(non_empty_lines)
            expert_confirmation_text = f"【请确认以下航班信息】\n{final_text}"
            st.code(expert_confirmation_text, language="text")
            st.success("价格已移除！请点击右上角复制按钮，将此信息发送给专家确认。")
        else:
            st.warning("请先在左侧粘贴票务的回复。")
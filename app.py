from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from dea_engine import (
    audit_dea_result,
    evaluate_dea,
    evaluate_malmquist,
    evaluate_sbm,
    load_table,
    make_demo_data,
    make_student_demo_data,
)


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

st.set_page_config(
    page_title="智能大学生学业成绩因素评估系统",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root { --primary:#3f73b8; --primary-dark:#2f5f9f; --accent:#6b7f98; --success:#2e8b72; --text:#273548; --muted:#6f7d8f; --line:#e3e7ed; }
    .stApp { background:#f6f7f9; color:var(--text); font-family:"Microsoft YaHei","Noto Sans SC","Segoe UI",sans-serif; }
    [data-testid="stHeader"] { background:#ffffff; border-bottom:1px solid #e8ebf0; }
    [data-testid="stSidebar"], section[data-testid="stSidebar"] { background:#3f485b; border-right:1px solid #323a4b; min-width:270px !important; max-width:270px !important; }
    [data-testid="stSidebar"] > div:first-child { padding-top:1rem; }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] li,
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
    [data-testid="stSidebar"] label { color:#e6ebf4 !important; font-size:14px; line-height:1.55; }
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"],
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p { color:#c1c9d8 !important; }
    [data-testid="stSidebar"] h3 { color:#ffffff !important; letter-spacing:.3px; margin:0 0 8px; }
    [data-testid="stSidebar"] hr { border-color:#62697c !important; margin:18px 0; }
    [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"], [data-testid="stSidebar"] .stMultiSelect [data-baseweb="select"] { background:#ffffff !important; background-color:#ffffff !important; border:1px solid #d8deea !important; border-radius:7px; min-height:42px; }
    [data-testid="stSidebar"] [data-baseweb="select"] * { color:#344054 !important; }
    [data-testid="stSidebar"] [data-baseweb="select"] svg { fill:#7890ac !important; color:#7890ac !important; }
    [data-testid="stSidebar"] [data-baseweb="tag"] { background:#e8f1ff !important; border:1px solid #b5cef9 !important; border-radius:6px !important; }
    [data-testid="stSidebar"] [data-baseweb="tag"] * { color:#2767c7 !important; fill:#2767c7 !important; }
    [data-testid="stSidebar"] [role="radiogroup"] label { color:#e6ebf4 !important; }
    [data-testid="stSidebar"] [role="radiogroup"] label p { color:#e6ebf4 !important; font-size:14px; }
    [data-baseweb="popover"] { background:#ffffff !important; border:1px solid #dfe5ee !important; box-shadow:0 8px 24px #1d2b3d1c !important; }
    [data-baseweb="popover"] [role="option"] { color:#344054 !important; background:#ffffff !important; }
    [data-baseweb="popover"] [role="option"]:hover { background:#eef5ff !important; }
    .side-brand { display:flex; align-items:center; gap:10px; margin:0 0 14px; }
    .side-brand-mark { width:34px; height:34px; border-radius:9px; display:grid; place-items:center; color:#ffffff; background:#6a9df4; font-weight:900; box-shadow:0 3px 10px #26324a55; }
    .side-brand-title { color:#ffffff; font-weight:800; letter-spacing:.5px; }
    .side-brand-sub { color:#bdc6d6; font-size:10px; letter-spacing:1.4px; margin-top:2px; }
    .side-section { color:#b9d3fb; font-size:11px; font-weight:800; letter-spacing:1.6px; text-transform:uppercase; margin:17px 0 7px; }
    .side-note { color:#e4e9f2; background:#42485a; border:1px solid #667086; border-radius:7px; padding:10px 11px; line-height:1.7; font-size:12px; }
    .block-container { padding-top:1.5rem; padding-bottom:3rem; max-width:1480px; }
    .topline { display:flex; justify-content:space-between; align-items:center; margin:22px -36px 20px; padding:12px 36px; min-height:68px; background:#ffffff; border-bottom:1px solid #e8ebf0; }
    .brand { display:flex; gap:14px; align-items:center; }
    .logo { width:46px; height:46px; border-radius:11px; display:grid; place-items:center; color:#ffffff;
            background:linear-gradient(145deg,#5b9cff,#7d77ed); box-shadow:0 4px 12px #497fe044; font-size:24px; font-weight:800; }
    .brand-title { font-size:22px; font-weight:800; letter-spacing:.5px; line-height:1.2; color:#253247; }
    .brand-sub { color:#7891af; font-size:11px; letter-spacing:3px; margin-top:5px; }
    .online { color:#238b70; border:1px solid #b9e5d9; background:#effbf7; border-radius:18px; padding:7px 13px; font-size:11px; letter-spacing:1px; }
    .hero { border:1px solid #e1e5eb; background:#ffffff; border-radius:7px;
            padding:22px 28px; margin:6px 0 18px; box-shadow:0 2px 9px #28384c0a; }
    .eyebrow { color:#4b8ff3; letter-spacing:2px; font-size:12px; font-weight:850; }
    .hero h1 { font-size:30px; margin:9px 0 8px; letter-spacing:.5px; color:#263448; }
    .hero p { color:#6f7d8f; max-width:920px; line-height:1.7; margin:0; font-size:14px; }
    .section-title { font-size:19px; font-weight:800; margin:18px 0 10px; color:#293648; }
    .section-note { color:#8190a2; font-size:12px; float:right; font-weight:500; }
    .kpi { background:#ffffff; border:1px solid #e1e5eb; border-radius:7px; border-top:3px solid #d6e3f4; padding:14px 16px; min-height:102px; box-shadow:0 2px 8px #28384c07; }
    .kpi-label { color:#7b899b; font-size:13px; }
    .kpi-value { font-size:30px; font-weight:850; margin-top:10px; color:#263448; }
    .kpi-hint { color:#4c8ff2; font-size:12px; margin-top:5px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
    .panel { border:1px solid #e1e5eb; background:#ffffff; border-radius:7px; padding:16px; box-shadow:0 2px 8px #28384c07; }
    .score-ring { width:148px; height:148px; border-radius:50%; display:grid; place-items:center; margin:2px auto 12px;
      background:radial-gradient(circle at center,#ffffff 56%,transparent 57%),conic-gradient(#5c94c9 var(--score),#e7edf3 0); box-shadow:none; }
    .score-number { font-size:34px; font-weight:850; color:#263448; }
    .score-caption { text-align:center; color:#7b899b; font-size:12px; }
    .formula { background:#f7f9fb; border:1px solid #e1e6ed; border-radius:6px; padding:13px 15px; color:#53657b; font-size:13px; line-height:1.75; margin-top:16px; }
    .passed { color:#267e68; background:#effaf6; border:1px solid #b9e5d9; border-radius:8px; padding:9px 12px; font-size:13px; }
    .failed { color:#b34755; background:#fff3f4; border:1px solid #f0c4c9; border-radius:8px; padding:9px 12px; font-size:13px; }
    div[data-testid="stDataFrame"] { border:1px solid #dfe5ed; border-radius:9px; overflow:hidden; background:#ffffff; }
    .stButton > button { border:1px solid #79a9ef; background:#ffffff; color:#3676d3; border-radius:7px; }
    main [data-testid="stMarkdownContainer"] p, main [data-testid="stMarkdownContainer"] li { color:#435267; }
    main [data-testid="stTabs"] button, main [data-testid="stTabs"] button p, main [data-testid="stTabs"] [data-baseweb="tab"], main [data-testid="stTabs"] [data-baseweb="tab"] p { color:#6c7b8d !important; font-size:14px; }
    main [data-testid="stTabs"] button[aria-selected="true"], main [data-testid="stTabs"] button[aria-selected="true"] p, main [data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"], main [data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] p { color:#2f66a5 !important; border-bottom-color:#2f66a5 !important; }
    main [data-testid="stTabs"] [data-baseweb="tab-highlight"] { background:#2f66a5 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


def numeric_columns(frame: pd.DataFrame) -> list[str]:
    return [col for col in frame.columns if pd.api.types.is_numeric_dtype(frame[col])]


def first_text_column(frame: pd.DataFrame) -> str:
    for col in frame.columns:
        if not pd.api.types.is_numeric_dtype(frame[col]):
            return str(col)
    return str(frame.columns[0])


def select_default(options: list[str], preferred: list[str]) -> list[str]:
    selected = [item for item in preferred if item in options]
    return selected or options[:1]


def data_source(source: str, uploaded) -> tuple[pd.DataFrame | None, str]:
    if source == "公开大学生学业数据（UCI）":
        return pd.read_csv(DATA_DIR / "uci_higher_education_dea_sample.csv"), "UCI：Predict Students' Dropout and Academic Success（180人公开样本）"
    if source == "内置学生成绩演示数据":
        return make_student_demo_data(), "内置学生成绩演示数据"
    if source == "内置效率演示数据":
        return make_demo_data(), "内置效率演示数据"
    if source == "公开医院效率数据":
        return pd.read_csv(DATA_DIR / "hospital_public.csv"), "GitHub：mathmodels-book / hospital.csv"
    if source == "公开工业面板数据":
        return pd.read_csv(DATA_DIR / "economy_public.csv"), "GitHub：mathmodels-book / economy.csv"
    if uploaded is None:
        return None, "等待上传"
    return load_table(uploaded), uploaded.name


with st.sidebar:
    st.markdown('<div class="side-brand"><div class="side-brand-mark">◈</div><div><div class="side-brand-title">大学生学业评估工作台</div><div class="side-brand-sub">HIGHER EDUCATION ANALYTICS</div></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="side-section">数据与模型</div>', unsafe_allow_html=True)
    source = st.radio("数据源", ["公开大学生学业数据（UCI）", "内置学生成绩演示数据", "上传学生成绩文件", "内置效率演示数据", "公开医院效率数据", "公开工业面板数据"], label_visibility="collapsed")
    uploaded = None
    if source == "上传学生成绩文件":
        uploaded = st.file_uploader("上传 CSV / Excel / Parquet", type=["csv", "tsv", "xlsx", "xls", "parquet"])
    previous_source = st.session_state.get("_dea_source")
    if previous_source != source:
        st.session_state["_dea_source"] = source
        if source == "公开工业面板数据":
            st.session_state["dea_mode"] = "Malmquist指数"
        elif previous_source == "公开工业面板数据":
            st.session_state["dea_mode"] = "径向DEA（CCR / BCC）"
    mode = st.selectbox("分析模型", ["径向DEA（CCR / BCC）", "SBM效率", "超效率SBM", "Malmquist指数"], key="dea_mode")
    st.divider()
    st.markdown('<div class="side-section">评价口径</div>', unsafe_allow_html=True)
    if source in {"公开大学生学业数据（UCI）", "内置学生成绩演示数据", "上传学生成绩文件"}:
        st.markdown('<div class="side-note">每行 = 一名大学生或一个班级<br>投入 = 学习时间与学习资源<br>产出 = 出勤、作业、参与和课程成绩<br>结果反映相对学习效率，不等同于因果影响。</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="side-note">每行 = 一个 DMU<br>投入 = 资源消耗，越小越好<br>产出 = 绩效结果，越大越好</div>', unsafe_allow_html=True)

try:
    data, data_label = data_source(source, uploaded)
except Exception as exc:
    st.error(f"数据读取失败：{exc}")
    st.stop()
if data is None:
    st.markdown('<div class="hero"><div class="eyebrow">HIGHER EDUCATION ANALYTICS · DEA</div><h1>导入大学生数据，开始学业效率评估</h1><p>上传大学生学习过程与课程成绩数据，系统会把每一行识别为一名学生或一个班级，计算相对学习效率并输出可解释的改进方向。</p></div>', unsafe_allow_html=True)
    st.stop()

num_cols = numeric_columns(data)
if len(num_cols) < 2:
    st.error("当前数据至少需要两个数值字段。")
    st.stop()

is_panel = mode == "Malmquist指数"
student_mode = source in {"公开大学生学业数据（UCI）", "内置学生成绩演示数据", "上传学生成绩文件"}
default_dmu = "DMU" if "DMU" in data.columns else "DMUs" if "DMUs" in data.columns else first_text_column(data)
if student_mode:
    for student_id_col in ["学号", "学生ID", "Student_ID"]:
        if student_id_col in data.columns:
            default_dmu = student_id_col
            break
with st.sidebar:
    st.markdown('<div class="side-section">评价配置</div>', unsafe_allow_html=True)
    dmu_col = st.selectbox("决策单元（DMU）", list(data.columns), index=list(data.columns).index(default_dmu))
    if is_panel:
        period_candidates = [col for col in data.columns if col != dmu_col]
        default_period = "Period" if "Period" in period_candidates else period_candidates[0]
        period_col = st.selectbox("时期字段", period_candidates, index=period_candidates.index(default_period))
    else:
        period_col = None

    available_num = [col for col in num_cols if col != dmu_col and col != period_col]
    if student_mode:
        preferred_inputs = ["第一学期选课数", "第二学期选课数", "学习时长(小时/周)", "学习时长", "Study_Hours"]
        preferred_outputs = ["第一学期通过课程数", "第二学期通过课程数", "第一学期平均成绩", "第二学期平均成绩", "出勤率(%)", "作业完成率(%)", "课堂参与度(分)", "期末成绩(分)", "课程成绩(分)", "Final_Score"]
        preferred_bad = []
    elif source == "公开医院效率数据":
        preferred_inputs = ["床位数(万个)", "卫技人员数(万个)"]
        preferred_outputs = ["诊疗人次数(万人次)", "入院人数(万人)"]
        preferred_bad = ["医疗废弃物(万套)"]
    elif source == "公开工业面板数据":
        preferred_inputs = ["Capital", "Labor"]
        preferred_outputs = ["GIOV"]
        preferred_bad = []
    else:
        preferred_inputs = ["人员投入", "资金投入"]
        preferred_outputs = ["服务产出", "经济产出"]
        preferred_bad = []
    input_label = "学习资源投入（越小越好）" if student_mode else "投入指标（越小越好）"
    output_label = "学习结果与成绩（越大越好）" if student_mode else "期望产出（越大越好）"
    input_cols = st.multiselect(input_label, available_num, default=select_default(available_num, preferred_inputs))
    remaining_num = [col for col in available_num if col not in input_cols]
    output_cols = st.multiselect(output_label, remaining_num + input_cols, default=select_default(remaining_num + input_cols, preferred_outputs))

    undesirable_cols: list[str] = []
    if mode in {"SBM效率", "超效率SBM"}:
        bad_options = [col for col in available_num if col not in input_cols and col not in output_cols] + input_cols
        undesirable_cols = st.multiselect("非期望产出（越小越好，可选）", bad_options, default=[col for col in preferred_bad if col in bad_options])

    if mode in {"径向DEA（CCR / BCC）", "SBM效率", "超效率SBM"}:
        model_label = st.selectbox("规模报酬", ["BCC / VRS（可变规模）", "CCR / CRS（固定规模）"])
        model_code = "BCC" if model_label.startswith("BCC") else "CCR"
    else:
        model_label = st.selectbox("Malmquist参考前沿", ["BCC / VRS（可变规模）", "CCR / CRS（固定规模）"])
        model_code = "BCC" if model_label.startswith("BCC") else "CCR"
    orientation_label = None
    if mode == "径向DEA（CCR / BCC）":
        orientation_label = st.selectbox("优化方向", ["投入导向", "产出导向"])

if mode == "径向DEA（CCR / BCC）":
    try:
        result = evaluate_dea(data, dmu_col, input_cols, output_cols, model_code, "input" if orientation_label == "投入导向" else "output")
        audit = audit_dea_result(data, dmu_col, input_cols, output_cols, model_code, "input" if orientation_label == "投入导向" else "output")
    except Exception as exc:
        result = None
        audit = None
        error_message = str(exc)
        if source == "公开工业面板数据" and data[dmu_col].duplicated().any():
            error_message = "公开工业数据是‘地区 × 年份’面板数据，同一地区会出现多个时期。请切换到 Malmquist 指数；如果要做单期径向 DEA，请先筛选一个时期。"
elif mode in {"SBM效率", "超效率SBM"}:
    try:
        result = evaluate_sbm(data, dmu_col, input_cols, output_cols, undesirable_cols, model_code, mode == "超效率SBM")
        audit = None
    except Exception as exc:
        result = None
        audit = None
        error_message = str(exc)
else:
    try:
        result = evaluate_malmquist(data, dmu_col, period_col, input_cols, output_cols, model_code)
        audit = None
    except Exception as exc:
        result = None
        audit = None
        error_message = str(exc)

system_title = "智能大学生学业成绩因素评估系统" if student_mode else "智能DEA效率评价系统"
hero_eyebrow = "HIGHER EDUCATION ANALYTICS · DEA" if student_mode else ("OPERATIONS RESEARCH · MALMQUIST PRODUCTIVITY" if is_panel else f"OPERATIONS RESEARCH · {mode.upper()}")
hero_title = "识别学业效率，定位提升抓手" if student_mode else ("追踪跨期生产率，分解效率与技术进步" if is_panel else "识别效率前沿，定位改进标杆")
hero_copy = "系统把学习时长等资源投入，与出勤、作业完成、课堂参与和课程成绩等期望产出进行相对效率比较，帮助教师发现需要关注的大学生和可改善的学习环节。" if student_mode else ("基于相邻时期的距离函数，计算效率变化、技术进步和Malmquist生产率指数。指数大于1表示生产率提升。" if is_panel else "将每个决策单元与效率前沿进行比较，输出相对效率、参考标杆、规模报酬、松弛变量和投入产出改进目标。")
st.markdown(f'<div class="topline"><div class="brand"><div class="logo">◈</div><div><div class="brand-title">{system_title}</div><div class="brand-sub">HIGHER EDUCATION ANALYTICS · DEA · V1.3</div></div></div><div class="online">● SOLVER READY</div></div>', unsafe_allow_html=True)
st.markdown(f'<div class="hero"><div class="eyebrow">{hero_eyebrow}</div><h1>{hero_title}</h1><p>{hero_copy}</p></div>', unsafe_allow_html=True)

if result is None:
    st.warning(error_message)
    st.info("请检查：DMU必须唯一；投入/产出必须为非负数值；投入与产出不能重复；Malmquist需要同一DMU至少出现两个时期。")
    st.dataframe(data.head(12), use_container_width=True, hide_index=True)
    st.stop()


def kpi_card(label: str, value: str, hint: str) -> str:
    return f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div><div class="kpi-hint">{hint}</div></div>'


table = result["table"]
summary = result["summary"]
if is_panel:
    kpi_values = [
        ("面板DMU", f"{summary['dmu_count']}", "跨期匹配单元"),
        ("时期数量", f"{summary['period_count']}", "连续时期"),
        ("平均M指数", f"{summary['average_malmquist']:.3f}", "大于1表示提升"),
        ("平均EC", f"{table['效率变化EC'].mean():.3f}", "技术效率变化"),
        ("平均TC", f"{table['技术进步TC'].mean():.3f}", "技术进步变化"),
    ]
else:
    score_col = "DEA效率" if mode == "径向DEA（CCR / BCC）" else "SBM效率"
    kpi_values = [
        ("大学生 / 决策单元" if student_mode else "决策单元", f"{summary['dmu_count']:,}", "学生数量" if student_mode else "DMU数量"),
        ("高效学习单元" if student_mode else "有效单元", f"{summary['efficient_count']:,}", "相对效率接近1" if student_mode else "标准效率接近1"),
        ("平均学业效率" if student_mode else "平均效率", f"{table[score_col].mean():.3f}", "样本内相对效率"),
        ("学习因素" if student_mode else "投入指标", f"{len(input_cols)}", "过程维度" if student_mode else "资源消耗维度"),
        ("成绩产出" if student_mode else "产出指标", f"{len(output_cols)}", "结果维度" if student_mode else "绩效结果维度"),
    ]

st.markdown(f'<div class="section-title">{("学生学习效率概览" if student_mode else "生产率资产概览" if is_panel else "效率资产概览")} <span class="section-note">{data_label}</span></div>', unsafe_allow_html=True)
columns = st.columns(5)
for col, values in zip(columns, kpi_values):
    with col:
        st.markdown(kpi_card(*values), unsafe_allow_html=True)

tab_overview, tab_rank, tab_detail, tab_data = st.tabs(["结果总览", "效率排行", "改进诊断", "数据与模型"])

with tab_overview:
    if is_panel:
        st.markdown('<div class="section-title">Malmquist指数分布</div>', unsafe_allow_html=True)
        chart = table.set_index("DMU")[["Malmquist指数"]]
        st.bar_chart(chart, color="#38d5ff", height=280)
        st.dataframe(table, use_container_width=True, hide_index=True)
    else:
        score_col = "DEA效率" if mode == "径向DEA（CCR / BCC）" else "SBM效率"
        score_value = float(table[score_col].mean())
        ring_score = min(max(score_value, 0), 1) * 100
        left, right = st.columns([1, 2.25])
        with left:
            st.markdown(f'<div class="panel"><div class="score-ring" style="--score:{ring_score:.2f}%"><div class="score-number">{score_value:.3f}</div></div><div class="score-caption">{("平均Malmquist指数" if is_panel else "平均效率值")}</div><div class="formula"><b>解释</b><br>{"SBM直接利用投入冗余、期望产出不足和非期望产出超额刻画非径向低效。" if mode in {"SBM效率", "超效率SBM"} else "径向DEA效率越接近1，表示越接近样本效率前沿。CCR与BCC结果用于区分技术效率和规模效率。"}</div></div>', unsafe_allow_html=True)
        with right:
            display = table.copy()
            format_cols = [col for col in ["DEA效率", "CCR效率", "BCC效率", "规模效率", "SBM效率", "标准SBM效率"] if col in display.columns]
            for col in format_cols:
                display[col] = display[col].map(lambda value: f"{value:.4f}" if pd.notna(value) else "—")
            st.dataframe(display, use_container_width=True, hide_index=True, height=340)
        st.markdown('<div class="section-title">效率分布</div>', unsafe_allow_html=True)
        st.bar_chart(table.set_index("DMU")[[score_col]], color="#38d5ff", height=250)

with tab_rank:
    st.markdown('<div class="section-title">排序结果</div>', unsafe_allow_html=True)
    st.dataframe(table, use_container_width=True, hide_index=True, height=480)
    csv_data = table.to_csv(index=False).encode("utf-8-sig")
    st.download_button("下载当前结果 CSV", data=csv_data, file_name="dea_result.csv", mime="text/csv")

with tab_detail:
    if is_panel:
        selected_dmu = st.selectbox("选择DMU查看跨期变化", sorted(table["DMU"].unique().tolist()))
        selected = table[table["DMU"] == selected_dmu]
        st.dataframe(selected, use_container_width=True, hide_index=True)
        st.markdown('<div class="formula"><b>分解关系</b><br>Malmquist指数 = √[(跨期距离函数组合)]；结果同时展示效率变化（EC）与技术进步（TC），两者乘积构成生产率变化。</div>', unsafe_allow_html=True)
    else:
        detail_names = table["DMU"].tolist()
        selected_dmu = st.selectbox("选择需要诊断的决策单元", detail_names)
        detail = result["details"][selected_dmu]
        score_col = "DEA效率" if mode == "径向DEA（CCR / BCC）" else "SBM效率"
        score_value = float(table.loc[table["DMU"] == selected_dmu, score_col].iloc[0])
        d1, d2, d3 = st.columns(3)
        with d1:
            st.markdown(kpi_card("当前效率", f"{score_value:.4f}", "效率前沿" if score_value >= 0.99999 else "存在改进空间"), unsafe_allow_html=True)
        with d2:
            peers = detail.get("peers", [])
            peer_text = "、".join(item.get("DMU", "") for item in peers) or "无"
            st.markdown(kpi_card("参考标杆", f"{len(peers)} 个", peer_text), unsafe_allow_html=True)
        with d3:
            suggestion_count = sum(len(detail.get(key, {})) for key in ["input_reduction", "output_increase", "input_slacks", "good_output_shortage", "bad_output_reduction"])
            st.markdown(kpi_card("改进项数", f"{suggestion_count}", "松弛 / 压缩 / 提升"), unsafe_allow_html=True)
        left, right = st.columns(2)
        with left:
            st.markdown("**参考标杆及权重**")
            st.dataframe(pd.DataFrame(detail.get("peers", [])) if detail.get("peers") else pd.DataFrame([{"DMU": "—", "权重": 0}]), use_container_width=True, hide_index=True)
        with right:
            st.markdown("**改进诊断**")
            rows = []
            for key, title in [("input_reduction", "投入压缩"), ("output_increase", "产出提升"), ("input_slacks", "投入冗余"), ("good_output_shortage", "期望产出不足"), ("bad_output_reduction", "非期望产出削减")]:
                for name, value in detail.get(key, {}).items():
                    rows.append({"指标": name, "诊断": title, "建议量": value})
            st.dataframe(pd.DataFrame(rows) if rows else pd.DataFrame([{"指标": "—", "诊断": "当前位于效率前沿", "建议量": 0}]), use_container_width=True, hide_index=True)

with tab_data:
    if audit is not None:
        if audit["passed"]:
            st.markdown('<div class="passed">✓ DEA数值校核通过：效率范围、CCR/BCC关系、规模效率上界和DMU数量均符合约束。</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="failed">! DEA数值校核发现异常，请检查模型配置或数据口径。</div>', unsafe_allow_html=True)
        st.json(audit["checks"])
    st.markdown("**当前模型配置**")
    config = result["config"].copy()
    st.json(config)
    st.markdown("**原始数据预览**")
    st.dataframe(data.head(15), use_container_width=True, hide_index=True)
    st.download_button("下载模型配置 JSON", data=json.dumps(config, ensure_ascii=False, indent=2), file_name="dea_config.json", mime="application/json")

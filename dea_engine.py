"""Data Envelopment Analysis (DEA) engine.

The module keeps the mathematical core independent from Streamlit so it can
later be exposed as an API, batch job, or desktop application.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import linprog


def make_demo_data() -> pd.DataFrame:
    """Return a small positive-input/positive-output DEA demonstration table."""

    return pd.DataFrame(
        {
            "地区": ["华东A", "华东B", "华南A", "华南B", "华北A", "华北B", "西南A", "西南B", "东北A", "东北B", "西北A", "西北B"],
            "人员投入": [118, 132, 96, 108, 154, 141, 88, 102, 127, 116, 73, 81],
            "资金投入": [860, 945, 720, 810, 1090, 1010, 660, 735, 900, 835, 520, 590],
            "能耗投入": [430, 482, 355, 398, 570, 535, 318, 368, 465, 421, 250, 286],
            "服务产出": [920, 965, 810, 872, 1015, 1002, 760, 801, 936, 918, 645, 701],
            "经济产出": [1190, 1255, 1075, 1148, 1320, 1301, 1008, 1064, 1228, 1206, 842, 930],
        }
    )


def make_student_demo_data() -> pd.DataFrame:
    """Return a teaching-oriented student learning-efficiency demo table."""

    return pd.DataFrame(
        {
            "学生ID": [f"S{i:03d}" for i in range(1, 25)],
            "专业班级": ["2024级计科1班"] * 12 + ["2024级经管1班"] * 12,
            "学习时长(小时/周)": [8, 10, 12, 9, 14, 11, 7, 13, 10, 15, 8, 12, 9, 11, 13, 7, 15, 10, 12, 14, 8, 9, 11, 13],
            "出勤率(%)": [98, 96, 94, 92, 99, 95, 88, 97, 93, 91, 96, 98, 95, 97, 92, 89, 98, 94, 96, 93, 90, 95, 97, 94],
            "作业完成率(%)": [96, 91, 88, 94, 97, 90, 82, 95, 86, 89, 93, 96, 92, 94, 87, 80, 98, 90, 95, 91, 84, 93, 96, 88],
            "课堂参与度(分)": [86, 79, 74, 82, 91, 77, 68, 88, 72, 80, 83, 90, 81, 85, 75, 65, 93, 78, 87, 76, 70, 84, 89, 73],
            "期末成绩(分)": [92, 86, 82, 88, 96, 84, 73, 94, 79, 87, 89, 95, 88, 91, 81, 70, 98, 85, 93, 86, 76, 90, 94, 80],
        }
    )


def load_table(source: Any, filename: str | None = None) -> pd.DataFrame:
    """Load CSV, TSV, Excel, or Parquet data from a path or file-like object."""

    name = filename or getattr(source, "name", str(source))
    suffix = Path(name).suffix.lower()
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(source)
    if suffix == ".parquet":
        return pd.read_parquet(source)

    last_error: Exception | None = None
    for encoding in ("utf-8-sig", "utf-8", "gb18030", "latin-1"):
        try:
            return pd.read_csv(source, encoding=encoding, sep=None, engine="python")
        except Exception as exc:
            last_error = exc
            if hasattr(source, "seek"):
                source.seek(0)
    raise ValueError(f"无法读取数据文件：{last_error}")


def _as_numeric(frame: pd.DataFrame, columns: list[str]) -> np.ndarray:
    return frame[columns].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)


def validate_inputs(
    frame: pd.DataFrame,
    dmu_col: str,
    input_cols: list[str],
    output_cols: list[str],
) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """Validate and return the cleaned DMU table, input matrix and output matrix."""

    if frame is None or frame.empty:
        raise ValueError("数据为空，无法进行DEA评价。")
    if not dmu_col or dmu_col not in frame.columns:
        raise ValueError("请选择有效的决策单元（DMU）字段。")
    if not input_cols:
        raise ValueError("至少选择一个投入指标。")
    if not output_cols:
        raise ValueError("至少选择一个产出指标。")
    if set(input_cols) & set(output_cols):
        raise ValueError("投入指标和产出指标不能重复。")

    work = frame.copy()
    work[dmu_col] = work[dmu_col].astype(str).str.strip()
    work = work[work[dmu_col].ne("")].copy()
    x = _as_numeric(work, input_cols)
    y = _as_numeric(work, output_cols)
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("投入和产出指标中存在空值或非数值内容，请先清洗数据。")
    if (x < 0).any() or (y < 0).any():
        raise ValueError("当前版本要求投入和产出指标为非负数。")
    if (x.sum(axis=1) <= 0).any():
        raise ValueError("存在投入指标全部为0的DMU，无法建立稳定的DEA模型。")
    if (y.sum(axis=1) <= 0).any():
        raise ValueError("存在产出指标全部为0的DMU，无法建立稳定的DEA模型。")
    if work[dmu_col].duplicated().any():
        raise ValueError("DMU名称存在重复，请确保每一行对应一个唯一决策单元。")
    if len(work) < 3:
        raise ValueError("DEA至少需要3个决策单元。")
    return work.reset_index(drop=True), x, y


def _solve_one(
    x: np.ndarray,
    y: np.ndarray,
    index: int,
    model: str,
    orientation: str,
) -> dict[str, Any]:
    """Solve one DMU using the envelopment form of CCR/BCC DEA."""

    n, input_count = x.shape
    output_count = y.shape[1]
    model = model.upper()
    orientation = orientation.lower()
    if model not in {"CCR", "BCC"}:
        raise ValueError("模型必须为CCR或BCC。")
    if orientation not in {"input", "output"}:
        raise ValueError("方向必须为input或output。")

    if orientation == "input":
        c = np.r_[np.zeros(n), 1.0]
        a_ub = []
        b_ub = []
        for col in range(input_count):
            row = np.zeros(n + 1)
            row[:n] = x[:, col]
            row[n] = -x[index, col]
            a_ub.append(row)
            b_ub.append(0.0)
        for col in range(output_count):
            row = np.zeros(n + 1)
            row[:n] = -y[:, col]
            a_ub.append(row)
            b_ub.append(-y[index, col])
        bounds = [(0.0, None)] * n + [(0.0, None)]
    else:
        c = np.r_[np.zeros(n), -1.0]
        a_ub = []
        b_ub = []
        for col in range(input_count):
            row = np.zeros(n + 1)
            row[:n] = x[:, col]
            a_ub.append(row)
            b_ub.append(x[index, col])
        for col in range(output_count):
            row = np.zeros(n + 1)
            row[:n] = -y[:, col]
            row[n] = y[index, col]
            a_ub.append(row)
            b_ub.append(0.0)
        bounds = [(0.0, None)] * n + [(0.0, None)]

    a_eq = None
    b_eq = None
    if model == "BCC":
        a_eq = np.zeros((1, n + 1))
        a_eq[0, :n] = 1.0
        b_eq = np.array([1.0])

    result = linprog(
        c,
        A_ub=np.asarray(a_ub),
        b_ub=np.asarray(b_ub),
        A_eq=a_eq,
        b_eq=b_eq,
        bounds=bounds,
        method="highs",
    )
    if not result.success:
        raise RuntimeError(f"DMU {index + 1} 求解失败：{result.message}")

    lambdas = np.maximum(result.x[:n], 0.0)
    raw = float(result.x[n])
    if orientation == "input":
        efficiency = raw
    else:
        efficiency = 1.0 / max(raw, 1e-12)
    projected_x = lambdas @ x
    projected_y = lambdas @ y
    input_reduction = np.maximum(x[index] - projected_x, 0.0)
    output_increase = np.maximum(projected_y - y[index], 0.0)

    return {
        "raw_score": raw,
        "efficiency": float(np.clip(efficiency, 0.0, 1.0)),
        "lambdas": lambdas,
        "projected_x": projected_x,
        "projected_y": projected_y,
        "input_reduction": input_reduction,
        "output_increase": output_increase,
        "lambda_sum": float(lambdas.sum()),
    }


def evaluate_dea(
    frame: pd.DataFrame,
    dmu_col: str,
    input_cols: list[str],
    output_cols: list[str],
    model: str = "BCC",
    orientation: str = "input",
) -> dict[str, Any]:
    """Evaluate all DMUs and return scores, peers, projections and recommendations."""

    work, x, y = validate_inputs(frame, dmu_col, input_cols, output_cols)
    model = model.upper()
    orientation = orientation.lower()
    n = len(work)
    selected_solutions = [_solve_one(x, y, i, model, orientation) for i in range(n)]
    ccr_solutions = [_solve_one(x, y, i, "CCR", orientation) for i in range(n)]
    bcc_solutions = [_solve_one(x, y, i, "BCC", orientation) for i in range(n)]

    records: list[dict[str, Any]] = []
    details: dict[str, Any] = {}
    for i, solution in enumerate(selected_solutions):
        ccr_score = ccr_solutions[i]["efficiency"]
        bcc_score = bcc_solutions[i]["efficiency"]
        scale_efficiency = min(1.0, ccr_score / bcc_score) if bcc_score > 1e-12 else 0.0
        lambda_sum = ccr_solutions[i]["lambda_sum"]
        if abs(lambda_sum - 1.0) <= 1e-5:
            returns = "规模报酬不变"
        elif lambda_sum < 1.0:
            returns = "规模报酬递增"
        else:
            returns = "规模报酬递减"

        peers = [
            {"DMU": str(work.iloc[j][dmu_col]), "权重": round(float(weight), 4)}
            for j, weight in enumerate(solution["lambdas"])
            if weight > 1e-6
        ]
        current_x = x[i]
        current_y = y[i]
        input_changes = {
            col: round(float(solution["input_reduction"][k]), 6)
            for k, col in enumerate(input_cols)
            if solution["input_reduction"][k] > 1e-6
        }
        output_changes = {
            col: round(float(solution["output_increase"][k]), 6)
            for k, col in enumerate(output_cols)
            if solution["output_increase"][k] > 1e-6
        }
        name = str(work.iloc[i][dmu_col])
        details[name] = {
            "peers": peers,
            "input_reduction": input_changes,
            "output_increase": output_changes,
            "current_input": {col: round(float(current_x[k]), 6) for k, col in enumerate(input_cols)},
            "current_output": {col: round(float(current_y[k]), 6) for k, col in enumerate(output_cols)},
            "projected_input": {col: round(float(solution["projected_x"][k]), 6) for k, col in enumerate(input_cols)},
            "projected_output": {col: round(float(solution["projected_y"][k]), 6) for k, col in enumerate(output_cols)},
        }
        records.append(
            {
                "DMU": name,
                "DEA效率": round(float(solution["efficiency"]), 6),
                "CCR效率": round(float(ccr_score), 6),
                "BCC效率": round(float(bcc_score), 6),
                "规模效率": round(float(scale_efficiency), 6),
                "规模报酬": returns,
                "标杆数量": len(peers),
                "改进项数": len(input_changes) + len(output_changes),
            }
        )

    result_table = pd.DataFrame(records).sort_values(["DEA效率", "DMU"], ascending=[False, True]).reset_index(drop=True)
    efficient_count = int((result_table["DEA效率"] >= 1.0 - 1e-5).sum())
    return {
        "config": {
            "dmu": dmu_col,
            "inputs": input_cols,
            "outputs": output_cols,
            "model": model,
            "orientation": orientation,
        },
        "summary": {
            "dmu_count": n,
            "efficient_count": efficient_count,
            "average_efficiency": round(float(result_table["DEA效率"].mean()), 6),
            "min_efficiency": round(float(result_table["DEA效率"].min()), 6),
        },
        "table": result_table,
        "details": details,
    }


def _solve_input_target(
    reference_x: np.ndarray,
    reference_y: np.ndarray,
    target_x: np.ndarray,
    target_y: np.ndarray,
    model: str,
) -> float:
    """Input distance of an arbitrary target against a reference technology."""

    n = reference_x.shape[0]
    c = np.r_[np.zeros(n), 1.0]
    a_ub: list[np.ndarray] = []
    b_ub: list[float] = []
    for col in range(reference_x.shape[1]):
        row = np.zeros(n + 1)
        row[:n] = reference_x[:, col]
        row[n] = -target_x[col]
        a_ub.append(row)
        b_ub.append(0.0)
    for col in range(reference_y.shape[1]):
        row = np.zeros(n + 1)
        row[:n] = -reference_y[:, col]
        a_ub.append(row)
        b_ub.append(-target_y[col])
    a_eq = None
    b_eq = None
    if model.upper() == "BCC":
        a_eq = np.zeros((1, n + 1))
        a_eq[0, :n] = 1.0
        b_eq = np.array([1.0])
    result = linprog(
        c,
        A_ub=np.asarray(a_ub),
        b_ub=np.asarray(b_ub),
        A_eq=a_eq,
        b_eq=b_eq,
        bounds=[(0.0, None)] * (n + 1),
        method="highs",
    )
    if not result.success:
        # Cross-period distance functions can be infeasible when the two
        # period frontiers do not share a common production possibility set.
        # Mark the term unavailable so the corresponding pair is excluded
        # instead of aborting the complete panel analysis.
        return float("nan")
    return float(result.x[-1])


def audit_dea_result(
    frame: pd.DataFrame,
    dmu_col: str,
    input_cols: list[str],
    output_cols: list[str],
    model: str,
    orientation: str,
) -> dict[str, Any]:
    """Run numerical sanity checks for a radial DEA result."""

    work, x, y = validate_inputs(frame, dmu_col, input_cols, output_cols)
    result = evaluate_dea(work, dmu_col, input_cols, output_cols, model, orientation)
    table = result["table"]
    scores = table["DEA效率"].to_numpy(dtype=float)
    checks = {
        "所有效率值在0到1之间": bool(np.all((scores >= -1e-7) & (scores <= 1.0 + 1e-6))),
        "CCR效率不高于BCC效率": bool(np.all(table["CCR效率"].to_numpy() <= table["BCC效率"].to_numpy() + 1e-6)),
        "规模效率不高于1": bool(np.all(table["规模效率"].to_numpy() <= 1.0 + 1e-6)),
        "DMU数量与结果数量一致": bool(len(work) == len(table)),
    }
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "result": result,
        "rows": len(work),
        "inputs": x.shape[1],
        "outputs": y.shape[1],
    }


def _solve_sbm_one(
    x: np.ndarray,
    good_y: np.ndarray,
    bad_y: np.ndarray,
    index: int,
    model: str,
    exclude_self: bool = False,
) -> dict[str, Any]:
    """Solve Tone's linearized SBM, optionally leaving the evaluated DMU out."""

    n, m = x.shape
    good_count = good_y.shape[1]
    bad_count = bad_y.shape[1]
    ref_indices = [j for j in range(n) if not exclude_self or j != index]
    xr = x[ref_indices]
    yr = good_y[ref_indices]
    br = bad_y[ref_indices] if bad_count else np.zeros((len(ref_indices), 0))
    ref_n = len(ref_indices)
    slack_count = m + good_count + bad_count
    if slack_count == 0:
        raise ValueError("SBM至少需要一个投入或产出指标。")

    x0 = x[index]
    y0 = good_y[index]
    b0 = bad_y[index] if bad_count else np.zeros(0)
    total = ref_n + slack_count + 1
    t_index = total - 1
    s_input_start = ref_n
    s_good_start = s_input_start + m
    s_bad_start = s_good_start + good_count
    objective = np.zeros(total)
    objective[t_index] = 1.0
    objective[s_input_start:s_good_start] = -1.0 / max(m, 1) / np.maximum(x0, 1e-12)
    if good_count:
        objective[s_good_start:s_bad_start] = -1.0 / max(good_count + bad_count, 1) / np.maximum(y0, 1e-12)
    if bad_count:
        objective[s_bad_start:t_index] = -1.0 / max(good_count + bad_count, 1) / np.maximum(b0, 1e-12)

    a_eq: list[np.ndarray] = []
    b_eq: list[float] = []
    for col in range(m):
        row = np.zeros(total)
        row[:ref_n] = xr[:, col]
        row[s_input_start + col] = 1.0
        row[t_index] = -x0[col]
        a_eq.append(row)
        b_eq.append(0.0)
    for col in range(good_count):
        row = np.zeros(total)
        row[:ref_n] = yr[:, col]
        row[s_good_start + col] = -1.0
        row[t_index] = -y0[col]
        a_eq.append(row)
        b_eq.append(0.0)
    for col in range(bad_count):
        row = np.zeros(total)
        row[:ref_n] = br[:, col]
        row[s_bad_start + col] = 1.0
        row[t_index] = -b0[col]
        a_eq.append(row)
        b_eq.append(0.0)
    if model.upper() == "BCC":
        row = np.zeros(total)
        row[:ref_n] = 1.0
        row[t_index] = -1.0
        a_eq.append(row)
        b_eq.append(0.0)
    # Charnes-Cooper normalization for the SBM denominator:
    # t + mean(output slacks / observed output) = 1.
    normalization = np.zeros(total)
    normalization[t_index] = 1.0
    if good_count:
        normalization[s_good_start:s_bad_start] = 1.0 / max(good_count + bad_count, 1) / np.maximum(y0, 1e-12)
    if bad_count:
        normalization[s_bad_start:t_index] = 1.0 / max(good_count + bad_count, 1) / np.maximum(b0, 1e-12)
    a_eq.append(normalization)
    b_eq.append(1.0)

    result = linprog(
        objective,
        A_eq=np.asarray(a_eq),
        b_eq=np.asarray(b_eq),
        bounds=[(0.0, None)] * ref_n + [(0.0, None)] * slack_count + [(1e-9, None)],
        method="highs",
    )
    if not result.success:
        return {"status": "failed", "message": result.message}

    t = max(float(result.x[t_index]), 1e-12)
    lambdas = result.x[:ref_n] / t
    input_slacks = result.x[s_input_start:s_good_start] / t
    good_slacks = result.x[s_good_start:s_bad_start] / t if good_count else np.zeros(0)
    bad_slacks = result.x[s_bad_start:t_index] / t if bad_count else np.zeros(0)
    projected_x = lambdas @ xr
    projected_good_y = lambdas @ yr if good_count else np.zeros(0)
    projected_bad_y = lambdas @ br if bad_count else np.zeros(0)
    peers = [
        {"DMU_INDEX": int(ref_indices[j]), "权重": round(float(weight), 6)}
        for j, weight in enumerate(lambdas)
        if weight > 1e-6
    ]
    return {
        "status": "ok",
        "efficiency": float(result.fun),
        "lambdas": lambdas,
        "input_slacks": input_slacks,
        "good_slacks": good_slacks,
        "bad_slacks": bad_slacks,
        "projected_x": projected_x,
        "projected_good_y": projected_good_y,
        "projected_bad_y": projected_bad_y,
        "peers": peers,
    }


def evaluate_sbm(
    frame: pd.DataFrame,
    dmu_col: str,
    input_cols: list[str],
    output_cols: list[str],
    undesirable_cols: list[str] | None = None,
    model: str = "BCC",
    super_efficiency: bool = False,
) -> dict[str, Any]:
    """Evaluate standard SBM or super-efficiency SBM with optional bad outputs."""

    undesirable_cols = undesirable_cols or []
    if set(output_cols) & set(undesirable_cols):
        raise ValueError("期望产出和非期望产出不能重复。")
    all_outputs = list(output_cols) + list(undesirable_cols)
    work, x, all_y = validate_inputs(frame, dmu_col, input_cols, all_outputs)
    good_y = all_y[:, : len(output_cols)] if output_cols else np.zeros((len(work), 0))
    bad_y = all_y[:, len(output_cols):] if undesirable_cols else np.zeros((len(work), 0))
    records: list[dict[str, Any]] = []
    details: dict[str, Any] = {}
    for i in range(len(work)):
        selected = _solve_sbm_one(x, good_y, bad_y, i, model, exclude_self=super_efficiency)
        standard = _solve_sbm_one(x, good_y, bad_y, i, model, exclude_self=False)
        if selected.get("status") != "ok":
            if not super_efficiency:
                raise RuntimeError(f"DMU {i + 1} SBM求解失败：{selected.get('message')}")
            name = str(work.iloc[i][dmu_col])
            details[name] = {"status": "无可行超效率解", "message": selected.get("message", "") , "peers": []}
            records.append({
                "DMU": name,
                "SBM效率": np.nan,
                "标准SBM效率": round(float(standard["efficiency"]), 6) if standard.get("status") == "ok" else np.nan,
                "类型": "超效率SBM（无可行解）",
                "标杆数量": 0,
                "松弛项数": np.nan,
            })
            continue
        name = str(work.iloc[i][dmu_col])
        peers = [
            {"DMU": str(work.iloc[item["DMU_INDEX"]][dmu_col]), "权重": item["权重"]}
            for item in selected["peers"]
        ]
        input_slacks = {col: round(float(selected["input_slacks"][k]), 6) for k, col in enumerate(input_cols) if selected["input_slacks"][k] > 1e-6}
        good_slacks = {col: round(float(selected["good_slacks"][k]), 6) for k, col in enumerate(output_cols) if selected["good_slacks"][k] > 1e-6}
        bad_slacks = {col: round(float(selected["bad_slacks"][k]), 6) for k, col in enumerate(undesirable_cols) if selected["bad_slacks"][k] > 1e-6}
        details[name] = {
            "peers": peers,
            "input_slacks": input_slacks,
            "good_output_shortage": good_slacks,
            "bad_output_reduction": bad_slacks,
            "projected_input": {col: round(float(selected["projected_x"][k]), 6) for k, col in enumerate(input_cols)},
            "projected_output": {col: round(float(selected["projected_good_y"][k]), 6) for k, col in enumerate(output_cols)},
            "projected_undesirable": {col: round(float(selected["projected_bad_y"][k]), 6) for k, col in enumerate(undesirable_cols)},
        }
        records.append({
            "DMU": name,
            "SBM效率": round(float(selected["efficiency"]), 6),
            "标准SBM效率": round(float(standard["efficiency"]), 6) if standard.get("status") == "ok" else np.nan,
            "类型": "超效率SBM" if super_efficiency else "标准SBM",
            "状态": "可行",
            "标杆数量": len(peers),
            "松弛项数": len(input_slacks) + len(good_slacks) + len(bad_slacks),
        })
    # 统一按效率从高到低展示；无可行超效率解的 NaN 会自然排到末尾。
    table = pd.DataFrame(records).sort_values(["SBM效率", "DMU"], ascending=[False, True], na_position="last").reset_index(drop=True)
    return {
        "config": {"dmu": dmu_col, "inputs": input_cols, "outputs": output_cols, "undesirable": undesirable_cols, "model": model, "super_efficiency": super_efficiency},
        "summary": {"dmu_count": len(work), "efficient_count": int((table["标准SBM效率"] >= 1.0 - 1e-5).sum()), "average_efficiency": round(float(table["SBM效率"].dropna().mean()), 6) if table["SBM效率"].notna().any() else float("nan")},
        "table": table,
        "details": details,
    }


def _validate_network_frame(
    frame: pd.DataFrame,
    dmu_col: str,
    input_cols: list[str],
    intermediate_cols: list[str],
    output_cols: list[str],
) -> tuple[pd.DataFrame, np.ndarray, np.ndarray, np.ndarray]:
    """Validate a two-stage serial learning-production table."""

    if frame is None or frame.empty:
        raise ValueError("数据为空，无法进行两阶段网络DEA。")
    if not input_cols or not intermediate_cols or not output_cols:
        raise ValueError("两阶段网络DEA需要至少一个投入、一个中间过程指标和一个最终产出。")
    groups = [input_cols, intermediate_cols, output_cols]
    flattened = [col for group in groups for col in group]
    if len(set(flattened)) != len(flattened):
        raise ValueError("投入、中间过程指标和最终产出不能重复。")
    required = [dmu_col] + flattened
    missing = [col for col in required if col not in frame.columns]
    if missing:
        raise ValueError(f"网络DEA字段不存在：{missing}")

    work = frame[required].copy()
    work[dmu_col] = work[dmu_col].astype(str).str.strip()
    if work[dmu_col].eq("").any() or work[dmu_col].duplicated().any():
        raise ValueError("网络DEA要求DMU名称非空且唯一。")
    if len(work) < 3:
        raise ValueError("网络DEA至少需要3个决策单元。")

    matrices = []
    for columns, label in ((input_cols, "投入"), (intermediate_cols, "中间过程指标"), (output_cols, "最终产出")):
        values = _as_numeric(work, columns)
        if not np.isfinite(values).all():
            raise ValueError(f"{label}中存在空值或非数值内容。")
        if (values < 0).any():
            raise ValueError(f"{label}必须为非负数。")
        if (values.sum(axis=1) <= 0).any():
            raise ValueError(f"{label}存在整行均为0的DMU，无法建立稳定的网络DEA模型。")
        matrices.append(values)
    return work.reset_index(drop=True), matrices[0], matrices[1], matrices[2]


def _solve_sbm_target(
    reference_x: np.ndarray,
    reference_good_y: np.ndarray,
    target_x: np.ndarray,
    target_good_y: np.ndarray,
    model: str = "BCC",
    reference_bad_y: np.ndarray | None = None,
    target_bad_y: np.ndarray | None = None,
) -> dict[str, Any]:
    """Solve an SBM target against an arbitrary reference technology.

    The existing SBM solver evaluates one row against a table that contains
    that same row.  Bootstrap and group-frontier analysis need a target that
    is not necessarily part of the reference sample, so this helper exposes
    the same linearized SBM formulation with separate target arrays.
    """

    model = model.upper()
    if model not in {"CCR", "BCC"}:
        raise ValueError("网络SBM规模报酬必须为CCR或BCC。")
    reference_x = np.asarray(reference_x, dtype=float)
    reference_good_y = np.asarray(reference_good_y, dtype=float)
    target_x = np.asarray(target_x, dtype=float)
    target_good_y = np.asarray(target_good_y, dtype=float)
    bad_y = np.asarray(reference_bad_y, dtype=float) if reference_bad_y is not None else np.zeros((len(reference_x), 0))
    target_bad = np.asarray(target_bad_y, dtype=float) if target_bad_y is not None else np.zeros(0)
    ref_n, input_count = reference_x.shape
    good_count = reference_good_y.shape[1]
    bad_count = bad_y.shape[1]
    if ref_n < 1 or target_x.shape != (input_count,) or target_good_y.shape != (good_count,):
        raise ValueError("网络SBM目标或参考数据维度不一致。")
    if bad_count and target_bad.shape != (bad_count,):
        raise ValueError("网络SBM非期望产出维度不一致。")

    slack_count = input_count + good_count + bad_count
    total = ref_n + slack_count + 1
    t_index = total - 1
    s_input_start = ref_n
    s_good_start = s_input_start + input_count
    s_bad_start = s_good_start + good_count
    objective = np.zeros(total)
    objective[t_index] = 1.0
    objective[s_input_start:s_good_start] = -1.0 / max(input_count, 1) / np.maximum(target_x, 1e-12)
    if good_count:
        objective[s_good_start:s_bad_start] = -1.0 / max(good_count + bad_count, 1) / np.maximum(target_good_y, 1e-12)
    if bad_count:
        objective[s_bad_start:t_index] = -1.0 / max(good_count + bad_count, 1) / np.maximum(target_bad, 1e-12)

    a_eq: list[np.ndarray] = []
    b_eq: list[float] = []
    for col in range(input_count):
        row = np.zeros(total)
        row[:ref_n] = reference_x[:, col]
        row[s_input_start + col] = 1.0
        row[t_index] = -target_x[col]
        a_eq.append(row)
        b_eq.append(0.0)
    for col in range(good_count):
        row = np.zeros(total)
        row[:ref_n] = reference_good_y[:, col]
        row[s_good_start + col] = -1.0
        row[t_index] = -target_good_y[col]
        a_eq.append(row)
        b_eq.append(0.0)
    for col in range(bad_count):
        row = np.zeros(total)
        row[:ref_n] = bad_y[:, col]
        row[s_bad_start + col] = 1.0
        row[t_index] = -target_bad[col]
        a_eq.append(row)
        b_eq.append(0.0)
    if model == "BCC":
        row = np.zeros(total)
        row[:ref_n] = 1.0
        row[t_index] = -1.0
        a_eq.append(row)
        b_eq.append(0.0)

    normalization = np.zeros(total)
    normalization[t_index] = 1.0
    if good_count:
        normalization[s_good_start:s_bad_start] = 1.0 / max(good_count + bad_count, 1) / np.maximum(target_good_y, 1e-12)
    if bad_count:
        normalization[s_bad_start:t_index] = 1.0 / max(good_count + bad_count, 1) / np.maximum(target_bad, 1e-12)
    a_eq.append(normalization)
    b_eq.append(1.0)

    result = linprog(
        objective,
        A_eq=np.asarray(a_eq),
        b_eq=np.asarray(b_eq),
        bounds=[(0.0, None)] * ref_n + [(0.0, None)] * slack_count + [(1e-9, None)],
        method="highs",
    )
    if not result.success:
        raise RuntimeError(f"网络SBM求解失败：{result.message}")

    t = max(float(result.x[t_index]), 1e-12)
    lambdas = result.x[:ref_n] / t
    return {
        "efficiency": float(np.clip(result.fun, 0.0, 1.0)),
        "lambdas": lambdas,
        "input_slacks": result.x[s_input_start:s_good_start] / t,
        "good_slacks": result.x[s_good_start:s_bad_start] / t if good_count else np.zeros(0),
        "bad_slacks": result.x[s_bad_start:t_index] / t if bad_count else np.zeros(0),
    }


def evaluate_network_sbm(
    frame: pd.DataFrame,
    dmu_col: str,
    input_cols: list[str],
    intermediate_cols: list[str],
    output_cols: list[str],
    model: str = "BCC",
) -> dict[str, Any]:
    """Evaluate a transparent two-stage serial SBM learning process.

    Stage 1 maps initial learning inputs to intermediate learning-process
    indicators; stage 2 maps those linked indicators to final academic
    outputs. The network score is the geometric mean of the two stage scores,
    which keeps the score in [0, 1] and makes a weak stage visible.
    """

    work, x, z, y = _validate_network_frame(frame, dmu_col, input_cols, intermediate_cols, output_cols)
    stage1_solutions = []
    stage2_solutions = []
    records: list[dict[str, Any]] = []
    details: dict[str, Any] = {}
    for i in range(len(work)):
        stage1 = _solve_sbm_target(x, z, x[i], z[i], model)
        stage2 = _solve_sbm_target(z, y, z[i], y[i], model)
        stage1_solutions.append(stage1)
        stage2_solutions.append(stage2)
        stage1_score = stage1["efficiency"]
        stage2_score = stage2["efficiency"]
        network_score = float(np.sqrt(max(stage1_score, 0.0) * max(stage2_score, 0.0)))
        bottleneck = "投入→学习过程" if stage1_score < stage2_score - 1e-6 else "学习过程→学业结果" if stage2_score < stage1_score - 1e-6 else "两个阶段接近"
        name = str(work.iloc[i][dmu_col])
        peers1 = [{"DMU": str(work.iloc[j][dmu_col]), "权重": round(float(w), 6)} for j, w in enumerate(stage1["lambdas"]) if w > 1e-6]
        peers2 = [{"DMU": str(work.iloc[j][dmu_col]), "权重": round(float(w), 6)} for j, w in enumerate(stage2["lambdas"]) if w > 1e-6]
        details[name] = {
            "阶段1标杆": peers1,
            "阶段2标杆": peers2,
            "阶段1投入冗余": {col: round(float(stage1["input_slacks"][k]), 6) for k, col in enumerate(input_cols) if stage1["input_slacks"][k] > 1e-6},
            "阶段1过程不足": {col: round(float(stage1["good_slacks"][k]), 6) for k, col in enumerate(intermediate_cols) if stage1["good_slacks"][k] > 1e-6},
            "阶段2过程冗余": {col: round(float(stage2["input_slacks"][k]), 6) for k, col in enumerate(intermediate_cols) if stage2["input_slacks"][k] > 1e-6},
            "阶段2产出不足": {col: round(float(stage2["good_slacks"][k]), 6) for k, col in enumerate(output_cols) if stage2["good_slacks"][k] > 1e-6},
        }
        records.append({
            "DMU": name,
            "网络SBM效率": round(network_score, 6),
            "阶段1效率": round(float(stage1_score), 6),
            "阶段2效率": round(float(stage2_score), 6),
            "瓶颈阶段": bottleneck,
            "阶段差值": round(abs(float(stage1_score) - float(stage2_score)), 6),
        })
    table = pd.DataFrame(records).sort_values(["网络SBM效率", "DMU"], ascending=[False, True]).reset_index(drop=True)
    return {
        "config": {"dmu": dmu_col, "inputs": input_cols, "intermediate": intermediate_cols, "outputs": output_cols, "model": model, "network_score": "sqrt(stage1 * stage2)"},
        "summary": {
            "dmu_count": len(work),
            "efficient_count": int((table["网络SBM效率"] >= 1.0 - 1e-5).sum()),
            "average_efficiency": round(float(table["网络SBM效率"].mean()), 6),
            "average_stage1": round(float(table["阶段1效率"].mean()), 6),
            "average_stage2": round(float(table["阶段2效率"].mean()), 6),
        },
        "table": table,
        "details": details,
    }


def evaluate_group_meta_frontier(
    frame: pd.DataFrame,
    dmu_col: str,
    group_col: str,
    input_cols: list[str],
    intermediate_cols: list[str],
    output_cols: list[str],
    model: str = "BCC",
) -> dict[str, Any]:
    """Compare pooled and within-group two-stage frontiers.

    The pooled score is the meta-frontier score. The within-group score is
    the score against peers sharing the selected group. Their ratio is shown
    as a technology-gap indicator and is intentionally labelled as a
    comparative diagnostic rather than a causal effect.
    """

    work, x, z, y = _validate_network_frame(frame, dmu_col, input_cols, intermediate_cols, output_cols)
    if group_col not in frame.columns or group_col == dmu_col:
        raise ValueError("请选择有效的群体字段。")
    groups = frame[group_col].astype(str).str.strip().to_numpy()
    if len(groups) != len(work):
        raise ValueError("群体字段行数与有效DMU行数不一致。")
    if (groups == "").any():
        raise ValueError("群体字段存在空值，请先补齐专业、年级或班级信息。")
    pooled = evaluate_network_sbm(work.assign(**{group_col: groups}), dmu_col, input_cols, intermediate_cols, output_cols, model)
    pooled_scores = {str(row["DMU"]): float(row["网络SBM效率"]) for _, row in pooled["table"].iterrows()}
    group_scores: dict[str, float] = {}
    group_stage: dict[str, tuple[float, float]] = {}
    group_sizes = pd.Series(groups).value_counts().to_dict()
    valid_groups = 0
    for group in sorted(set(groups)):
        idx = np.flatnonzero(groups == group)
        if len(idx) < 3:
            continue
        valid_groups += 1
        scores = []
        stage_scores = []
        for i in idx:
            s1 = _solve_sbm_target(x[idx], z[idx], x[i], z[i], model)["efficiency"]
            s2 = _solve_sbm_target(z[idx], y[idx], z[i], y[i], model)["efficiency"]
            scores.append(np.sqrt(max(s1, 0.0) * max(s2, 0.0)))
            stage_scores.append((s1, s2))
        for local, i in enumerate(idx):
            name = str(work.iloc[i][dmu_col])
            group_scores[name] = float(scores[local])
            group_stage[name] = stage_scores[local]
    name_to_group = {str(work.iloc[i][dmu_col]): str(groups[i]) for i in range(len(work))}
    records = []
    for _, row in pooled["table"].iterrows():
        name = str(row["DMU"])
        within = group_scores.get(name, np.nan)
        meta = pooled_scores[name]
        group = name_to_group[name]
        records.append({
            "DMU": name,
            "群体": group,
            "群体内效率": round(within, 6) if np.isfinite(within) else np.nan,
            "元前沿效率": round(meta, 6),
            "技术差距比": round(float(meta / within), 6) if np.isfinite(within) and within > 1e-12 else np.nan,
            "群体样本量": int(group_sizes.get(group, 0)),
        })
    table = pd.DataFrame(records).sort_values(["元前沿效率", "DMU"], ascending=[False, True], na_position="last").reset_index(drop=True)
    group_table = table.groupby("群体", dropna=False).agg(
        群体样本量=("DMU", "count"),
        群体内平均效率=("群体内效率", "mean"),
        元前沿平均效率=("元前沿效率", "mean"),
        平均技术差距比=("技术差距比", "mean"),
    ).reset_index()
    return {
        "config": {"dmu": dmu_col, "group": group_col, "inputs": input_cols, "intermediate": intermediate_cols, "outputs": output_cols, "model": model},
        "summary": {"group_count": int(len(set(groups))), "valid_group_count": int(valid_groups), "average_meta_efficiency": round(float(table["元前沿效率"].mean()), 6)},
        "table": table,
        "group_table": group_table,
        "base": pooled,
    }


def bootstrap_network_sbm(
    frame: pd.DataFrame,
    dmu_col: str,
    input_cols: list[str],
    intermediate_cols: list[str],
    output_cols: list[str],
    model: str = "BCC",
    replications: int = 80,
    random_state: int = 42,
) -> dict[str, Any]:
    """Bootstrap the two-stage network scores and return uncertainty bands."""

    if replications < 10:
        raise ValueError("Bootstrap重复次数至少为10。")
    work, x, z, y = _validate_network_frame(frame, dmu_col, input_cols, intermediate_cols, output_cols)
    base = evaluate_network_sbm(work, dmu_col, input_cols, intermediate_cols, output_cols, model)
    n = len(work)
    bootstrap_scores = np.full((replications, n), np.nan, dtype=float)
    rng = np.random.default_rng(random_state)
    for replicate in range(replications):
        sample = rng.integers(0, n, size=n)
        reference_x = x[sample]
        reference_z = z[sample]
        reference_y = y[sample]
        for i in range(n):
            try:
                stage1 = _solve_sbm_target(reference_x, reference_z, x[i], z[i], model)
                stage2 = _solve_sbm_target(reference_z, reference_y, z[i], y[i], model)
            except RuntimeError:
                # A resampled frontier can fail to dominate a target whose
                # output lies above every sampled peer. Add the target as a
                # feasibility anchor for this replicate, while retaining the
                # sampled peers for discrimination.
                stage1 = _solve_sbm_target(np.vstack([reference_x, x[i]]), np.vstack([reference_z, z[i]]), x[i], z[i], model)
                stage2 = _solve_sbm_target(np.vstack([reference_z, z[i]]), np.vstack([reference_y, y[i]]), z[i], y[i], model)
            bootstrap_scores[replicate, i] = np.sqrt(max(stage1["efficiency"], 0.0) * max(stage2["efficiency"], 0.0))

    base_by_name = {str(work.iloc[i][dmu_col]): float(base["table"].set_index("DMU").loc[str(work.iloc[i][dmu_col]), "网络SBM效率"]) for i in range(n)}
    base_scores = np.array([base_by_name[str(work.iloc[i][dmu_col])] for i in range(n)], dtype=float)
    means = np.zeros(n, dtype=float)
    lows = np.zeros(n, dtype=float)
    highs = np.zeros(n, dtype=float)
    for i in range(n):
        values = bootstrap_scores[:, i]
        values = values[np.isfinite(values)]
        if len(values) < 3:
            means[i] = base_scores[i]
            lows[i] = base_scores[i]
            highs[i] = base_scores[i]
        else:
            means[i] = float(np.mean(values))
            lows[i] = float(np.percentile(values, 2.5))
            highs[i] = float(np.percentile(values, 97.5))
    corrected = np.clip(2 * base_scores - means, 0.0, 1.0)
    rank_correlations: list[float] = []
    base_rank = pd.Series(base_scores).rank(method="average").to_numpy()
    for values in bootstrap_scores:
        if np.isfinite(values).all() and np.std(values) > 1e-12:
            sample_rank = pd.Series(values).rank(method="average").to_numpy()
            rank_correlations.append(float(np.corrcoef(base_rank, sample_rank)[0, 1]))

    uncertainty = []
    for i in range(n):
        if lows[i] >= 0.999999:
            label = "稳定高效"
        elif highs[i] < 0.8:
            label = "稳定偏低"
        else:
            label = "边界不确定"
        uncertainty.append((means[i], lows[i], highs[i], corrected[i], label))
    table = base["table"].copy()
    by_name = {str(work.iloc[i][dmu_col]): i for i in range(n)}
    table["Bootstrap均值"] = [round(float(uncertainty[by_name[str(name)]][0]), 6) for name in table["DMU"]]
    table["Bootstrap下限95%"] = [round(float(uncertainty[by_name[str(name)]][1]), 6) for name in table["DMU"]]
    table["Bootstrap上限95%"] = [round(float(uncertainty[by_name[str(name)]][2]), 6) for name in table["DMU"]]
    table["偏差修正效率"] = [round(float(uncertainty[by_name[str(name)]][3]), 6) for name in table["DMU"]]
    table["稳健性标签"] = [uncertainty[by_name[str(name)]][4] for name in table["DMU"]]
    result = dict(base)
    result["config"] = {**base["config"], "bootstrap_replications": int(replications), "random_state": int(random_state)}
    result["summary"] = {**base["summary"], "bootstrap_replications": int(replications), "average_ci_width": round(float(np.nanmean(highs - lows)), 6), "mean_rank_correlation": round(float(np.mean(rank_correlations)), 6) if rank_correlations else None}
    result["table"] = table
    result["bootstrap_scores"] = bootstrap_scores
    return result


def evaluate_malmquist(
    frame: pd.DataFrame,
    dmu_col: str,
    period_col: str,
    input_cols: list[str],
    output_cols: list[str],
    model: str = "BCC",
) -> dict[str, Any]:
    """Calculate adjacent-period input-oriented Malmquist productivity indices."""

    if frame is None or frame.empty:
        raise ValueError("数据为空，无法计算Malmquist指数。")
    if dmu_col not in frame.columns or period_col not in frame.columns:
        raise ValueError("请选择有效的DMU和时期字段。")
    work = frame.copy().reset_index(drop=True)
    work[dmu_col] = work[dmu_col].astype(str).str.strip()
    if work[dmu_col].eq("").any():
        raise ValueError("DMU字段存在空名称。")
    x_frame = work[input_cols].apply(pd.to_numeric, errors="coerce")
    y_frame = work[output_cols].apply(pd.to_numeric, errors="coerce")
    if x_frame.isna().any().any() or y_frame.isna().any().any():
        raise ValueError("Malmquist的投入和产出字段必须全部为数值。")
    if (x_frame.to_numpy() < 0).any() or (y_frame.to_numpy() < 0).any():
        raise ValueError("Malmquist的投入和产出字段必须为非负数。")
    if (x_frame.sum(axis=1) <= 0).any() or (y_frame.sum(axis=1) <= 0).any():
        raise ValueError("Malmquist存在投入或产出合计为0的记录。")
    if not input_cols or not output_cols:
        raise ValueError("Malmquist至少需要一个投入指标和一个产出指标。")
    if period_col not in work.columns:
        raise ValueError("请选择有效的时期字段。")
    periods = sorted(work[period_col].astype(str).unique().tolist())
    if len(periods) < 2:
        raise ValueError("Malmquist至少需要两个时期。")
    x_all = x_frame.to_numpy(dtype=float)
    y_all = y_frame.to_numpy(dtype=float)
    results: list[dict[str, Any]] = []
    for left, right in zip(periods, periods[1:]):
        left_frame = work[work[period_col].astype(str) == left]
        right_frame = work[work[period_col].astype(str) == right]
        left_idx = left_frame.index.to_numpy()
        right_idx = right_frame.index.to_numpy()
        left_names = {str(work.loc[idx, dmu_col]): idx for idx in left_idx}
        right_names = {str(work.loc[idx, dmu_col]): idx for idx in right_idx}
        common = sorted(set(left_names) & set(right_names))
        if not common:
            continue
        ref_left_x = x_all[left_idx]
        ref_left_y = y_all[left_idx]
        ref_right_x = x_all[right_idx]
        ref_right_y = y_all[right_idx]
        for name in common:
            idx_left = left_names[name]
            idx_right = right_names[name]
            e_tt = _solve_input_target(ref_left_x, ref_left_y, x_all[idx_left], y_all[idx_left], model)
            e_tnext = _solve_input_target(ref_left_x, ref_left_y, x_all[idx_right], y_all[idx_right], model)
            e_nextt = _solve_input_target(ref_right_x, ref_right_y, x_all[idx_left], y_all[idx_left], model)
            e_nextnext = _solve_input_target(ref_right_x, ref_right_y, x_all[idx_right], y_all[idx_right], model)
            values = [e_tt, e_tnext, e_nextt, e_nextnext]
            if not np.isfinite(values).all() or min(values) <= 0:
                continue
            efficiency_change = e_tt / e_nextnext
            technical_change = float(np.sqrt((e_nextt / e_tt) * (e_nextnext / e_tnext)))
            malmquist = float(np.sqrt((e_tt / e_tnext) * (e_nextt / e_nextnext)))
            results.append({
                "DMU": name,
                "起始期": left,
                "结束期": right,
                "效率变化EC": round(float(efficiency_change), 6),
                "技术进步TC": round(technical_change, 6),
                "Malmquist指数": round(malmquist, 6),
                "生产率变化": "提升" if malmquist > 1.000001 else "下降" if malmquist < 0.999999 else "不变",
            })
    table = pd.DataFrame(results)
    if table.empty:
        raise ValueError("没有找到跨期重复出现的DMU，无法计算Malmquist指数。")
    return {
        "config": {"dmu": dmu_col, "period": period_col, "inputs": input_cols, "outputs": output_cols, "model": model},
        "summary": {"dmu_count": int(table["DMU"].nunique()), "period_count": len(periods), "average_malmquist": round(float(table["Malmquist指数"].mean()), 6)},
        "table": table.sort_values(["起始期", "DMU"]).reset_index(drop=True),
    }

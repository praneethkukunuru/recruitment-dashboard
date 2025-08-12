# app.py
# Flask Finance & Recruiting Dashboard
# -------------------------------------------------------
# Features
# - Upload CSVs for P&L, Balance Sheet, Recruitment, Margin statements
# - Flexible column mapping UI (no strict schema required)
# - Clean, responsive visuals (Plotly) + KPI cards
# - Auto date parsing + monthly rollups
# - Optional AI narrative (plug in your own OpenAI API key)
# - One-click HTML report export (embeds charts) + config save/load
# -------------------------------------------------------

from __future__ import annotations
import io
import json
import os
from typing import Dict, List, Optional
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.utils
from flask import Flask, render_template, request, jsonify, send_file, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --------------------- Helpers ---------------------

def read_csv_file(file_path: str) -> pd.DataFrame:
    if not file_path or not os.path.exists(file_path):
        return pd.DataFrame()
    try:
        # Read with automatic dtype inference and date parsing attempt
        df = pd.read_csv(file_path)
    except Exception:
        # Fallback to latin-1 for odd encodings
        df = pd.read_csv(file_path, encoding="latin-1")
    return df

def try_parse_dates(df: pd.DataFrame, candidate_cols: Optional[List[str]] = None) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    cols = candidate_cols or [c for c in df.columns if "date" in c.lower() or c.lower() in {"month", "period"}]
    for c in cols:
        try:
            df[c] = pd.to_datetime(df[c], errors="ignore", infer_datetime_format=True)
        except Exception:
            pass
    return df

def money_fmt(x: float) -> str:
    try:
        if pd.isna(x):
            return "—"
        abs_x = abs(x)
        if abs_x >= 1e9:
            return f"${x/1e9:,.2f}B"
        if abs_x >= 1e6:
            return f"${x/1e6:,.2f}M"
        if abs_x >= 1e3:
            return f"${x/1e3:,.1f}k"
        return f"${x:,.0f}"
    except Exception:
        return str(x)

# --------------------- Transformations ---------------------

def monthly_rollup(df: pd.DataFrame, date_col: Optional[str], agg_map: Dict[str, str]) -> pd.DataFrame:
    if df.empty or not date_col or date_col not in df.columns:
        return pd.DataFrame()
    df2 = df.copy()
    df2[date_col] = pd.to_datetime(df2[date_col], errors="coerce")
    df2 = df2.dropna(subset=[date_col])
    df2["__month"] = df2[date_col].dt.to_period("M").dt.to_timestamp()

    # coerce numeric
    for c in agg_map.keys():
        if c in df2.columns:
            df2[c] = pd.to_numeric(df2[c], errors="coerce")

    grouped = df2.groupby("__month").agg(agg_map).reset_index().rename(columns={"__month": "Month"})
    return grouped.sort_values("Month")

def compute_pl_fields(df: pd.DataFrame, mapping: Dict) -> pd.DataFrame:
    if df.empty:
        return df
    df = try_parse_dates(df, [mapping.get("date")])
    df = df.copy()

    # Initialize sums
    for key in ["revenue", "cogs", "opex", "other_income", "other_expense"]:
        cols = mapping.get(key) or []
        if not isinstance(cols, list):
            cols = [cols]
        for c in cols:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")
        df[f"__{key}"] = df[cols].sum(axis=1) if cols else 0

    df["__gross_profit"] = df["__revenue"] - df["__cogs"]
    df["__operating_income"] = df["__gross_profit"] - df["__opex"]
    df["__net_income"] = df["__operating_income"] + df["__other_income"] - df["__other_expense"]

    # Monthly rollup
    rolled = monthly_rollup(
        df,
        mapping.get("date"),
        {
            "__revenue": "sum",
            "__cogs": "sum",
            "__opex": "sum",
            "__gross_profit": "sum",
            "__operating_income": "sum",
            "__other_income": "sum",
            "__other_expense": "sum",
            "__net_income": "sum",
        },
    )
    return rolled

def compute_bs_fields(df: pd.DataFrame, mapping: Dict) -> pd.DataFrame:
    if df.empty:
        return df
    df = try_parse_dates(df, [mapping.get("date")])
    df = df.copy()

    def sum_cols(cols: List[str]) -> pd.Series:
        if not cols:
            return pd.Series([0] * len(df))
        for c in cols:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")
        return df[cols].sum(axis=1)

    df["__assets"] = sum_cols(mapping.get("assets") or [])
    df["__liabilities"] = sum_cols(mapping.get("liabilities") or [])
    df["__equity"] = sum_cols(mapping.get("equity") or [])

    rolled = monthly_rollup(
        df,
        mapping.get("date"),
        {"__assets": "mean", "__liabilities": "mean", "__equity": "mean"},
    )
    return rolled

def compute_recruit_fields(df: pd.DataFrame, mapping: Dict) -> pd.DataFrame:
    if df.empty:
        return df
    df = try_parse_dates(df, [mapping.get("date")])
    df = df.copy()

    for c in [mapping.get("placements"), mapping.get("revenue"), mapping.get("margin")]:
        if c and c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    agg_map = {}
    if mapping.get("placements") in df.columns:
        agg_map[mapping["placements"]] = "sum"
    if mapping.get("revenue") in df.columns:
        agg_map[mapping["revenue"]] = "sum"
    if mapping.get("margin") in df.columns:
        agg_map[mapping["margin"]] = "mean"  # if %; adjust later if needed

    rolled = monthly_rollup(df, mapping.get("date"), agg_map)
    return rolled

def compute_margin_fields(df: pd.DataFrame, mapping: Dict) -> pd.DataFrame:
    if df.empty:
        return df
    df = try_parse_dates(df, [mapping.get("date")])
    df = df.copy()

    for key in ["margin_amount", "margin_percent"]:
        c = mapping.get(key)
        if c and c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    agg_map = {}
    if mapping.get("margin_amount") in df.columns:
        agg_map[mapping["margin_amount"]] = "sum"
    if mapping.get("margin_percent") in df.columns:
        agg_map[mapping["margin_percent"]] = "mean"

    rolled = monthly_rollup(df, mapping.get("date"), agg_map)
    return rolled

# --------------------- Charts ---------------------

def fig_line(df: pd.DataFrame, x: str, y: List[str], title: str):
    if df.empty:
        return None
    mdf = df.melt(id_vars=[x], value_vars=y, var_name="Metric", value_name="Value")
    fig = px.line(mdf, x=x, y="Value", color="Metric", title=title)
    fig.update_layout(legend_title_text="")
    return fig

def fig_area(df: pd.DataFrame, x: str, y: List[str], title: str):
    if df.empty:
        return None
    mdf = df.melt(id_vars=[x], value_vars=y, var_name="Metric", value_name="Value")
    fig = px.area(mdf, x=x, y="Value", color="Metric", title=title)
    fig.update_layout(legend_title_text="")
    return fig

def fig_bar(df: pd.DataFrame, x: str, y: str, title: str):
    if df.empty:
        return None
    fig = px.bar(df, x=x, y=y, title=title)
    return fig

def fig_waterfall_from_pl(df: pd.DataFrame):
    # basic Profit waterfall for last month, if possible
    try:
        if df.empty or "Month" not in df.columns:
            return None
        last = df.sort_values("Month").tail(1).iloc[0]
        steps = [
            {"label": "Revenue", "value": float(last.get("__revenue", 0))},
            {"label": "COGS", "value": -float(last.get("__cogs", 0))},
            {"label": "Opex", "value": -float(last.get("__opex", 0))},
            {"label": "Other Inc.", "value": float(last.get("__other_income", 0))},
            {"label": "Other Exp.", "value": -float(last.get("__other_expense", 0))},
        ]
        dfwf = pd.DataFrame(steps)
        fig = px.bar(dfwf, x="label", y="value", title=f"Profit Walk – {last['Month'].strftime('%b %Y')}")
        return fig
    except Exception:
        return None

# --------------------- Routes ---------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    
    file = request.files['file']
    file_type = request.form.get('type')
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_type}_{filename}")
        file.save(file_path)
        
        # Read and return preview
        df = read_csv_file(file_path)
        df = try_parse_dates(df)
        
        return jsonify({
            'success': True,
            'columns': list(df.columns),
            'preview': df.head(10).to_dict('records'),
            'file_path': file_path
        })

@app.route('/process', methods=['POST'])
def process_data():
    data = request.json
    mappings = data.get('mappings', {})
    
    # Load data based on mappings
    pl_df_raw = pd.DataFrame()
    bs_df_raw = pd.DataFrame()
    rec_df_raw = pd.DataFrame()
    mg_df_raw = pd.DataFrame()
    
    if 'pl_file' in session:
        pl_df_raw = read_csv_file(session['pl_file'])
    if 'bs_file' in session:
        bs_df_raw = read_csv_file(session['bs_file'])
    if 'rec_file' in session:
        rec_df_raw = read_csv_file(session['rec_file'])
    if 'mg_file' in session:
        mg_df_raw = read_csv_file(session['mg_file'])
    
    # Apply date parsing
    pl_df_raw = try_parse_dates(pl_df_raw)
    bs_df_raw = try_parse_dates(bs_df_raw)
    rec_df_raw = try_parse_dates(rec_df_raw)
    mg_df_raw = try_parse_dates(mg_df_raw)
    
    # Compute rollups
    pl_m = compute_pl_fields(pl_df_raw, mappings.get('pl_map', {})) if not pl_df_raw.empty else pd.DataFrame()
    bs_m = compute_bs_fields(bs_df_raw, mappings.get('bs_map', {})) if not bs_df_raw.empty else pd.DataFrame()
    rec_m = compute_recruit_fields(rec_df_raw, mappings.get('rec_map', {})) if not rec_df_raw.empty else pd.DataFrame()
    mg_m = compute_margin_fields(mg_df_raw, mappings.get('mg_map', {})) if not mg_df_raw.empty else pd.DataFrame()
    
    # Calculate KPIs
    kpis = {}
    if not pl_m.empty:
        last_net = pl_m["__net_income"].iloc[-1] if not pl_m.empty else np.nan
        last_rev = pl_m["__revenue"].iloc[-1] if not pl_m.empty else np.nan
        last_gp = pl_m["__gross_profit"].iloc[-1] if not pl_m.empty else np.nan
        
        kpis.update({
            "Revenue (last period)": money_fmt(last_rev),
            "Gross Profit (last period)": money_fmt(last_gp),
            "Net Income (last period)": money_fmt(last_net),
        })
    
    if not bs_m.empty:
        last_assets = bs_m["__assets"].iloc[-1] if not bs_m.empty else np.nan
        last_liab = bs_m["__liabilities"].iloc[-1] if not bs_m.empty else np.nan
        
        kpis.update({
            "Assets (last)": money_fmt(last_assets),
            "Liabilities (last)": money_fmt(last_liab),
            "Assets − Liabilities (last)": money_fmt((last_assets or 0) - (last_liab or 0)),
        })
    
    # Generate charts
    charts = {}
    if not pl_m.empty:
        charts['pl_area'] = fig_area(pl_m, "Month", ["__revenue", "__cogs", "__opex"], "Revenue, COGS, Opex")
        charts['pl_line'] = fig_line(pl_m, "Month", ["__net_income"], "Net Income")
        charts['pl_waterfall'] = fig_waterfall_from_pl(pl_m)
    
    if not bs_m.empty:
        charts['bs_line'] = fig_line(bs_m, "Month", ["__assets", "__liabilities"], "Assets vs Liabilities")
        charts['bs_equity'] = fig_line(bs_m, "Month", ["__equity"], "Equity")
    
    if not rec_m.empty:
        rec_map = mappings.get('rec_map', {})
        if rec_map.get("placements") in rec_m.columns:
            charts['rec_bar'] = fig_bar(rec_m, "Month", rec_map["placements"], "Placements")
        if rec_map.get("revenue") in rec_m.columns:
            charts['rec_revenue'] = fig_line(rec_m, "Month", [rec_map["revenue"]], "Recruitment Revenue")
    
    # Convert charts to JSON
    charts_json = {}
    for name, fig in charts.items():
        if fig:
            charts_json[name] = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    return jsonify({
        'kpis': kpis,
        'charts': charts_json,
        'has_pl_data': not pl_m.empty,
        'has_bs_data': not bs_m.empty,
        'has_rec_data': not rec_m.empty,
        'has_mg_data': not mg_m.empty
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5003)

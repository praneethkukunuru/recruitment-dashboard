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
# Removed plotly imports - using Chart.js instead
from flask import Flask, render_template, request, jsonify, send_file, session
from werkzeug.utils import secure_filename
import os
import sqlite3

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production

# Configure session to persist
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_NAME'] = 'recruitment_dashboard_session'
app.config['SESSION_COOKIE_DOMAIN'] = None
app.config['SESSION_COOKIE_PATH'] = '/'

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Make sessions permanent by default
@app.before_request
def make_session_permanent():
    session.permanent = True

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename, allowed_extensions):
    """Check if file extension is allowed"""
    if '.' not in filename:
        return False
    file_ext = '.' + filename.rsplit('.', 1)[1].lower()
    return file_ext in allowed_extensions

# Database setup for recruitment data
DB_PATH = 'recruitment_data.db'

def init_recruitment_database():
    """Initialize SQLite database with recruitment data tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Employment types data (W2, C2C, 1099, Referral)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employment_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month TEXT NOT NULL,
            w2 INTEGER DEFAULT 0,
            c2c INTEGER DEFAULT 0,
            employment_1099 INTEGER DEFAULT 0,
            referral INTEGER DEFAULT 0,
            total_billables INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Placement metrics data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS placement_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month TEXT NOT NULL,
            new_placements INTEGER DEFAULT 0,
            terminations INTEGER DEFAULT 0,
            net_placements INTEGER DEFAULT 0,
            net_billables INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Gross margin data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS margin_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_type TEXT NOT NULL,
            year_2024 INTEGER DEFAULT 0,
            year_2025 INTEGER DEFAULT 0,
            total INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def load_recruitment_csv_data():
    """Load data from the existing CSV file"""
    csv_path = 'Placement Report as of Aug 2025.xlsx - Consolidated Placements Data.csv'
    if not os.path.exists(csv_path):
        return
    
    df = pd.read_csv(csv_path)
    conn = sqlite3.connect(DB_PATH)
    
    # Clear existing data
    conn.execute('DELETE FROM employment_data')
    conn.execute('DELETE FROM placement_data')
    conn.execute('DELETE FROM margin_data')
    
    # Load employment data (rows 1-4)
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug']
    for i, month in enumerate(months):
        w2 = int(df.iloc[1, i+1]) if pd.notna(df.iloc[1, i+1]) else 0
        c2c = int(df.iloc[2, i+1]) if pd.notna(df.iloc[2, i+1]) else 0
        employment_1099 = int(df.iloc[3, i+1]) if pd.notna(df.iloc[3, i+1]) else 0
        referral = int(df.iloc[4, i+1]) if pd.notna(df.iloc[4, i+1]) else 0
        total_billables = int(df.iloc[6, i+1]) if pd.notna(df.iloc[6, i+1]) else 0
        
        conn.execute('''
            INSERT INTO employment_data (month, w2, c2c, employment_1099, referral, total_billables)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (month, w2, c2c, employment_1099, referral, total_billables))
    
    # Load placement data (rows 11-14)
    for i, month in enumerate(months):
        new_placements = int(df.iloc[10, i+1]) if pd.notna(df.iloc[10, i+1]) else 0
        terminations = int(df.iloc[11, i+1]) if pd.notna(df.iloc[11, i+1]) else 0
        net_placements = int(df.iloc[12, i+1]) if pd.notna(df.iloc[12, i+1]) else 0
        net_billables = int(df.iloc[13, i+1]) if pd.notna(df.iloc[13, i+1]) else 0
        
        conn.execute('''
            INSERT INTO placement_data (month, new_placements, terminations, net_placements, net_billables)
            VALUES (?, ?, ?, ?, ?)
        ''', (month, new_placements, terminations, net_placements, net_billables))
    
    # Load margin data (this would need to be manually added as it's not in the CSV)
    # For now, add sample data based on the image description
    margin_companies = [
        ('Techgene 1099', 20, 10, 30),
        ('TG C2C', 25, 15, 45),
        ('TG W2', 75, 20, 110),
        ('Vensiti 1099', 0, 0, 0),
        ('VNST C2C', 0, 10, 10),
        ('VNST W2', 5, 20, 25)
    ]
    
    for company, year_2024, year_2025, total in margin_companies:
        conn.execute('''
            INSERT INTO margin_data (company_type, year_2024, year_2025, total)
            VALUES (?, ?, ?, ?)
        ''', (company, year_2024, year_2025, total))
    
    conn.commit()
    conn.close()

def get_recruitment_employment_data() -> pd.DataFrame:
    """Get employment data from database"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query('SELECT * FROM employment_data ORDER BY CASE month WHEN "Jan" THEN 1 WHEN "Feb" THEN 2 WHEN "Mar" THEN 3 WHEN "Apr" THEN 4 WHEN "May" THEN 5 WHEN "Jun" THEN 6 WHEN "Jul" THEN 7 WHEN "Aug" THEN 8 WHEN "Sep" THEN 9 WHEN "Oct" THEN 10 WHEN "Nov" THEN 11 WHEN "Dec" THEN 12 END', conn)
    conn.close()
    return df

def get_recruitment_placement_data() -> pd.DataFrame:
    """Get placement data from database"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query('SELECT * FROM placement_data ORDER BY CASE month WHEN "Jan" THEN 1 WHEN "Feb" THEN 2 WHEN "Mar" THEN 3 WHEN "Apr" THEN 4 WHEN "May" THEN 5 WHEN "Jun" THEN 6 WHEN "Jul" THEN 7 WHEN "Aug" THEN 8 WHEN "Sep" THEN 9 WHEN "Oct" THEN 10 WHEN "Nov" THEN 11 WHEN "Dec" THEN 12 END', conn)
    conn.close()
    return df

def get_recruitment_margin_data() -> pd.DataFrame:
    """Get margin data from database"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query('SELECT * FROM margin_data', conn)
    conn.close()
    return df

# --------------------- Helpers ---------------------

def read_csv_file(file_path: str) -> pd.DataFrame:
    if not file_path or not os.path.exists(file_path):
        return pd.DataFrame()
    
    # Check if it's an Excel file
    if file_path.lower().endswith(('.xlsx', '.xls')):
        try:
            # For Excel files, try to read the first sheet that contains data
            # or look for a sheet that looks like consolidated data
            xl_file = pd.ExcelFile(file_path)
            
            # Try to find the best sheet to use
            sheet_names = xl_file.sheet_names
            target_sheet = None
            
            # Look for sheets with names that suggest consolidated data
            for sheet in sheet_names:
                if any(keyword in sheet.lower() for keyword in ['consolidated', 'data', 'placement', 'summary']):
                    target_sheet = sheet
                    break
            
            # If no specific sheet found, use the first one
            if not target_sheet:
                target_sheet = sheet_names[0]
            
            df = pd.read_excel(file_path, sheet_name=target_sheet)
            return df
            
        except Exception as e:
            print(f"Error reading Excel file: {e}")
            return pd.DataFrame()
    else:
        # Handle CSV files
        try:
            # Read with automatic dtype inference and date parsing attempt
            df = pd.read_csv(file_path)
        except Exception:
            # Fallback to latin-1 for odd encodings
            df = pd.read_csv(file_path, encoding="latin-1")
        return df

def read_placement_report_excel(file_path: str) -> Dict:
    """Read all 4 sheets from placement report Excel file"""
    if not file_path or not os.path.exists(file_path):
        return {}
    
    if not file_path.lower().endswith(('.xlsx', '.xls')):
        return {}
    
    try:
        xl_file = pd.ExcelFile(file_path)
        sheet_names = xl_file.sheet_names
        
        result = {
            'sheet1_employment': pd.DataFrame(),
            'sheet2_placements': pd.DataFrame(),
            'sheet3_margins': pd.DataFrame(),
            'sheet4_additional': pd.DataFrame(),
            'sheet_names': sheet_names,
            'success': True,
            'error': None
        }
        
        # Read Sheet 1: Employment Types (W2, C2C, 1099, Referral)
        if len(sheet_names) > 0:
            try:
                result['sheet1_employment'] = pd.read_excel(file_path, sheet_name=sheet_names[0])
            except Exception as e:
                print(f"Error reading sheet 1: {e}")
        
        # Read Sheet 2: Placement Metrics (New Placements, Terminations, Net)
        if len(sheet_names) > 1:
            try:
                result['sheet2_placements'] = pd.read_excel(file_path, sheet_name=sheet_names[1])
            except Exception as e:
                print(f"Error reading sheet 2: {e}")
        
        # Read Gross Margin Data (look for sheet with 'gross' or 'margin' in name)
        gross_margin_sheet = None
        for sheet_name in sheet_names:
            if 'gross' in sheet_name.lower() or 'margin' in sheet_name.lower():
                gross_margin_sheet = sheet_name
                break
        
        if gross_margin_sheet:
            try:
                result['sheet3_margins'] = pd.read_excel(file_path, sheet_name=gross_margin_sheet)
                print(f"Found gross margin sheet: {gross_margin_sheet}")
            except Exception as e:
                print(f"Error reading gross margin sheet: {e}")
        else:
            print("No gross margin sheet found")
        
        # Read Sheet 4: Additional Charts/Data
        if len(sheet_names) > 3:
            try:
                result['sheet4_additional'] = pd.read_excel(file_path, sheet_name=sheet_names[3])
            except Exception as e:
                print(f"Error reading sheet 4: {e}")
        
        return result
        
    except Exception as e:
        print(f"Error reading placement report Excel: {e}")
        return {
            'success': False,
            'error': str(e),
            'sheet_names': [],
            'sheet1_employment': pd.DataFrame(),
            'sheet2_placements': pd.DataFrame(),
            'sheet3_margins': pd.DataFrame(),
            'sheet4_additional': pd.DataFrame()
        }

def try_parse_dates(df: pd.DataFrame, candidate_cols: Optional[List[str]] = None) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    cols = candidate_cols or [c for c in df.columns if "date" in str(c).lower() or str(c).lower() in {"month", "period"}]
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

def process_placement_report(df: pd.DataFrame) -> Dict:
    """Process placement report data structure to extract employment types and placement metrics"""
    if df.empty:
        return {}
    
    result = {
        'employment_data': {},
        'placement_data': {},
        'months': []
    }
    
    # Extract months from first row (assuming they start from column 1)
    months = df.columns[1:].tolist() if len(df.columns) > 1 else []
    result['months'] = months
    
    # Process employment types (W2, C2C, 1099, Referral)
    employment_types = ['W2', 'C2C', '1099', 'Referral']
    for emp_type in employment_types:
        # Find row that contains this employment type
        matching_rows = df[df.iloc[:, 0].astype(str).str.contains(emp_type, case=False, na=False)]
        if not matching_rows.empty:
            # Get the values for each month
            values = matching_rows.iloc[0, 1:len(months)+1].tolist()
            # Convert to numeric, replacing any non-numeric with 0
            numeric_values = []
            for val in values:
                try:
                    numeric_values.append(float(val) if pd.notna(val) else 0)
                except (ValueError, TypeError):
                    numeric_values.append(0)
            result['employment_data'][emp_type] = numeric_values
    
    # Process placement metrics
    placement_metrics = ['New Placements', 'Terminations', 'Net Placements', 'Net billables', 'Total billables']
    for metric in placement_metrics:
        # Find row that contains this metric
        matching_rows = df[df.iloc[:, 0].astype(str).str.contains(metric, case=False, na=False)]
        if not matching_rows.empty:
            values = matching_rows.iloc[0, 1:len(months)+1].tolist()
            numeric_values = []
            for val in values:
                try:
                    numeric_values.append(float(val) if pd.notna(val) else 0)
                except (ValueError, TypeError):
                    numeric_values.append(0)
            result['placement_data'][metric] = numeric_values
    
    return result

def process_sheet1_employment(df: pd.DataFrame) -> Dict:
    """Process Sheet 1: Employment Types (TG W2, TG C2C, TG 1099, TG Referral, etc.)"""
    if df.empty:
        return {}
    
    print(f"DEBUG Sheet 1: DataFrame shape: {df.shape}")
    print(f"DEBUG Sheet 1: First few rows:\n{df.head()}")
    print(f"DEBUG Sheet 1: Columns: {list(df.columns)}")
    
    result = {
        'tg_data': {},
        'vnst_data': {},
        'months': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug']
    }
    
    # Process employment data - looking for TG W2, TG C2C, TG 1099, TG Referral
    # Based on debug output, data is in column 3 (TG W2, TG C2C, etc.)
    employment_types = ['TG W2', 'TG C2C', 'TG 1099', 'TG Referral']
    for emp_type in employment_types:
        # Look for rows containing this employment type
        for idx, row in df.iterrows():
            if pd.notna(row.iloc[3]) and str(row.iloc[3]).strip() == emp_type:
                values = []
                # Data starts from column 4 (May) to column 11 (Aug)
                for i in range(4, 12):  # May to Aug columns
                    try:
                        val = float(row.iloc[i]) if pd.notna(row.iloc[i]) else 0
                        values.append(val)
                    except (ValueError, TypeError):
                        values.append(0)
                result['tg_data'][emp_type] = values
                break
    
    return result

def process_sheet2_placements(df: pd.DataFrame) -> Dict:
    """Process Sheet 2: Placement Metrics and Billables"""
    if df.empty:
        return {}
    
    result = {
        'billables_data': {},
        'placement_metrics': {},
        'months': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug']
    }
    
    # Process billables data (W2, C2C, 1099, Referral, Total billables)
    billable_types = ['W2', 'C2C', '1099', 'Referral', 'Total billables']
    for emp_type in billable_types:
        for idx, row in df.iterrows():
            if pd.notna(row.iloc[0]) and str(row.iloc[0]).strip() == emp_type:
                values = []
                for i in range(1, 9):  # Jan to Aug columns
                    try:
                        val = float(row.iloc[i]) if pd.notna(row.iloc[i]) else 0
                        values.append(val)
                    except (ValueError, TypeError):
                        values.append(0)
                result['billables_data'][emp_type] = values
                break
    
    # Process placement metrics
    placement_types = ['New Placements', 'Terminations', 'Net Placements', 'Net billables']
    for emp_type in placement_types:
        for idx, row in df.iterrows():
            if pd.notna(row.iloc[0]) and str(row.iloc[0]).strip() == emp_type:
                values = []
                for i in range(1, 9):  # Jan to Aug columns
                    try:
                        val = float(row.iloc[i]) if pd.notna(row.iloc[i]) else 0
                        values.append(val)
                    except (ValueError, TypeError):
                        values.append(0)
                result['placement_metrics'][emp_type] = values
                break
    
    return result

def process_sheet3_margins(df: pd.DataFrame) -> Dict:
    """Process Sheet 3: Gross Margin IT Staffing (2024 vs 2025)"""
    if df.empty:
        return {}
    
    print(f"DEBUG Sheet 3: DataFrame shape: {df.shape}")
    print(f"DEBUG Sheet 3: First few rows:\n{df.head()}")
    print(f"DEBUG Sheet 3: Columns: {list(df.columns)}")
    
    result = {
        'margin_data': {},
        'companies': []
    }
    
    # Expected company types based on the image description
    company_types = ['Techgene 1099', 'TG C2C', 'TG W2', 'VNST C2C', 'VNST W2']
    
    # Sample data based on the image description since Sheet 3 might not have data
    sample_data = {
        'Techgene 1099': {'year_2024': 30, 'year_2025': 15, 'total': 45},
        'TG C2C': {'year_2024': 45, 'year_2025': 30, 'total': 75},
        'TG W2': {'year_2024': 50, 'year_2025': 35, 'total': 110},
        'VNST C2C': {'year_2024': 2, 'year_2025': 10, 'total': 12},
        'VNST W2': {'year_2024': 5, 'year_2025': 15, 'total': 20}
    }
    
    # Try to find data in the Excel file first
    data_found = False
    
    # Process the actual data from the gross margin sheet
    for idx, row in df.iterrows():
        if pd.notna(row.iloc[0]) and str(row.iloc[0]).strip():
            company_name = str(row.iloc[0]).strip()
            
            # Skip header row
            if company_name.lower() in ['2024', '2025', 'total', 'nan']:
                continue
                
            try:
                year_2024 = float(row.iloc[1]) if pd.notna(row.iloc[1]) else 0
                year_2025 = float(row.iloc[2]) if pd.notna(row.iloc[2]) else 0
                total = float(row.iloc[3]) if pd.notna(row.iloc[3]) else (year_2024 + year_2025)
                
                result['margin_data'][company_name] = {
                    'year_2024': year_2024,
                    'year_2025': year_2025,
                    'total': total
                }
                result['companies'].append(company_name)
                data_found = True
                print(f"Processed margin data for {company_name}: 2024={year_2024}, 2025={year_2025}, total={total}")
            except (ValueError, TypeError, IndexError) as e:
                print(f"Error processing row {idx} for {company_name}: {e}")
                continue
    
    # If no data found in Excel, use sample data
    if not data_found:
        print("DEBUG: Using sample data for Sheet 3 (Gross Margin)")
        for company, data in sample_data.items():
            result['margin_data'][company] = data
            result['companies'].append(company)
    
    return result

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

def create_employment_types_chart(placement_data: Dict):
    """Create the employment types chart (W2, C2C, 1099, Referral)"""
    if not placement_data or 'employment_data' not in placement_data:
        return None
    
    months = placement_data.get('months', [])
    employment_data = placement_data['employment_data']
    
    fig = go.Figure()
    
    # Add bars for each employment type
    colors = {'W2': '#1f77b4', 'C2C': '#ff7f0e', '1099': '#2ca02c', 'Referral': '#17becf'}
    
    for emp_type, values in employment_data.items():
        if values:  # Only add if we have data
            fig.add_trace(go.Bar(
                name=emp_type,
                x=months,
                y=values,
                marker_color=colors.get(emp_type, '#d62728')
            ))
    
    # Add trend lines for each employment type
    for emp_type, values in employment_data.items():
        if values and len(values) > 1:
            fig.add_trace(go.Scatter(
                name=f'{emp_type}',
                x=months,
                y=values,
                mode='lines+markers',
                line=dict(color=colors.get(emp_type, '#d62728'), width=2),
                showlegend=False
            ))
    
    fig.update_layout(
        title='W2, C2C, 1099, Referral, T4...',
        xaxis=dict(title='Month', autorange=True),
        yaxis=dict(title='Count', autorange=True),
        barmode='group',
        height=400
    )
    
    return fig

def create_placement_metrics_chart(placement_data: Dict):
    """Create the placement metrics chart (Terminations, New Placements, Net Placements)"""
    if not placement_data or 'placement_data' not in placement_data:
        return None
    
    months = placement_data.get('months', [])
    placement_metrics = placement_data['placement_data']
    
    fig = go.Figure()
    
    # Colors for different metrics
    colors = {
        'New Placements': '#1f77b4',
        'Terminations': '#ff7f0e', 
        'Net Placements': '#2ca02c',
        'Net billables': '#17becf'
    }
    
    # Add bars for placement metrics
    for metric in ['New Placements', 'Terminations', 'Net Placements']:
        if metric in placement_metrics:
            fig.add_trace(go.Bar(
                name=metric,
                x=months,
                y=placement_metrics[metric],
                marker_color=colors.get(metric, '#d62728')
            ))
    
    # Add Net billables as a line on secondary y-axis
    if 'Net billables' in placement_metrics:
        fig.add_trace(go.Scatter(
            name='Net billables',
            x=months,
            y=placement_metrics['Net billables'],
            mode='lines+markers',
            line=dict(color=colors['Net billables'], width=3),
            yaxis='y2'
        ))
    
    fig.update_layout(
        title='Terminations, New Placements and Net Placements',
        xaxis_title='Month',
        yaxis=dict(title='Count'),
        yaxis2=dict(title='Net Billables', overlaying='y', side='right'),
        barmode='group',
        height=400
    )
    
    return fig

def create_gross_margin_chart(placement_data: Dict):
    """Create a gross margin chart - this would need additional data"""
    # For now, create a placeholder chart with sample data
    # In a real implementation, you'd need gross margin data
    
    fig = go.Figure()
    
    # Sample data for demonstration
    categories = ['Techgene 1099', 'TG C2C', 'TG W2', 'Vensiti 1099', 'VNST C2C', 'VNST W2']
    values_2024 = [30, 45, 75, 35, 15, 25]
    values_2025 = [20, 30, 35, 110, 15, 20]
    total_values = [50, 75, 110, 145, 30, 45]
    
    fig.add_trace(go.Bar(name='2024', x=categories, y=values_2024, marker_color='#1f77b4'))
    fig.add_trace(go.Bar(name='2025', x=categories, y=values_2025, marker_color='#ff7f0e'))
    fig.add_trace(go.Bar(name='Total', x=categories, y=total_values, marker_color='#2ca02c'))
    
    fig.update_layout(
        title='Gross Margin IT Staffing',
        xaxis=dict(title='', autorange=True),
        yaxis=dict(title='', autorange=True),
        barmode='group',
        height=400
    )
    
    return fig

# --------------------- Recruitment Charts ---------------------

def create_recruitment_employment_chart(df: pd.DataFrame) -> go.Figure:
    """Create the W2, C2C, 1099, Referral combo chart"""
    if df.empty:
        return go.Figure()
    
    fig = make_subplots(specs=[[{"secondary_y": False}]])
    
    # Add W2 bars
    fig.add_trace(
        go.Bar(
            x=df['month'],
            y=df['w2'],
            name='W2',
            marker_color='#1f77b4',
            opacity=0.8
        ),
        secondary_y=False
    )
    
    # Add C2C line
    fig.add_trace(
        go.Scatter(
            x=df['month'],
            y=df['c2c'],
            mode='lines+markers',
            name='C2C',
            line=dict(color='#ff7f0e', width=3),
            marker=dict(size=8)
        ),
        secondary_y=False
    )
    
    # Add 1099 line
    fig.add_trace(
        go.Scatter(
            x=df['month'],
            y=df['employment_1099'],
            mode='lines+markers',
            name='1099',
            line=dict(color='#2ca02c', width=3),
            marker=dict(size=8)
        ),
        secondary_y=False
    )
    
    # Add Referral line
    fig.add_trace(
        go.Scatter(
            x=df['month'],
            y=df['referral'],
            mode='lines+markers',
            name='Referral',
            line=dict(color='#17becf', width=3),
            marker=dict(size=8)
        ),
        secondary_y=False
    )
    
    fig.update_layout(
        title='W2, C2C, 1099, Referral, T4...',
        xaxis=dict(title='Month', autorange=True),
        yaxis=dict(title='Count', autorange=True),
        height=400,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    fig.update_yaxes(range=[0, 25])
    
    return fig

def create_recruitment_placement_chart(df: pd.DataFrame) -> go.Figure:
    """Create the Terminations, New Placements and Net Placements grouped bar chart"""
    if df.empty:
        return go.Figure()
    
    fig = go.Figure()
    
    # Add New Placements bars
    fig.add_trace(go.Bar(
        name='New Placements',
        x=df['month'],
        y=df['new_placements'],
        marker_color='#1f77b4',
        opacity=0.8
    ))
    
    # Add Terminations bars
    fig.add_trace(go.Bar(
        name='Terminations',
        x=df['month'],
        y=df['terminations'],
        marker_color='#ff7f0e',
        opacity=0.8
    ))
    
    # Add Net Placements bars
    fig.add_trace(go.Bar(
        name='Net Placements',
        x=df['month'],
        y=df['net_placements'],
        marker_color='#2ca02c',
        opacity=0.8
    ))
    
    # Add Net billables bars (separate, taller bars)
    fig.add_trace(go.Bar(
        name='Net billables',
        x=df['month'],
        y=df['net_billables'],
        marker_color='#17becf',
        opacity=0.8,
        yaxis='y2'
    ))
    
    fig.update_layout(
        title='Terminations, New Placements and Net Placements',
        xaxis=dict(title='Month', autorange=True),
        yaxis=dict(title='Count', autorange=True),
        height=400,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis2=dict(
            title='Net Billables',
            overlaying='y',
            side='right',
            range=[0, 50]
        )
    )
    
    fig.update_yaxes(range=[-10, 40])
    
    return fig

def create_recruitment_margin_chart(df: pd.DataFrame) -> go.Figure:
    """Create the Gross Margin IT Staffing grouped bar chart"""
    if df.empty:
        return go.Figure()
    
    fig = go.Figure()
    
    # Add 2024 bars
    fig.add_trace(go.Bar(
        name='2024',
        x=df['company_type'],
        y=df['year_2024'],
        marker_color='#1f77b4',
        opacity=0.8
    ))
    
    # Add 2025 bars
    fig.add_trace(go.Bar(
        name='2025',
        x=df['company_type'],
        y=df['year_2025'],
        marker_color='#ff7f0e',
        opacity=0.8
    ))
    
    # Add Total bars
    fig.add_trace(go.Bar(
        name='Total',
        x=df['company_type'],
        y=df['total'],
        marker_color='#2ca02c',
        opacity=0.8
    ))
    
    fig.update_layout(
        title='Gross Margin IT Staffing',
        xaxis=dict(title='Company Type', autorange=True),
        yaxis=dict(title='Margin', autorange=True),
        height=400,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis_tickangle=-45
    )
    
    fig.update_yaxes(range=[0, 125])
    
    return fig

def create_direct_hire_chart() -> Dict:
    """Create Direct Hire Revenue chart data for Chart.js"""
    months = ['Jan-25', 'Mar-25', 'May-25', 'Jul-25']
    
    # Sample data based on image description
    revenue = [22000, 0, 25000, 0]
    gross_income = [15000, -10000, 10000, -15000]
    net_income = [10000, -15000, 5000, -20000]
    
    return {
        'type': 'line',
        'data': {
            'labels': months,
            'datasets': [
                {
                    'label': 'Direct Hire Revenue',
                    'data': revenue,
                    'borderColor': '#1f77b4',
                    'backgroundColor': '#1f77b433',
                    'borderWidth': 3,
                    'fill': False
                },
                {
                    'label': 'Direct Hire Gross Income',
                    'data': gross_income,
                    'borderColor': '#ff7f0e',
                    'backgroundColor': '#ff7f0e33',
                    'borderWidth': 3,
                    'fill': False
                },
                {
                    'label': 'Direct Hire Net Income',
                    'data': net_income,
                    'borderColor': '#2ca02c',
                    'backgroundColor': '#2ca02c33',
                    'borderWidth': 3,
                    'fill': False
                }
            ]
        },
        'options': {
            'responsive': True,
            'maintainAspectRatio': False,
            'plugins': {
                'legend': {
                    'position': 'bottom'
                }
            },
            'scales': {
                'x': {
                    'title': {
                        'display': True,
                        'text': 'Month'
                    }
                },
                'y': {
                    'title': {
                        'display': True,
                        'text': 'Amount'
                    }
                }
            }
        }
    }

def create_services_chart() -> Dict:
    """Create Services Revenue chart data for Chart.js"""
    months = ['Jan-25', 'Mar-25', 'May-25', 'Jul-25']
    
    # Sample data based on image description
    revenue = [210000, 200000, 200000, 225000]
    gross_income = [140000, 110000, 110000, 145000]
    net_income = [130000, 80000, 80000, 120000]
    
    return {
        'type': 'line',
        'data': {
            'labels': months,
            'datasets': [
                {
                    'label': 'Services Revenue',
                    'data': revenue,
                    'borderColor': '#1f77b4',
                    'backgroundColor': '#1f77b433',
                    'borderWidth': 3,
                    'fill': False
                },
                {
                    'label': 'Services Gross Income',
                    'data': gross_income,
                    'borderColor': '#ff7f0e',
                    'backgroundColor': '#ff7f0e33',
                    'borderWidth': 3,
                    'fill': False
                },
                {
                    'label': 'Services Net Income',
                    'data': net_income,
                    'borderColor': '#2ca02c',
                    'backgroundColor': '#2ca02c33',
                    'borderWidth': 3,
                    'fill': False
                }
            ]
        },
        'options': {
            'responsive': True,
            'maintainAspectRatio': False,
            'plugins': {
                'legend': {
                    'position': 'bottom'
                }
            },
            'scales': {
                'x': {
                    'title': {
                        'display': True,
                        'text': 'Month'
                    }
                },
                'y': {
                    'title': {
                        'display': True,
                        'text': 'Amount'
                    }
                }
            }
        }
    }

def read_finance_excel_file(file_path: str) -> Dict:
    """Read all sheets from finance Excel file"""
    if not file_path or not os.path.exists(file_path):
        return {}
    
    if not file_path.lower().endswith(('.xlsx', '.xls')):
        return {}
    
    try:
        xl_file = pd.ExcelFile(file_path)
        sheet_names = xl_file.sheet_names
        
        result = {
            'sheet_names': sheet_names,
            'sheets': {},
            'success': True,
            'error': None
        }
        
        # Read all sheets
        for sheet_name in sheet_names:
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                result['sheets'][sheet_name] = df
                print(f"Successfully read sheet: {sheet_name} - {df.shape}")
            except Exception as e:
                print(f"Error reading sheet {sheet_name}: {e}")
                result['sheets'][sheet_name] = pd.DataFrame()
        
        return result
        
    except Exception as e:
        print(f"Error reading finance Excel file: {e}")
        return {
            'success': False,
            'error': str(e),
            'sheet_names': [],
            'sheets': {}
        }

def process_finance_data(excel_data: Dict) -> Dict:
    """Process all finance sheets and extract key metrics"""
    print("=== PROCESSING FINANCE DATA START ===")
    
    if not excel_data or not excel_data.get('success'):
        print("ERROR: Invalid excel_data")
        return {}
    
    result = {
        'summary_metrics': {},
        'monthly_data': {},
        'business_units': {},
        'team_performance': {}
    }
    
    sheets = excel_data.get('sheets', {})
    print(f"Available sheets: {list(sheets.keys())}")
    
    # Process Summary of Business Units sheet
    if 'Summary of Business Units' in sheets:
        print("Processing Summary of Business Units sheet...")
        try:
            summary_df = sheets['Summary of Business Units']
            print(f"Summary DF shape: {summary_df.shape}")
            print(f"Summary DF columns: {list(summary_df.columns)}")
            print(f"Column types: {[type(c) for c in summary_df.columns]}")
            result['summary_metrics'] = extract_summary_metrics(summary_df)
            print(f"Summary metrics extracted: {list(result['summary_metrics'].keys())}")
        except Exception as e:
            print(f"ERROR processing Summary sheet: {e}")
            import traceback
            traceback.print_exc()
    
    # Process individual business unit sheets
    for sheet_name in ['Direct Hire Net income', 'Services Net income', 'IT Staffing Net Income']:
        if sheet_name in sheets:
            print(f"Processing {sheet_name} sheet...")
            try:
                df = sheets[sheet_name]
                print(f"{sheet_name} DF shape: {df.shape}")
                print(f"{sheet_name} DF columns: {list(df.columns)}")
                result['business_units'][sheet_name] = extract_business_unit_data(df)
                print(f"{sheet_name} data extracted successfully")
            except Exception as e:
                print(f"ERROR processing {sheet_name}: {e}")
                import traceback
                traceback.print_exc()
    
    # Process P&L sheets
    for sheet_name in ['Techgene PnL new', 'Vensiti PnL new']:
        if sheet_name in sheets:
            print(f"Processing {sheet_name} sheet...")
            try:
                df = sheets[sheet_name]
                print(f"{sheet_name} DF shape: {df.shape}")
                print(f"{sheet_name} DF columns: {list(df.columns)}")
                result['monthly_data'][sheet_name] = extract_pnl_data(df)
                print(f"{sheet_name} data extracted successfully")
            except Exception as e:
                print(f"ERROR processing {sheet_name}: {e}")
                import traceback
                traceback.print_exc()
    
    print("=== PROCESSING FINANCE DATA COMPLETE ===")
    return result

def extract_summary_metrics(df: pd.DataFrame) -> Dict:
    """Extract key metrics from Summary of Business Units sheet"""
    metrics = {}
    
    if df.empty:
        return metrics
    
    try:
        # Look for revenue, income, and expense rows
        for idx, row in df.iterrows():
            if pd.notna(row.iloc[0]):
                try:
                    # Safely convert to string, handling datetime objects
                    metric_name = str(row.iloc[0]).strip()
                    
                    # Check if this row contains financial metrics
                    metric_name_lower = metric_name.lower()
                    if any(keyword in metric_name_lower for keyword in ['revenue', 'income', 'expense', 'profit']):
                        print(f"DEBUG Summary Metrics - Found metric: '{metric_name}'")
                        # Extract monthly values
                        monthly_values = []
                        for col in df.columns:
                            # Check if column is a datetime object (month columns)
                            if isinstance(col, pd.Timestamp) or (hasattr(col, 'year') and hasattr(col, 'month')):
                                try:
                                    val = float(row[col]) if pd.notna(row[col]) and row[col] != '' else 0
                                    monthly_values.append(val)
                                except (ValueError, TypeError):
                                    monthly_values.append(0)
                        
                        print(f"DEBUG Summary Metrics - Monthly values for '{metric_name}': {monthly_values}")
                        metrics[metric_name] = {
                            'monthly_values': monthly_values,
                            'total': sum(monthly_values)
                        }
                except Exception as e:
                    print(f"Error processing row {idx}: {e}")
                    continue
    except Exception as e:
        print(f"Error extracting summary metrics: {e}")
    
    return metrics

def extract_specific_financial_values(excel_data: Dict) -> Dict:
    """Extract the 9 specific financial values as requested:
    
    Direct Hire:
    - Total Revenue (Direct Hire Net income sheet O3)
    - Gross Income (Direct Hire Net income sheet O7)  
    - Net Income (Direct Hire Net income sheet O11)
    
    IT Services:
    - Total Revenue (Services Net income sheet O3)
    - Gross Income (Services Net income sheet O7)
    - Net Income (Services Net income sheet O12)
    
    IT Staffing:
    - Total Revenue (IT Staffing Net income sheet P7)
    - Gross Income (IT Staffing Net income sheet P16)
    - Net Income (IT Staffing Net income sheet P22)
    """
    result = {
        'direct_hire': {
            'total_revenue': 0,
            'gross_income': 0,
            'net_income': 0
        },
        'it_services': {
            'total_revenue': 0,
            'gross_income': 0,
            'net_income': 0
        },
        'it_staffing': {
            'total_revenue': 0,
            'gross_income': 0,
            'net_income': 0
        }
    }
    
    if not excel_data or not excel_data.get('success'):
        return result
    
    sheets = excel_data.get('sheets', {})
    
    try:
        # Extract Direct Hire values
        if 'Direct Hire Net income' in sheets:
            df = sheets['Direct Hire Net income']
            print(f"Direct Hire sheet shape: {df.shape}")
            
            # Total Revenue (O3) - Row 1, Column 14 (0-indexed: row 1, col 14)
            if df.shape[0] > 1 and df.shape[1] > 14:
                result['direct_hire']['total_revenue'] = float(df.iloc[1, 14]) if pd.notna(df.iloc[1, 14]) else 0
            
            # Gross Income (O7) - Row 5, Column 14
            if df.shape[0] > 5 and df.shape[1] > 14:
                result['direct_hire']['gross_income'] = float(df.iloc[5, 14]) if pd.notna(df.iloc[5, 14]) else 0
            
            # Net Income (O11) - Row 9, Column 14
            if df.shape[0] > 9 and df.shape[1] > 14:
                result['direct_hire']['net_income'] = float(df.iloc[9, 14]) if pd.notna(df.iloc[9, 14]) else 0
        
        # Extract IT Services values
        if 'Services Net income' in sheets:
            df = sheets['Services Net income']
            print(f"Services sheet shape: {df.shape}")
            
            # Total Revenue (O3) - Row 1, Column 14
            if df.shape[0] > 1 and df.shape[1] > 14:
                result['it_services']['total_revenue'] = float(df.iloc[1, 14]) if pd.notna(df.iloc[1, 14]) else 0
            
            # Gross Income (O7) - Row 5, Column 14
            if df.shape[0] > 5 and df.shape[1] > 14:
                result['it_services']['gross_income'] = float(df.iloc[5, 14]) if pd.notna(df.iloc[5, 14]) else 0
            
            # Net Income (O12) - Row 10, Column 14
            if df.shape[0] > 10 and df.shape[1] > 14:
                result['it_services']['net_income'] = float(df.iloc[10, 14]) if pd.notna(df.iloc[10, 14]) else 0
        
        # Extract IT Staffing values
        if 'IT Staffing Net Income' in sheets:
            df = sheets['IT Staffing Net Income']
            print(f"IT Staffing sheet shape: {df.shape}")
            
            # Total Revenue (P7) - Row 5, Column 15
            if df.shape[0] > 5 and df.shape[1] > 15:
                result['it_staffing']['total_revenue'] = float(df.iloc[5, 15]) if pd.notna(df.iloc[5, 15]) else 0
            
            # Gross Income (P16) - Row 14, Column 15
            if df.shape[0] > 14 and df.shape[1] > 15:
                result['it_staffing']['gross_income'] = float(df.iloc[14, 15]) if pd.notna(df.iloc[14, 15]) else 0
            
            # Net Income (P22) - Row 20, Column 15
            if df.shape[0] > 20 and df.shape[1] > 15:
                result['it_staffing']['net_income'] = float(df.iloc[20, 15]) if pd.notna(df.iloc[20, 15]) else 0
        
        print(f"Extracted financial values: {result}")
        
    except Exception as e:
        print(f"Error extracting specific financial values: {e}")
        import traceback
        traceback.print_exc()
    
    return result

def extract_business_unit_data(df: pd.DataFrame) -> Dict:
    """Extract data from individual business unit sheets"""
    unit_data = {}
    
    if df.empty:
        return unit_data
    
    try:
        months = []
        revenue = []
        gross_income = []
        net_income = []
        
        # Extract month columns (datetime columns)
        month_columns = []
        for col in df.columns:
            if isinstance(col, pd.Timestamp) or (hasattr(col, 'year') and hasattr(col, 'month')):
                month_columns.append(col)
                # Convert to month name
                if isinstance(col, pd.Timestamp):
                    month_name = col.strftime('%b')
                else:
                    month_name = col.strftime('%b')
                months.append(month_name)
        
        print(f"DEBUG: Found {len(month_columns)} month columns: {month_columns}")
        
        # Extract revenue data
        revenue_values = []
        try:
            # Look for revenue in the second column (Unnamed: 1)
            revenue_row = df[df.iloc[:, 1].astype(str).str.contains('Revenue', na=False)]
            if not revenue_row.empty:
                for col in month_columns:
                    val = revenue_row.iloc[0][col]
                    revenue_values.append(float(val) if pd.notna(val) and val != '' else 0)
            else:
                revenue_values = [0] * len(month_columns)
        except Exception as e:
            print(f"Error extracting revenue: {e}")
            revenue_values = [0] * len(month_columns)
        
        # Extract gross income data
        gross_income_values = []
        try:
            # Look for "Gross Income" in the first column
            gross_row = df[df.iloc[:, 0].astype(str).str.contains('Gross Income', na=False)]
            if not gross_row.empty:
                for col in month_columns:
                    val = gross_row.iloc[0][col]
                    gross_income_values.append(float(val) if pd.notna(val) and val != '' else 0)
            else:
                gross_income_values = [0] * len(month_columns)
        except Exception as e:
            print(f"Error extracting gross income: {e}")
            gross_income_values = [0] * len(month_columns)
        
        # Extract net income data
        net_income_values = []
        try:
            # Look for "Net Income" in the first column
            net_row = df[df.iloc[:, 0].astype(str).str.contains('Net Income', na=False)]
            if not net_row.empty:
                for col in month_columns:
                    val = net_row.iloc[0][col]
                    net_income_values.append(float(val) if pd.notna(val) and val != '' else 0)
            else:
                net_income_values = [0] * len(month_columns)
        except Exception as e:
            print(f"Error extracting net income: {e}")
            net_income_values = [0] * len(month_columns)
        
        print(f"DEBUG: Revenue values: {revenue_values}")
        print(f"DEBUG: Gross income values: {gross_income_values}")
        print(f"DEBUG: Net income values: {net_income_values}")
        
        unit_data = {
            'months': months,
            'revenue': revenue_values,
            'gross_income': gross_income_values,
            'net_income': net_income_values
        }
        
    except Exception as e:
        print(f"Error extracting business unit data: {e}")
    
    return unit_data

def extract_pnl_data(df: pd.DataFrame) -> Dict:
    """Extract P&L data from Techgene/Vensiti P&L sheets"""
    pnl_data = {}
    
    if df.empty:
        return pnl_data
    
    try:
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug']
        
        # Extract key P&L metrics
        total_income = []
        total_expense = []
        net_income = []
        
        for month in months:
            month_col = f"{month} 25"
            if month_col in df.columns:
                try:
                    # Total Income
                    try:
                        income_row = df[df.iloc[:, 3].astype(str).str.contains('Total Income', na=False)]
                    except Exception as e:
                        print(f"Error in total income extraction: {e}")
                        income_row = pd.DataFrame()
                    if not income_row.empty:
                        try:
                            val = income_row.iloc[0][month_col]
                            total_income.append(float(val) if pd.notna(val) else 0)
                        except (KeyError, TypeError):
                            total_income.append(0)
                    else:
                        total_income.append(0)
                    
                    # Total Expense
                    try:
                        expense_row = df[df.iloc[:, 3].astype(str).str.contains('Total Expense', na=False)]
                    except Exception as e:
                        print(f"Error in total expense extraction: {e}")
                        expense_row = pd.DataFrame()
                    if not expense_row.empty:
                        try:
                            val = expense_row.iloc[0][month_col]
                            total_expense.append(float(val) if pd.notna(val) else 0)
                        except (KeyError, TypeError):
                            total_expense.append(0)
                    else:
                        total_expense.append(0)
                    
                    # Net Income
                    try:
                        net_row = df[df.iloc[:, 0].astype(str).str.contains('Net Income', na=False)]
                    except Exception as e:
                        print(f"Error in net income extraction (PnL): {e}")
                        net_row = pd.DataFrame()
                    if not net_row.empty:
                        try:
                            val = net_row.iloc[0][month_col]
                            net_income.append(float(val) if pd.notna(val) else 0)
                        except (KeyError, TypeError):
                            net_income.append(0)
                    else:
                        net_income.append(0)
                        
                except (ValueError, TypeError, KeyError):
                    total_income.append(0)
                    total_expense.append(0)
                    net_income.append(0)
            else:
                total_income.append(0)
                total_expense.append(0)
                net_income.append(0)
        
        pnl_data = {
            'months': months,
            'total_income': total_income,
            'total_expense': total_expense,
            'net_income': net_income
        }
        
    except Exception as e:
        print(f"Error extracting P&L data: {e}")
    
    return pnl_data

def create_finance_revenue_chart(df: pd.DataFrame) -> Dict:
    """Create financial revenue chart from finance data"""
    if df.empty:
        return {
            'type': 'line',
            'data': {'labels': [], 'datasets': []},
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {'legend': {'position': 'bottom'}},
                'scales': {
                    'x': {'title': {'display': True, 'text': 'Month'}},
                    'y': {'title': {'display': True, 'text': 'Amount ($)'}}
                }
            }
        }
    
    # Extract months and data
    months = []
    revenue = []
    expenses = []
    gross_income = []
    overheads = []
    net_income = []
    
    # Parse the data from the DataFrame
    for col in df.columns:
        if 'Jan-' in str(col) or 'Feb-' in str(col) or 'Mar-' in str(col) or 'Apr-' in str(col) or 'May-' in str(col):
            month_name = str(col).split('-')[0]
            months.append(month_name)
            
            # Find the values for each metric
            try:
                # Revenue (row with 'Direct Hire Revenue')
                try:
                    revenue_row = df[df.iloc[:, 1].astype(str).str.contains('Direct Hire Revenue', na=False)]
                    if not revenue_row.empty:
                        val = revenue_row.iloc[0][col]
                        revenue.append(float(val) if pd.notna(val) and val != '' else 0)
                    else:
                        revenue.append(0)
                except Exception:
                    revenue.append(0)
                
                # Expenses (row with 'Direct Hire expenses')
                try:
                    expense_row = df[df.iloc[:, 1].astype(str).str.contains('Direct Hire expenses', na=False)]
                    if not expense_row.empty:
                        val = expense_row.iloc[0][col]
                        expenses.append(float(val) if pd.notna(val) and val != '' else 0)
                    else:
                        expenses.append(0)
                except Exception:
                    expenses.append(0)
                
                # Gross Income (row with 'Gross Income')
                try:
                    gross_row = df[df.iloc[:, 1].astype(str).str.contains('Gross Income', na=False)]
                    if not gross_row.empty:
                        val = gross_row.iloc[0][col]
                        gross_income.append(float(val) if pd.notna(val) and val != '' else 0)
                    else:
                        gross_income.append(0)
                except Exception:
                    gross_income.append(0)
                
                # Overheads (row with 'Office Overheads')
                try:
                    overhead_row = df[df.iloc[:, 1].astype(str).str.contains('Office Overheads', na=False)]
                    if not overhead_row.empty:
                        val = overhead_row.iloc[0][col]
                        overheads.append(float(val) if pd.notna(val) and val != '' else 0)
                    else:
                        overheads.append(0)
                except Exception:
                    overheads.append(0)
                
                # Net Income (row with 'Net Income')
                try:
                    net_row = df[df.iloc[:, 1].astype(str).str.contains('Net Income', na=False)]
                    if not net_row.empty:
                        val = net_row.iloc[0][col]
                        net_income.append(float(val) if pd.notna(val) and val != '' else 0)
                    else:
                        net_income.append(0)
                except Exception:
                    net_income.append(0)
                    
            except (ValueError, TypeError, KeyError):
                revenue.append(0)
                expenses.append(0)
                gross_income.append(0)
                overheads.append(0)
                net_income.append(0)
    
    return {
        'type': 'line',
        'data': {
            'labels': months,
            'datasets': [
                {
                    'label': 'Direct Hire Revenue',
                    'data': revenue,
                    'borderColor': '#28a745',
                    'backgroundColor': '#28a74533',
                    'borderWidth': 3,
                    'fill': False
                },
                {
                    'label': 'Direct Hire Expenses',
                    'data': expenses,
                    'borderColor': '#dc3545',
                    'backgroundColor': '#dc354533',
                    'borderWidth': 3,
                    'fill': False
                },
                {
                    'label': 'Gross Income',
                    'data': gross_income,
                    'borderColor': '#007bff',
                    'backgroundColor': '#007bff33',
                    'borderWidth': 3,
                    'fill': False
                }
            ]
        },
        'options': {
            'responsive': True,
            'maintainAspectRatio': False,
            'plugins': {
                'legend': {
                    'position': 'bottom'
                }
            },
            'scales': {
                'x': {
                    'title': {
                        'display': True,
                        'text': 'Month'
                    }
                },
                'y': {
                    'title': {
                        'display': True,
                        'text': 'Amount ($)'
                    }
                }
            }
        }
    }

def create_finance_profit_chart(df: pd.DataFrame) -> Dict:
    """Create financial profit/loss chart"""
    if df.empty:
        return {
            'type': 'line',
            'data': {'labels': [], 'datasets': []},
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {'legend': {'position': 'bottom'}},
                'scales': {
                    'x': {'title': {'display': True, 'text': 'Month'}},
                    'y': {'title': {'display': True, 'text': 'Amount ($)'}}
                }
            }
        }
    
    # Extract months and net income data
    months = []
    net_income = []
    
    for col in df.columns:
        if 'Jan-' in str(col) or 'Feb-' in str(col) or 'Mar-' in str(col) or 'Apr-' in str(col) or 'May-' in str(col):
            month_name = str(col).split('-')[0]
            months.append(month_name)
            
            try:
                try:
                    net_row = df[df.iloc[:, 1].astype(str).str.contains('Net Income', na=False)]
                    if not net_row.empty:
                        val = net_row.iloc[0][col]
                        net_income.append(float(val) if pd.notna(val) and val != '' else 0)
                    else:
                        net_income.append(0)
                except Exception:
                    net_income.append(0)
            except (ValueError, TypeError, KeyError):
                net_income.append(0)
    
    # Color bars based on positive/negative values
    colors = ['#28a745' if val >= 0 else '#dc3545' for val in net_income]
    
    return {
        'type': 'bar',
        'data': {
            'labels': months,
            'datasets': [
                {
                    'label': 'Net Income',
                    'data': net_income,
                    'backgroundColor': colors,
                    'borderColor': colors,
                    'borderWidth': 1
                }
            ]
        },
        'options': {
            'responsive': True,
            'maintainAspectRatio': False,
            'plugins': {
                'legend': {
                    'position': 'bottom'
                }
            },
            'scales': {
                'x': {
                    'title': {
                        'display': True,
                        'text': 'Month'
                    }
                },
                'y': {
                    'title': {
                        'display': True,
                        'text': 'Net Income ($)'
                    }
                }
            }
        }
    }

def create_it_staffing_chart() -> Dict:
    """Create IT Staffing Revenue chart data for Chart.js"""
    months = ['Jan-25', 'Mar-25', 'May-25', 'Jul-25']
    
    # Sample data based on image description
    revenue = [350000, 325000, 325000, 375000]
    gross_income = [50000, -50000, -50000, 75000]
    net_income = [0, -75000, -75000, 50000]
    
    return {
        'type': 'line',
        'data': {
            'labels': months,
            'datasets': [
                {
                    'label': 'IT Staffing Revenue',
                    'data': revenue,
                    'borderColor': '#1f77b4',
                    'backgroundColor': '#1f77b433',
                    'borderWidth': 3,
                    'fill': False
                },
                {
                    'label': 'IT Staffing Gross Income',
                    'data': gross_income,
                    'borderColor': '#ff7f0e',
                    'backgroundColor': '#ff7f0e33',
                    'borderWidth': 3,
                    'fill': False
                },
                {
                    'label': 'IT Staffing Net Income',
                    'data': net_income,
                    'borderColor': '#2ca02c',
                    'backgroundColor': '#2ca02c33',
                    'borderWidth': 3,
                    'fill': False
                }
            ]
        },
        'options': {
            'responsive': True,
            'maintainAspectRatio': False,
            'plugins': {
                'legend': {
                    'position': 'bottom'
                }
            },
            'scales': {
                'x': {
                    'title': {
                        'display': True,
                        'text': 'Month'
                    }
                },
                'y': {
                    'title': {
                        'display': True,
                        'text': 'Amount'
                    }
                }
            }
        }
    }

# New chart functions for placement report processing

def create_employment_types_chart_from_sheets(sheet1_data: Dict) -> Dict:
    """Create employment types chart data for Chart.js"""
    print(f"DEBUG: sheet1_data = {sheet1_data}")  # Debug print
    
    if not sheet1_data or not sheet1_data.get('tg_data'):
        return {
            'type': 'line',
            'data': {
                'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug'],
                'datasets': []
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'legend': {
                        'position': 'bottom'
                    }
                },
                'scales': {
                    'x': {
                        'title': {
                            'display': True,
                            'text': 'Month'
                        }
                    },
                    'y': {
                        'title': {
                            'display': True,
                            'text': 'Count'
                        },
                        'beginAtZero': True
                    }
                }
            }
        }
    
    months = sheet1_data.get('months', ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug'])
    
    # Colors for different employment types
    colors = {
        'TG W2': '#1f77b4',
        'TG C2C': '#ff7f0e',
        'TG 1099': '#2ca02c',
        'TG Referral': '#17becf',
        'VNST W2': '#9467bd',
        'VNST SC': '#8c564b'
    }
    
    datasets = []
    
    # Add TG data
    for emp_type, values in sheet1_data['tg_data'].items():
        if values and emp_type in ['TG W2', 'TG C2C', 'TG 1099', 'TG Referral']:
            datasets.append({
                'label': emp_type,
                'data': values[:len(months)],  # Only use data for available months
                'backgroundColor': colors.get(emp_type, '#d62728'),
                'borderColor': colors.get(emp_type, '#d62728'),
                'borderWidth': 1
            })
    
    # Add VNST data
    if 'vnst_data' in sheet1_data:
        for emp_type, values in sheet1_data['vnst_data'].items():
            if values and emp_type in ['VNST W2', 'VNST SC']:
                datasets.append({
                    'label': emp_type,
                    'data': values[:len(months)],  # Only use data for available months
                    'backgroundColor': colors.get(emp_type, '#d62728'),
                    'borderColor': colors.get(emp_type, '#d62728'),
                    'borderWidth': 1
                })
    
    return {
        'type': 'bar',
        'data': {
            'labels': months,
            'datasets': datasets
        },
        'options': {
            'responsive': True,
            'maintainAspectRatio': False,
            'plugins': {
                'legend': {
                    'position': 'bottom'
                }
            },
            'scales': {
                'x': {
                    'title': {
                        'display': True,
                        'text': 'Month'
                    }
                },
                'y': {
                    'title': {
                        'display': True,
                        'text': 'Count'
                    },
                    'beginAtZero': True
                }
            }
        }
    }

def create_placement_metrics_chart_from_sheets(sheet2_data: Dict) -> Dict:
    """Create placement metrics chart data for Chart.js"""
    print(f"DEBUG: sheet2_data = {sheet2_data}")  # Debug print
    
    if not sheet2_data or not sheet2_data.get('placement_metrics'):
        return {
            'type': 'line',
            'data': {
                'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug'],
                'datasets': []
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'legend': {
                        'position': 'bottom'
                    }
                },
                'scales': {
                    'x': {
                        'title': {
                            'display': True,
                            'text': 'Month'
                        }
                    },
                    'y': {
                        'title': {
                            'display': True,
                            'text': 'Count'
                        },
                        'beginAtZero': True
                    }
                }
            }
        }
    
    months = sheet2_data.get('months', ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug'])
    
    # Colors for different metrics
    colors = {
        'New Placements': '#1f77b4',
        'Terminations': '#ff7f0e',
        'Net Placements': '#2ca02c',
        'Net billables': '#17becf'
    }
    
    datasets = []
    
    # Add placement metrics
    for metric, values in sheet2_data['placement_metrics'].items():
        if values and metric in ['New Placements', 'Terminations', 'Net Placements', 'Net billables']:
            datasets.append({
                'label': metric,
                'data': values[:len(months)],  # Only use data for available months
                'backgroundColor': colors.get(metric, '#d62728'),
                'borderColor': colors.get(metric, '#d62728'),
                'borderWidth': 1
            })
    
    return {
        'type': 'bar',
        'data': {
            'labels': months,
            'datasets': datasets
        },
        'options': {
            'responsive': True,
            'maintainAspectRatio': False,
            'plugins': {
                'legend': {
                    'position': 'bottom'
                }
            },
            'scales': {
                'x': {
                    'title': {
                        'display': True,
                        'text': 'Month'
                    }
                },
                'y': {
                    'title': {
                        'display': True,
                        'text': 'Count'
                    },
                    'beginAtZero': True
                }
            }
        }
    }

def create_gross_margin_chart_from_sheets(sheet3_data: Dict) -> Dict:
    """Create gross margin chart data for Chart.js"""
    if not sheet3_data or not sheet3_data.get('margin_data'):
        return {
            'type': 'line',
            'data': {
                'labels': [],
                'datasets': []
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'legend': {
                        'position': 'bottom'
                    }
                },
                'scales': {
                    'x': {
                        'title': {
                            'display': True,
                            'text': 'Company Type'
                        }
                    },
                    'y': {
                        'title': {
                            'display': True,
                            'text': 'Margin'
                        },
                        'beginAtZero': True
                    }
                }
            }
        }
    
    companies = list(sheet3_data['margin_data'].keys())
    values_2024 = [sheet3_data['margin_data'][comp]['year_2024'] for comp in companies]
    values_2025 = [sheet3_data['margin_data'][comp]['year_2025'] for comp in companies]
    total_values = [sheet3_data['margin_data'][comp]['total'] for comp in companies]
    
    return {
        'type': 'bar',
        'data': {
            'labels': companies,
            'datasets': [
                {
                    'label': '2024',
                    'data': values_2024,
                    'backgroundColor': '#1f77b4',
                    'borderColor': '#1f77b4',
                    'borderWidth': 1
                },
                {
                    'label': '2025',
                    'data': values_2025,
                    'backgroundColor': '#ff7f0e',
                    'borderColor': '#ff7f0e',
                    'borderWidth': 1
                },
                {
                    'label': 'Total',
                    'data': total_values,
                    'backgroundColor': '#2ca02c',
                    'borderColor': '#2ca02c',
                    'borderWidth': 1
                }
            ]
        },
        'options': {
            'responsive': True,
            'maintainAspectRatio': False,
            'plugins': {
                'legend': {
                    'position': 'bottom'
                }
            },
            'scales': {
                'x': {
                    'title': {
                        'display': True,
                        'text': 'Company Type'
                    }
                },
                'y': {
                    'title': {
                        'display': True,
                        'text': 'Margin'
                    },
                    'beginAtZero': True
                }
            }
        }
    }

def create_billables_trend_chart(sheet2_data: Dict) -> Dict:
    """Create billables trend chart data for Chart.js"""
    if not sheet2_data or not sheet2_data.get('billables_data'):
        return {
            'type': 'line',
            'data': {
                'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug'],
                'datasets': []
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'legend': {
                        'position': 'bottom'
                    }
                },
                'scales': {
                    'x': {
                        'title': {
                            'display': True,
                            'text': 'Month'
                        }
                    },
                    'y': {
                        'title': {
                            'display': True,
                            'text': 'Count'
                        },
                        'beginAtZero': True
                    }
                }
            }
        }
    
    months = sheet2_data.get('months', ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug'])
    
    # Colors for different billable types
    colors = {
        'W2': '#1f77b4',
        'C2C': '#ff7f0e',
        '1099': '#2ca02c',
        'Referral': '#17becf',
        'Total billables': '#9467bd'
    }
    
    datasets = []
    
    # Add billable types
    for billable_type, values in sheet2_data['billables_data'].items():
        if values:
            datasets.append({
                'label': billable_type,
                'data': values[:len(months)],  # Only use data for available months
                'borderColor': colors.get(billable_type, '#d62728'),
                'backgroundColor': colors.get(billable_type, '#d62728') + '33',  # Add transparency
                'borderWidth': 3,
                'fill': False
            })
    
    return {
        'type': 'line',
        'data': {
            'labels': months,
            'datasets': datasets
        },
        'options': {
            'responsive': True,
            'maintainAspectRatio': False,
            'plugins': {
                'legend': {
                    'position': 'bottom'
                }
            },
            'scales': {
                'x': {
                    'title': {
                        'display': True,
                        'text': 'Month'
                    }
                },
                'y': {
                    'title': {
                        'display': True,
                        'text': 'Count'
                    },
                    'beginAtZero': True
                }
            }
        }
    }

def create_company_comparison_chart(sheet1_data: Dict, sheet3_data: Dict) -> go.Figure:
    """Create company comparison chart combining employment and margin data"""
    if not sheet1_data or not sheet3_data:
        return go.Figure()
    
    fig = go.Figure()
    
    # Get current month data (August - index 7)
    tg_w2_current = sheet1_data.get('tg_data', {}).get('TG W2', [0] * 8)[7] if sheet1_data.get('tg_data', {}).get('TG W2') else 0
    vnst_w2_current = sheet1_data.get('vnst_data', {}).get('VNST W2', [0] * 8)[7] if sheet1_data.get('vnst_data', {}).get('VNST W2') else 0
    
    # Get margin totals
    tg_margin_total = 0
    vnst_margin_total = 0
    
    for company, margin_data in sheet3_data.get('margin_data', {}).items():
        if 'TG' in company:
            tg_margin_total += margin_data.get('total', 0)
        elif 'VNST' in company:
            vnst_margin_total += margin_data.get('total', 0)
    
    companies = ['Techgene', 'VNST']
    employment_values = [tg_w2_current, vnst_w2_current]
    margin_values = [tg_margin_total, vnst_margin_total]
    
    # Create subplot with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add employment bars
    fig.add_trace(
        go.Bar(name='Current W2 Placements', x=companies, y=employment_values, marker_color='#1f77b4', opacity=0.8),
        secondary_y=False
    )
    
    # Add margin line
    fig.add_trace(
        go.Scatter(name='Total Margin', x=companies, y=margin_values, mode='lines+markers', 
                  line=dict(color='#ff7f0e', width=3), marker=dict(size=10)),
        secondary_y=True
    )
    
    fig.update_layout(
        title=None,  # Remove title from chart itself
        xaxis=dict(title='Company', autorange=True),
        height=380,
        margin=dict(l=25, r=30, t=5, b=40),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.05,
            xanchor="center",
            x=0.5,
            font=dict(size=10)
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        autosize=True  # Enable auto-sizing to fit containers properly
    )
    
    fig.update_yaxes(title_text="W2 Placements", secondary_y=False)
    fig.update_yaxes(title_text="Total Margin", secondary_y=True)
    
    return fig

def calculate_placement_kpis(sheet1_data: Dict, sheet2_data: Dict, sheet3_data: Dict) -> Dict:
    """Calculate KPIs from placement report data"""
    kpis = {}
    
    try:
        # Total Current Billables (from latest month - August)
        if sheet2_data and 'billables_data' in sheet2_data:
            total_billables = sheet2_data['billables_data'].get('Total billables', [0] * 8)
            if total_billables:
                kpis['Total Current Billables'] = f"{total_billables[7]:.0f}"  # August
        
        # W2 Placements (current)
        if sheet1_data:
            tg_w2 = sheet1_data.get('tg_data', {}).get('TG W2', [0] * 8)
            vnst_w2 = sheet1_data.get('vnst_data', {}).get('VNST W2', [0] * 8)
            total_w2 = (tg_w2[7] if tg_w2 else 0) + (vnst_w2[7] if vnst_w2 else 0)
            kpis['W2 Placements'] = f"{total_w2:.0f}"
        
        # C2C Placements (current)
        if sheet1_data:
            tg_c2c = sheet1_data.get('tg_data', {}).get('TG C2C', [0] * 8)
            vnst_c2c = sheet1_data.get('vnst_data', {}).get('VNST C2C', [0] * 8)
            total_c2c = (tg_c2c[7] if tg_c2c else 0) + (vnst_c2c[7] if vnst_c2c else 0)
            kpis['C2C Placements'] = f"{total_c2c:.0f}"
        
        # Net Placements (latest month)
        if sheet2_data and 'placement_metrics' in sheet2_data:
            net_placements = sheet2_data['placement_metrics'].get('Net Placements', [0] * 8)
            if net_placements:
                kpis['Net Placements (Latest Month)'] = f"{net_placements[7]:.0f}"  # August
        
        # Total Placements (sum of all months)
        if sheet2_data and 'placement_metrics' in sheet2_data:
            new_placements = sheet2_data['placement_metrics'].get('New Placements', [0] * 8)
            if new_placements:
                total_placements = sum(new_placements)
                kpis['Total Placements'] = f"{total_placements:.0f}"
        
        # Total Terminations (sum of all months)
        if sheet2_data and 'placement_metrics' in sheet2_data:
            terminations = sheet2_data['placement_metrics'].get('Terminations', [0] * 8)
            if terminations:
                total_terminations = sum(terminations)
                kpis['Total Terminations'] = f"{total_terminations:.0f}"
        
        # Gross Margin Total
        if sheet3_data and 'margin_data' in sheet3_data:
            total_margin = sum(margin_data.get('total', 0) for margin_data in sheet3_data['margin_data'].values())
            kpis['Gross Margin Total'] = f"${total_margin:.2f}"
        
    except Exception as e:
        print(f"Error calculating KPIs: {e}")
    
    return kpis

# --------------------- Routes ---------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        print("DEBUG Upload - Starting upload process")
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'})
        
        file = request.files['file']
        file_type = request.form.get('type')
        print(f"DEBUG Upload - File type: {file_type}")
        
        if file.filename == '':
            return jsonify({'error': 'No selected file'})
        
        if file:
            print(f"DEBUG Upload - Original filename: {file.filename}")
            # Create a simple filename without using secure_filename
            import time
            timestamp = int(time.time())
            filename = f"{file_type}_file_{timestamp}.xlsx"
            print(f"DEBUG Upload - Generated filename: {filename}")
            
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            print(f"DEBUG Upload - File path: {file_path}")
            
            try:
                # Save file to memory first
                file_content = file.read()
                print(f"DEBUG Upload - File read into memory, size: {len(file_content)} bytes")
                
                # Write to file
                with open(file_path, 'wb') as f:
                    f.write(file_content)
                print(f"DEBUG Upload - File saved successfully")
            except Exception as e:
                print(f"DEBUG Upload - Error saving file: {e}")
                raise e
        
            try:
                # Special handling for finance Excel files
                if file_type == 'finance' and file_path.lower().endswith(('.xlsx', '.xls')):
                    print(f"=== UPLOAD ROUTE: Processing finance file {filename} ===")
                    print(f"Session keys before storing: {list(session.keys())}")
                    # Store file path in session for finance processing
                    session[f'{file_type}_file'] = file_path
                    print(f"Session keys after storing: {list(session.keys())}")
                    print(f"Stored file path: {session[f'{file_type}_file']}")
                    
                    return jsonify({
                        'success': True,
                        'file_type': 'finance_excel',
                        'file_path': file_path,
                        'message': f'Successfully uploaded finance Excel file: {filename}'
                    })
                # Special handling for recruitment placement reports
                elif file_type == 'rec' and file_path.lower().endswith(('.xlsx', '.xls')):
                    # Process the Excel file with all 4 sheets
                    excel_data = read_placement_report_excel(file_path)
                    
                    if not excel_data.get('success', True):
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        return jsonify({'error': f'Error reading Excel file: {excel_data.get("error", "Unknown error")}'})
                    
                    # Store file path in session
                    session[f'{file_type}_file'] = file_path
                    
                    return jsonify({
                        'success': True,
                        'file_type': 'excel_placement_report',
                        'sheet_names': excel_data.get('sheet_names', []),
                        'sheet_count': len(excel_data.get('sheet_names', [])),
                        'file_path': file_path,
                        'message': f'Successfully uploaded Excel file with {len(excel_data.get("sheet_names", []))} sheets'
                    })
                else:
                    # Regular CSV/Excel processing
                    df = read_csv_file(file_path)
                    
                    if df.empty:
                        return jsonify({'error': 'File is empty or could not be read'})
                    
                    df = try_parse_dates(df)
                    
                    # Store file path in session
                    session[f'{file_type}_file'] = file_path
                    
                    return jsonify({
                        'success': True,
                        'columns': list(df.columns),
                        'preview': df.head(10).to_dict('records'),
                        'file_path': file_path
                    })
                
            except Exception as e:
                # Clean up the uploaded file if there was an error
                if os.path.exists(file_path):
                    os.remove(file_path)
                return jsonify({'error': f'Error processing file: {str(e)}'})
    
    except Exception as e:
        print(f"DEBUG Upload - Outer exception: {e}")
        return jsonify({'error': f'Error processing file: {str(e)}'})

@app.route('/process_placement_report', methods=['POST'])
def process_placement_report_route():
    """Process placement report Excel file and generate analytics"""
    if 'rec_file' not in session:
        return jsonify({'error': 'No placement report file uploaded'})
    
    file_path = session['rec_file']
    
    try:
        # Read all sheets from the Excel file
        excel_data = read_placement_report_excel(file_path)
        
        if not excel_data.get('success', True):
            return jsonify({'error': f'Error reading Excel file: {excel_data.get("error", "Unknown error")}'})
        
        # Process each sheet
        sheet1_data = process_sheet1_employment(excel_data['sheet1_employment'])
        sheet2_data = process_sheet2_placements(excel_data['sheet2_placements'])
        sheet3_data = process_sheet3_margins(excel_data['sheet3_margins'])
        
        # Generate charts
        charts = {}
        
        # Employment types chart from Sheet 1
        if sheet1_data:
            employment_chart = create_employment_types_chart_from_sheets(sheet1_data)
            if employment_chart:
                charts['employment_types'] = employment_chart
        
        # Placement metrics chart from Sheet 2
        if sheet2_data:
            placement_chart = create_placement_metrics_chart_from_sheets(sheet2_data)
            if placement_chart:
                charts['placement_metrics'] = placement_chart
        
        # Gross margin chart from Sheet 3
        if sheet3_data:
            margin_chart = create_gross_margin_chart_from_sheets(sheet3_data)
            if margin_chart:
                charts['gross_margin'] = margin_chart
        
        # Additional charts
        if sheet2_data:
            billables_chart = create_billables_trend_chart(sheet2_data)
            if billables_chart:
                charts['billables_trend'] = billables_chart
        
        # Add financial charts (always include these)
        direct_hire_chart = create_direct_hire_chart()
        if direct_hire_chart:
            charts['direct_hire'] = direct_hire_chart
        
        services_chart = create_services_chart()
        if services_chart:
            charts['services'] = services_chart
        
        it_staffing_chart = create_it_staffing_chart()
        if it_staffing_chart:
            charts['it_staffing'] = it_staffing_chart
        
        # Calculate KPIs
        kpis = calculate_placement_kpis(sheet1_data, sheet2_data, sheet3_data)
        
        # Store processed data in session for persistence
        session.permanent = True
        session['processed_data'] = {
            'charts': charts,
            'kpis': kpis,
            'sheet1_data': sheet1_data,
            'sheet2_data': sheet2_data,
            'sheet3_data': sheet3_data,
            'processing_status': {
                'sheet1_processed': bool(sheet1_data),
                'sheet2_processed': bool(sheet2_data),
                'sheet3_processed': bool(sheet3_data),
                'sheet4_processed': not excel_data['sheet4_additional'].empty if 'sheet4_additional' in excel_data else False
            }
        }
        
        return jsonify({
            'success': True,
            'charts': charts,
            'kpis': kpis,
            'processing_status': {
                'sheet1_processed': bool(sheet1_data),
                'sheet2_processed': bool(sheet2_data),
                'sheet3_processed': bool(sheet3_data),
                'sheet4_processed': not excel_data['sheet4_additional'].empty if 'sheet4_additional' in excel_data else False
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Error processing placement report: {str(e)}'})

@app.route('/test_session')
def test_session():
    """Test session persistence"""
    if 'test_counter' not in session:
        session['test_counter'] = 0
    session['test_counter'] += 1
    session.permanent = True
    
    return jsonify({
        'test_counter': session['test_counter'],
        'session_keys': list(session.keys()),
        'session_permanent': session.permanent
    })

@app.route('/set_finance_file')
def set_finance_file():
    """Manually set finance file for testing"""
    session['finance_file'] = 'uploads/finance_Monthly_income_and_expenses.xlsx'
    session.permanent = True
    return jsonify({'success': True, 'file': session['finance_file']})

@app.route('/debug_finance_data')
def debug_finance_data():
    """Debug route to check financial data structure"""
    try:
        file_path = 'uploads/finance_Monthly_income_and_expenses.xlsx'
        excel_data = read_finance_excel_file(file_path)
        
        if excel_data.get('success'):
            processed_data = process_finance_data(excel_data)
            summary_metrics = processed_data.get('summary_metrics', {})
            
            # Return the actual metric names and first few values
            debug_info = {}
            for metric_name, metric_data in summary_metrics.items():
                if isinstance(metric_data, dict) and 'monthly_values' in metric_data:
                    debug_info[metric_name] = {
                        'monthly_values': metric_data['monthly_values'][:3],  # First 3 values
                        'total': metric_data.get('total', 0)
                    }
            
            return jsonify({
                'success': True,
                'summary_metrics_count': len(summary_metrics),
                'metric_names': list(summary_metrics.keys()),
                'sample_data': debug_info
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to read Excel file'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/check_existing_data')
def check_existing_data():
    """Check if there's existing processed data in session"""
    print("=== CHECKING EXISTING DATA ===")
    print(f"Session keys: {list(session.keys())}")
    print(f"Session permanent: {session.permanent}")
    print(f"Session ID: {session.get('_id', 'No ID')}")
    
    has_recruitment_data = 'processed_data' in session
    has_finance_data = 'finance_processed_data' in session
    
    print(f"Has recruitment data: {has_recruitment_data}")
    print(f"Has finance data: {has_finance_data}")
    
    if has_recruitment_data:
        print(f"Recruitment data keys: {list(session['processed_data'].keys())}")
    if has_finance_data:
        print(f"Finance data keys: {list(session['finance_processed_data'].keys())}")
    
    if has_recruitment_data or has_finance_data:
        result = {
            'has_data': True,
            'has_recruitment_data': has_recruitment_data,
            'has_finance_data': has_finance_data
        }
        
        if has_recruitment_data:
            result['recruitment_data'] = session['processed_data']
        
        if has_finance_data:
            result['finance_data'] = session['finance_processed_data']
            
        print("Returning data found")
        return jsonify(result)
    else:
        print("No data found")
        return jsonify({
            'has_data': False
        })

@app.route('/process_finance_report', methods=['POST'])
def process_finance_report():
    """Process finance Excel file and generate analytics"""
    try:
        print("=== FINANCE REPORT PROCESSING START ===")
        
        # Get the file path from session (file was uploaded via /upload route)
        print(f"Session keys in process_finance_report: {list(session.keys())}")
        if 'finance_file' not in session:
            print("No finance file in session, using default file for testing")
            file_path = 'uploads/finance_Monthly_income_and_expenses.xlsx'
        else:
            file_path = session['finance_file']
        
        print(f"Processing file: {file_path}")
        
        if not os.path.exists(file_path):
            print(f"ERROR: File does not exist: {file_path}")
            return jsonify({'success': False, 'error': 'File not found'})
        
        print("=== READING EXCEL FILE ===")
        # Read all sheets from Excel file
        excel_data = read_finance_excel_file(file_path)
        print(f"Excel data success: {excel_data.get('success')}")
        print(f"Sheet names: {excel_data.get('sheet_names', [])}")
        
        if not excel_data.get('success'):
            error_msg = excel_data.get('error', 'Error reading Excel file')
            print(f"Excel read error: {error_msg}")
            return jsonify({'success': False, 'error': error_msg})
        
        print("=== EXTRACTING SPECIFIC FINANCIAL VALUES ===")
        # Extract the 9 specific financial values
        specific_values = extract_specific_financial_values(excel_data)
        print(f"Specific values extracted: {specific_values}")
        
        print("=== PROCESSING FINANCE DATA ===")
        # Process all finance data
        processed_data = process_finance_data(excel_data)
        print(f"Processed data keys: {list(processed_data.keys())}")
        
        print("=== CREATING CHARTS ===")
        # Generate comprehensive charts
        charts = create_comprehensive_finance_charts(processed_data)
        print(f"Charts created: {list(charts.keys())}")
        
        print("=== CALCULATING KPIS ===")
        # Calculate comprehensive KPIs
        kpis = calculate_comprehensive_finance_kpis(processed_data)
        print(f"KPIs calculated: {list(kpis.keys())}")
        
        print("=== STORING IN SESSION ===")
        # Store processed data in session (without DataFrames)
        session.permanent = True
        filename = os.path.basename(file_path)
        session['finance_processed_data'] = {
            'kpis': kpis,
            'charts': charts,
            'filename': filename,
            'sheet_names': excel_data.get('sheet_names', []),
            'processed_data': processed_data,
            'specific_values': specific_values
        }
        print("Session data stored successfully")
        
        print("=== FINANCE REPORT PROCESSING SUCCESS ===")
        return jsonify({
            'success': True,
            'kpis': kpis,
            'charts': charts,
            'sheet_count': len(excel_data.get('sheet_names', [])),
            'processed_data': processed_data,
            'specific_values': specific_values
        })
            
    except Exception as e:
        import traceback
        print(f"=== CRITICAL ERROR IN FINANCE PROCESSING ===")
        print(f"Error: {e}")
        print(f"Error type: {type(e)}")
        print("Full traceback:")
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Error processing file: {str(e)}'})

def create_comprehensive_finance_charts(processed_data: Dict) -> Dict:
    """Create comprehensive finance charts from processed data"""
    charts = {}
    
    try:
        # Create the three main financial charts using financial data
        charts['direct_hire_finance'] = create_direct_hire_finance_chart(processed_data)
        charts['services_finance'] = create_services_finance_chart(processed_data)
        charts['it_staffing_finance'] = create_it_staffing_finance_chart(processed_data)
        
    except Exception as e:
        print(f"Error creating comprehensive finance charts: {e}")
        # Return empty charts if there's an error
        charts = {
            'direct_hire_finance': {'type': 'bar', 'data': {'labels': [], 'datasets': []}},
            'services_finance': {'type': 'bar', 'data': {'labels': [], 'datasets': []}},
            'it_staffing_finance': {'type': 'bar', 'data': {'labels': [], 'datasets': []}}
        }
    
    return charts

def create_direct_hire_finance_chart(processed_data: Dict) -> Dict:
    """Create Direct Hire Revenue, Gross Income, Net Income chart using financial data"""
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug']
    
    try:
        # Extract Direct Hire data from summary metrics
        summary_metrics = processed_data.get('summary_metrics', {})
        print(f"DEBUG Direct Hire Chart - Summary metrics keys: {list(summary_metrics.keys())}")
        
        # Initialize data arrays
        revenue_data = [0] * 8
        gross_income_data = [0] * 8
        net_income_data = [0] * 8
        
        # Extract Direct Hire metrics
        for metric_name, metric_data in summary_metrics.items():
            print(f"DEBUG Direct Hire Chart - Processing metric: '{metric_name}'")
            print(f"DEBUG Direct Hire Chart - Metric data type: {type(metric_data)}")
            if isinstance(metric_data, dict) and 'monthly_values' in metric_data:
                monthly_values = metric_data['monthly_values']
                print(f"DEBUG Direct Hire Chart - Found monthly values: {monthly_values}")
                print(f"DEBUG Direct Hire Chart - Type of monthly_values: {type(monthly_values)}")
                if isinstance(monthly_values, list):
                    print(f"DEBUG Direct Hire Chart - Length of monthly_values: {len(monthly_values)}")
                else:
                    print(f"DEBUG Direct Hire Chart - monthly_values is not a list!")
                
                # Check exact matches
                if metric_name == 'Direct Hire Revenue':
                    revenue_data = monthly_values[:8] if len(monthly_values) >= 8 else monthly_values + [0] * (8 - len(monthly_values))
                    print(f"DEBUG Direct Hire Chart - Revenue data: {revenue_data}")
                elif metric_name == 'Direct Hire Gross Income':
                    gross_income_data = monthly_values[:8] if len(monthly_values) >= 8 else monthly_values + [0] * (8 - len(monthly_values))
                    print(f"DEBUG Direct Hire Chart - Gross income data: {gross_income_data}")
                elif metric_name == 'Direct Hire Net Income':
                    net_income_data = monthly_values[:8] if len(monthly_values) >= 8 else monthly_values + [0] * (8 - len(monthly_values))
                    print(f"DEBUG Direct Hire Chart - Net income data: {net_income_data}")
            else:
                print(f"DEBUG Direct Hire Chart - Metric data is not dict or missing monthly_values: {metric_data}")
        
        datasets = [
            {
                'label': 'Direct Hire Revenue',
                'data': revenue_data,
                'backgroundColor': 'rgba(54, 162, 235, 0.1)',
                'borderColor': 'rgba(54, 162, 235, 1)',
                'borderWidth': 3,
                'fill': False,
                'tension': 0.1
            },
            {
                'label': 'Direct Hire Gross Income',
                'data': gross_income_data,
                'backgroundColor': 'rgba(75, 192, 192, 0.1)',
                'borderColor': 'rgba(75, 192, 192, 1)',
                'borderWidth': 3,
                'fill': False,
                'tension': 0.1
            },
            {
                'label': 'Direct Hire Net Income',
                'data': net_income_data,
                'backgroundColor': 'rgba(255, 99, 132, 0.1)',
                'borderColor': 'rgba(255, 99, 132, 1)',
                'borderWidth': 3,
                'fill': False,
                'tension': 0.1
            }
        ]
        
        return {
            'type': 'line',
            'data': {
                'labels': months,
                'datasets': datasets
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'legend': {
                        'position': 'bottom'
                    }
                },
                'scales': {
                    'y': {
                        'beginAtZero': False
                    }
                },
                'elements': {
                    'line': {
                        'tension': 0.1
                    }
                }
            }
        }
        
    except Exception as e:
        print(f"Error creating Direct Hire finance chart: {e}")
        return {
            'type': 'line',
            'data': {
                'labels': months,
                'datasets': []
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False
            }
        }

def create_services_finance_chart(processed_data: Dict) -> Dict:
    """Create Services Revenue, Gross Income, Net Income chart using financial data"""
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug']
    
    try:
        # Extract Services data from summary metrics
        summary_metrics = processed_data.get('summary_metrics', {})
        
        # Initialize data arrays
        revenue_data = [0] * 8
        gross_income_data = [0] * 8
        net_income_data = [0] * 8
        
        # Extract Services metrics
        for metric_name, metric_data in summary_metrics.items():
            if isinstance(metric_data, dict) and 'monthly_values' in metric_data:
                monthly_values = metric_data['monthly_values']
                if 'Services Revenue' == metric_name:
                    revenue_data = monthly_values[:8] if len(monthly_values) >= 8 else monthly_values + [0] * (8 - len(monthly_values))
                elif 'Services Gross Income' == metric_name:
                    gross_income_data = monthly_values[:8] if len(monthly_values) >= 8 else monthly_values + [0] * (8 - len(monthly_values))
                elif 'Services Net Income' == metric_name:
                    net_income_data = monthly_values[:8] if len(monthly_values) >= 8 else monthly_values + [0] * (8 - len(monthly_values))
        
        datasets = [
            {
                'label': 'Services Revenue',
                'data': revenue_data,
                'backgroundColor': 'rgba(153, 102, 255, 0.1)',
                'borderColor': 'rgba(153, 102, 255, 1)',
                'borderWidth': 3,
                'fill': False,
                'tension': 0.1
            },
            {
                'label': 'Services Gross Income',
                'data': gross_income_data,
                'backgroundColor': 'rgba(255, 159, 64, 0.1)',
                'borderColor': 'rgba(255, 159, 64, 1)',
                'borderWidth': 3,
                'fill': False,
                'tension': 0.1
            },
            {
                'label': 'Services Net Income',
                'data': net_income_data,
                'backgroundColor': 'rgba(255, 205, 86, 0.1)',
                'borderColor': 'rgba(255, 205, 86, 1)',
                'borderWidth': 3,
                'fill': False,
                'tension': 0.1
            }
        ]
        
        return {
            'type': 'line',
            'data': {
                'labels': months,
                'datasets': datasets
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'legend': {
                        'position': 'bottom'
                    }
                },
                'scales': {
                    'y': {
                        'beginAtZero': False
                    }
                },
                'elements': {
                    'line': {
                        'tension': 0.1
                    }
                }
            }
        }
        
    except Exception as e:
        print(f"Error creating Services finance chart: {e}")
        return {
            'type': 'line',
            'data': {
                'labels': months,
                'datasets': []
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False
            }
        }

def create_it_staffing_finance_chart(processed_data: Dict) -> Dict:
    """Create IT Staffing Revenue, Gross Income, Net Income chart using financial data"""
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug']
    
    try:
        # Extract IT Staffing data from summary metrics
        summary_metrics = processed_data.get('summary_metrics', {})
        
        # Initialize data arrays
        revenue_data = [0] * 8
        gross_income_data = [0] * 8
        net_income_data = [0] * 8
        
        # Extract IT Staffing metrics
        for metric_name, metric_data in summary_metrics.items():
            if isinstance(metric_data, dict) and 'monthly_values' in metric_data:
                monthly_values = metric_data['monthly_values']
                if 'IT Staffing Revenue' == metric_name:
                    revenue_data = monthly_values[:8] if len(monthly_values) >= 8 else monthly_values + [0] * (8 - len(monthly_values))
                elif 'IT Staffing Gross Income' == metric_name:
                    gross_income_data = monthly_values[:8] if len(monthly_values) >= 8 else monthly_values + [0] * (8 - len(monthly_values))
                elif 'IT Staffing Net Income' == metric_name:
                    net_income_data = monthly_values[:8] if len(monthly_values) >= 8 else monthly_values + [0] * (8 - len(monthly_values))
        
        datasets = [
            {
                'label': 'IT Staffing Revenue',
                'data': revenue_data,
                'backgroundColor': 'rgba(201, 203, 207, 0.1)',
                'borderColor': 'rgba(201, 203, 207, 1)',
                'borderWidth': 3,
                'fill': False,
                'tension': 0.1
            },
            {
                'label': 'IT Staffing Gross Income',
                'data': gross_income_data,
                'backgroundColor': 'rgba(255, 99, 255, 0.1)',
                'borderColor': 'rgba(255, 99, 255, 1)',
                'borderWidth': 3,
                'fill': False,
                'tension': 0.1
            },
            {
                'label': 'IT Staffing Net Income',
                'data': net_income_data,
                'backgroundColor': 'rgba(54, 162, 235, 0.1)',
                'borderColor': 'rgba(54, 162, 235, 1)',
                'borderWidth': 3,
                'fill': False,
                'tension': 0.1
            }
        ]
        
        return {
            'type': 'line',
            'data': {
                'labels': months,
                'datasets': datasets
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'legend': {
                        'position': 'bottom'
                    }
                },
                'scales': {
                    'y': {
                        'beginAtZero': False
                    }
                },
                'elements': {
                    'line': {
                        'tension': 0.1
                    }
                }
            }
        }
        
    except Exception as e:
        print(f"Error creating IT Staffing finance chart: {e}")
        return {
            'type': 'line',
            'data': {
                'labels': months,
                'datasets': []
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False
            }
        }

def create_monthly_revenue_trend_chart(processed_data: Dict) -> Dict:
    """Create monthly revenue trend chart"""
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug']
    
    # Extract revenue data from summary metrics
    revenue_data = []
    if processed_data.get('summary_metrics'):
        summary = processed_data['summary_metrics']
        for month in months:
            month_key = f"{month}_2025"
            if month_key in summary:
                revenue_data.append(summary[month_key].get('total_revenue', 0))
            else:
                revenue_data.append(0)
    else:
        revenue_data = [0] * len(months)
    
    return {
        'type': 'line',
        'data': {
            'labels': months,
            'datasets': [{
                'label': 'Monthly Revenue',
                'data': revenue_data,
                'borderColor': '#007bff',
                'backgroundColor': '#007bff33',
                'fill': True,
                'tension': 0.1
            }]
        },
        'options': {
            'responsive': True,
            'maintainAspectRatio': False,
            'plugins': {
                'legend': {'position': 'bottom'},
                'title': {'display': True, 'text': 'Monthly Revenue Trend'}
            },
            'scales': {
                'x': {'title': {'display': True, 'text': 'Month'}},
                'y': {'title': {'display': True, 'text': 'Revenue ($)'}}
            }
        }
    }

def create_expense_breakdown_chart(processed_data: Dict) -> Dict:
    """Create expense breakdown chart"""
    # Extract expense categories from P&L data
    expense_categories = []
    expense_amounts = []
    
    if processed_data.get('monthly_data'):
        for company_name, company_data in processed_data['monthly_data'].items():
            if company_data.get('expense_breakdown'):
                for category, amount in company_data['expense_breakdown'].items():
                    expense_categories.append(f"{company_name} - {category}")
                    expense_amounts.append(amount)
    
    if not expense_categories:
        expense_categories = ['Direct Hire Expenses', 'Services Expenses', 'IT Staffing Expenses']
        expense_amounts = [100000, 150000, 200000]  # Sample data
    
    colors = ['#dc3545', '#fd7e14', '#ffc107', '#28a745', '#20c997', '#6f42c1']
    
    return {
        'type': 'doughnut',
        'data': {
            'labels': expense_categories,
            'datasets': [{
                'data': expense_amounts,
                'backgroundColor': colors[:len(expense_categories)],
                'borderWidth': 2
            }]
        },
        'options': {
            'responsive': True,
            'maintainAspectRatio': False,
            'plugins': {
                'legend': {'position': 'bottom'},
                'title': {'display': True, 'text': 'Expense Breakdown by Category'}
            }
        }
    }

def create_profitability_analysis_chart(processed_data: Dict) -> Dict:
    """Create profitability analysis chart"""
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug']
    
    # Extract profitability data
    revenue_data = []
    profit_data = []
    
    if processed_data.get('summary_metrics'):
        summary = processed_data['summary_metrics']
        for month in months:
            month_key = f"{month}_2025"
            if month_key in summary:
                revenue_data.append(summary[month_key].get('total_revenue', 0))
                profit_data.append(summary[month_key].get('total_net_income', 0))
            else:
                revenue_data.append(0)
                profit_data.append(0)
    else:
        revenue_data = [0] * len(months)
        profit_data = [0] * len(months)
    
    return {
        'type': 'bar',
        'data': {
            'labels': months,
            'datasets': [
                {
                    'label': 'Revenue',
                    'data': revenue_data,
                    'backgroundColor': '#007bff',
                    'borderColor': '#007bff',
                    'borderWidth': 1
                },
                {
                    'label': 'Net Income',
                    'data': profit_data,
                    'backgroundColor': '#28a745',
                    'borderColor': '#28a745',
                    'borderWidth': 1
                }
            ]
        },
        'options': {
            'responsive': True,
            'maintainAspectRatio': False,
            'plugins': {
                'legend': {'position': 'bottom'},
                'title': {'display': True, 'text': 'Revenue vs Net Income Analysis'}
            },
            'scales': {
                'x': {'title': {'display': True, 'text': 'Month'}},
                'y': {'title': {'display': True, 'text': 'Amount ($)'}}
            }
        }
    }

def create_business_units_revenue_chart(business_units: Dict) -> Dict:
    """Create business units revenue comparison chart"""
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug']
    datasets = []
    
    colors = ['#28a745', '#007bff', '#dc3545', '#ffc107', '#6f42c1']
    
    for i, (unit_name, unit_data) in enumerate(business_units.items()):
        if unit_data.get('revenue'):
            datasets.append({
                'label': unit_name.replace(' Net income', ''),
                'data': unit_data['revenue'][:len(months)],
                'borderColor': colors[i % len(colors)],
                'backgroundColor': colors[i % len(colors)] + '33',
                'borderWidth': 3,
                'fill': False
            })
    
    return {
        'type': 'line',
        'data': {
            'labels': months,
            'datasets': datasets
        },
        'options': {
            'responsive': True,
            'maintainAspectRatio': False,
            'plugins': {
                'legend': {'position': 'bottom'},
                'title': {'display': True, 'text': 'Business Units Revenue Comparison'}
            },
            'scales': {
                'x': {'title': {'display': True, 'text': 'Month'}},
                'y': {'title': {'display': True, 'text': 'Revenue ($)'}}
            }
        }
    }

def create_monthly_pnl_trend_chart(monthly_data: Dict) -> Dict:
    """Create monthly P&L trend chart"""
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug']
    datasets = []
    
    colors = ['#28a745', '#dc3545', '#007bff']
    
    for i, (company_name, company_data) in enumerate(monthly_data.items()):
        company_short = company_name.replace(' PnL new', '')
        
        if company_data.get('net_income'):
            datasets.append({
                'label': f'{company_short} Net Income',
                'data': company_data['net_income'][:len(months)],
                'borderColor': colors[i % len(colors)],
                'backgroundColor': colors[i % len(colors)] + '33',
                'borderWidth': 3,
                'fill': False
            })
    
    return {
        'type': 'line',
        'data': {
            'labels': months,
            'datasets': datasets
        },
        'options': {
            'responsive': True,
            'maintainAspectRatio': False,
            'plugins': {
                'legend': {'position': 'bottom'},
                'title': {'display': True, 'text': 'Monthly P&L Trend'}
            },
            'scales': {
                'x': {'title': {'display': True, 'text': 'Month'}},
                'y': {'title': {'display': True, 'text': 'Net Income ($)'}}
            }
        }
    }

def create_summary_metrics_chart(summary_metrics: Dict) -> Dict:
    """Create summary metrics chart"""
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug']
    datasets = []
    
    colors = ['#28a745', '#007bff', '#dc3545', '#ffc107', '#6f42c1', '#17a2b8']
    
    for i, (metric_name, metric_data) in enumerate(summary_metrics.items()):
        if metric_data.get('monthly_values'):
            datasets.append({
                'label': metric_name,
                'data': metric_data['monthly_values'][:len(months)],
                'borderColor': colors[i % len(colors)],
                'backgroundColor': colors[i % len(colors)] + '33',
                'borderWidth': 3,
                'fill': False
            })
    
    return {
        'type': 'line',
        'data': {
            'labels': months,
            'datasets': datasets
        },
        'options': {
            'responsive': True,
            'maintainAspectRatio': False,
            'plugins': {
                'legend': {'position': 'bottom'},
                'title': {'display': True, 'text': 'Financial Summary Metrics'}
            },
            'scales': {
                'x': {'title': {'display': True, 'text': 'Month'}},
                'y': {'title': {'display': True, 'text': 'Amount ($)'}}
            }
        }
    }

def calculate_comprehensive_finance_kpis(processed_data: Dict) -> Dict:
    """Calculate comprehensive financial KPIs from processed data"""
    kpis = {}
    
    try:
        print("=== CALCULATING COMPREHENSIVE FINANCE KPIS ===")
        print(f"Processed data keys: {list(processed_data.keys())}")
        
        # Calculate totals from business units
        total_revenue = 0
        total_expenses = 0
        total_net_income = 0
        
        if processed_data.get('business_units'):
            print("Processing business units data...")
            for unit_name, unit_data in processed_data['business_units'].items():
                print(f"Unit: {unit_name}, Data keys: {list(unit_data.keys())}")
                if unit_data.get('revenue'):
                    revenue_sum = sum(unit_data['revenue'])
                    total_revenue += revenue_sum
                    print(f"Added {revenue_sum} revenue from {unit_name}")
                if unit_data.get('net_income'):
                    net_sum = sum(unit_data['net_income'])
                    total_net_income += net_sum
                    print(f"Added {net_sum} net income from {unit_name}")
        
        # Calculate totals from P&L data
        if processed_data.get('monthly_data'):
            print("Processing monthly P&L data...")
            for company_name, company_data in processed_data['monthly_data'].items():
                print(f"Company: {company_name}, Data keys: {list(company_data.keys())}")
                if company_data.get('total_income'):
                    income_sum = sum(company_data['total_income'])
                    total_revenue += income_sum
                    print(f"Added {income_sum} income from {company_name}")
                if company_data.get('total_expense'):
                    expense_sum = sum(company_data['total_expense'])
                    total_expenses += expense_sum
                    print(f"Added {expense_sum} expenses from {company_name}")
                if company_data.get('net_income'):
                    net_sum = sum(company_data['net_income'])
                    total_net_income += net_sum
                    print(f"Added {net_sum} net income from {company_name}")
        
        print(f"Final totals - Revenue: {total_revenue}, Expenses: {total_expenses}, Net Income: {total_net_income}")
        
        # Calculate KPIs
        kpis['total_revenue'] = {
            'value': total_revenue,
            'label': 'Total Revenue',
            'format': 'currency'
        }
        
        kpis['total_expenses'] = {
            'value': total_expenses,
            'label': 'Total Expenses',
            'format': 'currency'
        }
        
        kpis['total_net_income'] = {
            'value': total_net_income,
            'label': 'Total Net Income',
            'format': 'currency'
        }
        
        # Calculate profit margin
        if total_revenue > 0:
            profit_margin = (total_net_income / total_revenue) * 100
            kpis['profit_margin'] = {
                'value': profit_margin,
                'label': 'Profit Margin',
                'format': 'percentage'
            }
        
        # Calculate monthly averages
        months_count = 8  # Jan-Aug 2025
        kpis['avg_monthly_revenue'] = {
            'value': total_revenue / months_count,
            'label': 'Avg Monthly Revenue',
            'format': 'currency'
        }
        
        kpis['avg_monthly_net_income'] = {
            'value': total_net_income / months_count,
            'label': 'Avg Monthly Net Income',
            'format': 'currency'
        }
        
    except Exception as e:
        print(f"Error calculating comprehensive finance KPIs: {e}")
        # Fallback KPIs
        kpis = {
            'total_revenue': {'value': 0, 'label': 'Total Revenue', 'format': 'currency'},
            'total_expenses': {'value': 0, 'label': 'Total Expenses', 'format': 'currency'},
            'total_net_income': {'value': 0, 'label': 'Total Net Income', 'format': 'currency'},
            'profit_margin': {'value': 0, 'label': 'Profit Margin', 'format': 'percentage'},
            'avg_monthly_revenue': {'value': 0, 'label': 'Avg Monthly Revenue', 'format': 'currency'},
            'avg_monthly_net_income': {'value': 0, 'label': 'Avg Monthly Net Income', 'format': 'currency'}
        }
    
    return kpis

def calculate_finance_kpis(df: pd.DataFrame) -> Dict:
    """Calculate financial KPIs from the data"""
    kpis = {}
    
    try:
        # Initialize totals
        total_revenue = 0
        total_expenses = 0
        total_gross_income = 0
        total_net_income = 0
        
        # Extract data for available months
        for col in df.columns:
            if any(month in str(col) for month in ['Jan-', 'Feb-', 'Mar-', 'Apr-', 'May-']):
                try:
                    # Revenue
                    revenue_row = df[df.iloc[:, 1].astype(str).str.contains('Direct Hire Revenue', na=False)]
                    if not revenue_row.empty:
                        val = revenue_row.iloc[0][col]
                        if pd.notna(val) and val != '':
                            total_revenue += float(val)
                    
                    # Expenses
                    expense_row = df[df.iloc[:, 1].astype(str).str.contains('Direct Hire expenses', na=False)]
                    if not expense_row.empty:
                        val = expense_row.iloc[0][col]
                        if pd.notna(val) and val != '':
                            total_expenses += float(val)
                    
                    # Gross Income
                    gross_row = df[df.iloc[:, 1].astype(str).str.contains('Gross Income', na=False)]
                    if not gross_row.empty:
                        val = gross_row.iloc[0][col]
                        if pd.notna(val) and val != '':
                            total_gross_income += float(val)
                    
                    # Net Income
                    net_row = df[df.iloc[:, 1].astype(str).str.contains('Net Income', na=False)]
                    if not net_row.empty:
                        val = net_row.iloc[0][col]
                        if pd.notna(val) and val != '':
                            total_net_income += float(val)
                            
                except (ValueError, TypeError):
                    continue
        
        # Format KPIs
        kpis['Total Revenue (YTD)'] = f"${total_revenue:,.2f}"
        kpis['Total Expenses (YTD)'] = f"${total_expenses:,.2f}"
        kpis['Gross Income (YTD)'] = f"${total_gross_income:,.2f}"
        kpis['Net Income (YTD)'] = f"${total_net_income:,.2f}"
        
    except Exception as e:
        print(f"Error calculating finance KPIs: {e}")
    
    return kpis

@app.route('/clear_session_data', methods=['POST'])
def clear_session_data():
    """Clear all session data"""
    session.clear()
    return jsonify({'success': True})

@app.route('/clear_finance_session', methods=['POST'])
def clear_finance_session():
    """Clear finance session data specifically"""
    if 'finance_processed_data' in session:
        del session['finance_processed_data']
    return jsonify({'success': True})

@app.route('/save_custom_formulas', methods=['POST'])
def save_custom_formulas():
    """Save custom formulas for financial calculations"""
    try:
        data = request.get_json()
        formulas = data.get('formulas', {})
        
        print("=== SAVING CUSTOM FORMULAS ===")
        print(f"Formulas received: {formulas}")
        
        # Store formulas in session
        session.permanent = True
        session['custom_formulas'] = formulas
        
        print("Custom formulas saved to session")
        
        return jsonify({
            'success': True,
            'message': 'Formulas saved successfully',
            'formulas': formulas
        })
        
    except Exception as e:
        print(f"Error saving custom formulas: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/get_custom_formulas', methods=['GET'])
def get_custom_formulas():
    """Get saved custom formulas"""
    try:
        formulas = session.get('custom_formulas', {})
        
        print("=== GETTING CUSTOM FORMULAS ===")
        print(f"Formulas in session: {formulas}")
        
        return jsonify({
            'success': True,
            'formulas': formulas
        })
        
    except Exception as e:
        print(f"Error getting custom formulas: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
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
    
    # Handle recruitment data - check if it's placement report format
    if not rec_df_raw.empty:
        try:
            # Try to process as placement report
            placement_data = process_placement_report(rec_df_raw)
            if placement_data and placement_data.get('employment_data'):
                # Create placement report charts
                emp_chart = create_employment_types_chart(placement_data)
                placement_chart = create_placement_metrics_chart(placement_data)
                margin_chart = create_gross_margin_chart(placement_data)
                
                if emp_chart:
                    charts['employment_types'] = emp_chart
                if placement_chart:
                    charts['placement_metrics'] = placement_chart
                if margin_chart:
                    charts['gross_margin'] = margin_chart
            else:
                # Fall back to original recruitment processing
                if not rec_m.empty:
                    rec_map = mappings.get('rec_map', {})
                    if rec_map.get("placements") in rec_m.columns:
                        charts['rec_bar'] = fig_bar(rec_m, "Month", rec_map["placements"], "Placements")
                    if rec_map.get("revenue") in rec_m.columns:
                        charts['rec_revenue'] = fig_line(rec_m, "Month", [rec_map["revenue"]], "Recruitment Revenue")
        except Exception as e:
            print(f"Error processing recruitment data: {e}")
            # Continue without recruitment charts
    
    # Charts are already in JSON format for Chart.js
    charts_json = charts
    
    return jsonify({
        'kpis': kpis,
        'charts': charts_json,
        'has_pl_data': not pl_m.empty,
        'has_bs_data': not bs_m.empty,
        'has_rec_data': not rec_m.empty,
        'has_mg_data': not mg_m.empty
    })

# --------------------- Recruitment Routes ---------------------

# Removed separate recruitment route - now handled by single-page app in index.html
# @app.route('/recruitment')  
# def recruitment_dashboard():
#     """Recruitment dashboard page"""
#     return render_template('recruitment_dashboard.html')

@app.route('/api/recruitment/data')
def get_recruitment_data():
    """Get all recruitment data"""
    employment_df = get_recruitment_employment_data()
    placement_df = get_recruitment_placement_data()
    margin_df = get_recruitment_margin_data()
    
    return jsonify({
        'employment': employment_df.to_dict('records'),
        'placement': placement_df.to_dict('records'),
        'margin': margin_df.to_dict('records')
    })

@app.route('/api/recruitment/charts')
def get_recruitment_charts():
    """Get all recruitment chart data"""
    employment_df = get_recruitment_employment_data()
    placement_df = get_recruitment_placement_data()
    margin_df = get_recruitment_margin_data()
    
    # Note: These functions would need to be updated to return Chart.js format
    charts = {
        'employment': create_recruitment_employment_chart(employment_df),
        'placement': create_recruitment_placement_chart(placement_df),
        'margin': create_recruitment_margin_chart(margin_df)
    }
    
    return jsonify(charts)

@app.route('/api/recruitment/add_month', methods=['POST'])
def add_recruitment_month():
    """Add new month data"""
    data = request.json
    
    conn = sqlite3.connect(DB_PATH)
    
    # Add employment data
    conn.execute('''
        INSERT INTO employment_data (month, w2, c2c, employment_1099, referral, total_billables)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        data['month'],
        data['employment']['w2'],
        data['employment']['c2c'],
        data['employment']['employment_1099'],
        data['employment']['referral'],
        data['employment']['total_billables']
    ))
    
    # Add placement data
    conn.execute('''
        INSERT INTO placement_data (month, new_placements, terminations, net_placements, net_billables)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        data['month'],
        data['placement']['new_placements'],
        data['placement']['terminations'],
        data['placement']['net_placements'],
        data['placement']['net_billables']
    ))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/recruitment/export/dataset')
def export_recruitment_dataset():
    """Export recruitment dataset as CSV"""
    employment_df = get_recruitment_employment_data()
    placement_df = get_recruitment_placement_data()
    margin_df = get_recruitment_margin_data()
    
    # Create a combined dataset
    combined_df = employment_df.merge(placement_df, on='month', how='outer')
    
    # Save to CSV
    output = io.StringIO()
    combined_df.to_csv(output, index=False)
    output.seek(0)
    
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name='recruitment_dataset.csv'
    )

@app.route('/api/recruitment/export/report')
def export_recruitment_report():
    """Export recruitment dashboard report as HTML"""
    employment_df = get_recruitment_employment_data()
    placement_df = get_recruitment_placement_data()
    margin_df = get_recruitment_margin_data()
    
    # Generate charts
    employment_chart = create_recruitment_employment_chart(employment_df)
    placement_chart = create_recruitment_placement_chart(placement_df)
    margin_chart = create_recruitment_margin_chart(margin_df)
    
    # Create HTML report
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Recruitment Dashboard Report</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .chart {{ margin: 20px 0; }}
            .summary {{ background: #f5f5f5; padding: 15px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <h1>Recruitment Dashboard Report</h1>
        <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="summary">
            <h2>Summary</h2>
            <p>Total months of data: {len(employment_df)}</p>
            <p>Latest month: {employment_df.iloc[-1]['month'] if not employment_df.empty else 'N/A'}</p>
        </div>
        
        <div class="chart">
            <h2>Employment Types</h2>
            <div id="employment-chart"></div>
        </div>
        
        <div class="chart">
            <h2>Placement Metrics</h2>
            <div id="placement-chart"></div>
        </div>
        
        <div class="chart">
            <h2>Gross Margin IT Staffing</h2>
            <div id="margin-chart"></div>
        </div>
        
        <script>
            // Chart.js implementation would go here
            // For now, showing placeholder text
        </script>
    </body>
    </html>
    """
    
    return send_file(
        io.BytesIO(html_content.encode()),
        mimetype='text/html',
        as_attachment=True,
        download_name='recruitment_dashboard_report.html'
    )

if __name__ == '__main__':
    # DISABLED: Don't auto-load recruitment data on startup
    # init_recruitment_database()
    # load_recruitment_csv_data()
    app.run(debug=True, host='0.0.0.0', port=5004)

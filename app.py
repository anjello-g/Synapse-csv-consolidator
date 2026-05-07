import streamlit as st
import pandas as pd
from io import BytesIO

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="CSV Consolidator",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== DARK MODE CSS ====================
st.markdown("""
    <style>
    /* Force dark background */
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    
    /* Sidebar dark */
    [data-testid="stSidebar"] {
        background-color: #161b22;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #58a6ff !important;
    }
    
    /* Dataframes */
    .stDataFrame {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
    }
    
    /* Buttons */
    .stButton>button, .stDownloadButton>button {
        background-color: #238636 !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease;
    }
    .stButton>button:hover, .stDownloadButton>button:hover {
        background-color: #2ea043 !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(46, 160, 67, 0.3);
    }
    
    /* File uploader */
    [data-testid="stFileUploader"] {
        background-color: #161b22;
        border: 2px dashed #30363d;
        border-radius: 8px;
        padding: 20px;
    }
    
    /* Metric cards */
    [data-testid="stMetricValue"] {
        color: #3fb950 !important;
        font-weight: 700 !important;
    }
    [data-testid="stMetricLabel"] {
        color: #8b949e !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 6px;
        color: #c9d1d9;
    }
    
    /* Success/Info/Warning boxes */
    .stSuccess {
        background-color: #23863620 !important;
        border: 1px solid #238636 !important;
    }
    .stInfo {
        background-color: #1f6feb20 !important;
        border: 1px solid #1f6feb !important;
    }
    .stWarning {
        background-color: #d2992220 !important;
        border: 1px solid #d29922 !important;
    }
    .stError {
        background-color: #da363320 !important;
        border: 1px solid #da3633 !important;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #0e1117;
    }
    ::-webkit-scrollbar-thumb {
        background: #30363d;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #484f58;
    }
    </style>
""", unsafe_allow_html=True)

# ==================== HEADER ====================
st.markdown("""
    <div style='text-align: center; padding: 20px 0 30px 0;'>
        <h1 style='font-size: 2.5rem; margin-bottom: 8px;'>📁 CSV Consolidator</h1>
        <p style='color: #8b949e; font-size: 1.1rem;'>
            Upload monthly CSV files → Preview → Export clean consolidated data
        </p>
    </div>
""", unsafe_allow_html=True)

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("<h2 style='color: #58a6ff;'>⚙️ Settings</h2>", unsafe_allow_html=True)
    
    KEEP_COLUMNS = [
        "Actual Time",
        "Adherence (%)",
        "Agent",
        "Conformance (%)",
        "Exceptions",
        "Exceptions Duration (Adherence)",
        "Exceptions Duration Minutes",
        "Management Unit",
        "Net Impact",
        "Scheduled (Adherence)",
        "Scheduled Minutes",
        "Scheduled On Queue",
        "Work Time On Queue"
    ]
    
    st.markdown("<p style='color: #8b949e; margin-bottom: 8px;'><b>Columns extracted:</b></p>", unsafe_allow_html=True)
    for col in KEEP_COLUMNS:
        st.markdown(f"<span style='color: #c9d1d9; font-size: 0.85rem;'>• {col}</span>", unsafe_allow_html=True)
    
    st.markdown("---")
    output_format = st.radio("📤 Output format", ["CSV", "Excel"], index=0)
    st.markdown("---")
    st.markdown("<p style='color: #484f58; font-size: 0.75rem;'>Dark mode enabled by default</p>", unsafe_allow_html=True)

# ==================== HELPER FUNCTIONS ====================

def clean_percentage(val):
    if pd.isna(val):
        return None
    s = str(val).strip()
    if s.lower() in ("nan%", "infinity%", "-infinity%", "inf%", "-inf%"):
        return None
    return s


def parse_actual_time(val):
    if pd.isna(val):
        return None
    s = str(val).strip()
    if s in ("0", "0.0", "0:00", "00:00:00", ""):
        return None
    return s


def process_file(uploaded_file):
    try:
        df = pd.read_csv(uploaded_file, dtype=str, low_memory=False, on_bad_lines='warn')
    except Exception as e:
        st.error(f"❌ Failed to read `{uploaded_file.name}`: {e}")
        return None
    
    month_name = uploaded_file.name.rsplit('.', 1)[0]
    df["Month"] = month_name
    
    available_cols = [c for c in KEEP_COLUMNS if c in df.columns]
    missing_cols = [c for c in KEEP_COLUMNS if c not in df.columns]
    
    if missing_cols:
        st.warning(f"⚠️ `{uploaded_file.name}` missing: {', '.join(missing_cols)}")
    
    if not available_cols:
        st.error(f"❌ `{uploaded_file.name}` has no required columns.")
        return None
    
    df = df[available_cols + ["Month"]]
    
    if "Actual Time" in df.columns:
        df["Actual Time"] = df["Actual Time"].apply(parse_actual_time)
    
    for col in ["Adherence (%)", "Conformance (%)"]:
        if col in df.columns:
            df[col] = df[col].apply(clean_percentage)
    
    for col in df.columns:
        df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
    
    return df


# ==================== FILE UPLOADER ====================
uploaded_files = st.file_uploader(
    "",
    type=["csv"],
    accept_multiple_files=True,
    help="Select all your monthly CSV files. Filename becomes the Month column."
)

# ==================== PROCESSING ====================
if uploaded_files:
    st.markdown(f"<p style='color: #8b949e;'>📎 <b>{len(uploaded_files)}</b> file(s) selected</p>", unsafe_allow_html=True)
    
    all_dfs = []
    file_details = []
    
    progress_bar = st.progress(0, text="Processing files...")
    
    for i, uploaded_file in enumerate(uploaded_files):
        df = process_file(uploaded_file)
        if df is not None:
            all_dfs.append(df)
            file_details.append({
                "File": uploaded_file.name,
                "Month": uploaded_file.name.rsplit('.', 1)[0],
                "Rows": len(df)
            })
        progress_bar.progress((i + 1) / len(uploaded_files), text=f"Processed {i+1} of {len(uploaded_files)}...")
    
    progress_bar.empty()
    
    if all_dfs:
        consolidated = pd.concat(all_dfs, ignore_index=True)
        consolidated.dropna(how='all', inplace=True)
        
        final_cols = ["Month"] + [c for c in KEEP_COLUMNS if c in consolidated.columns]
        consolidated = consolidated[final_cols]
        
        # ==================== SUMMARY CARDS ====================
        st.markdown("---")
        st.subheader("📊 Summary")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Files", len(all_dfs))
        c2.metric("Total Rows", f"{len(consolidated):,}")
        c3.metric("Columns", len(consolidated.columns))
        c4.metric("Months", consolidated["Month"].nunique())
        
        # ==================== FILE DETAILS ====================
        with st.expander("📋 View File Breakdown"):
            st.dataframe(
                pd.DataFrame(file_details),
                use_container_width=True,
                hide_index=True
            )
        
        # ==================== DATA PREVIEW ====================
        st.markdown("---")
        st.subheader("🔍 Data Preview")
        
        preview_rows = st.slider("Rows to preview", min_value=5, max_value=min(500, len(consolidated)), value=50)
        
        st.dataframe(
            consolidated.head(preview_rows),
            use_container_width=True,
            hide_index=True,
            height=min(600, (preview_rows + 1) * 35)
        )
        
        # ==================== EXPORT ====================
        st.markdown("---")
        st.subheader("⬇️ Export")
        
        col_dl, _ = st.columns([1, 3])
        
        with col_dl:
            if output_format == "CSV":
                csv_buffer = BytesIO()
                consolidated.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
                csv_buffer.seek(0)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv_buffer,
                    file_name="consolidated.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                excel_buffer = BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    consolidated.to_excel(writer, index=False, sheet_name="Consolidated")
                excel_buffer.seek(0)
                st.download_button(
                    label="📥 Download Excel",
                    data=excel_buffer,
                    file_name="consolidated.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        
        # ==================== COLUMN STATS ====================
        with st.expander("📈 Column Statistics"):
            st.dataframe(
                consolidated.describe(include='all').transpose(),
                use_container_width=True
            )
            
    else:
        st.error("No files could be processed. Check your CSV formats.")
else:
    st.markdown("""
        <div style='text-align: center; padding: 60px 20px; color: #484f58;'>
            <h3>👆 Upload CSV files to begin</h3>
            <p>Drag and drop one or more CSV files above.<br>
            Each filename will be used as the <b>Month</b> column.</p>
        </div>
    """, unsafe_allow_html=True)

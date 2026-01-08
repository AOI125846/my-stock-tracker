# -*- coding: utf-8 -*-
"""
Streamlit – "התיק החכם"
"""

import uuid
import io
import sys
from datetime import datetime
import os

import pandas as pd
import numpy as np
import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px
import plotly.graph_objects as go

# הוספת נתיבי התיקיות למערכת
sys.path.insert(0, './core')
sys.path.insert(0, './utils')

# ייבוא מודולים מותאמים עם טיפול בשגיאות
try:
    from core.indicators import calculate_all_indicators, calculate_final_score, get_smart_analysis, analyze_fundamentals
    from core.data import load_stock_data
    from utils.export import to_excel
except ImportError as e:
    st.error(f"❌ שגיאה בייבוא מודולים: {e}")
    st.info("""
    **מבנה הפרויקט הנדרש:**
    ```
    📁 my-stock-tracker/
    ├── 📁 core/
    │   ├── indicators.py
    │   └── data.py
    ├── 📁 utils/
    │   └── export.py
    ├── app.py
    └── requirements.txt
    ```
    
    ודא שהקבצים נמצאים בתיקיות הנכונות.
    """)
    st.stop()

# ----------------------------------------------------------------------
# שאר הקוד נשאר זהה כמו בקובץ הקודם
# רק שיניתי את היבואים למעלה
# ----------------------------------------------------------------------

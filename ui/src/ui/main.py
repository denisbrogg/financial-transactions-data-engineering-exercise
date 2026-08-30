from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent

st.set_page_config(
    page_title="Transaction Intelligence",
    page_icon="📊",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp {
        background: #ffffff;
    }
    div[data-testid="stSidebar"] {
        background: #f8fafc;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

pages = [
    st.Page(BASE_DIR / "pages" / "01_home.py", title="Home", icon="🏠"),
    st.Page(BASE_DIR / "pages" / "02_general.py", title="Analysis", icon="📈"),
    st.Page(
        BASE_DIR / "pages" / "03_customer_behaviour.py",
        title="Customer behaviour",
        icon="📊",
    ),
    st.Page(BASE_DIR / "pages" / "04_customers.py", title="Customers", icon="👥"),
    st.Page(
        BASE_DIR / "pages" / "05_company_performers.py",
        title="Company performers",
        icon="💼",
    ),
    st.Page(BASE_DIR / "pages" / "06_side_quests.py", title="Side quests", icon="💡"),
]

navigation = st.navigation(pages)
navigation.run()

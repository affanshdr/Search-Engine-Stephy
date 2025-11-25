import streamlit as st

# CSS untuk styling input dan tombol
st.markdown("""
    <style>
    /* Style input text */
    div[data-testid="stTextInput"] input {
        height: 40px !important;
        width: 100% !important;
        border-radius: 12px 4px 12px 4px !important; /* top-left, top-right, bottom-right, bottom-left */
        padding: 8px 12px !important;
        border: 1px solid #ccc !important;
    }
    /* Style button */
    button[data-baseweb="button"] {
        height: 40px !important;
        width: 100% !important;
        border-radius: 4px 12px 4px 12px !important;
        background-color: #0055ff !important;
        color: white !important;
        font-weight: bold !important;
    }
    </style>
""", unsafe_allow_html=True)

col1, col2 = st.columns([5, 1])

with col1:
    form = st.text_input(
        "",
        placeholder="Search About Games.....",
        label_visibility="collapsed"
    )

with col2:
    tombol = st.button("🔍", use_container_width=True)

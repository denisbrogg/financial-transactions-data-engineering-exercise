import sys
from pathlib import Path

import streamlit as st

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ui.db import require_db


def main():
    require_db()
    st.title("Side quests")
    st.write(
        "These are exploratory extensions designed to turn transaction history into future business intelligence."
    )

    ideas = [
        {
            "title": "Churn risk and elite-candidate detection",
            "text": "Identify customers whose transaction activity, fee contribution, or engagement trend suggests they may churn or are close to entering the top tier of value creation.",
        },
        {
            "title": "Notes insights by status",
            "text": "Group notes or narrative records by status, then cluster or summarize the customer narrative and use LLM-assisted interpretation to explain the drivers behind each cohort.",
        },
        {
            "title": "Customer growth analysis",
            "text": "Compare the fastest-growing customers against the best customers to see whether the most valuable accounts are also the ones expanding the most over time.",
        },
        {
            "title": "Outlier transaction detection",
            "text": "Flag unusual transactions based on size, currency mix, pricing, or channel anomalies that may require review or investigation.",
        },
    ]

    for item in ideas:
        with st.container():
            st.subheader(item["title"])
            st.write(item["text"])
            st.markdown("---")


if __name__ == "__main__":
    main()

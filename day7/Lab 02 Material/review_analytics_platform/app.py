import streamlit as st

import config
from database.db_manager import (
    init_db,
    save_summary,
    get_summaries_by_category,
    get_summary_by_id,
)
from services.gemini_service import analyze_review_sentiment


# ---------------------------------------------------------
# Page setup
# ---------------------------------------------------------

st.set_page_config(
    page_title="Review Analyst Pro",
    layout="wide",
)

init_db()


# ---------------------------------------------------------
# Session state
# ---------------------------------------------------------

if "view_mode" not in st.session_state:
    st.session_state.view_mode = "new_analysis"

if "selected_summary_id" not in st.session_state:
    st.session_state.selected_summary_id = None


# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------

with st.sidebar:
    st.title("Navigation & History")

    if st.button(
        "Analyze New Review",
        use_container_width=True,
        type="primary",
    ):
        st.session_state.view_mode = "new_analysis"
        st.session_state.selected_summary_id = None
        st.rerun()

    st.divider()
    st.subheader("📜 Past Summaries")

    categories = {
        "Good (8–10)": "Good",
        "Average (4–7)": "Average",
        "Bad (0–3)": "Bad",
    }

    for label, category in categories.items():
        with st.expander(label):
            records = get_summaries_by_category(category)

            if not records:
                st.caption("No saved records.")

            for summary_id, filename, created_at in records:
                button_label = f"{filename}"

                if st.button(
                    button_label,
                    key=f"record_{summary_id}",
                    use_container_width=True,
                ):
                    st.session_state.view_mode = "view_past"
                    st.session_state.selected_summary_id = summary_id
                    st.rerun()


# ---------------------------------------------------------
# View saved result
# ---------------------------------------------------------

if (
    st.session_state.view_mode == "view_past"
    and st.session_state.selected_summary_id is not None
):
    record = get_summary_by_id(
        st.session_state.selected_summary_id
    )

    if record:
        filename, summary, rating, category, created_at = record

        st.title(f"Saved Analysis: {filename}")
        st.caption(
            f"Analyzed on: {created_at} | Category: {category}"
        )

        st.divider()

        metric_column, result_column = st.columns([1, 4])

        with metric_column:
            st.metric(
                label="Overall Rating",
                value=f"{rating} / 10",
            )

        with result_column:
            if category == "Good":
                st.success(
                    "This review reflects positive customer sentiment."
                )
            elif category == "Average":
                st.warning(
                    "This review reflects mixed or average customer sentiment."
                )
            else:
                st.error(
                    "This review reflects negative customer sentiment."
                )

        st.subheader("📋 Summary")
        st.markdown(summary)

    else:
        st.error("Could not retrieve the saved record.")


# ---------------------------------------------------------
# New analysis
# ---------------------------------------------------------

else:
    st.title("Customer Review Analytics Platform")
    st.caption(f"AI model: {config.MODEL_NAME}")

    st.divider()

    st.write(
        "Upload a text file containing a customer review. "
        "The app will summarize it, generate a rating, "
        "classify the sentiment, and save the result."
    )

    uploaded_file = st.file_uploader(
        "Upload customer review",
        type=["txt"],
    )

    if uploaded_file is not None:
        try:
            review_text = uploaded_file.read().decode("utf-8")
        except UnicodeDecodeError:
            st.error("The uploaded file must use UTF-8 encoding.")
            st.stop()

        if not review_text.strip():
            st.error("The uploaded file is empty.")
            st.stop()

        with st.expander("Review Preview"):
            st.text(review_text)

        st.divider()

        if st.button(
            "Analyze Review",
            use_container_width=True,
            type="primary",
        ):
            try:
                with st.spinner(
                    "Analyzing customer sentiment..."
                ):
                    summary, rating, category = (
                        analyze_review_sentiment(review_text)
                    )

                    save_summary(
                        uploaded_file.name,
                        summary,
                        rating,
                        category,
                    )

                st.success(
                    f"Analysis complete and saved under "
                    f"the {category} category."
                )

                metric_column, result_column = st.columns([1, 4])

                with metric_column:
                    st.metric(
                        label="Calculated Rating",
                        value=f"{rating} / 10",
                    )

                with result_column:
                    if category == "Good":
                        st.success(
                            "Positive customer sentiment"
                        )
                    elif category == "Average":
                        st.warning(
                            "Mixed or average customer sentiment"
                        )
                    else:
                        st.error(
                            "Negative customer sentiment"
                        )

                st.subheader("Analysis Summary")
                st.markdown(summary)

            except Exception as error:
                st.error(f"Analysis failed: {error}")
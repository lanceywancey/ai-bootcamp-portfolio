import json
import os
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from report import render_markdown
from parse import read_resume_pdf

from analyzer import (
    extract_resume_profile, extract_jd_profile, analyse_keyword_match,
    analyse_bullets, analyse_jargon, analyse_structure,
    analyse_background_fit, analyse_degree_alignment, summarise_overall, compute_overall_score,
)

load_dotenv()
VALID_DEGREES = ["RTIS", "IMGD", "UXGD", "BFA"]

st.set_page_config(page_title="Resume Analyzer", layout="wide")
st.title("📄 AI Resume Analyzer")

resume_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
jd_text = st.text_area("Paste Job Description", height=250)
degree = st.selectbox("Select Degree", VALID_DEGREES)
run = st.button("Analyze Resume")

if run:
    if not resume_file or not jd_text:
        st.error("Please upload resume and paste job description.")
        st.stop()

    try:
        # Read the uploaded PDF
        with st.spinner("Reading résumé PDF..."):
            resume_text = read_resume_pdf(resume_file)
            
        with st.spinner("Extracting résumé profile..."):
            resume_profile = extract_resume_profile(resume_text)

        with st.spinner("Extracting résumé profile..."):
            resume_profile = extract_resume_profile(resume_text)

        with st.spinner("Extracting job description profile..."):
            jd_profile = extract_jd_profile(jd_text)

        with st.spinner("Checking keyword matches..."):
            keyword_match = analyse_keyword_match(
                resume_profile,
                jd_profile,
            )

        with st.spinner("Analysing résumé bullets..."):
            bullets = analyse_bullets(resume_profile)

        with st.spinner("Analysing jargon..."):
            jargon = analyse_jargon(
                resume_profile,
                jd_profile,
            )

        with st.spinner("Analysing résumé structure..."):
            structure = analyse_structure(resume_text)

        with st.spinner("Analysing background fit..."):
            background_fit = analyse_background_fit(
                resume_profile,
                jd_profile,
            )

        with st.spinner("Analysing degree alignment..."):
            degree_alignment = analyse_degree_alignment(
                resume_profile,
                degree
            )

        # Combine all results into one report
        report = {
            "selected_degree": degree,
            "resume_profile": resume_profile,
            "jd_profile": jd_profile,
            "keyword_match": keyword_match,
            "bullets": bullets,
            "jargon": jargon,
            "structure": structure,
            "background_fit": background_fit,
            "degree_alignment": degree_alignment,
        }

        overall_score = compute_overall_score(report)

        report["overall_score"] = overall_score
        report["passes_ats_threshold"] = overall_score >= 60

        with st.spinner("Generating final summary..."):
            report["summary"] = summarise_overall(report)

        st.success("Analysis complete!")

        st.metric(
            "Overall ATS Score",
            f"{overall_score}/100",
        )

        if report["passes_ats_threshold"]:
            st.success("PASS — résumé meets the 60% ATS threshold.")
        else:
            st.warning("FAIL — résumé is below the 60% ATS threshold.")

        st.subheader("Overall Summary")
        st.write(report["summary"])

        st.subheader("Keyword Match")
        st.json(keyword_match)

        st.subheader("Bullet Analysis")
        st.json(bullets)

        st.subheader("Jargon Analysis")
        st.json(jargon)

        st.subheader("Structure Analysis")
        st.json(structure)

        st.subheader("Background Fit")
        st.json(background_fit)

        st.subheader("Degree Alignment")
        st.json(degree_alignment)

    except RuntimeError as e:
        st.error(f"LLM error: {e}")

    except Exception as e:
        st.error(f"Unexpected error: {e}")
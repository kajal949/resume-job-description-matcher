
import json
import streamlit as st

from resume_parser import extract_resume_text
from matcher import compare_resume_to_job
from llm_analyzer import generate_resume_analysis


# ==================================================
# 1. PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Resume & Job Matcher",
    page_icon="🎯",
    layout="wide",
)


# ==================================================
# 2. SESSION STATE
# ==================================================

if "analysis_results" not in st.session_state:
    st.session_state["analysis_results"] = None

if "ai_report" not in st.session_state:
    st.session_state["ai_report"] = None


# ==================================================
# 3. STYLING
# ==================================================

st.markdown(
    """
    <style>
        .main-title {
            font-size: 2.3rem;
            font-weight: 700;
            margin-bottom: 0.2rem;
        }

        .subtitle {
            color: #777;
            font-size: 1rem;
            margin-bottom: 1.5rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==================================================
# 4. HEADER
# ==================================================

st.markdown(
    '<div class="main-title">'
    '🎯 Resume & Job Description Matcher'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    'Analyze resume relevance using NLP, semantic similarity, '
    'and LLM-powered explanations.'
    '</div>',
    unsafe_allow_html=True,
)

st.info(
    "This application provides preliminary skill matching and "
    "evidence-based suggestions. Its score is not a hiring probability."
)


# ==================================================
# 5. INPUTS
# ==================================================

left_column, right_column = st.columns(2)

with left_column:
    st.subheader("📄 Upload Resume")

    uploaded_file = st.file_uploader(
        "Choose a PDF or DOCX resume",
        type=["pdf", "docx"],
        help="Upload a text-based PDF or Word document.",
    )

with right_column:
    st.subheader("💼 Job Description")

    job_description = st.text_area(
        "Paste the job description",
        height=240,
        placeholder=(
            "Paste the role, responsibilities, required skills, "
            "and qualifications here."
        ),
    )


# ==================================================
# 6. ANALYZE BUTTON
# ==================================================

analyze_clicked = st.button(
    "🔍 Analyze Resume",
    type="primary",
    use_container_width=True,
)


if analyze_clicked:

    # Clear the previous report before starting a new analysis.
    st.session_state["analysis_results"] = None
    st.session_state["ai_report"] = None

    if uploaded_file is None:
        st.warning("Please upload your resume.")

    elif not job_description.strip():
        st.warning("Please enter a job description.")

    else:
        try:
            # ------------------------------------------
            # Extract resume text
            # ------------------------------------------
            with st.spinner("Extracting resume text..."):
                resume_text = extract_resume_text(uploaded_file)

            if not resume_text.strip():
                st.error(
                    "No readable text was extracted from the resume. "
                    "A scanned PDF may require OCR."
                )
                st.stop()

            # ------------------------------------------
            # Run the NLP matcher
            # ------------------------------------------
            with st.spinner("Running NLP skill matching..."):
                results = compare_resume_to_job(
                    resume_text,
                    job_description,
                )

            st.session_state["analysis_results"] = results

            # ------------------------------------------
            # Generate the LLM report
            # ------------------------------------------
            with st.spinner(
                "Generating AI explanations and resume suggestions..."
            ):
                try:
                    ai_report = generate_resume_analysis(
                        resume_text=resume_text,
                        job_description=job_description,
                        match_results=results,
                    )

                    st.session_state["ai_report"] = ai_report

                except Exception as api_error:
                    st.warning(
                        "NLP matching succeeded, but the AI report "
                        "could not be generated. Check your API key, "
                        "model setting, account access, and internet connection."
                    )
                    st.error(str(api_error))

        except Exception as error:
            st.error("An error occurred during resume analysis.")
            st.exception(error)


# ==================================================
# 7. DISPLAY ANALYSIS RESULTS
# ==================================================

results = st.session_state["analysis_results"]

if results is not None:

    st.divider()
    st.header("📊 Analysis Results")

    # ----------------------------------------------
    # Summary metrics
    # ----------------------------------------------
    metric1, metric2, metric3, metric4 = st.columns(4)

    with metric1:
        st.metric(
            "Preliminary Match Score",
            f'{results["match_score"]}%',
        )

    with metric2:
        st.metric(
            "Explicit Skill Matches",
            len(results["matched_skills"]),
        )

    with metric3:
        st.metric(
            "Potential Semantic Matches",
            len(results["semantic_matches"]),
        )

    with metric4:
        st.metric(
            "Unmatched Requirements",
            len(results["missing_skills"]),
        )

    st.caption(
        "Explicit matches receive full credit and potential semantic "
        "matches receive partial credit under the current scoring formula. "
        "This score does not measure overall candidate suitability."
    )

    # ----------------------------------------------
    # Explicit matches
    # ----------------------------------------------
    st.subheader("✅ Explicit Skill Matches")

    if results["matched_skills"]:
        st.write(" · ".join(results["matched_skills"]))
    else:
        st.info("No explicit skill matches were detected.")

    # ----------------------------------------------
    # Semantic matches
    # ----------------------------------------------
    st.subheader("🧠 Potential Semantic Matches")

    if results["semantic_matches"]:
        for item in results["semantic_matches"]:
            with st.expander(
                f'{item["skill"]} — {item["similarity"]}% similarity'
            ):
                st.write("**Supporting resume evidence:**")
                st.write(item["evidence"])

                st.caption(
                    "Semantic similarity indicates related wording, "
                    "not verified proficiency."
                )
    else:
        st.info(
            "No additional semantic matches passed the current threshold."
        )

    # ----------------------------------------------
    # Requirements without matching evidence
    # ----------------------------------------------
    st.subheader("📌 Requirements Without Matching Evidence")

    if results["missing_skills"]:
        for skill in results["missing_skills"]:
            st.markdown(f"- {skill}")

        st.caption(
            "A requirement may still be present in your resume if it "
            "is described using different wording."
        )
    else:
        st.success(
            "All detected job requirements have matching evidence "
            "under the current matching rules."
        )

    # ----------------------------------------------
    # Evidence
    # ----------------------------------------------
    st.divider()
    st.subheader("🔎 Match Evidence")

    if results["skill_evidence"]:
        for item in results["skill_evidence"]:

            similarity = item.get("similarity")

            if similarity is None:
                evidence_title = (
                    f'{item["match_type"]}: {item["skill"]}'
                )
            else:
                evidence_title = (
                    f'{item["match_type"]}: {item["skill"]} '
                    f'— {similarity}% similarity'
                )

            with st.expander(evidence_title):
                if item.get("evidence"):
                    st.write("**Resume evidence:**")
                    st.write(item["evidence"])
                else:
                    st.info("No supporting sentence was identified.")
    else:
        st.info("No supporting evidence was found.")

    # ----------------------------------------------
    # Detected skills
    # ----------------------------------------------
    st.divider()
    st.subheader("🧾 Detected Skills")

    skills_column1, skills_column2 = st.columns(2)

    with skills_column1:
        with st.expander("View all detected resume skills"):
            if results["resume_skills"]:
                for skill in results["resume_skills"]:
                    st.markdown(f"- {skill}")
            else:
                st.write("No skills detected.")

    with skills_column2:
        with st.expander("View all detected job requirements"):
            if results["job_skills"]:
                for skill in results["job_skills"]:
                    st.markdown(f"- {skill}")
            else:
                st.write("No job requirements detected.")

    # ----------------------------------------------
    # LLM-powered analysis
    # ----------------------------------------------
    st.divider()
    st.header("🤖 AI-Powered Resume Insights")

    ai_report = st.session_state.get("ai_report")

    if ai_report:
        st.markdown(ai_report)

        st.download_button(
            label="⬇️ Download AI Analysis",
            data=ai_report,
            file_name="ai_resume_analysis.txt",
            mime="text/plain",
            key="download_ai_resume_analysis",
        )

    else:
        st.info(
            "The NLP analysis is available. The AI-generated report "
            "is unavailable for this run. Check the API error above "
            "and analyze the resume again after resolving it."
        )

    # ----------------------------------------------
    # Download structured NLP report
    # ----------------------------------------------
    st.divider()
    st.subheader("📥 Download NLP Analysis Report")

    report = {
        "match_score": results["match_score"],
        "resume_skills": results["resume_skills"],
        "job_skills": results["job_skills"],
        "matched_skills": results["matched_skills"],
        "semantic_matches": results["semantic_matches"],
        "missing_skills": results["missing_skills"],
        "skill_evidence": results["skill_evidence"],
    }

    report_json = json.dumps(
        report,
        indent=4,
        ensure_ascii=False,
    )

    st.download_button(
        label="⬇️ Download JSON Report",
        data=report_json,
        file_name="resume_match_report.json",
        mime="application/json",
        key="download_nlp_resume_report",
    )


# ==================================================
# 8. FOOTER
# ==================================================

st.divider()

st.caption(
    "Resume & Job Matcher | NLP + Semantic Similarity + LLM API"
)
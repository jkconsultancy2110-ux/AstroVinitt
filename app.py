import streamlit as st
from google import genai
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io
import re

st.set_page_config(page_title="AI Astrology Studio", page_icon="🔮", layout="centered")

# --- Sidebar: API Configuration ---
st.sidebar.title("⚙️ AI Configuration")
api_key = st.sidebar.text_input(
    "Google Gemini API Key", 
    type="password", 
    help="Enter your API key. Get one for free at aistudio.google.com"
)
model_name = st.sidebar.selectbox("Gemini Model", ["gemini-2.5-flash", "gemini-2.5-pro"])

# --- Main Form ---
st.title("🔮 AI Astrologer & PDF Generator")
st.caption("Enter client details once to generate an AI-powered astrology reading and branded PDF report.")

with st.form("client_intake_form"):
    col1, col2 = st.columns(2)
    with col1:
        client_name = st.text_input("Client Full Name", "Priya Sharma")
        dob = st.date_input("Date of Birth")
        birth_time = st.time_input("Exact Time of Birth")
    with col2:
        birth_place = st.text_input("Place of Birth (City, Country)", "Mumbai, India")
        gender = st.selectbox("Gender", ["Female", "Male", "Other"])
        focus_area = st.selectbox(
            "Primary Reading Focus", 
            ["Career & Wealth", "Love, Marriage & Relationships", "Spiritual Path & Health", "Yearly Overview (2026-2027)"]
        )

    astrology_system = st.radio("Astrology Tradition", ["Vedic Astrology (Jyotish)", "Western Astrology"], horizontal=True)
    specific_notes = st.text_area("Specific Question / Notes", "Looking for insights on career transition and relationship stability.")

    generate_btn = st.form_submit_button("✨ Generate AI Report & PDF")

# --- PDF Builder Helper ---
def create_pdf(name, dob_str, time_str, place, focus, system, ai_text):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter, 
        rightMargin=45, 
        leftMargin=45, 
        topMargin=45, 
        bottomMargin=45
    )
    styles = getSampleStyleSheet()
    
    # Custom Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=10
    )
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=13,
        leading=17,
        textColor=colors.HexColor('#1A5276'),
        spaceBefore=10,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#34495E')
    )

    story = []
    story.append(Paragraph(f"Astrological Chart & Life Guidance Report", title_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#1A5276'), spaceAfter=12))

    # Client Summary Table / Meta
    client_meta = f"""
    <b>Client Name:</b> {name} &nbsp;|&nbsp; <b>Tradition:</b> {system}<br/>
    <b>Date of Birth:</b> {dob_str} &nbsp;|&nbsp; <b>Time:</b> {time_str}<br/>
    <b>Place of Birth:</b> {place}<br/>
    <b>Focus Area:</b> {focus}
    """
    story.append(Paragraph(client_meta, body_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#BDC3C7'), spaceAfter=12))

    # Clean and parse AI Markdown lines into ReportLab paragraphs
    lines = ai_text.split("\n")
    for line in lines:
        clean_line = line.strip()
        if not clean_line:
            story.append(Spacer(1, 4))
            continue
        
        # Replace markdown bold with HTML bold for ReportLab
        clean_line = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", clean_line)
        
        if clean_line.startswith("# ") or clean_line.startswith("## "):
            header_text = clean_line.lstrip("#").strip()
            story.append(Paragraph(header_text, section_style))
        elif clean_line.startswith("### "):
            header_text = clean_line.lstrip("#").strip()
            story.append(Paragraph(f"<b>{header_text}</b>", section_style))
        elif clean_line.startswith("* ") or clean_line.startswith("- "):
            bullet_text = "• " + clean_line[2:]
            story.append(Paragraph(bullet_text, body_style))
        else:
            story.append(Paragraph(clean_line, body_style))
            
    doc.build(story)
    buffer.seek(0)
    return buffer

# --- Execution Logic ---
if generate_btn:
    if not api_key:
        st.error("⚠️ Please enter your Gemini API Key in the left sidebar to generate the report.")
    else:
        with st.spinner("Invoking astrology chart analysis with Gemini AI..."):
            try:
                # Initialize Gemini client
                client = genai.Client(api_key=api_key) #
                
                system_prompt = (
                    f"You are a master practitioner of {astrology_system}. "
                    "Write an insightful, professional, empathetic, and detailed astrological reading report. "
                    "Structure your response with clear headers (##) covering: "
                    "1. Core Astrological Foundations (Ascendant, Sun & Moon energy), "
                    "2. Major Planetary Periods & Current Transits, "
                    f"3. In-Depth Insights on {focus_area}, "
                    "4. Actionable Remedies, Lucky Colors, and Supportive Practices."
                )
                
                user_content = f"""
                Client Details:
                - Name: {client_name}
                - DOB: {dob.strftime('%d %B %Y')}
                - Time of Birth: {birth_time.strftime('%I:%M %p')}
                - Location: {birth_place}
                - Gender: {gender}
                - Focus Area: {focus_area}
                - Client Query / Notes: {specific_notes}
                """

                # Call Gemini model
                response = client.models.generate_content(
                    model=model_name,
                    contents=[system_prompt, user_content]
                ) #
                ai_reading = response.text #

                # Render preview in app
                st.success("✅ Astrological Report Generated Successfully!")
                
                # Create downloadable PDF
                pdf_buffer = create_pdf(
                    client_name,
                    dob.strftime('%d %B %Y'),
                    birth_time.strftime('%I:%M %p'),
                    birth_place,
                    focus_area,
                    astrology_system,
                    ai_reading
                )
                
                # Download Button
                st.download_button(
                    label=f"📥 Download {client_name}'s PDF Report",
                    data=pdf_buffer,
                    file_name=f"{client_name.replace(' ', '_')}_Astrology_Reading.pdf",
                    mime="application/pdf"
                )
                
                # Display reading preview
                with st.expander("👁️ Preview Full Reading", expanded=True):
                    st.markdown(ai_reading)

            except Exception as e:
                st.error(f"Error communicating with AI API: {str(e)}")

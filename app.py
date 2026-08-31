import io
import re
import streamlit as st
from google import genai
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

st.set_page_config(page_title="Astro Vinitt - AI Astrology Studio", page_icon="🔮", layout="centered")

# --- Sidebar: API Configuration ---
st.sidebar.title("⚙️ AI Configuration")
api_key = st.sidebar.text_input(
    "Google Gemini API Key", 
    type="password", 
    help="Enter your API key from aistudio.google.com"
)
model_name = st.sidebar.selectbox("Gemini Model", ["gemini-2.5-flash", "gemini-2.5-pro"])

# --- Main Interface ---
st.title("🔮 Astro Vinitt - Client Consultation & PDF Report")
st.caption("Astrologer: Vinitt Parmar | Contact: +91 7874066576")

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
            ["Career & Wealth", "Love, Marriage & Relationships", "Spiritual Path & Health", "Yearly Life Overview"]
        )

    astrology_system = st.radio("Astrology Tradition", ["Vedic Astrology (Jyotish)", "Western Astrology"], horizontal=True)
    specific_notes = st.text_area("Specific Question / Notes", "Looking for insights on career transition and personal growth.")

    generate_btn = st.form_submit_button("✨ Generate AI Report & PDF")

# --- PDF Generation Helper ---
def create_pdf(name, dob_str, time_str, place, focus, system, ai_text):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter, 
        rightMargin=45, 
        leftMargin=45, 
        topMargin=40, 
        bottomMargin=40
    )
    styles = getSampleStyleSheet()
    
    branding_name_style = ParagraphStyle(
        'AstrologerName',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1A5276'),
        spaceAfter=2
    )
    branding_contact_style = ParagraphStyle(
        'AstrologerContact',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#5D6D7E'),
        spaceAfter=8
    )
    report_title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading2'],
        fontSize=13,
        leading=17,
        textColor=colors.HexColor('#2C3E50'),
        spaceBefore=6,
        spaceAfter=6
    )
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading3'],
        fontSize=12,
        leading=16,
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

    # 1. Astrologer Header Branding
    story.append(Paragraph("<b>ASTROLOGER VINITT PARMAR</b>", branding_name_style))
    story.append(Paragraph("<b>Vedic & Remedial Astrology Consultation</b> &nbsp;|&nbsp; <b>Phone / WhatsApp:</b> +91 7874066576", branding_contact_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#1A5276'), spaceAfter=10))

    # 2. Client Details Section
    story.append(Paragraph("<b>Personalized Astrological Chart & Life Guidance Report</b>", report_title_style))
    
    client_meta = (
        f"<b>Client Name:</b> {name} &nbsp;|&nbsp; <b>Tradition:</b> {system}<br/>"
        f"<b>Date of Birth:</b> {dob_str} &nbsp;|&nbsp; <b>Time:</b> {time_str}<br/>"
        f"<b>Place of Birth:</b> {place}<br/>"
        f"<b>Focus Area:</b> {focus}"
    )
    story.append(Paragraph(client_meta, body_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#BDC3C7'), spaceAfter=10))

    # 3. AI Content Parsing
    lines = ai_text.split("\n")
    for line in lines:
        clean_line = line.strip()
        if not clean_line:
            story.append(Spacer(1, 4))
            continue
        
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

# --- Generation Logic ---
if generate_btn:
    if not api_key:
        st.error("⚠️ Please enter your Gemini API Key in the left sidebar to generate the report.")
    else:
        with st.spinner("Analyzing astrological chart with Gemini AI..."):
            try:
                client = genai.Client(api_key=api_key)
                
                system_prompt = (
                    f"You are writing a professional astrology reading prepared by Astrologer Vinitt Parmar in the {astrology_system} tradition. "
                    "Write an insightful, encouraging, and detailed astrological reading report. "
                    "Structure your response with clear headers (##) covering: "
                    "1. Core Astrological Foundations (Ascendant, Sun & Moon dynamics), "
                    "2. Current Planetary Periods (Dasha/Transits), "
                    f"3. In-Depth Guidance on {focus_area}, "
                    "4. Practical Remedies, Gemstones/Color Guidance & Lucky Elements."
                )
                
                user_content = (
                    f"Client Details:\n"
                    f"- Name: {client_name}\n"
                    f"- DOB: {dob.strftime('%d %B %Y')}\n"
                    f"- Time of Birth: {birth_time.strftime('%I:%M %p')}\n"
                    f"- Location: {birth_place}\n"
                    f"- Gender: {gender}\n"
                    f"- Focus Area: {focus_area}\n"
                    f"- Client Query / Notes: {specific_notes}"
                )

                response = client.models.generate_content(
                    model=model_name,
                    contents=[system_prompt, user_content]
                )
                ai_reading = response.text

                st.success("✅ Astrological Report Generated Successfully!")
                
                pdf_buffer = create_pdf(
                    client_name,
                    dob.strftime('%d %B %Y'),
                    birth_time.strftime('%I:%M %p'),
                    birth_place,
                    focus_area,
                    astrology_system,
                    ai_reading
                )
                
                file_safe_name = client_name.replace(" ", "_")
                st.download_button(
                    label=f"📥 Download {client_name}'s PDF Report",
                    data=pdf_buffer,
                    file_name=f"{file_safe_name}_Astrology_Reading.pdf",
                    mime="application/pdf"
                )
                
                with st.expander("👁️ Preview Full Reading", expanded=True):
                    st.markdown(ai_reading)

            except Exception as e:
                st.error(f"Error communicating with AI API: {str(e)}")

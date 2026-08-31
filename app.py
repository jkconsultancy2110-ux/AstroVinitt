import io
import os
import re
import urllib.request
import streamlit as st
from google import genai
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- Page Configuration ---
st.set_page_config(page_title="જ્યોતિષી વિનિત પરમાર - AI Astrology Studio", page_icon="🔮", layout="centered")

# --- Setup Gujarati Font for ReportLab ---
@st.cache_resource
def setup_gujarati_font():
    font_path = "NotoSansGujarati.ttf"
    if not os.path.exists(font_path):
        url = "https://raw.githubusercontent.com/google/fonts/main/ofl/notosansgujarati/NotoSansGujarati%5Bwdth%2Cwght%5D.ttf"
        try:
            urllib.request.urlretrieve(url, font_path)
        except Exception:
            return "Helvetica"  # Fallback if download fails
    
    try:
        pdfmetrics.registerFont(TTFont('GujaratiFont', font_path))
        return 'GujaratiFont'
    except Exception:
        return "Helvetica"

active_font = setup_gujarati_font()

# --- Sidebar: API Configuration ---
st.sidebar.title("⚙️ AI Configuration")
api_key = st.sidebar.text_input(
    "Google Gemini API Key", 
    type="password", 
    help="Enter your API key from aistudio.google.com"
)
model_name = st.sidebar.selectbox("Gemini Model", ["gemini-3.6-flash"])

# --- Main Interface ---
st.title("🔮 જ્યોતિષી વિનિત પરમાર - કુંડળી વિશ્લેષણ રિપોર્ટ")
st.caption("જ્યોતિષાચાર્ય: વિનિત પરમાર | મો.: +91 7874066576")

with st.form("client_intake_form"):
    col1, col2 = st.columns(2)
    with col1:
        client_name = st.text_input("ગ્રાહકનું પૂરું નામ (Client Name)", "પ્રિયા શર્મા")
        dob = st.date_input("જન્મ તારીખ (Date of Birth)")
        
        st.write("જન્મ સમય (Time of Birth)")
        t_col1, t_col2, t_col3 = st.columns(3)
        with t_col1:
            birth_hour = st.selectbox("કલાક", [f"{i:02d}" for i in range(1, 13)], index=7)
        with t_col2:
            birth_minute = st.selectbox("મિનિટ", [f"{i:02d}" for i in range(0, 60, 1)], index=30)
        with t_col3:
            birth_period = st.selectbox("સમયગાળો", ["AM", "PM"], index=0)
            
        formatted_time = f"{birth_hour}:{birth_minute} {birth_period}"

    with col2:
        birth_place = st.text_input("જન્મ સ્થળ (Place of Birth)", "અમદાવાદ, ગુજરાત")
        gender = st.selectbox("જાતિ (Gender)", ["સ્ત્રી (Female)", "પુરુષ (Male)", "અન્ય (Other)"])
        focus_area = st.selectbox(
            "માર્ગદર્શન ક્ષેત્ર (Primary Reading Focus)", 
            ["કારકિર્દી અને ધન લાભ (Career & Wealth)", 
             "લગ્નજીવન અને સંબંધો (Love & Marriage)", 
             "સ્વાસ્થ્ય અને માનસિક શાંતિ (Health & Peace)", 
             "વાર્ષિક ભવિષ્યવાણી (Yearly Overview)"]
        )

    astrology_system = st.radio("જ્યોતિષ પદ્ધતિ (Astrology Tradition)", ["વૈદિક જ્યોતિષ (Vedic Astrology)", "વેસ્ટર્ન જ્યોતિષ (Western Astrology)"], horizontal=True)
    specific_notes = st.text_area("વિશેષ પ્રશ્ન / વિગત (Specific Question / Notes)", "કારકિર્દીમાં બદલાવ અને આગામી સમયના ગ્રહ પ્રભાવ વિશે માર્ગદર્શન આપો.")

    generate_btn = st.form_submit_button("✨ ગુજરાતી રિપોર્ટ અને PDF બનાવો")

# --- PDF Generation Helper ---
def create_pdf(name, dob_str, time_str, place, focus, system, ai_text, font_name):
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
        fontName=font_name,
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1A5276'),
        spaceAfter=3
    )
    branding_contact_style = ParagraphStyle(
        'AstrologerContact',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#5D6D7E'),
        spaceAfter=8
    )
    report_title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading2'],
        fontName=font_name,
        fontSize=13,
        leading=17,
        textColor=colors.HexColor('#2C3E50'),
        spaceBefore=6,
        spaceAfter=6
    )
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading3'],
        fontName=font_name,
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#1A5276'),
        spaceBefore=10,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#34495E')
    )

    story = []

    # 1. Astrologer Header Branding
    story.append(Paragraph("<b>જ્યોતિષાચાર્ય વિનિત પરમાર (VINITT PARMAR)</b>", branding_name_style))
    story.append(Paragraph("<b>વૈદિક જ્યોતિષ અને સચોટ ઉપાય માર્ગદર્શન</b> &nbsp;|&nbsp; <b>મોબાઇલ / WhatsApp:</b> +91 7874066576", branding_contact_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#1A5276'), spaceAfter=10))

    # 2. Client Details Section
    story.append(Paragraph("<b>વ્યક્તિગત જન્માક્ષર અને જીવન માર્ગદર્શન રિપોર્ટ</b>", report_title_style))
    
    client_meta = (
        f"<b>ગ્રાહકનું નામ:</b> {name} &nbsp;|&nbsp; <b>પદ્ધતિ:</b> {system}<br/>"
        f"<b>જન્મ તારીખ:</b> {dob_str} &nbsp;|&nbsp; <b>જન્મ સમય:</b> {time_str}<br/>"
        f"<b>જન્મ સ્થળ:</b> {place}<br/>"
        f"<b>મુખ્ય પ્રશ્ન/વિષય:</b> {focus}"
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
            story.append(Paragraph(f"<b>{header_text}</b>", section_style))
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
        st.error("⚠️ કૃપા કરીને ડાબી બાજુની પેનલમાં તમારો Google Gemini API Key દાખલ કરો.")
    else:
        with st.spinner("કુંડળીનું વિશ્લેષણ અને ગુજરાતી રિપોર્ટ તૈયાર થઈ રહ્યો છે..."):
            try:
                client = genai.Client(api_key=api_key)
                
                system_prompt = (
                    f"તમે જ્યોતિષાચાર્ય વિનિત પરમાર વતી {astrology_system} પદ્ધતિ મુજબ વિગતવાર અને સચોટ જ્યોતિષ રિપોર્ટ તૈયાર કરી રહ્યા છો. "
                    "આખો રિપોર્ટ સંપૂર્ણપણે શુદ્ધ અને સરળ ગુજરાતી ભાષામાં (Gujarati Language) લખવાનો છે. "
                    "નીચે મુજબના શીર્ષકો (##) સાથે વિશ્લેષણ તૈયાર કરો: "
                    "1. કુંડળીનું પાયાનું વિશ્લેષણ (લગ્ન ભાવ, સૂર્ય અને ચંદ્રની સ્થિતિ), "
                    "2. વર્તમાન ગ્રહ દશા અને ગોચર પ્રભાવ, "
                    f"3. {focus_area} પર વિશેષ વિશ્લેષણ અને માર્ગદર્શન, "
                    "4. સરળ અને સચોટ વૈદિક ઉપાયો, ભાગ્યશાળી રંગ, રત્ન અને શુભ વાર."
                )
                
                user_content = (
                    f"ગ્રાહકની વિગતો:\n"
                    f"- નામ: {client_name}\n"
                    f"- જન્મ તારીખ: {dob.strftime('%d-%m-%Y')}\n"
                    f"- જન્મ સમય: {formatted_time}\n"
                    f"- જન્મ સ્થળ: {birth_place}\n"
                    f"- જાતિ: {gender}\n"
                    f"- મુખ્ય વિષય: {focus_area}\n"
                    f"- પ્રશ્ન / નોંધ: {specific_notes}"
                )

                response = client.models.generate_content(
                    model=model_name,
                    contents=[system_prompt, user_content]
                )
                ai_reading = response.text

                st.success("✅ જ્યોતિષ રિપોર્ટ સફળતાપૂર્વક તૈયાર થઈ ગયો છે!")
                
                pdf_buffer = create_pdf(
                    client_name,
                    dob.strftime('%d-%m-%Y'),
                    formatted_time,
                    birth_place,
                    focus_area,
                    astrology_system,
                    ai_reading,
                    active_font
                )
                
                file_safe_name = re.sub(r'[^a-zA-Z0-9_\u0A80-\u0AFF]', '_', client_name)
                st.download_button(
                    label=f"📥 {client_name} નો ગુજરાતી PDF રિપોર્ટ ડાઉનલોડ કરો",
                    data=pdf_buffer,
                    file_name=f"{file_safe_name}_Kundali_Report.pdf",
                    mime="application/pdf"
                )
                
                with st.expander("👁️ રિપોર્ટ અહીં વાંચો (Preview Reading)", expanded=True):
                    st.markdown(ai_reading)

            except Exception as e:
                st.error(f"Error communicating with AI API: {str(e)}")

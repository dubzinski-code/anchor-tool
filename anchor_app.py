import streamlit as st
import pandas as pd
import io
import base64
import re
from fpdf import FPDF

# ==========================================
# Page Config
# ==========================================
st.set_page_config(
    page_title="מנתוני העוגן לתוכנית עבודה",
    layout="wide",
    page_icon="⚓",
    initial_sidebar_state="expanded"
)

# ==========================================
# CSS RTL
# ==========================================
st.markdown("""
<style>
body {direction: rtl; text-align: right; font-family: Arial;}
.stApp {direction: rtl;}
.stMarkdown, .stButton, .stSelectbox, .stHeader, .stSubheader, .stText, .stTable {text-align: right; direction: rtl;}
th {text-align: right !important; background-color: #e6f3ff !important;}
td {text-align: right !important;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# מסך פתיחה
# ==========================================
st.title("⚓ מנתוני 'העוגן' לתוכנית עבודה")

st.markdown("""
<div style="background-color:#eef5ff; padding:25px; border-radius:15px; border-right:6px solid #4e8cff; margin-bottom:20px;">
<h3>כלי לתכנון תוכנית עבודה כיתתית ואישית מבוססת נתונים</h3>

<p>
כלי זה נועד לסייע למחנכות לבנות תוכנית עבודה כיתתית ואישית על בסיס נתוני מיפוי "העוגן",
בהתאם לתפיסת ה־MTSS והעיצוב האוניברסלי (UDL).
</p>

<ul>
<li>הכלי תומך בקובצי CSV מקוריים של "העוגן"</li>
<li>הקובץ חייב להיות אנונימי – מספרי תלמידים בלבד</li>
<li>קובץ עם שמות תלמידים ייחסם אוטומטית</li>
</ul>

</div>
""", unsafe_allow_html=True)

# ==========================================
# פונקציות פרטיות
# ==========================================

def contains_real_names(name_series):
    for val in name_series.dropna():
        val = str(val).strip()
        if re.search(r'[א-ת]', val):
            return True
        if not val.isdigit():
            return True
        if len(val) > 4:
            return True
    return False


def load_data(file):
    try:
        df = pd.read_csv(file, header=1, encoding='utf-8')
        main_rows = df.iloc[::2].copy().reset_index(drop=True)

        col_map = {
            'Unnamed: 0': 'Name',
            'שליטה במיומנויות השפה (דבורה וכתובה) בהתאם למצופה מבני הגיל': 'Language',
            'שליטה במתמטיקה בהתאם למצופה מבני הגיל': 'Math',
            'היבטים רגשיים בהתאם למצופה מבני הגיל': 'Emotional',
            'היבטים חברתיים בהתאם למצופה מבני הגיל': 'Social',
            'היבטים התנהגותיים בהתאם למצופה מבני הגיל': 'Behavioral'
        }

        existing_cols = {k: v for k, v in col_map.items() if k in main_rows.columns}
        main_rows.rename(columns=existing_cols, inplace=True)

        return main_rows

    except Exception as e:
        st.error(f"שגיאה בטעינת הקובץ: {e}")
        return None


def analyze_challenges(row):
    challenges = []
    domain_labels = {
        'Language': 'שפה',
        'Math': 'מתמטיקה',
        'Emotional': 'רגשי',
        'Social': 'חברתי',
        'Behavioral': 'התנהגותי'
    }

    for col, label in domain_labels.items():
        if col in row and pd.notnull(row[col]) and str(row[col]).strip() != 'תקין':
            challenges.append(label)
    return challenges


# ==========================================
# PDF Generator
# ==========================================

class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, "דוח כיתתי מסכם – כלי העוגן", ln=True, align="C")


def generate_pdf(report_text):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for line in report_text.split("\n"):
        pdf.multi_cell(0, 8, line)

    output = io.BytesIO()
    pdf.output(output)
    return output.getvalue()


# ==========================================
# Sidebar
# ==========================================

with st.sidebar:
    st.header("טעינת נתונים")
    uploaded_file = st.file_uploader("טען קובץ CSV אנונימי", type=['csv'])
    st.info("הקובץ חייב להכיל מספרי תלמידים בלבד — ללא שמות")

# ==========================================
# Main Logic
# ==========================================

if uploaded_file:
    df = load_data(uploaded_file)

    if df is not None:

        if contains_real_names(df['Name']):
            st.error("⛔ הקובץ מכיל שמות תלמידים. יש להעלות קובץ אנונימי בלבד.")
            st.stop()

        df['Challenges'] = df.apply(analyze_challenges, axis=1)
        df['Num_Challenges'] = df['Challenges'].apply(len)

        # ==========================================
        # דוח כיתתי מסכם אוטומטי
        # ==========================================

        st.header("📊 דוח כיתתי מסכם")

        all_challenges = [c for sub in df['Challenges'] for c in sub]
        challenge_counts = pd.Series(all_challenges).value_counts()

        st.subheader("אתגרים מרכזיים בכיתה")
        st.table(challenge_counts)

        report_text = "דוח כיתתי מסכם:\n\n"
        for domain, count in challenge_counts.items():
            report_text += f"{domain}: {count} תלמידים\n"

        # ==========================================
        # ייצוא PDF
        # ==========================================

        pdf_bytes = generate_pdf(report_text)
        b64 = base64.b64encode(pdf_bytes).decode()

        st.markdown(
            f'<a href="data:application/pdf;base64,{b64}" download="class_report.pdf" '
            f'style="padding:10px; background:#4e8cff; color:white; border-radius:8px; text-decoration:none;">'
            f'📄 הורדת דוח כיתתי PDF</a>',
            unsafe_allow_html=True
        )

        # ==========================================
        # גרסת שיתוף מנהל
        # ==========================================

        st.markdown("---")
        st.header("👩‍💼 גרסת שיתוף מנהל")

        manager_summary = df[['Name', 'Num_Challenges']].copy()
        manager_summary.columns = ['תלמיד', 'מספר אתגרים']

        st.table(manager_summary)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            manager_summary.to_excel(writer, index=False, sheet_name='Manager_View')

        b64_excel = base64.b64encode(output.getvalue()).decode()

        st.markdown(
            f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64_excel}" '
            f'download="manager_view.xlsx" '
            f'style="padding:10px; background:#00a86b; color:white; border-radius:8px; text-decoration:none;">'
            f'📊 הורדת דוח מנהל לאקסל</a>',
            unsafe_allow_html=True
        )

        st.success("המערכת מוכנה. ניתן להוריד דוחות ולשתף מנהל.")

else:
    st.info("אנא העלי קובץ נתונים אנונימי כדי להתחיל.")

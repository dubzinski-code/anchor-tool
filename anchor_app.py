import streamlit as st
import pandas as pd
import io
import base64
from fpdf import FPDF

# ==========================================
# Page Config & CSS
# ==========================================
st.set_page_config(
    page_title="מנתוני 'העוגן' לתוכנית עבודה",
    layout="wide",
    page_icon="⚓",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
body {direction: rtl; text-align: right; font-family: 'Heebo', sans-serif;}
.stApp {direction: rtl; font-family: 'Heebo', sans-serif;}
.stMarkdown, .stButton, .stSelectbox, .stHeader, .stSubheader, .stText, .stTable {text-align: right; direction: rtl;}
th {text-align: right !important; background-color: #e6f3ff !important; color: #000 !important; border-bottom: 2px solid #4e8cff !important;}
td {text-align: right !important;}
@media print {.stSidebar, header, .stFileUploader, button, .stButton {display: none !important;}}
</style>
""", unsafe_allow_html=True)

# ==========================================
# Pedagogical Logic
# ==========================================
def get_domain_strategies(domain):
    strategies = {
        'שפה': {'school': 'הטרמת אוצר מילים...', 'home': 'קריאה משותפת...', 'tech': 'אפליקציות להקראה', 'emotional': 'חיזוק על מאמץ'},
        'מתמטיקה': {'school': 'שימוש באמצעי המחשה...', 'home': 'שילוב בחיי היומיום', 'tech': 'אפליקציות משחקיות', 'emotional': 'נטרול חרדת מתמטיקה'},
        'קשב': {'school': 'ישיבה בקדמת הכיתה...', 'home': 'סידור סביבת למידה שקטה', 'tech': 'טיימר ויזואלי', 'emotional': 'שיחות רפלקציה קצרות'},
        'רגשי': {'school': 'מרחב רגיעה בכיתה...', 'home': 'זמן איכות הורה-ילד', 'tech': 'יומן רגשות דיגיטלי', 'emotional': 'שיחות אישיות לחיזוק מסוגלות'},
        'חברתי': {'school': 'למידת עמיתים...', 'home': 'הזמנת חבר אחד הביתה', 'tech': 'קבוצות וואטסאפ כיתתיות', 'emotional': 'ניתוח אירועים חברתיים'},
        'התנהגותי': {'school': 'בניית חוזה התנהגותי אישי...', 'home': 'תיאום ציפיות אחיד', 'tech': 'אפליקציות למעקב', 'emotional': 'לימוד טכניקות הרגעה עצמית'},
        'חושי/מוטורי': {'school': 'שימוש באביזרים תחושתיים...', 'home': 'חוגי ספורט/שחייה', 'tech': 'מקלדת מותאמת', 'emotional': 'לגיטימציה לצורך בתנועה'}
    }
    return strategies.get(domain, {'school': 'התאמה אישית לפי צורך.', 'home': '-', 'tech': '-', 'emotional': '-'})

# ==========================================
# Data Processing with Name Check
# ==========================================
def load_data(file):
    try:
        try:
            df = pd.read_csv(file, header=1, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(file, header=1, encoding='cp1255')

        main_rows = df.iloc[::2].copy().reset_index(drop=True)
        detail_rows = df.iloc[1::2].copy().reset_index(drop=True)

        col_map = {
            'Unnamed: 0': 'Name',
            'שליטה במיומנויות השפה (דבורה וכתובה) בהתאם למצופה מבני הגיל': 'Language',
            'שליטה במתמטיקה בהתאם למצופה מבני הגיל': 'Math',
            'מוטיבציה והרגלי למידה בהתאם למצופה מבני הגיל': 'Motivation',
            'היבטים רגשיים בהתאם למצופה מבני הגיל': 'Emotional',
            'היבטים התנהגותיים בהתאם למצופה מבני הגיל': 'Behavioral',
            'היבטים חברתיים בהתאם למצופה מבני הגיל': 'Social',
            'תפקודי קשב ופעלתנות יתר בהתאם למצופה מבני הגיל': 'Attention',
            'תפקוד חושי - תנועתי - מרחבי בהתאם למצופה מבני הגיל': 'Sensory',
            'התלמיד מגלה עניין ו/או חוזקות בתחום ייחודי אחד או יותר': 'Strengths_Bool',
            'היבטים אישיים ו/או משפחתיים שיש לתת עליהם את הדעת': 'Family',
        }
        existing_cols = {k: v for k, v in col_map.items() if k in main_rows.columns}
        main_rows.rename(columns=existing_cols, inplace=True)

        if 'התלמיד מגלה עניין ו/או חוזקות בתחום ייחודי אחד או יותר' in detail_rows.columns:
            main_rows['Strengths_Detail'] = detail_rows['התלמיד מגלה עניין ו/או חוזקות בתחום ייחודי אחד או יותר']

        main_rows['Name'] = main_rows['Name'].fillna('ללא שם')

        # --- מנגנון חסימת שמות משודרג ---
        non_numeric_names = main_rows['Name'].astype(str).apply(lambda x: not x.strip().isdigit())
        if non_numeric_names.any():
            st.error("הקובץ מכיל שמות אמיתיים. הכלי מקבל רק מספרי תלמידים (לצורך אנונימיות).")
            return None

        return main_rows

    except Exception as e:
        st.error(f"שגיאה בטעינת הקובץ. ודאי שהקובץ הוא CSV תקין. שגיאה: {e}")
        return None

# ==========================================
# PDF & Excel Export Functions
# ==========================================
def to_excel_download_link(df, filename="plan.xlsx"):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Plan')
    processed_data = output.getvalue()
    b64 = base64.b64encode(processed_data).decode()
    return f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}" class="stButton" style="text-decoration:none; color:black; background-color:#e0e2e6; padding:8px 15px; border-radius:5px; border:1px solid #ccc; font-weight:bold;">📥 הורדת קובץ Excel</a>'

# פונקציות נוספות ליצוא PDF או דוחות כיתה/אישיים ניתן להוסיף כאן

# ==========================================
# Main App
# ==========================================
st.title("⚓ מנתוני 'העוגן' לתוכנית עבודה")
st.markdown("כלי זה מנתח את קובץ הנתונים ומפיק טיוטת תוכנית עבודה אנונימית, כיתתית ואישית.")

with st.sidebar:
    st.header("1. טעינת נתונים")
    uploaded_file = st.file_uploader("טען קובץ CSV", type=['csv'])
    st.info("הקובץ חייב להכיל מספרי תלמידים בלבד.")
    st.markdown("---")

if uploaded_file:
    df = load_data(uploaded_file)
    if df is not None:
        st.success(f"טענת {len(df)} תלמידים בהצלחה! ✅")
        st.write("כאן יוצגו דוחות כיתתיים ואישיים.")

else:
    st.info("אנא טען קובץ CSV כדי להתחיל.")


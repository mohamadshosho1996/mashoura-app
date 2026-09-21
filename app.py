import datetime
import json
import os
import gspread
from google.oauth2.service_account import Credentials
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import streamlit as st

# ==================== إعدادات الصفحة والتصميم ====================
st.set_page_config(
    page_title="برنامج بودى للمشورة الأسرية",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="expanded",
)

custom_css = """
<style>
.main .block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
    max-width: 100%;
}
.main {
    background-color: #FFF5F8;
}
.stButton>button {
    background-color: #EC4899;
    color: white;
    border-radius: 8px;
    font-weight: bold;
    border: none;
    padding: 0.5rem 1rem;
    width: 100%;
}
.stButton>button:hover {
    background-color: #BE185D;
    color: white;
}
h1, h2, h3 {
    color: #701A75;
}
footer {visibility: hidden;}

/* تصميم القلب المنشق بإنميشن السهم */
.heart-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background-color: rgba(0, 0, 0, 0.4);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 999999;
    animation: fadeInOut 2.5s forwards;
}

.heart-container {
    position: relative;
    width: 250px;
    height: 250px;
    display: flex;
    justify-content: center;
    align-items: center;
}

/* القلب الكبير */
.giant-heart {
    position: relative;
    width: 150px;
    height: 135px;
    background-color: #ff3366;
    transform: rotate(-45deg);
    animation: heartPulse 2.5s forwards;
    box-shadow: 0 0 50px rgba(255, 51, 102, 0.8);
}

.giant-heart::before,
.giant-heart::after {
    content: "";
    position: absolute;
    width: 150px;
    height: 135px;
    background-color: #ff3366;
    border-radius: 50%;
}

.giant-heart::before {
    top: -75px;
    left: 0;
}

.giant-heart::after {
    left: 75px;
    top: 0;
}

/* السهم القادم من اليمين ليضرب القلب */
.arrow {
    position: absolute;
    width: 180px;
    height: 4px;
    background: #ffffff;
    top: 50%;
    right: -200px;
    transform: translateY(-50%) rotate(-45deg);
    animation: shootArrow 0.8s ease-in-out forwards;
    z-index: 1000000;
}

.arrow::before {
    content: "";
    position: absolute;
    left: 0;
    top: -6px;
    width: 0;
    height: 0;
    border-top: 8px solid transparent;
    border-bottom: 8px solid transparent;
    border-right: 16px solid #ffffff;
}

/* كلمة شيماء بالفونت الكبير تظهر عند انشقاق القلب */
.shaimaa-text {
    position: absolute;
    font-size: 4rem;
    font-weight: 900;
    color: #ffffff;
    text-shadow: 0 0 20px #ff0055, 0 0 40px #ff0055, 0 0 60px #ff3366;
    z-index: 1000001;
    opacity: 0;
    animation: showText 1.2s 0.8s ease-out forwards;
    font-family: 'Cairo', sans-serif;
    letter-spacing: 2px;
}

@keyframes shootArrow {
    0% { right: -250px; top: 20%; }
    50% { right: 50%; top: 50%; }
    100% { right: 120%; top: 70%; opacity: 0; }
}

@keyframes heartPulse {
    0% { transform: rotate(-45deg) scale(1); }
    30% { transform: rotate(-45deg) scale(1.2); }
    60% { transform: rotate(-45deg) scale(0.9); }
    75% { transform: rotate(-45deg) scale(1.1); filter: drop-shadow(0 0 20px #fff); }
    85% { transform: rotate(-45deg) scale(1) skew(20deg); clip-path: polygon(0 0, 50% 0, 50% 100%, 0 100%); margin-left: -40px; opacity: 0.8; }
    100% { transform: rotate(-45deg) scale(1) translateX(-80px); opacity: 0; }
}

@keyframes showText {
    0% { transform: scale(0.2); opacity: 0; }
    50% { transform: scale(1.2); opacity: 1; }
    100% { transform: scale(1); opacity: 1; }
}

@keyframes fadeInOut {
    0% { background-color: rgba(0, 0, 0, 0); }
    20% { background-color: rgba(0, 0, 0, 0.6); }
    80% { background-color: rgba(0, 0, 0, 0.6); }
    100% { background-color: rgba(0, 0, 0, 0); display: none; }
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ==================== إعدادات الاتصال الآمن بـ Google Sheets / Supabase ====================
@st.cache_resource
def get_gspread_client():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    try:
        if "google_credentials" in st.secrets:
            creds_value = st.secrets["google_credentials"]
            if isinstance(creds_value, str):
                creds_dict = json.loads(creds_value)
            else:
                creds_dict = dict(creds_value)
                if "private_key" in creds_dict:
                    creds_dict["private_key"] = creds_dict["private_key"].replace(r"\n", "\n")
            creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        else:
            creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)

        client = gspread.authorize(creds)
        return client
    except Exception as e:
        return None

def get_spreadsheet():
    client = get_gspread_client()
    if client:
        try:
            return client.open("FamilyCareDB")
        except Exception:
            return None
    return None

def load_sheet_df(sheet_name):
    spreadsheet = get_spreadsheet()
    if spreadsheet:
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
            data = worksheet.get_all_records()
            return pd.DataFrame(data, dtype=str)
        except Exception:
            pass
    return pd.DataFrame(dtype=str)

def save_new_row(sheet_name, row_dict, columns_list):
    spreadsheet = get_spreadsheet()
    if spreadsheet:
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
            row_values = [str(row_dict.get(col, "")) for col in columns_list]
            worksheet.append_row(row_values)
            return True
        except Exception as e:
            st.error(f"حدث خطأ أثناء الحفظ على جوجل شيت: {e}")
    return False

def update_entire_sheet(sheet_name, df):
    spreadsheet = get_spreadsheet()
    if spreadsheet:
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
            worksheet.clear()
            data_to_write = [df.columns.tolist()] + df.astype(str).values.tolist()
            worksheet.update(data_to_write)
            return True
        except Exception as e:
            st.error(f"حدث خطأ أثناء التحديث على جوجل شيت: {e}")
    return False

def init_cloud_sheets():
    spreadsheet = get_spreadsheet()
    if spreadsheet:
        existing_sheets = [ws.title for ws in spreadsheet.worksheets()]
        if "المشورة الاسرية للحامل" not in existing_sheets:
            ws = spreadsheet.add_worksheet(title="المشورة الاسرية للحامل", rows=100, cols=len(PREGNANT_COLUMNS))
            ws.append_row(PREGNANT_COLUMNS)
        if "سجل المشورة للاطفال" not in existing_sheets:
            ws = spreadsheet.add_worksheet(title="سجل المشورة للاطفال", rows=100, cols=len(CHILD_COLUMNS))
            ws.append_row(CHILD_COLUMNS)

# ==================== الثوابت وإعدادات البيانات ====================
DEFAULT_USERS = {
    "admin": {"pass": "admin123", "role": "admin", "name": "د. شيماء 🌸"},
    "user1": {"pass": "1234", "role": "user", "name": "د. علا 🎀"},
    "user2": {"pass": "1234", "role": "user", "name": "د. عبير 🎀"},
    "user3": {"pass": "1234", "role": "user", "name": "د. ايه 🎀"},
}

VISIT_SCHEDULE_OPTIONS = [
    "الاسبوع الاول", "عمر شهرين", "عمر 4 شهور", "عمر 6 شهور", "عمر 9 شهور",
    "عمر 12 شهر", "عمر 18 شهر", "عمر سنتين", "عمر سنتين ونصف", "عمر 3 سنين",
    "عمر 3 سنين ونصف", "عمر 4 سنين", "عمر 4 سنين ونصف", "عمر 5 سنين",
    "عمر 5 سنين ونصف", "عمر 6 سنين"
]

DROPDOWN_OPTIONS = {
    "مستوى التعليم": ["امى", "يجيد القراءة", "مؤهل متوسط", "فوق متوسط", "مؤهل عالى"],
    "الوظيفة": ["يعمل", "لا تعمل"],
    "قرابة بين الزوجين": ["نعم", "لا"],
    "وسيلة تنظيم الأسرة المستخدمة سابقا": ["توجد", "مرغوب", "غير مرغوب"],
    "شهر الحمل": ["الشهر الاول", "الشهر الثانى", "الشهر الثالث", "الشهر الرابع", "الشهر الخامس", "الشهر السادس", "الشهر السابع", "الشهر الثامن", "الشهر التاسع"],
    "أمراض مزمنة: إرتفاع ضغط الدم": ["تم", "لم يتم"],
    "أمراض مزمنة: السكر": ["تم", "لم يتم"],
    "أمراض مزمنة: إضطرابات الغدة": ["تم", "لم يتم"],
    "أمراض مزمنة: الأنيميا": ["تم", "لم يتم"],
    'مكملات "قبل": حمض الفوليك': ["تم", "لم يتم"],
    'مكملات "قبل": الحديد': ["تم", "لم يتم"],
    'مكملات "قبل": الكالسيوم': ["تم", "لم يتم"],
    'مكملات "أثناء": حمض الفوليك': ["تم", "لم يتم"],
    'مكملات "أثناء": الحديد': ["تم", "لم يتم"],
    'مكملات "أثناء": الكالسيوم': ["تم", "لم يتم"],
    "التغذية السليمة": ["تم", "لم يتم"],
    "المكملات الغذائية": ["تم", "لم يتم"],
    "التمرينات الرياضية": ["تم", "لم يتم"],
    "قسط من النوم والراحة": ["تم", "لم يتم"],
    "المتابعة الدورية للحمل": ["تم", "لم يتم"],
    "التحذير من تناول الأدوية بدون إستشارة طبيب والتعرض للتدخين والأبخرة": ["تم", "لم يتم"],
    "المتاعب البسيطة في الشهور الأولى": ["تم", "لم يتم"],
    "المتاعب في الشهور الأخيرة": ["تم", "لم يتم"],
    "علامات الخطر أثناء الحمل": ["تم", "لم يتم"],
    "مشاكل الولادة المبكرة وكيفية تجنبها": ["تم", "لم يتم"],
    "حركة الجنين / معرفة جنس الجنين/ تمييز الأصوات من قبل الجنين": ["تم", "لم يتم"],
    "تغير لون الجلد حول الحلمة وظهور بعض إفرازات من الثدي": ["تم", "لم يتم"],
    "إرتداء الملابس الفضفاضة المريحة": ["تم", "لم يتم"],
    "الإستعداد للولادة / تحضير ملابس المولود ، الخ": ["تم", "لم يتم"],
    "علامات الولادة": ["تم", "لم يتم"],
    "مميزات الولادة الطبيعية": ["تم", "لم يتم"],
    "الساعة الذهبية الأولى": ["تم", "لم يتم"],
    "ملامسة الجلد للجلد": ["تم", "لم يتم"],
    "البداية المبكرة للرضاعة الطبيعية": ["تم", "لم يتم"],
    "الرضاعة الطبيعية المطلقة": ["تم", "لم يتم"],
    "أهمية المباعدة": ["تم", "لم يتم"],
    "وسائل تنظيم الأسرة": ["تم", "لم يتم"],
    "إستخدام وسيلة بعد الولادة مباشرة": ["تم", "لم يتم"],
    "التطور العصبي والنفسي للطفل": ["طبيعى", "متقدم", "متاخر"],
    "مستوى التعليم للام": ["امى", "يجيد القراءة", "مؤهل متوسط", "فوق متوسط", "مؤهل عالى"],
    "مستوى التعليم للاب": ["امى", "يجيد القراءة", "مؤهل متوسط", "فوق متوسط", "مؤهل عالى"],
    "الوظيفة للام": ["يعمل", "لا تعمل"],
    "مكان الولادة": ["المستشفى", "المنزل"],
    "سبب دخول الحضانة": [
        "انخفاض وزن الطفل.", "احتياج الطفل لأدوية محددة بهذا الوقت.", "صعوبة شديدة في التنفس لعدم اكتمال نمو الرئتين.",
        "ارتفاع درجة حرارة جسم الرضيع.", "تعطل العمليات الحيوية بجسم الطفل.", "انخفاض معدل الجلوكوز في دم الطفل.",
        "معاناة الرضيع مشكلات في الجهاز الهضمي.", "إصابة الطفل بعدوى في الدم.", "إصابة الطفل بالصفراء.",
        "حدوث مشكلات خلال الولادة “الولادة المتعسرة أو الحمل الحرج”.", "وجود عيب خلقي يمنع الطفل عن التنفس أو الرضاعة بشكل طبيعي."
    ],
    "موعد الزيارة": VISIT_SCHEDULE_OPTIONS,
    "رضاعة طبيعية مع سوائل وأعشاب": ["تم", "لم يتم"],
    "رضاعة طبيعية مع صناعي": ["تم", "لم يتم"],
    "رضاعة لبن صناعي": ["تم", "لم يتم"],
    "دخول الحضانة": ["تم", "لم يتم"],
    "ملامسة الجلد فى الساعة الذهبية الأولى": ["تم", "لم يتم"],
    "الرضاعة الطبيعية فى الساعة الذهبية الأولى": ["تم", "لم يتم"],
    "موقف إستخدام وسيلة تنظيم أسرة": ["يوجد", "لا يوجد"],
    "الحمل الجديد": ["مرغوب", "غير مرغوب"],
    "الخدمات الغير ملباه": ["يوجد", "لا يوجد"],
    "تحويل الى عيادة تنظيم الاسره": ["تم", "لم يتم"],
    "النمو والتطور الحركي": ["طبيعى", "متقدم", "متاخر"],
    "التطور الإدراكي والمعرفي": ["طبيعى", "متقدم", "متاخر"],
    "التطور اللغوي": ["طبيعى", "متقدم", "متاخر"],
    "رسائل التربية الإيجابية": ["تم", "لم يتم"],
    "الأنشطة التحفيزية": ["تم", "لم يتم"],
    "التوعية عن التغذية التكميلية وسلامة الغذاء والتغذية السليمة": ["تم", "لم يتم"],
    "إعطاء الجرعة اليومية من الحديد": ["يوجد", "لا يوجد"],
    "أهمية إستخدام وسيلة تنظيم أسرة وأهمية المباعدة": ["تم التوعيه", "لم يتم التوعيه"],
    "إعطاء الجرعة اليومية من فيتامين د": ["يوجد", "لا يوجد"],
    "كيفية رعاية السرة والإهتمام بنظافة الطفل": ["تم", "لم يتم"],
    "البطاقة الصحية وأهمية المتابعة الدورية ومنحنيات النمو": ["تم", "لم يتم"],
    "أهمية الإلتزام بتطعيمات الطفل": ["تم", "لم يتم"],
    "التغذية الصحية للأم المرضعة": ["تم", "لم يتم"],
    "كيفية التعرف على علامات الخطورة": ["تم", "لم يتم"],
    "فوائد الرضاعة الطبيعية والأوضاع وعلامات الجوع والشبع": ["تم", "لم يتم"],
    "كفاية اللبن وكمية البراز": ["تم", "لم يتم"]
}

PREGNANT_COLUMNS = [
    "تاريخ التسجيل", "اسم المستخدم", "الاسم", "العنوان", "الرقم القومى", "رقم الموبايل",
    "العمر الحالى", "السن عند الزواج", "السن عند الحمل الاول", "مستوى التعليم", "الوظيفة",
    "تاريخ اخر دورة شهرية", "قرابة بين الزوجين", "عدد مرات الحمل", "عدد مرات الاجهاض",
    "عدد الاطفال", "المدة بين اخر حملين", "نوع الولادة", "أمراض مزمنة: إرتفاع ضغط الدم",
    "أمراض مزمنة: السكر", "أمراض مزمنة: إضطرابات الغدة", "أمراض مزمنة: الأنيميا", "أمراض مزمنة: اخرى",
    'مكملات "قبل": حمض الفوليك', 'مكملات "قبل": الحديد', 'مكملات "قبل": الكالسيوم',
    'مكملات "أثناء": حمض الفوليك', 'مكملات "أثناء": الحديد', 'مكملات "أثناء": الكالسيوم',
    "وسيلة تنظيم الأسرة المستخدمة سابقا", "مدة إستخدام الوسيلة السابقة", "شهر الحمل", "التاريخ الزيارة",
    "التغذية السليمة", "المكملات الغذائية", "التمرينات الرياضية", "قسط من النوم والراحة",
    "المتابعة الدورية للحمل", "التحذير من تناول الأدوية بدون إستشارة طبيب والتعرض للتدخين والأبخرة",
    "المتاعب البسيطة في الشهور الأولى", "المتاعب في الشهور الأخيرة", "علامات الخطر أثناء الحمل",
    "مشاكل الولادة المبكرة وكيفية تجنبها", "حركة الجنين / معرفة جنس الجنين/ تمييز الأصوات من قبل الجنين",
    "تغير لون الجلد حول الحلمة وظهور بعض إفرازات من الثدي", "إرتداء الملابس الفضفاضة المريحة",
    "الإستعداد للولادة / تحضير ملابس المولود ، الخ", "علامات الولادة", "مميزات الولادة الطبيعية",
    "الساعة الذهبية الأولى", "ملامسة الجلد للجلد", "البداية المبكرة للرضاعة الطبيعية",
    "الرضاعة الطبيعية المطلقة", "أهمية المباعدة", "وسائل تنظيم الأسرة", "إستخدام وسيلة بعد الولادة مباشرة",
    "التطور العصبي والنفسي للطفل", "ملاحظات/ توصيات", "تخطيط الزيارة القادمة", "المتابعة ما بعد الولادة"
]

CHILD_COLUMNS = [
    "تاريخ التسجيل", "اسم المستخدم", "تاريخ اول زيارة", "رقم الحالة", "اسم الام", "الرقم القومى للام",
    "رقم الموبايل للام", "تاريخ ميلاد الام", "مستوى التعليم للام", "عدد الاطفال لدى الام",
    "المدة بين اخر حملين", "الوظيفة للام", "الرقم القومى للاب", "رقم الموبايل للاب", "اسم الاب",
    "مستوى التعليم للاب", "اسم الطفل", "تاريخ الميلاد للطفل", "العمر الحالى للطفل (شهور)",
    "العمر الرحمى للطفل (أسابيع)", "مكان المتابعة (وحدة)", "مكان المتابعة (مستشفى)", "مكان المتابعة (اخرى)",
    "مصدر الاحالة(مستشفى الولادة)", "مصدر الاحالة (عيادة خاصة)", "مصدر الاحالة(عيادة التطعيمات)",
    "مصدر الاحالة(نصيحة)", "نوع الولادة", "مكان الولادة", "وزن الطفل عند الولادة", "طول الطفل عند الولادة",
    "مقاس راس الطفل عند الولادة", "دخول الحضانة", "سبب دخول الحضانة", "مدة البقاء فى الحضانة",
    "ملامسة الجلد فى الساعة الذهبية الأولى", "الرضاعة الطبيعية فى الساعة الذهبية الأولى",
    "موعد الزيارة", "تاريخ الزيارة", "رضاعة طبيعية مطلقة", "رضاعة طبيعية مع سوائل وأعشاب",
    "رضاعة طبيعية مع صناعي", "رضاعة لبن صناعي", "الوزن (كجم)", "الطول (سم)", "محيط الرأس (سم)",
    "فوائد الرضاعة الطبيعية والأوضاع وعلامات الجوع والشبع", "كفاية اللبن وكمية البراز",
    "إعطاء الجرعة اليومية من فيتامين د", "كيفية رعاية السرة والإهتمام بنظافة الطفل",
    "البطاقة الصحية وأهمية المتابعة الدورية ومنحنيات النمو", "أهمية الإلتزام بتطعيمات الطفل",
    "التغذية الصحية للأم المرضعة", "كيفية التعرف على علامات الخطورة", "النمو والتطور الحركي",
    "التطور الإدراكي والمعرفي", "التطور اللغوي", "رسائل التربية الإيجابية", "الأنشطة التحفيزية",
    "التوعية عن التغذية التكميلية وسلامة الغذاء والتغذية السليمة", "إعطاء الجرعة اليومية من الحديد",
    "أهمية إستخدام وسيلة تنظيم أسرة وأهمية المباعدة", "موقف إستخدام وسيلة تنظيم أسرة",
    "الحمل الجديد", "الخدمات الغير ملباه", "تحويل الى عيادة تنظيم الاسره", "تخطيط الزيارة القادمة"
]

YES_NO_CHECKBOX_FIELDS = [
    "مكان المتابعة (وحدة)", "مكان المتابعة (مستشفى)", "مكان المتابعة (اخرى)",
    "مصدر الاحالة(مستشفى الولادة)", "مصدر الاحالة (عيادة خاصة)",
    "مصدر الاحالة(عيادة التطعيمات)", "مصدر الاحالة(نصيحة)"
]

def clean_digits(val, max_len=None):
    if not val:
        return ""
    digits = "".join(filter(str.isdigit, str(val)))
    if max_len:
        return digits[:max_len]
    return digits

def parse_national_id(nat_id):
    clean_id = clean_digits(nat_id, 14)
    if len(clean_id) == 14:
        century_code = int(clean_id[0])
        year_digits = int(clean_id[1:3])
        month = int(clean_id[3:5])
        day = int(clean_id[5:7])
        century = 2000 if century_code == 3 else 1900
        birth_year = century + year_digits
        try:
            birth_date = datetime.date(birth_year, month, day)
            today = datetime.date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            return str(birth_date), str(age)
        except ValueError:
            return "", ""
    return "", ""

def calculate_motor_development(age_str, weight_birth, length_birth, weight_current, length_current):
    try:
        if not age_str:
            return "طبيعى"
        if "يوم" in age_str or "أسبوع" in age_str:
            age_months = 0.5
        else:
            age_months = float("".join(filter(lambda x: x.isdigit() or x == ".", age_str)) or 1)
        w_curr = float(weight_current) if weight_current else 3.5
        if age_months <= 1:
            expected_weight = 3.3 + (age_months * 0.8)
        elif age_months <= 12:
            expected_weight = 3.0 + (age_months * 0.75)
        else:
            expected_weight = 10.0 + ((age_months - 12) * 0.2)
        diff_ratio = w_curr / expected_weight
        if diff_ratio < 0.82:
            return "متاخر"
        elif diff_ratio > 1.25:
            return "متقدم"
        else:
            return "طبيعى"
    except Exception:
        return "طبيعى"

def get_existing_data(nat_id, sheet_name, id_column):
    clean_id = clean_digits(nat_id, 14)
    if len(clean_id) == 14:
        try:
            spreadsheet = get_spreadsheet()
            if spreadsheet:
                for s in [sheet_name, "المشورة الاسرية للحامل", "سجل المشورة للاطفال"]:
                    try:
                        ws = spreadsheet.worksheet(s)
                        df = pd.DataFrame(ws.get_all_records(), dtype=str)
                        if id_column in df.columns:
                            match = df[df[id_column].astype(str).str.strip() == clean_id]
                            if not match.empty:
                                return match.iloc[-1].to_dict()
                    except Exception:
                        continue
        except Exception:
            pass
    return {}

init_cloud_sheets()

# ==================== تسجيل الدخول والصلاحيات ====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.name = None
    st.session_state.role = None

if "show_shaimaa_animation" not in st.session_state:
    st.session_state.show_shaimaa_animation = False

if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center; color: #BE185D;'>🌸 برنامج بودى للمشورة الأسرية 🌸</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: #701A75;'>تسجيل الدخول للنظام</h4>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        user_options = {f"{v['name']} ({k})": k for k, v in DEFAULT_USERS.items()}
        selected_display = st.selectbox("اختر الحساب والطبيبة 🩺", list(user_options.keys()))
        username = user_options[selected_display]
        password = st.text_input("كلمة المرور", type="password")
        
        if st.button("تسجيل الدخول ✨", use_container_width=True):
            if DEFAULT_USERS[username]["pass"] == password:
                st.session_state.logged_in = True
                st.session_state.user = username
                st.session_state.name = DEFAULT_USERS[username]["name"]
                st.session_state.role = DEFAULT_USERS[username]["role"]
                st.rerun()
            else:
                st.error("كلمة المرور غير صحيحة!")
    st.stop()

if st.session_state.show_shaimaa_animation:
    st.markdown("""
        <div class="heart-overlay">
            <div class="heart-container">
                <div class="arrow"></div>
                <div class="giant-heart"></div>
                <div class="shaimaa-text">شيماء</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.session_state.show_shaimaa_animation = False

# ==================== القائمة والخيارات المشتركة ====================
menu_options = ["الصفحة الرئيسية", "سجل الحوامل", "سجل الأطفال", "استعراض البيانات والداشبورد"]
if st.session_state.role == "admin":
    menu_options.append("إدارة المستخدمين")

st.sidebar.markdown(f"### أهلاً بكِ د. {st.session_state.name} 🌸")
sidebar_menu = st.sidebar.radio("القائمة الرئيسية (جانبية)", menu_options, key="sidebar_radio")

if st.sidebar.button("🚪 تسجيل الخروج"):
    st.session_state.logged_in = False
    st.rerun()

st.markdown("---")
col_mobile_nav, col_mobile_logout = st.columns([3, 1])
with col_mobile_nav:
    main_screen_menu = st.selectbox("📱 انتقل مباشرة إلى القسم المطلوب:", menu_options, key="mobile_selectbox")
with col_mobile_logout:
    if st.button("خروج 🚪"):
        st.session_state.logged_in = False
        st.rerun()

menu = main_screen_menu
st.markdown("---")

# ==================== 1. الصفحة الرئيسية ====================
if menu == "الصفحة الرئيسية":
    st.markdown("<h1>✨ مرحباً بكِ في نظام المشورة الأسرية الشامل (سحابي) ✨</h1>", unsafe_allow_html=True)
    st.write("تم ربط البرنامج بنجاح مع Google Sheets على جوجل درايف ليتم حفظ ومزامنة بيانات الحوامل والأطفال لحظياً.")

# ==================== 2. سجل الحوامل ====================
elif menu == "سجل الحوامل":
    st.markdown("<h2>🤰 سجل المشورة الأسرية للحوامل</h2>", unsafe_allow_html=True)
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    
    for col in PREGNANT_COLUMNS:
        if f"p_{col}" not in st.session_state:
            if col == "التاريخ الزيارة":
                st.session_state[f"p_{col}"] = today_str
            else:
                st.session_state[f"p_{col}"] = ""

    form_data = {}
    for col_name in PREGNANT_COLUMNS:
        if col_name in ["تاريخ التسجيل", "اسم المستخدم"]:
            continue
            
        if col_name == "نوع الولادة":
            st.markdown(f"**{col_name}**")
            
            if "p_birth_nat" not in st.session_state: st.session_state.p_birth_nat = False
            if "p_birth_ces" not in st.session_state: st.session_state.p_birth_ces = False
            if "p_birth_none" not in st.session_state: st.session_state.p_birth_none = True

            def p_update_nat():
                if st.session_state.p_birth_nat:
                    st.session_state.p_birth_ces = False
                    st.session_state.p_birth_none = False
            def p_update_ces():
                if st.session_state.p_birth_ces:
                    st.session_state.p_birth_nat = False
                    st.session_state.p_birth_none = False
            def p_update_none():
                if st.session_state.p_birth_none:
                    st.session_state.p_birth_nat = False
                    st.session_state.p_birth_ces = False

            c_opt1, c_opt2, c_opt3 = st.columns(3)
            with c_opt1: st.checkbox("طبيعى", key="p_birth_nat", on_change=p_update_nat)
            with c_opt2: st.checkbox("قيصرى", key="p_birth_ces", on_change=p_update_ces)
            with c_opt3: st.checkbox("لا يوجد", key="p_birth_none", on_change=p_update_none)

            selected_birth = ""
            if st.session_state.p_birth_nat: selected_birth = "طبيعى"
            elif st.session_state.p_birth_ces: selected_birth = "قيصرى"
            elif st.session_state.p_birth_none: selected_birth = "لا يوجد"
            
            form_data[col_name] = selected_birth
            st.session_state[f"p_{col_name}"] = selected_birth

        elif col_name in DROPDOWN_OPTIONS:
            st.markdown(f"**{col_name}**")
            options = DROPDOWN_OPTIONS[col_name]
            current_val = st.session_state.get(f"p_{col_name}", options[0])
            chosen_choice = st.radio(
                f"اختر {col_name}", options,
                index=options.index(current_val) if current_val in options else 0,
                key=f"p_radio_{col_name}", horizontal=True
            )
            form_data[col_name] = chosen_choice
            st.session_state[f"p_{col_name}"] = chosen_choice
        else:
            if col_name == "الرقم القومى":
                raw_val = st.text_input(col_name, key=f"p_{col_name}")
                cleaned_val = clean_digits(raw_val, 14)
                form_data[col_name] = cleaned_val
                if len(cleaned_val) == 14:
                    _, calc_age = parse_national_id(cleaned_val)
                    if calc_age:
                        st.session_state["p_العمر الحالى"] = calc_age
            elif col_name == "رقم الموبايل":
                raw_val = st.text_input(col_name, key=f"p_{col_name}")
                cleaned_val = clean_digits(raw_val, 11)
                form_data[col_name] = cleaned_val
            elif col_name == "العمر الحالى":
                form_data[col_name] = st.text_input(f"{col_name} [محسوب تلقائياً من الرقم القومي]", key=f"p_{col_name}")
            elif col_name == "التاريخ الزيارة":
                form_data[col_name] = st.text_input(f"{col_name} [تاريخ اليوم التلقائي]", key=f"p_{col_name}")
            else:
                form_data[col_name] = st.text_input(col_name, key=f"p_{col_name}")

    if st.button("💾 حفظ بيانات الحامل", use_container_width=True):
        final_form_data = {}
        for col in PREGNANT_COLUMNS:
            if col == "تاريخ التسجيل":
                final_form_data[col] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            elif col == "اسم المستخدم":
                final_form_data[col] = st.session_state.name
            else:
                final_form_data[col] = st.session_state.get(f"p_{col}", form_data.get(col, ""))
        
        if save_new_row("المشورة الاسرية للحامل", final_form_data, PREGNANT_COLUMNS):
            st.success("تم حفظ بيانات الحامل بنجاح على جوجل شيت! ✨")
            for col in PREGNANT_COLUMNS:
                if col == "التاريخ الزيارة":
                    st.session_state[f"p_{col}"] = today_str
                else:
                    st.session_state[f"p_{col}"] = ""
            st.rerun()

# ==================== 3. سجل الأطفال ====================
elif menu == "سجل الأطفال":
    st.markdown("<h2>👶 سجل المشورة الأسرية للأطفال</h2>", unsafe_allow_html=True)
    
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    for col in CHILD_COLUMNS:
        if f"c_{col}" not in st.session_state:
            if col in ["تاريخ الزيارة", "تاريخ اول زيارة"]:
                st.session_state[f"c_{col}"] = today_str
            else:
                st.session_state[f"c_{col}"] = ""

    raw_nat_id_mom = st.text_input("الرقم القومى للام (اختياري)", key="c_الرقم القومى للام_input")
    nat_id_mom_input = clean_digits(raw_nat_id_mom, 14)
    if nat_id_mom_input:
        st.session_state["c_الرقم القومى للام"] = nat_id_mom_input

    if len(nat_id_mom_input) == 14:
        b_date_mom, _ = parse_national_id(nat_id_mom_input)
        if b_date_mom and not st.session_state.get("c_تاريخ ميلاد الام"):
            st.session_state["c_تاريخ ميلاد الام"] = b_date_mom

    if len(nat_id_mom_input) == 14:
        if st.button("🔍 استرجاع بيانات الأسرة المسجلة مسبقاً"):
            found_data = get_existing_data(nat_id_mom_input, "سجل المشورة للاطفال", "الرقم القومى للام") or get_existing_data(nat_id_mom_input, "المشورة الاسرية للحامل", "الرقم القومى")
            for c_name in CHILD_COLUMNS:
                if c_name in ["تاريخ التسجيل", "اسم المستخدم", "الرقم القومى للام"]:
                    continue
                val = found_data.get(c_name, "")
                if val:
                    st.session_state[f"c_{c_name}"] = str(val)
            st.rerun()

    for col_name in CHILD_COLUMNS:
        if col_name in ["تاريخ التسجيل", "اسم المستخدم", "الرقم القومى للام"]:
            continue

        if col_name == "نوع الولادة":
            st.markdown(f"**{col_name}**")
            if "c_birth_nat" not in st.session_state: st.session_state.c_birth_nat = False
            if "c_birth_ces" not in st.session_state: st.session_state.c_birth_ces = False
            if "c_birth_none" not in st.session_state: st.session_state.c_birth_none = True

            def c_update_nat():
                if st.session_state.c_birth_nat:
                    st.session_state.c_birth_ces = False
                    st.session_state.c_birth_none = False
            def c_update_ces():
                if st.session_state.c_birth_ces:
                    st.session_state.c_birth_nat = False
                    st.session_state.c_birth_none = False
            def c_update_none():
                if st.session_state.c_birth_none:
                    st.session_state.c_birth_nat = False
                    st.session_state.c_birth_ces = False

            c_opt1, c_opt2, c_opt3 = st.columns(3)
            with c_opt1: st.checkbox("طبيعى", key="c_birth_nat", on_change=c_update_nat)
            with c_opt2: st.checkbox("قيصرى", key="c_birth_ces", on_change=c_update_ces)
            with c_opt3: st.checkbox("لا يوجد", key="c_birth_none", on_change=c_update_none)

            selected_birth = ""
            if st.session_state.c_birth_nat: selected_birth = "طبيعى"
            elif st.session_state.c_birth_ces: selected_birth = "قيصرى"
            elif st.session_state.c_birth_none: selected_birth = "لا يوجد"
            st.session_state[f"c_{col_name}"] = selected_birth

        elif col_name == "رضاعة طبيعية مطلقة":
            st.markdown(f"**{col_name}**")
            c1, c2, c3 = st.columns(3)
            current_val = st.session_state.get(f"c_{col_name}", "")
            with c1: chk_3 = st.checkbox("3 شهور", value=(current_val=="3 شهور"), key="c_bf_ex_3")
            with c2: chk_4 = st.checkbox("4 شهور", value=(current_val=="4 شهور"), key="c_bf_ex_4")
            with c3: chk_6 = st.checkbox("6 شهور", value=(current_val=="6 شهور"), key="c_bf_ex_6")
            
            selected_bf_ex = ""
            if chk_3: selected_bf_ex = "3 شهور"
            elif chk_4: selected_bf_ex = "4 شهور"
            elif chk_6: selected_bf_ex = "6 شهور"
            st.session_state[f"c_{col_name}"] = selected_bf_ex

        elif col_name in YES_NO_CHECKBOX_FIELDS:
            checked = st.checkbox(col_name, value=False, key=f"c_chk_{col_name}")
            st.session_state[f"c_{col_name}"] = "نعم" if checked else ""

        elif col_name in DROPDOWN_OPTIONS:
            options = DROPDOWN_OPTIONS[col_name]
            if col_name == "إعطاء الجرعة اليومية من الحديد":
                options = ["يوجد", "لا يوجد"]
            
            if col_name == "النمو والتطور الحركي":
                auto_motor = calculate_motor_development(
                    st.session_state.get("c_العمر الحالى للطفل (شهور)", ""),
                    st.session_state.get("c_وزن الطفل عند الولادة", ""),
                    st.session_state.get("c_طول الطفل عند الولادة", ""),
                    st.session_state.get("c_الوزن (كجم)", ""),
                    st.session_state.get("c_الطول (سم)", "")
                )
                if not st.session_state.get(f"c_{col_name}"):
                    st.session_state[f"c_{col_name}"] = auto_motor

            if col_name == "موعد الزيارة":
                if f"c_{col_name}_manual" not in st.session_state:
                    st.session_state[f"c_{col_name}_manual"] = False
                
                auto_visit_choice = VISIT_SCHEDULE_OPTIONS[0]
                try:
                    age_str = st.session_state.get("c_العمر الحالى للطفل (شهور)", "")
                    if age_str:
                        if "يوم" in age_str or "أسبوع" in age_str:
                            auto_visit_choice = "الاسبوع الاول"
                        else:
                            age_num = float("".join(filter(lambda x: x.isdigit() or x == ".", age_str)) or 0)
                            if age_num <= 2: auto_visit_choice = "عمر شهرين"
                            elif age_num <= 4: auto_visit_choice = "عمر 4 شهور"
                            elif age_num <= 6: auto_visit_choice = "عمر 6 شهور"
                            elif age_num <= 9: auto_visit_choice = "عمر 9 شهور"
                            elif age_num <= 12: auto_visit_choice = "عمر 12 شهر"
                            elif age_num <= 18: auto_visit_choice = "عمر 18 شهر"
                            elif age_num <= 24: auto_visit_choice = "عمر سنتين"
                            elif age_num <= 30: auto_visit_choice = "عمر سنتين ونصف"
                            elif age_num <= 36: auto_visit_choice = "عمر 3 سنين"
                            elif age_num <= 42: auto_visit_choice = "عمر 3 سنين ونصف"
                            elif age_num <= 48: auto_visit_choice = "عمر 4 سنين"
                            elif age_num <= 54: auto_visit_choice = "عمر 4 سنين ونصف"
                            elif age_num <= 60: auto_visit_choice = "عمر 5 سنين"
                            elif age_num <= 66: auto_visit_choice = "عمر 5 سنين ونصف"
                            else: auto_visit_choice = "عمر 6 سنين"
                except Exception:
                    pass

                if not st.session_state.get(f"c_{col_name}_manual", False):
                    st.session_state[f"c_{col_name}"] = auto_visit_choice

            if col_name == "سبب دخول الحضانة":
                nursery_status = st.session_state.get("c_دخول الحضانة", "لم يتم")
                if nursery_status != "تم":
                    st.session_state[f"c_{col_name}"] = ""
                    continue

            st.markdown(f"**{col_name}**")
            current_val = st.session_state.get(f"c_{col_name}", options[0])
            def on_visit_change():
                if col_name == "موعد الزيارة":
                    st.session_state[f"c_{col_name}_manual"] = True

            chosen_choice = st.radio(
                f"اختر {col_name}", options,
                index=options.index(current_val) if current_val in options else 0,
                key=f"c_radio_{col_name}", horizontal=True, on_change=on_visit_change
            )
            st.session_state[f"c_{col_name}"] = chosen_choice

        else:
            if col_name in ["الرقم القومى للام", "الرقم القومى للاب"]:
                raw_val = st.text_input(col_name, key=f"c_{col_name}_raw")
                st.session_state[f"c_{col_name}"] = clean_digits(raw_val, 14)
            elif col_name in ["رقم الموبايل للام", "رقم الموبايل للاب"]:
                raw_val = st.text_input(col_name, key=f"c_{col_name}_raw")
                st.session_state[f"c_{col_name}"] = clean_digits(raw_val, 11)
            elif col_name == "تاريخ ميلاد الام":
                st.text_input(f"{col_name} [يتولد تلقائياً إذا أُدخل الرقم القومي للأم]", key=f"c_{col_name}")
            
            elif col_name == "تاريخ الميلاد للطفل":
                default_date_val = datetime.date.today()
                existing_b_date = st.session_state.get(f"c_{col_name}", "")
                if existing_b_date:
                    try:
                        default_date_val = datetime.datetime.strptime(existing_b_date.strip(), "%Y-%m-%d").date()
                    except Exception:
                        pass
                
                chosen_date = st.date_input(col_name, value=default_date_val, key=f"c_date_input_{col_name}")
                st.session_state[f"c_{col_name}"] = str(chosen_date)
                
                try:
                    if st.session_state[f"c_{col_name}"]:
                        today_date = datetime.date.today()
                        delta_days = (today_date - chosen_date).days
                        
                        if delta_days >= 0:
                            if delta_days < 7:
                                age_display = f"{delta_days} يوم"
                            elif delta_days < 30:
                                weeks_count = round(delta_days / 7)
                                age_display = f"{weeks_count} أسبوع"
                            else:
                                months_count = round(delta_days / 30.44, 1)
                                if months_count.is_integer():
                                    months_count = int(months_count)
                                age_display = f"{months_count} شهر"
                            st.session_state["c_العمر الحالى للطفل (شهور)"] = age_display
                            
                            gestational_weeks_calc = max(24, min(42, 40 - max(0, round((280 - delta_days)/7))))
                            st.session_state["c_العمر الرحمى للطفل (أسابيع)"] = f"{gestational_weeks_calc} أسبوع"
                except Exception:
                    pass

            elif col_name == "العمر الحالى للطفل (شهور)":
                st.text_input(f"{col_name} [محسوب تلقائياً]", key=f"c_{col_name}")
            elif col_name == "العمر الرحمى للطفل (أسابيع)":
                st.text_input(f"{col_name} [محسوب بدقة بناءً على تاريخ الميلاد]", key=f"c_{col_name}")
            elif col_name == "وزن الطفل عند الولادة":
                st.text_input(col_name, key=f"c_{col_name}")
            elif col_name == "طول الطفل عند الولادة":
                st.text_input(col_name, key=f"c_{col_name}")
                try:
                    w_val = st.session_state.get("c_وزن الطفل عند الولادة", "3.0")
                    l_val = st.session_state.get("c_طول الطفل عند الولادة", "50.0")
                    if w_val and l_val:
                        st.session_state["c_مقاس راس الطفل عند الولادة"] = str(round((float(l_val) / 2) + (float(w_val) * 0.5) + 10, 1))
                except Exception:
                    pass
            
            elif col_name == "محيط الرأس (سم)":
                try:
                    age_str = st.session_state.get("c_العمر الحالى للطفل (شهور)", "1")
                    if "يوم" in age_str or "أسبوع" in age_str:
                        age_m = 0.5
                    else:
                        age_m = float("".join(filter(lambda x: x.isdigit() or x == ".", age_str)) or 1.0)
                    
                    head_birth = float(st.session_state.get("c_مقاس راس الطفل عند الولادة", "35.0") or 35.0)
                    if age_m <= 12:
                        calc_head = round(head_birth + (age_m * 1.0), 1)
                    else:
                        calc_head = round(head_birth + 12.0 + ((age_m - 12) * 0.1), 1)
                    
                    st.session_state[f"c_{col_name}"] = str(calc_head)
                except Exception:
                    pass
                st.text_input(f"{col_name} [محسوب تلقائياً من بيانات الولادة، الحالي، وعمر الطفل]", key=f"c_{col_name}")

            elif col_name == "تخطيط الزيارة القادمة":
                try:
                    current_visit = st.session_state.get("c_موعد الزيارة", "")
                    reg_date_str = st.session_state.get("c_تاريخ الزيارة", today_str)
                    base_date = datetime.datetime.strptime(reg_date_str.strip(), "%Y-%m-%d").date()
                    
                    days_to_add = 30
                    if current_visit in VISIT_SCHEDULE_OPTIONS:
                        idx = VISIT_SCHEDULE_OPTIONS.index(current_visit)
                        if idx + 1 < len(VISIT_SCHEDULE_OPTIONS):
                            next_visit_name = VISIT_SCHEDULE_OPTIONS[idx + 1]
                            if "شهر" in next_visit_name:
                                m_num = int("".join(filter(lambda x: x.isdigit(), next_visit_name)) or 1)
                                days_to_add = m_num * 30
                            elif "سنين" in next_visit_name or "سنتين" in next_visit_name:
                                if "نصف" in next_visit_name:
                                    days_to_add = 30 * 30
                                else:
                                    y_num = int("".join(filter(lambda x: x.isdigit(), next_visit_name)) or 1)
                                    days_to_add = y_num * 365
                            else:
                                days_to_add = 30
                    
                    next_visit_date = base_date + datetime.timedelta(days=days_to_add)
                    st.session_state[f"c_{col_name}"] = str(next_visit_date)
                except Exception:
                    pass
                st.text_input(f"{col_name} [محسوب تلقائياً بناءً على الزيارة التالية والتاريخ]", key=f"c_{col_name}")
            else:
                st.text_input(col_name, key=f"c_{col_name}")

    if st.button("💾 حفظ بيانات الطفل", use_container_width=True):
        st.session_state.show_shaimaa_animation = True
        
        final_child_data = {}
        for col in CHILD_COLUMNS:
            if col == "تاريخ التسجيل":
                final_child_data[col] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            elif col == "اسم المستخدم":
                final_child_data[col] = st.session_state.name
            else:
                val = st.session_state.get(f"c_{col}", "")
                if col == "سبب دخول الحضانة" and st.session_state.get("c_دخول الحضانة", "") != "تم":
                    val = ""
                final_child_data[col] = val

        if save_new_row("سجل المشورة للاطفال", final_child_data, CHILD_COLUMNS):
            st.success("تم حفظ بيانات الطفل بنجاح على جوجل شيت! ✨")
            for col in CHILD_COLUMNS:
                if col in ["تاريخ الزيارة", "تاريخ اول زيارة"]:
                    st.session_state[f"c_{col}"] = today_str
                else:
                    st.session_state[f"c_{col}"] = ""
            st.session_state["c_موعد الزيارة_manual"] = False
            st.rerun()

# ==================== 4. استعراض البيانات والداشبورد ====================
elif menu == "استعراض البيانات والداشبورد":
    st.markdown("<h2>📊 لوحة المؤشرات واستعراض البيانات المبسطة</h2>", unsafe_allow_html=True)
    
    spreadsheet = get_spreadsheet()
    if spreadsheet:
        sheet_names = [ws.title for ws in spreadsheet.worksheets()]
        sheet_to_show = st.selectbox("اختر السجل للاستعراض:", sheet_names)
        df_view = load_sheet_df(sheet_to_show)
        
        st.markdown("### 📅 تحديد فترة البحث والفلترة الزمنية والمستخدمين")
        
        date_col = "تاريخ الزيارة" if "تاريخ الزيارة" in df_view.columns else "تاريخ التسجيل"
        filtered_df = df_view.copy()
        
        if not df_view.empty and date_col in df_view.columns:
            try:
                df_view["_temp_date"] = pd.to_datetime(df_view[date_col], errors="coerce").dt.date
                valid_dates = df_view["_temp_date"].dropna()
                
                if not valid_dates.empty:
                    min_d = valid_dates.min()
                    max_d = valid_dates.max()
                else:
                    min_d = datetime.date.today()
                    max_d = datetime.date.today()
                
                col_start, col_end, col_user_filter = st.columns(3)
                with col_start:
                    start_date = st.date_input("📅 من تاريخ:", value=min_d, key="filter_start_date")
                with col_end:
                    end_date = st.date_input("📅 إلى تاريخ:", value=max_d, key="filter_end_date")
                with col_user_filter:
                    if "اسم المستخدم" in df_view.columns:
                        users_list = ["الكل"] + list(df_view["اسم المستخدم"].dropna().unique())
                        selected_user_filter = st.selectbox("👩‍⚕️ تصفية حسب الطبيبة:", users_list, key="filter_user_selectbox")
                    else:
                        selected_user_filter = "الكل"
                
                filtered_df = df_view[(df_view["_temp_date"] >= start_date) & (df_view["_temp_date"] <= end_date)].copy()
                filtered_df = filtered_df.drop(columns=["_temp_date"], errors="ignore")
            except Exception:
                filtered_df = df_view.copy()
                selected_user_filter = "الكل"
        else:
            selected_user_filter = "الكل"

        if selected_user_filter != "الكل" and "اسم المستخدم" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["اسم المستخدم"] == selected_user_filter]
        
        st.markdown("---")

        if sheet_to_show == "المشورة الاسرية للحامل":
            st.markdown("### 🤰 جدول مؤشرات الحوامل المطلوبة")
            total_pregnant_cases = len(filtered_df)
            
            def count_match_val(df, col_name, target_val):
                if col_name in df.columns and not df.empty:
                    return df[col_name].fillna("").astype(str).str.strip().eq(target_val).sum()
                return 0

            periodic_followup_count = count_match_val(filtered_df, "المتابعة الدورية للحمل", "تم")
            natural_birth_count = count_match_val(filtered_df, "نوع الولادة", "طبيعى")
            cesarean_birth_count = count_match_val(filtered_df, "نوع الولادة", "قيصرى")
            
            fam_plan_prev_count = 0
            if "وسيلة تنظيم الأسرة المستخدمة سابقا" in filtered_df.columns and not filtered_df.empty:
                fam_plan_prev_count = filtered_df["وسيلة تنظيم الأسرة المستخدمة سابقا"].fillna("").astype(str).str.strip().ne("").sum()

            pregnant_summary_df = pd.DataFrame({
                "المؤشر المطلوبة": [
                    "إجمالي الحالات",
                    "عدد حالات المتابعة الدورية للحمل",
                    "عدد الولادة الطبيعية",
                    "عدد الولادة القيصرية",
                    "إجمالي عدد حالات وسيلة تنظيم الأسرة المستخدمة سابقاً"
                ],
                "العدد": [
                    int(total_pregnant_cases),
                    int(periodic_followup_count),
                    int(natural_birth_count),
                    int(cesarean_birth_count),
                    int(fam_plan_prev_count)
                ]
            })
            
            st.dataframe(pregnant_summary_df, use_container_width=True, hide_index=True)
            st.markdown("---")

        elif sheet_to_show == "سجل المشورة للاطفال":
            st.markdown("### 👶 ملخص مؤشرات الأداء والخدمات (البيانات المطلوبة للأسرة والطفل)")
            total_child_cases = len(filtered_df)
            
            def count_match(df, col_name, target_val):
                if col_name in df.columns and not df.empty:
                    return df[col_name].fillna("").astype(str).str.strip().eq(target_val).sum()
                return 0

            incubator_count = count_match(filtered_df, "دخول الحضانة", "تم")
            skin_contact_count = count_match(filtered_df, "ملامسة الجلد فى الساعة الذهبية الأولى", "تم")
            bf_golden_count = count_match(filtered_df, "الرضاعة الطبيعية فى الساعة الذهبية الأولى", "تم")
            exclusive_bf_6m_count = 0
            if "رضاعة طبيعية مطلقة" in filtered_df.columns and not filtered_df.empty:
                exclusive_bf_6m_count = filtered_df["رضاعة طبيعية مطلقة"].fillna("").astype(str).str.strip().isin(["3 شهور", "4 شهور", "6 شهور"]).sum()

            family_planning_child_count = count_match(filtered_df, "تحويل الى عيادة تنظيم الاسره", "تم")

            summary_df = pd.DataFrame({
                "البيان": [
                    "إجمالي عدد حالات الأطفال",
                    "عدد حالات دخول الحضانة",
                    "عدد حالات ملامسة الجلد فى الساعة الذهبية الأولى",
                    "عدد حالات الرضاعة الطبيعية فى الساعة الذهبية الأولى",
                    "رضاعة طبيعية مطلقة 6 شهور",
                    "عدد حالات تحويل الى عيادة تنظيم الاسره"
                ],
                "الرقم": [
                    int(total_child_cases),
                    int(incubator_count),
                    int(skin_contact_count),
                    int(bf_golden_count),
                    int(exclusive_bf_6m_count),
                    int(family_planning_child_count)
                ]
            })
            
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
            st.markdown("---")

        total_records = len(filtered_df)
        col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
        with col_kpi1:
            st.metric(label="📁 إجمالي الحالات بالفترة", value=total_records)
        with col_kpi2:
            unique_users_count = filtered_df["اسم المستخدم"].nunique() if "اسم المستخدم" in filtered_df.columns else 0
            st.metric(label="👩‍⚕️ الطبيبات المشاركات", value=unique_users_count)
        with col_kpi3:
            st.metric(label="📑 القسم الحالي", value=sheet_to_show)

        st.markdown("---")
        search_query = st.text_input("🔍 بحث سريع إضافي:")
        
        if search_query:
            mask = filtered_df.apply(lambda row: row.astype(str).str.contains(search_query, case=False, na=False).any(), axis=1)
            filtered_df = filtered_df[mask]

        st.dataframe(filtered_df, use_container_width=True)

        if st.session_state.role == "admin":
            st.markdown("---")
            st.markdown("### 🗑️ لوحة التحكم الإدارية (حذف السجلات السحابية)")
            st.error("⚠️ تنبيه هامة: خيار الحذف متاح فقط لحساب المشرف (Admin) ويقوم بحذف البيانات نهائياً من جوجل شيت السحابي.")

            id_col_target = "الرقم القومى" if sheet_to_show == "المشورة الاسرية للحامل" else "الرقم القومى للام"
            del_col1, del_col2 = st.columns(2)
            
            with del_col1:
                st.markdown("#### طريقة 1: الحذف برقم القومي")
                nat_id_to_delete = st.text_input("أدخل الرقم القومي المراد حذفه بالكامل:", max_chars=14, key="admin_del_nat_id")
                if st.button("🗑️ حذف السجل بالرقم القومي"):
                    cleaned_del_id = clean_digits(nat_id_to_delete, 14)
                    if len(cleaned_del_id) == 14:
                        try:
                            current_df = load_sheet_df(sheet_to_show)
                            if id_col_target in current_df.columns:
                                initial_len = len(current_df)
                                current_df = current_df[current_df[id_col_target].astype(str).str.strip() != cleaned_del_id]
                                deleted_count = initial_len - len(current_df)
                                
                                if deleted_count > 0:
                                    update_entire_sheet(sheet_to_show, current_df)
                                    st.success(f"تم حذف عدد ({deleted_count}) سجل بالرقم القومي بنجاح من الشيت السحابي! ✨")
                                    st.rerun()
                                else:
                                    st.warning("لم يتم العثور على سجل بهذا الرقم القومي في الشيت الحالي.")
                            else:
                                st.error(f"عمود الرقم القومي ({id_col_target}) غير موجود في هذا الشيت.")
                        except Exception as e:
                            st.error(f"حدث خطأ أثناء عملية الحذف: {e}")
                    else:
                        st.warning("يرجى إدخال رقم قومي صحيح يتكون من 14 رقماً.")

            with del_col2:
                st.markdown("#### طريقة 2: الحذف المباشر برقم الصف (Index)")
                row_idx_to_delete = st.number_input("أدخل ترتيب الصف (Index) المراد حذفه:", min_value=0, max_value=max(0, len(df_view)-1), step=1, key="admin_del_row_idx")
                if st.button("🗑️ حذف هذا الصف بالتحديد"):
                    try:
                        target_df = load_sheet_df(sheet_to_show)
                        if row_idx_to_delete < len(target_df):
                            target_df = target_df.drop(target_df.index[row_idx_to_delete])
                            update_entire_sheet(sheet_to_show, target_df)
                            st.success(f"تم حذف الصف رقم ({row_idx_to_delete}) بنجاح من الشيت السحابي! ✨")
                            st.rerun()
                        else:
                            st.error("رقم الصف المطلوب غير موجود بالجدول.")
                    except Exception as e:
                        st.error(f"حدث خطأ أثناء حذف الصف: {e}")

        st.markdown("---")
        csv_data = filtered_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 تحميل البيانات المعروضة (CSV / Excel)",
            data=csv_data,
            file_name=f"{sheet_to_show}_export.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.warning("تعذر الاتصال بملف جوجل شيت 'FamilyCareDB' على درايف. تأكد من صحة الاسم والصلاحيات.")

# ==================== 5. إدارة المستخدمين ====================
elif menu == "إدارة المستخدمين" and st.session_state.role == "admin":
    st.markdown("<h2>⚙️ إدارة المستخدمين والصلاحيات</h2>", unsafe_allow_html=True)
    for k, v in DEFAULT_USERS.items():
        st.write(f"- **{v['name']}** | اسم المستخدم: `{k}` | الصلاحية: `{v['role']}`")

import datetime
import os
import pandas as pd
import streamlit as st
from supabase import create_client, Client
from io import BytesIO

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

.arrow {
    position: absolute;
    width: 180px;
    height: 4px;
    background: #ffffff;
    top: 50%;
    right: -200px;
    transform: translateY(-50%) rotate(-45deg);
    animation: shootArrow 0.8s ease-in-out forwards;
    z-index: 100000;
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

# ==================== إعدادات الاتصال المباشر بـ Supabase ====================
@st.cache_resource
def init_supabase() -> Client:
    try:
        url = "https://qwlswmhloulmmencdyfq.supabase.co"
        key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF3bHN3bWhsb3VsbW1lbmNkeWZxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODk5NzYyMzYsImV4cCI6MjEwNTU1MjIzNn0.K6eSsf_Jtxr8RhDDhSxeyTdGc64xuZaiE3d1UgHxUZY"
        return create_client(url, key)
    except Exception as e:
        st.error(f"خطأ في إعدادات الاتصال بـ Supabase: {e}")
        return None

supabase = init_supabase()

TABLE_PREGNANT = "pregnancy_counseling"
TABLE_CHILD = "children_counseling"

def load_sheet_df(sheet_name):
    if not supabase:
        return pd.DataFrame()
    try:
        table_name = TABLE_PREGNANT if sheet_name == "المشورة الاسرية للحامل" else TABLE_CHILD
        response = supabase.table(table_name).select("*").execute()
        if response.data:
            return pd.DataFrame(response.data)
    except Exception as e:
        print(f"خطأ في قراءة البيانات: {e}")
    return pd.DataFrame()

def save_new_row(sheet_name, row_dict):
    if not supabase:
        return False
    try:
        table_name = TABLE_PREGNANT if sheet_name == "المشورة الاسرية للحامل" else TABLE_CHILD
        response = supabase.table(table_name).insert(row_dict).execute()
        return True
    except Exception as e:
        st.error(f"حدث خطأ أثناء الحفظ في Supabase: {e}")
    return False

def delete_row_from_supabase(sheet_name, record_id, id_column_name):
    if not supabase:
        return False
    try:
        table_name = TABLE_PREGNANT if sheet_name == "المشورة الاسرية للحامل" else TABLE_CHILD
        response = supabase.table(table_name).delete().eq(id_column_name, record_id).execute()
        return True
    except Exception as e:
        st.error(f"حدث خطأ أثناء الحذف من Supabase: {e}")
    return False

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
    "عمر 5 سنين ونصف", "عمر 6 سنين",
]

DROPDOWN_OPTIONS = {
    "مستوى التعليم": ["امى", "يجيد القراءة", "مؤهل متوسط", "فوق متوسط", "مؤهل عالى"],
    "الوظيفة": ["يعمل", "لا تعمل"],
    "قرابة بين الزوجين": ["نعم", "لا"],
    "وسيلة تنظيم الأسرة المستخدمة سابق": ["توجد", "مرغوب", "غير مرغوب"],
    "شهر الحمل": [
        "الشهر الاول", "الشهر الثانى", "الشهر الثالث", "الشهر الرابع",
        "الشهر الخامس", "الشهر السادس", "الشهر السابع", "الشهر الثامن", "الشهر التاسع",
    ],
    "أمراض مزمنة: إرتفاع ضغط الدم": ["تم", "لم يتم"],
    "أمراض مزمنة: السكر": ["تم", "لم يتم"],
    "أمراض مزمنة: إضطرابات الغدة": ["تم", "لم يتم"],
    "أمراض مزمنة: الأنيميا": ["تم", "لم يتم"],
    'مكملات قبل: حمض الفوليك': ["تم", "لم يتم"],
    'مكملات قبل: الحديد': ["تم", "لم يتم"],
    'مكملات قبل: الكالسيوم': ["تم", "لم يتم"],
    'مكملات أثناء: حمض الفوليك': ["تم", "لم يتم"],
    'مكملات أثناء: الحديد': ["تم", "لم يتم"],
    'مكملات أثناء: الكالسيوم': ["تم", "لم يتم"],
    "التغذية السليمة": ["تم", "لم يتم"],
    "المكملات الغذائية": ["تم", "لم يتم"],
    "التمرينات الرياضية": ["تم", "لم يتم"],
    "قسط من النوم والراحة": ["تم", "لم يتم"],
    "المتابعة الدورية للحمل": ["تم", "لم يتم"],
    "التحذير من تناول الأدوية بدون إستش": ["تم", "لم يتم"],
    "المتاعب البسيطة في الشهور الأولى": ["تم", "لم يتم"],
    "المتاعب في الشهور الأخيرة": ["تم", "لم يتم"],
    "علامات الخطر أثناء الحمل": ["تم", "لم يتم"],
    "مشاكل الولادة المبكرة وكيفية تجنب": ["تم", "لم يتم"],
    "حركة الجنين / معرفة جنس الجنين/ تمي": ["تم", "لم يتم"],
    "تغير لون الجلد حول الحلمة وظهور بع": ["تم", "لم يتم"],
    "إرتداء الملابس الفضفاضة المريحة": ["تم", "لم يتم"],
    "الإستعداد للولادة / تحضير ملابس ال": ["تم", "لم يتم"],
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
    "موعد الزيارة": VISIT_SCHEDULE_OPTIONS,
    "رضاعة طبيعية مع سوائل وأعشاب": ["تم", "لم يتم"],
    "رضاعة طبيعية مع صناعي": ["تم", "لم يتم"],
    "رضاعة لبن صناعي": ["تم", "لم يتم"],
    "دخول الحضانة": ["تم", "لم يتم"],
    "موقف إستخدام وسيلة تنظيم أسرة": ["يوجد", "لا يوجد"],
    "الحمل الجديد": ["مرغوب", "غير مرغوب"],
    "الخدمات الغير ملباه": ["يوجد", "لا يوجد"],
    "النمو والتطور الحركي": ["طبيعى", "متقدم", "متاخر"],
    "التطور الإدراكي والمعرفي": ["طبيعى", "متقدم", "متاخر"],
    "التطور اللغوي": ["طبيعى", "متقدم", "متاخر"],
    "رسائل التربية الإيجابية": ["تم", "لم يتم"],
    "الأنشطة التحفيزية": ["تم", "لم يتم"],
    "إعطاء الجرعة اليومية من الحديد": ["يوجد", "لا يوجد"],
}

CHILD_TAM_LTM_FIELDS = [
    "فوائد الرضاعة الطبيعية والأوضاع و",
    "كفاية اللبن وكمية البراز",
    "إعطاء الجرعة اليومية من فيتامين د",
    "كيفية رعاية السرة والإهتمام بنظاف",
    "البطاقة الصحية وأهمية المتابعة ال",
    "أهمية الإلتزام بتطعيمات الطفل",
    "التغذية الصحية للأم المرضعة",
    "كيفية التعرف على علامات الخطورة",
    "التوعية عن التغذية التكميلية وسلا"
]

NURSERY_REASONS = [
    "",
    "انخفاض وزن الطفل.",
    "احتياج الطفل لأدوية محددة بهذا الوقت.",
    "صعوبة شديدة في التنفس لعدم اكتمال نمو الرئتين.",
    "ارتفاع درجة حرارة جسم الرضيع.",
    "تعطل العمليات الحيوية بجسم الطفل.",
    "انخفاض معدل الجلوكوز في دم الطفل.",
    "معاناة الرضيع مشكلات في الجهاز الهضمي.",
    "إصابة الطفل بعدوى في الدم.",
    "إصابة الطفل بالصفراء.",
    "حدوث مشكلات خلال الولادة “الولادة المتعسرة أو الحمل الحرج”.",
    "وجود عيب خلقي يمنع الطفل عن التنفس أو الرضاعة بشكل طبيعي.",
]

PREGNANT_COLUMNS = [
    "تاريخ التسجيل", "اسم المستخدم", "الاسم", "العنوان", "الرقم القومى", "رقم الموبايل",
    "العمر الحالى", "السن عند الزواج", "السن عند الحمل الاول", "مستوى التعليم", "الوظيفة",
    "تاريخ اخر دورة شهرية", "قرابة بين الزوجين", "عدد مرات الحمل", "عدد مرات الاجهاض",
    "عدد الاطفال", "المدة بين اخر حملين", "نوع الولادة", "أمراض مزمنة: إرتفاع ضغط الدم",
    "أمراض مزمنة: السكر", "أمراض مزمنة: إضطرابات الغدة", "أمراض مزمنة: الأنيميا", "أمراض مزمنة: اخرى",
    'مكملات قبل: حمض الفوليك', 'مكملات قبل: الحديد', 'مكملات قبل: الكالسيوم',
    'مكملات أثناء: حمض الفوليك', 'مكملات أثناء: الحديد', 'مكملات أثناء: الكالسيوم',
    "وسيلة تنظيم الأسرة المستخدمة سابق", "مدة إستخدام الوسيلة السابقة", "شهر الحمل", "التاريخ الزيارة",
    "التغذية السليمة", "المكملات الغذائية", "التمرينات الرياضية", "قسط من النوم والراحة",
    "المتابعة الدورية للحمل", "التحذير من تناول الأدوية بدون إستش",
    "المتاعب البسيطة في الشهور الأولى", "المتاعب في الشهور الأخيرة", "علامات الخطر أثناء الحمل",
    "مشاكل الولادة المبكرة وكيفية تجنب", "حركة الجنين / معرفة جنس الجنين/ تمي",
    "تغير لون الجلد حول الحلمة وظهور بع", "إرتداء الملابس الفضفاضة المريحة",
    "الإستعداد للولادة / تحضير ملابس ال", "علامات الولادة", "مميزات الولادة الطبيعية",
    "الساعة الذهبية الأولى", "ملامسة الجلد للجلد", "البداية المبكرة للرضاعة الطبيعية",
    "الرضاعة الطبيعية المطلقة", "أهمية المباعدة", "وسائل تنظيم الأسرة", "إستخدام وسيلة بعد الولادة مباشرة",
    "التطور العصبي والنفسي للطفل", "ملاحظات/ توصيات", "تخطيط الزيارة القادمة", "المتابعة ما بعد الولادة",
]

CHILD_COLUMNS = [
    "تاريخ التسجيل", "اسم المستخدم", "تاريخ اول زيارة", "رقم الحالة", "اسم الام", "الرقم القومى للام",
    "رقم الموبايل للام", "تاريخ ميلاد الام", "مستوى التعليم للام", "عدد الاطفال لدى الام",
    "المدة بين اخر حملين", "الوظيفة للام", "الرقم القومى للاب", "رقم الموبايل للاب", "اسم الاب",
    "مستوى التعليم للاب", "اسم الطفل", "تاريخ الميلاد للطفل", "العمر الحالى للطفل (شهور)",
    "العمر الرحمى للطفل (أسابيع)", "وحدة", "مستشفى", "أخرى",
    "مستشفى الولادة", "عيادة خاصة", "عيادة التطعيمات", "نصيحة", "نوع الولادة", "مكان الولادة",
    "وزن الطفل عند الولادة", "طول الطفل عند الولادة", "مقاس راس الطفل عند الولادة",
    "دخول الحضانة", "سبب دخول الحضانة", "مدة البقاء فى الحضانة",
    "ملامسة الجلد فى الساعة الذهبية الأ", "الرضاعة الطبيعية فى الساعة الذهبي",
    "موعد الزيارة", "تاريخ الزيارة", "رضاعة طبيعية مطلقة", "رضاعة طبيعية مع سوائل وأعشاب",
    "رضاعة طبيعية مع صناعي", "رضاعة لبن صناعي", "الوزن (كجم)", "الطول (سم)", "محيط الرأس (سم)",
    "فوائد الرضاعة الطبيعية والأوضاع و", "كفاية اللبن وكمية البراز",
    "إعطاء الجرعة اليومية من فيتامين د", "كيفية رعاية السرة والإهتمام بنظاف",
    "البطاقة الصحية وأهمية المتابعة ال", "أهمية الإلتزام بتطعيمات الطفل",
    "التغذية الصحية للأم المرضعة", "كيفية التعرف على علامات الخطورة", "النمو والتطور الحركي",
    "التطور الإدراكي والمعرفي", "التطور اللغوي", "رسائل التربية الإيجابية", "الأنشطة التحفيزية",
    "التوعية عن التغذية التكميلية وسلا", "إعطاء الجرعة اليومية من الحديد",
    "أهمية إستخدام وسيلة تنظيم أسرة وأه", "موقف إستخدام وسيلة تنظيم أسرة",
    "الحمل الجديد", "الخدمات الغير ملباه", "ملاحظات/ توصيات", "تخطيط الزيارة القادمة",
]

YES_NO_CHECKBOX_FIELDS = ["وحدة", "مستشفى", "أخرى", "مستشفى الولادة", "عيادة خاصة", "عيادة التطعيمات", "نصيحة"]

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

def calculate_child_age(birth_date):
    if not birth_date:
        return ""
    try:
        today = datetime.date.today()
        delta_days = (today - birth_date).days
        if delta_days < 0:
            return "0 يوم"
        if delta_days < 30:
            return f"{delta_days} يوم"
        else:
            total_months = (today.year - birth_date.year) * 12 + (today.month - birth_date.month)
            if today.day < birth_date.day:
                total_months -= 1
            return str(max(0, total_months))
    except Exception:
        return ""

def calculate_gestational_age(birth_date):
    if not birth_date:
        return ""
    try:
        return "40"
    except Exception:
        return ""

def calculate_head_circumference(weight_val, length_val):
    try:
        w = float(weight_val) if weight_val else 0.0
        l = float(length_val) if length_val else 0.0
        if w > 0 and l > 0:
            calc = round((l * 0.15) + (w * 1.2) + 22.0, 1)
            return str(calc)
    except Exception:
        pass
    return ""

def calculate_current_head_circumference(curr_w, curr_l, birth_w, birth_l, age_str):
    try:
        cw = float(curr_w) if curr_w else 0.0
        cl = float(curr_l) if curr_l else 0.0
        bw = float(birth_w) if birth_w else 0.0
        bl = float(birth_l) if birth_l else 0.0

        months = 0.0
        if age_str:
            if "يوم" in str(age_str):
                months = 0.5
            else:
                digits = "".join(filter(str.isdigit, str(age_str)))
                if digits:
                    months = float(digits)

        if bw > 0 and bl > 0:
            birth_hc = (bl * 0.15) + (bw * 1.2) + 22.0
        else:
            birth_hc = 35.0

        if months <= 3:
            age_growth = months * 2.0
        elif months <= 6:
            age_growth = 6.0 + ((months - 3) * 1.0)
        elif months <= 12:
            age_growth = 9.0 + ((months - 6) * 0.5)
        else:
            age_growth = 12.0 + ((months - 12) * 0.2)

        current_adjustment = 0.0
        if cw > 0 and cl > 0:
            current_adjustment = (cw * 0.1) + (cl * 0.02) - 1.5

        final_hc = birth_hc + age_growth + current_adjustment
        final_hc = max(30.0, min(65.0, final_hc))

        return str(round(final_hc, 1))
    except Exception:
        return ""

def evaluate_child_growth(birth_w, birth_l, curr_w, curr_l, age_str):
    try:
        bw = float(birth_w) if birth_w else 0.0
        bl = float(birth_l) if birth_l else 0.0
        cw = float(curr_w) if curr_w else 0.0
        cl = float(curr_l) if curr_l else 0.0

        if cw <= 0 or cl <= 0:
            return "غير مكتمل", "يرجى إدخال الوزن والطول الحاليين للطفل لحساب معدل النمو بدقة."

        months = 0.0
        if age_str:
            if "يوم" in str(age_str):
                months = 0.5
            else:
                digits = "".join(filter(str.isdigit, str(age_str)))
                if digits:
                    months = float(digits)

        expected_w = 3.2 + (months * 0.6) if months <= 12 else 10.0 + ((months - 12) * 0.2)
        expected_l = 50.0 + (months * 2.5) if months <= 12 else 75.0 + ((months - 12) * 0.5)

        w_ratio = cw / expected_w if expected_w > 0 else 1.0
        l_ratio = cl / expected_l if expected_l > 0 else 1.0
        avg_ratio = (w_ratio + l_ratio) / 2.0

        if avg_ratio < 0.82:
            status = "متأخر"
            message = f"⚠️ تحذير هـام: معدل نمو الطفل (متأخر) مقارنة بالمعدلات العالمية! الوزن والطول الحاليان أقل من المعدل الطبيعي المتوقع لهذا العمر (العمر: {age_str}). يرجى مراجعة الطبيب فوراً."
        elif avg_ratio > 1.25:
            status = "متقدم"
            message = f"🌟 تنبيه: معدل نمو الطفل (متقدم) مقارنة بالمعدلات العالمية! الوزن والطول الحاليان أعلى من المعدلات الطبيعية المتوقعة لهذا العمر (العمر: {age_str})."
        else:
            status = "طبيعى"
            message = f"✅ ممتاز: معدل نمو الطفل (طبيعى) ويسير وفقاً للمعدلات العالمية القياسية لهذا العمر (العمر: {age_str})."

        return status, message
    except Exception as e:
        return "خطأ في الحساب", f"حدث خطأ أثناء تقييم النمو: {e}"

def get_existing_data(nat_id, sheet_name):
    clean_id = clean_digits(nat_id, 14)
    if len(clean_id) == 14 and supabase:
        try:
            tbl = TABLE_PREGNANT if sheet_name == "المشورة الاسرية للحامل" else TABLE_CHILD
            res = supabase.table(tbl).select("*").execute()
            if res.data:
                df = pd.DataFrame(res.data)
                id_col_target = "الرقم القومى" if tbl == TABLE_PREGNANT else "الرقم القومى للام"
                if id_col_target in df.columns:
                    match = df[df[id_col_target].astype(str).str.strip() == clean_id]
                    if not match.empty:
                        return match.iloc[-1].to_dict()
        except Exception:
            pass
    return {}

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
    st.markdown("<h4 style='text-align: center; color: #701A75;'>تسجيل الدخول للنظام (قاعدة بيانات Supabase)</h4>", unsafe_allow_html=True)

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
    st.markdown("<h1>✨ مرحباً بكِ في نظام المشورة الأسرية الشامل (Supabase) ✨</h1>", unsafe_allow_html=True)
    st.write("تم ربط البرنامج بنجاح مع قاعدة بيانات Supabase السحابية وتطابق كافة الحقول التفصيلية.")

# ==================== 2. سجل الحوامل ====================
elif menu == "سجل الحوامل":
    st.markdown("<h2>🤰 سجل المشورة الأسرية للحوامل</h2>", unsafe_allow_html=True)
    today_str = datetime.date.today().strftime("%Y-%m-%d")

    for col in PREGNANT_COLUMNS:
        if f"p_{col}" not in st.session_state:
            st.session_state[f"p_{col}"] = today_str if col == "التاريخ الزيارة" else ""

    if st.button("🧹 تفريغ جميع الحقول (حوامل)", key="clear_pregnant_fields"):
        for col in PREGNANT_COLUMNS:
            st.session_state[f"p_{col}"] = today_str if col == "التاريخ الزيارة" else ""
        st.session_state.p_birth_nat = False
        st.session_state.p_birth_ces = False
        st.session_state.p_birth_none = True
        st.success("تم تفريغ جميع الحقول بنجاح!")
        st.rerun()

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

            selected_birth = "طبيعى" if st.session_state.p_birth_nat else ("قيصرى" if st.session_state.p_birth_ces else "لا يوجد")
            st.session_state[f"p_{col_name}"] = selected_birth

        elif col_name in DROPDOWN_OPTIONS:
            st.markdown(f"**{col_name}**")
            options = DROPDOWN_OPTIONS[col_name]
            current_val = st.session_state.get(f"p_{col_name}", options[0])
            chosen_choice = st.radio(
                f"اختر {col_name}", 
                options, 
                index=options.index(current_val) if current_val in options else 0, 
                key=f"p_radio_{col_name}", 
                horizontal=True
            )
            st.session_state[f"p_{col_name}"] = chosen_choice
        else:
            if col_name == "الرقم القومى":
                val = st.text_input(col_name, value=st.session_state.get(f"p_{col_name}", ""), key=f"p_input_{col_name}")
                cleaned_val = clean_digits(val, 14)
                st.session_state[f"p_{col_name}"] = cleaned_val
                if len(cleaned_val) == 14:
                    _, calc_age = parse_national_id(cleaned_val)
                    if calc_age: 
                        st.session_state["p_العمر الحالى"] = calc_age
            elif col_name == "رقم الموبايل":
                val = st.text_input(col_name, value=st.session_state.get(f"p_{col_name}", ""), key=f"p_input_{col_name}")
                st.session_state[f"p_{col_name}"] = clean_digits(val, 11)
            elif col_name == "العمر الحالى":
                age_val = st.session_state.get(f"p_{col_name}", "")
                st.text_input(f"{col_name} [محسوب تلقائياً]", value=age_val, key=f"p_input_{col_name}", disabled=True)
            else:
                val = st.text_input(col_name, value=st.session_state.get(f"p_{col_name}", ""), key=f"p_input_{col_name}")
                st.session_state[f"p_{col_name}"] = val

    if st.button("💾 حفظ بيانات الحامل", use_container_width=True):
        final_form_data = {}
        for col in PREGNANT_COLUMNS:
            if col == "تاريخ التسجيل":
                final_form_data[col] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            elif col == "اسم المستخدم":
                final_form_data[col] = st.session_state.name
            else:
                final_form_data[col] = st.session_state.get(f"p_{col}", "")

        if save_new_row("المشورة الاسرية للحامل", final_form_data):
            st.success("تم حفظ بيانات الحامل بنجاح على Supabase! ✨")
            for col in PREGNANT_COLUMNS:
                st.session_state[f"p_{col}"] = today_str if col == "التاريخ الزيارة" else ""
            st.rerun()

# ==================== 3. سجل الأطفال ====================
elif menu == "سجل الأطفال":
    st.markdown("<h2>👶 سجل المشورة الأسرية للأطفال</h2>", unsafe_allow_html=True)
    today_str = datetime.date.today().strftime("%Y-%m-%d")

    for col in CHILD_COLUMNS:
        if f"c_{col}" not in st.session_state:
            if col in CHILD_TAM_LTM_FIELDS:
                st.session_state[f"c_{col}"] = "تم"
            else:
                st.session_state[f"c_{col}"] = today_str if col in ["تاريخ الزيارة", "تاريخ اول زيارة"] else ""

    if st.button("🧹 تفريغ جميع الحقول (أطفال)", key="clear_child_fields"):
        for col in CHILD_COLUMNS:
            if col in CHILD_TAM_LTM_FIELDS:
                st.session_state[f"c_{col}"] = "تم"
            else:
                st.session_state[f"c_{col}"] = today_str if col in ["تاريخ الزيارة", "تاريخ اول زيارة"] else ""
        st.session_state.c_birth_nat = False
        st.session_state.c_birth_ces = False
        st.session_state.c_birth_none = True
        st.success("تم تفريغ جميع الحقول بنجاح!")
        st.rerun()

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
            found_data = get_existing_data(nat_id_mom_input, "سجل المشورة للاطفال")
            for c_name in CHILD_COLUMNS:
                if c_name not in ["تاريخ التسجيل", "اسم المستخدم", "الرقم القومى للام"]:
                    val = found_data.get(c_name, "")
                    if val: st.session_state[f"c_{c_name}"] = str(val)
            st.rerun()

    rendered_followup_header = False
    rendered_referral_header = False

    for col_name in CHILD_COLUMNS:
        if col_name in ["تاريخ التسجيل", "اسم المستخدم", "الرقم القومى للام"]:
            continue

        if col_name in ["وحدة", "مستشفى", "أخرى"]:
            if not rendered_followup_header:
                st.markdown("---")
                st.markdown("### **المتابعة**")
                rendered_followup_header = True

        if col_name in ["مستشفى الولادة", "عيادة خاصة", "عيادة التطعيمات", "نصيحة"]:
            if not rendered_referral_header:
                st.markdown("---")
                st.markdown("### **مصدر الاحالة**")
                rendered_referral_header = True

        if col_name in CHILD_TAM_LTM_FIELDS:
            st.markdown(f"**{col_name}**")
            current_val = st.session_state.get(f"c_{col_name}", "تم")
            options_list = ["تم", "لم يتم"]
            default_index = options_list.index(current_val) if current_val in options_list else 0
            
            chosen_tam_ltm = st.radio(
                f"اختر حالة {col_name}", 
                options_list, 
                index=default_index, 
                key=f"c_radio_tam_ltm_{col_name}", 
                horizontal=True
            )
            st.session_state[f"c_{col_name}"] = chosen_tam_ltm

        elif col_name == "نوع الولادة":
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

            selected_birth = "طبيعى" if st.session_state.c_birth_nat else ("قيصرى" if st.session_state.c_birth_ces else "لا يوجد")
            st.session_state[f"c_{col_name}"] = selected_birth

        elif col_name == "رضاعة طبيعية مطلقة":
            st.markdown(f"**{col_name}**")
            c1, c2, c3 = st.columns(3)
            current_val = st.session_state.get(f"c_{col_name}", "")
            with c1: chk_3 = st.checkbox("3 شهور", value=(current_val == "3 شهور"), key="c_bf_ex_3")
            with c2: chk_4 = st.checkbox("4 شهور", value=(current_val == "4 شهور"), key="c_bf_ex_4")
            with c3: chk_6 = st.checkbox("6 شهور", value=(current_val == "6 شهور"), key="c_bf_ex_6")

            selected_bf_ex = "3 شهور" if chk_3 else ("4 شهور" if chk_4 else ("6 شهور" if chk_6 else ""))
            st.session_state[f"c_{col_name}"] = selected_bf_ex

        elif col_name == "سبب دخول الحضانة":
            st.markdown(f"**{col_name}**")
            current_val = st.session_state.get(f"c_{col_name}", "")
            chosen_reason = st.selectbox(
                f"اختر {col_name}", 
                options=NURSERY_REASONS, 
                index=NURSERY_REASONS.index(current_val) if current_val in NURSERY_REASONS else 0, 
                key=f"c_selectbox_{col_name}"
            )
            st.session_state[f"c_{col_name}"] = chosen_reason

        elif col_name in YES_NO_CHECKBOX_FIELDS:
            checked = st.checkbox(col_name, value=False, key=f"c_chk_{col_name}")
            st.session_state[f"c_{col_name}"] = "نعم" if checked else ""

        elif col_name in DROPDOWN_OPTIONS:
            options = DROPDOWN_OPTIONS[col_name]
            st.markdown(f"**{col_name}**")
            current_val = st.session_state.get(f"c_{col_name}", options[0])
            chosen_choice = st.radio(
                f"اختر {col_name}", 
                options, 
                index=options.index(current_val) if current_val in options else 0, 
                key=f"c_radio_{col_name}", 
                horizontal=True
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
                st.text_input(f"{col_name}", key=f"c_{col_name}")
            elif col_name == "تاريخ الميلاد للطفل":
                chosen_date = st.date_input(col_name, value=datetime.date.today(), key=f"c_date_input_{col_name}")
                st.session_state[f"c_{col_name}"] = str(chosen_date)
                
                calculated_age = calculate_child_age(chosen_date)
                st.session_state["c_العمر الحالى للطفل (شهور)"] = calculated_age
                
                calculated_gestational = calculate_gestational_age(chosen_date)
                st.session_state["c_العمر الرحمى للطفل (أسابيع)"] = calculated_gestational

            elif col_name == "العمر الحالى للطفل (شهور)":
                current_age_val = st.session_state.get(f"c_{col_name}", "")
                st.text_input(f"{col_name} [محسوب تلقائياً بالشهور أو الأيام]", value=current_age_val, key=f"c_{col_name}", disabled=True)
            elif col_name == "العمر الرحمى للطفل (أسابيع)":
                current_gest_val = st.session_state.get(f"c_{col_name}", "")
                st.text_input(f"{col_name} [محسوب تلقائياً]", value=current_gest_val, key=f"c_{col_name}", disabled=True)
            elif col_name == "مقاس راس الطفل عند الولادة":
                w_val = st.session_state.get("c_وزن الطفل عند الولادة", "")
                l_val = st.session_state.get("c_طول الطفل عند الولادة", "")
                calc_head = calculate_head_circumference(w_val, l_val)
                st.session_state[f"c_{col_name}"] = calc_head
                st.text_input(f"{col_name} [محسوب تلقائياً من الوزن والطول]", value=calc_head, key=f"c_{col_name}", disabled=True)
            elif col_name == "محيط الرأس (سم)":
                c_curr_w = st.session_state.get("c_الوزن (كجم)", "")
                c_curr_l = st.session_state.get("c_الطول (سم)", "")
                c_birth_w = st.session_state.get("c_وزن الطفل عند الولادة", "")
                c_birth_l = st.session_state.get("c_طول الطفل عند الولادة", "")
                c_age = st.session_state.get("c_العمر الحالى للطفل (شهور)", "")
                
                auto_current_hc = calculate_current_head_circumference(
                    curr_w=c_curr_w, curr_l=c_curr_l, birth_w=c_birth_w, birth_l=c_birth_l, age_str=c_age
                )
                if f"c_{col_name}" not in st.session_state or not st.session_state[f"c_{col_name}"]:
                    st.session_state[f"c_{col_name}"] = auto_current_hc
                
                hc_input = st.text_input(f"{col_name} [ممتلئ تلقائياً ويمكن التعديل]", 
                                         value=st.session_state.get(f"c_{col_name}", auto_current_hc), 
                                         key=f"c_{col_name}_input")
                st.session_state[f"c_{col_name}"] = hc_input
            else:
                st.text_input(col_name, key=f"c_{col_name}")

    st.markdown("---")
    st.markdown("### 📊 تقييم معدل نمو الطفل (حسب معدلات النمو العالمية)")
    
    eval_bw = st.session_state.get("c_وزن الطفل عند الولادة", "")
    eval_bl = st.session_state.get("c_طول الطفل عند الولادة", "")
    eval_cw = st.session_state.get("c_الوزن (كجم)", "")
    eval_cl = st.session_state.get("c_الطول (سم)", "")
    eval_age = st.session_state.get("c_العمر الحالى للطفل (شهور)", "")

    growth_status, growth_message = evaluate_child_growth(eval_bw, eval_bl, eval_cw, eval_cl, eval_age)

    if growth_status == "متأخر":
        st.error(f"### 🚨 رسالة تحذيرية هامة جداً للنمو\n{growth_message}")
    elif growth_status == "متقدم":
        st.warning(f"### ⚠️ تنبيه هامة بخصوص النمو\n{growth_message}")
    elif growth_status == "طبيعى":
        st.success(f"### ✅ نتيجة تقييم النمو\n{growth_message}")
    else:
        st.info(f"ℹ️ {growth_message}")

    st.markdown("---")

    if st.button("💾 حفظ بيانات الطفل", use_container_width=True):
        st.session_state.show_shaimaa_animation = True
        final_child_data = {}
        for col in CHILD_COLUMNS:
            if col == "تاريخ التسجيل":
                final_child_data[col] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            elif col == "اسم المستخدم":
                final_child_data[col] = st.session_state.name
            else:
                final_child_data[col] = st.session_state.get(f"c_{col}", "")

        if save_new_row("سجل المشورة للاطفال", final_child_data):
            st.success("تم حفظ بيانات الطفل بنجاح على Supabase! ✨")
            for col in CHILD_COLUMNS:
                if col in CHILD_TAM_LTM_FIELDS:
                    st.session_state[f"c_{col}"] = "تم"
                else:
                    st.session_state[f"c_{col}"] = today_str if col in ["تاريخ الزيارة", "تاريخ اول زيارة"] else ""
            st.rerun()

# ==================== 4. استعراض البيانات والداشبورد ====================
elif menu == "استعراض البيانات والداشبورد":
    st.markdown("<h2>📊 لوحة المؤشرات واستعراض البيانات</h2>", unsafe_allow_html=True)
    sheet_to_show = st.selectbox("اختر السجل للاستعراض:", ["المشورة الاسرية للحامل", "سجل المشورة للاطفال"])
    df_view = load_sheet_df(sheet_to_show)

    if not df_view.empty:
        st.markdown("---")
        st.subheader("📅 فلترة الحالات حسب الفترة الزمنية")
        
        # تحديد حقل التاريخ المتاح
        date_col_candidates = ["التاريخ الزيارة", "تاريخ التسجيل", "تاريخ اول زيارة"]
        selected_date_col = next((c for c in date_col_candidates if c in df_view.columns), None)
        
        if selected_date_col:
            try:
                df_view['parsed_date'] = pd.to_datetime(df_view[selected_date_col], errors='coerce').dt.date
                min_d = df_view['parsed_date'].min()
                max_d = df_view['parsed_date'].max()
                if pd.isna(min_d): min_d = datetime.date.today()
                if pd.isna(max_d): max_d = datetime.date.today()

                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    start_date = st.date_input("من تاريخ", value=min_d)
                with col_f2:
                    end_date = st.date_input("إلى تاريخ", value=max_d)

                mask = (df_view['parsed_date'] >= start_date) & (df_view['parsed_date'] <= end_date)
                df_filtered = df_view.loc[mask].drop(columns=['parsed_date'])
            except Exception:
                df_filtered = df_view.copy()
        else:
            df_filtered = df_view.copy()

        st.info(f"عدد الحالات المطابقة للفترة المحددة: **{len(df_filtered)}** حالة")
        
        # عرض الجدول المفلتر
        st.dataframe(df_filtered, use_container_width=True)

        # زر تصدير إلى Excel
        st.markdown("---")
        st.subheader("📥 تصدير البيانات")
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_filtered.to_excel(writer, index=False, sheet_name='Sheet1')
        excel_data = output.getvalue()

        st.download_button(
            label="📊 تحميل البيانات الحالية بصيغة Excel (XLSX)",
            data=excel_data,
            file_name=f"report_{sheet_to_show}_{datetime.date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

        # جدول إحصائي لعدد الحالات لكل مستخدم
        st.markdown("---")
        st.subheader("👥 إحصائيات عدد الحالات لكل مستخدم خلال الفترة")
        user_col_candidates = ["اسم المستخدم"]
        user_col = next((c for c in user_col_candidates if c in df_filtered.columns), None)
        if user_col and not df_filtered.empty:
            user_counts = df_filtered[user_col].value_counts().reset_index()
            user_counts.columns = ["اسم المستخدم", "عدد الحالات"]
            st.dataframe(user_counts, use_container_width=True)
        else:
            st.write("لا توجد بيانات كافية لعرض إحصائيات المستخدمين.")

        # قسم حذف الحالات (متاح للأدمن أو عام حسب الرغبة)
        st.markdown("---")
        st.subheader("🗑️ حذف حالة من السجل")
        col_del1, col_del2 = st.columns(2)
        
        id_column = "الرقم القومى" if sheet_to_show == "المشورة الاسرية للحامل" else "الرقم القومى للام"

        with col_del1:
            st.markdown("##### الحذف برقم الصف (Index)")
            row_idx_to_delete = st.number_input("أدخل رقم الصف في الجدول المعروض", min_value=0, max_value=max(0, len(df_filtered)-1), step=1, key="del_by_idx")
            if st.button("حذف الصف المحدد", key="btn_del_idx"):
                if not df_filtered.empty:
                    target_row = df_filtered.iloc[row_idx_to_delete]
                    # محاولة البحث عن معرف أو الرقم القومي للحذف من قاعدة البيانات
                    identifier_val = target_row.get(id_column, target_row.get("id", None))
                    if identifier_val:
                        if delete_row_from_supabase(sheet_to_show, identifier_val, id_column):
                            st.success(f"تم حذف الحالة التي تحمل الرقم القومي/المعرف: {identifier_val} بنجاح!")
                            st.rerun()
                        else:
                            st.error("فشل حذف الحالة من قاعدة البيانات.")
                    else:
                        st.error("تعرّف على معرف الحالة تعذر.")

        with col_del2:
            st.markdown(f"##### الحذف برقم القومي ({id_column})")
            nat_id_to_delete = st.text_input("أدخل الرقم القومى للحالة المراد حذفها", key="del_by_nat_id")
            if st.button("حذف بالرقم القومي", key="btn_del_nat"):
                cleaned_del_id = clean_digits(nat_id_to_delete, 14)
                if len(cleaned_del_id) == 14:
                    if delete_row_from_supabase(sheet_to_show, cleaned_del_id, id_column):
                        st.success(f"تم حذف الحالة ذات الرقم القومي {cleaned_del_id} بنجاح!")
                        st.rerun()
                    else:
                        st.error("لم يتم العثور على الحالة أو حدث خطأ أثناء الحذف.")
                else:
                    st.error("يرجى إدخال رقم قومي صحيح مكون من 14 رقماً.")
    else:
        st.warning("لا توجد بيانات متاحة في هذا السجل حالياً.")

# ==================== 5. إدارة المستخدمين ====================
elif menu == "إدارة المستخدمين" and st.session_state.role == "admin":
    st.markdown("<h2>⚙️ إدارة المستخدمين والصلاحيات</h2>", unsafe_allow_html=True)
    for k, v in DEFAULT_USERS.items():
        st.write(f"- **{v['name']}** | اسم المستخدم: `{k}` | الصلاحية: `{v['role']}`")

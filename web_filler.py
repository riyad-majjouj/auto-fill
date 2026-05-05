import os
import platform
import subprocess
import keyboard
from playwright.sync_api import sync_playwright

def unlock_arabic_fields(page):
    try:
        page.evaluate("""
            document.querySelectorAll('input[readonly], textarea[readonly], select[readonly]').forEach(el => {
                el.removeAttribute('readonly');
                el.removeAttribute('disabled');
            });
        """)
    except: pass

def wait_for_shortcut():
    print("⏳ بانتظار (Ctrl+Alt+M) للبدء...")
    keyboard.wait('ctrl+alt+m')
    print("🚀 جاري الحقن...")

def handle_download(download):
    download_folder = os.path.join(os.path.expanduser("~"), "Downloads")
    file_path = os.path.join(download_folder, "Document_Auto.pdf")
    download.save_as(file_path)
    print(f"✅ تم تحميل الملف: {file_path}")
    try:
        if platform.system() == 'Windows': os.startfile(file_path)
    except: pass

# ==========================================
# منطق البطاقة الوطنية (CNIE)
# ==========================================
def smart_fill_input_cnie(page, label_text, value):
    if not value: return
    try:
        container = page.locator(".cnie-form-group").filter(has_text=label_text).first
        container.locator("input").first.fill(value, force=True)
    except: pass

def smart_select_dropdown_cnie(page, label_text, value):
    if not value: return
    try:
        container = page.locator(".cnie-form-group").filter(has_text=label_text).first
        container.locator(".ui-dropdown-trigger").first.click(force=True)
        option = page.locator("li").filter(has_text=value).first
        option.wait_for(state="visible", timeout=3000)
        option.click(force=True)
        page.wait_for_timeout(1000) 
    except: pass

def fill_cnie_site(page, data, mode):
    is_first_time = "First Time" in mode
    if "cnie.ma" not in page.url: page.goto("https://www.cnie.ma")
    
    print("\n📢 1. افتح (معلومات شخصية) واضغط Ctrl+Alt+M")
    wait_for_shortcut()
    unlock_arabic_fields(page)
    
    if data.get("n_cine") and not is_first_time: 
        try: page.locator("input[formcontrolname='n_cine']").first.fill(data["n_cine"], force=True)
        except: pass
        
    smart_fill_input_cnie(page, "الإسم الشخصي", data.get("first_name_arabic"))
    smart_fill_input_cnie(page, "الإسم العائلي", data.get("last_name_arabic"))
    smart_fill_input_cnie(page, "Prénom", data.get("first_name_latin"))
    smart_fill_input_cnie(page, "Nom", data.get("last_name_latin"))
    
    try:
        page.locator("input[formcontrolname='birth_date_day']").first.fill(data["dob_day"], force=True)
        page.locator("input[formcontrolname='birth_date_month']").first.fill(data["dob_month"], force=True)
        page.locator("input[formcontrolname='birth_date_year']").first.fill(data["dob_year"], force=True)
    except: pass
    
    if data.get("gender") == "M": page.evaluate("document.querySelector('input[value=\"M\"]').click()")
    elif data.get("gender") == "F": page.evaluate("document.querySelector('input[value=\"F\"]').click()")

    smart_fill_input_cnie(page, "مكان الإزدياد", data.get("place_of_birth_arabic"))
    smart_fill_input_cnie(page, "Lieu de naissance", data.get("place_of_birth_latin"))
    smart_fill_input_cnie(page, "المهنة", data.get("profession_arabic"))
    smart_fill_input_cnie(page, "Profession", data.get("profession_latin"))

    if is_first_time:
        smart_select_dropdown_cnie(page, "بلد الإزدياد", "المغرب")
        # ملاحظة: العمالة والجماعة للإزدياد تحتاج تدخل يدوي أو إضافة ذكاء اصطناعي لها لاحقاً.

    print("\n📢 2. افتح (مكان الإقامة) واضغط Ctrl+Alt+M")
    wait_for_shortcut()
    unlock_arabic_fields(page)
    
    smart_select_dropdown_cnie(page, "بلد الإقامة", "المغرب")
    smart_select_dropdown_cnie(page, "عمالة أو مدينة الإقامة", "الصخيرات تمارة")
    smart_select_dropdown_cnie(page, "جماعة الإقامة", "الصخيرات")

    # جمع العنوان مع المدينة إذا وجدت
    full_address_latin = f"{data.get('address_latin', '')} {data.get('city_latin', '')}".strip()
    full_address_arabic = f"{data.get('address_arabic', '')} {data.get('city_arabic', '')}".strip()

    if full_address_latin:
        try: page.locator("textarea[formcontrolname='adresse']").first.fill(full_address_latin, force=True)
        except: pass
    if full_address_arabic:
        try: page.locator("textarea[formcontrolname='arabic_adresse']").first.fill(full_address_arabic, force=True)
        except: pass

    if is_first_time:
        print("\n📢 3. افتح (النسب - Filiation) واضغط Ctrl+Alt+M")
        wait_for_shortcut()
        unlock_arabic_fields(page)
        
        smart_fill_input_cnie(page, "الإسم الشخصي للأب", data.get("father_first_name_arabic"))
        smart_fill_input_cnie(page, "Prénom père", data.get("father_first_name_latin"))
        smart_fill_input_cnie(page, "الإسم الشخصي للأم", data.get("mother_first_name_arabic"))
        smart_fill_input_cnie(page, "Prénom mère", data.get("mother_first_name_latin"))
        smart_fill_input_cnie(page, "الإسم الشخصي للجد من الأب", data.get("paternal_grandfather_arabic"))
        smart_fill_input_cnie(page, "Prénom grand père paternel", data.get("paternal_grandfather_latin"))
        smart_fill_input_cnie(page, "الإسم الشخصي للجد من الأم", data.get("maternal_grandfather_arabic"))
        smart_fill_input_cnie(page, "Prénom grand père maternel", data.get("maternal_grandfather_latin"))

    print("\n✨ انتهت تعبئة البطاقة الوطنية!")

# ==========================================
# منطق جواز السفر (Passeport)
# ==========================================
def fill_passeport_site(page, data):
    if "passeport.ma" not in page.url: page.goto("https://www.passeport.ma/ar")
    
    print("\n📢 توجه إلى استمارة (الراشدون) في موقع الجواز، ثم اضغط Ctrl+Alt+M")
    wait_for_shortcut()
    
    try: 
        if data.get("n_cine"): page.locator("#num_Cnie").fill(data["n_cine"], force=True)
    except: pass
    
    try:
        if data.get("last_name_latin"): page.locator("input[name='_Nom_FR']").fill(data["last_name_latin"], force=True)
        if data.get("first_name_latin"): page.locator("input[name='_Prenom_FR']").fill(data["first_name_latin"], force=True)
        if data.get("first_name_arabic"): page.locator("#prenomAr").fill(data["first_name_arabic"], force=True)
        if data.get("last_name_arabic"): page.locator("#NomAr").fill(data["last_name_arabic"], force=True)
    except: pass
    
    try:
        if data.get("dob_day"): page.locator("#txtJour").fill(data["dob_day"], force=True)
        if data.get("dob_month"): page.locator("#txtMois").fill(data["dob_month"], force=True)
        if data.get("dob_year"): page.locator("#txtAnnee").fill(data["dob_year"], force=True)
    except: pass
    
    try:
        if data.get("gender") == "M": 
            page.evaluate("document.getElementById('Masculain').click()")
        elif data.get("gender") == "F": 
            page.evaluate("document.getElementById('Féminin').click()")
    except: pass
    
    try:
        if data.get("place_of_birth_latin"): page.locator("input[name='_LieuNaissance_FR']").fill(data["place_of_birth_latin"], force=True)
    except: pass

    try:
        if data.get("address_latin"): page.locator("input[name='_Adresse_FR']").fill(data["address_latin"], force=True)
        if data.get("city_latin"): page.locator("input[name='_Ville']").fill(data["city_latin"], force=True)
    except: pass

    print("✔️ تمت تعبئة بيانات جواز السفر بنجاح! (قم بإدخال الهاتف والرمز البريدي يدوياً)")

# ==========================================
# المُوجّه الرئيسي (Router)
# ==========================================
def start_auto_fill(data, site, mode):
    user_data_dir = os.path.join(os.getcwd(), "chrome_profiles_data")
    
    with sync_playwright() as p:
        browser_context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            channel="chrome",
            headless=False,
            accept_downloads=True,
            no_viewport=True
        )
        
        page = browser_context.pages[0] if browser_context.pages else browser_context.new_page()
        page.on("download", handle_download)
        
        if "CNIE" in site:
            fill_cnie_site(page, data, mode)
        elif "Passeport" in site:
            fill_passeport_site(page, data)
            
        page.wait_for_event("close", timeout=0)
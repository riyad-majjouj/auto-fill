import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("AIzaSyD1zRLbBKGfgcLozp-bpcc3hsDQv33Xg_E"))

def extract_data_from_documents(file_paths):
    print(f"⏳ جاري رفع الوثائق وإرسالها للذكاء الاصطناعي...")
    uploaded_files = []
    
    try:
        for path in file_paths:
            if os.path.exists(path):
                file_obj = genai.upload_file(path)
                uploaded_files.append(file_obj)
                
        if not uploaded_files:
            return None

        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        
        prompt = """
        أنت نظام دقيق جداً لاستخراج البيانات من وثائق الهوية المغربية (CNIE).
        استخرج البيانات المطلوبة بدقة عالية باللغتين العربية والفرنسية.
        يجب تقسيم تاريخ الميلاد إلى يوم، شهر، وسنة.
        
        ملاحظة هامة بخصوص العنوان:
        في ظهر البطاقة يوجد عنوان. استخرج العنوان وافصل منه "المدينة" في حقل مستقل.
        
        الرد يجب أن يكون حصرياً بصيغة JSON صالحة كما يلي:
        {
            "n_cine": "رقم البطاقة الوطنية",
            "first_name_latin": "الاسم الشخصي باللاتينية",
            "last_name_latin": "الاسم العائلي باللاتينية",
            "first_name_arabic": "الاسم الشخصي بالعربية",
            "last_name_arabic": "الاسم العائلي بالعربية",
            "dob_day": "يوم الميلاد",
            "dob_month": "شهر الميلاد",
            "dob_year": "سنة الميلاد",
            "gender": "M للذكر، F للأنثى",
            "place_of_birth_latin": "مكان الازدياد بالفرنسية",
            "place_of_birth_arabic": "مكان الازدياد بالعربية",
            "nationality_arabic": "الجنسية بالعربية",
            "profession_arabic": "المهنة بالعربية",
            "profession_latin": "المهنة بالفرنسية",
            "address_arabic": "العنوان بالعربية (بدون المدينة)",
            "address_latin": "العنوان بالفرنسية (بدون المدينة)",
            "city_arabic": "المدينة المستخرجة من العنوان بالعربية",
            "city_latin": "المدينة المستخرجة من العنوان بالفرنسية",
            "father_first_name_arabic": "الاسم الشخصي للأب بالعربية",
            "father_first_name_latin": "الاسم الشخصي للأب بالفرنسية",
            "mother_first_name_arabic": "الاسم الشخصي للأم بالعربية",
            "mother_first_name_latin": "الاسم الشخصي للأم بالفرنسية",
            "paternal_grandfather_arabic": "الاسم الشخصي للجد من الأب بالعربية",
            "paternal_grandfather_latin": "الاسم الشخصي للجد من الأب بالفرنسية",
            "maternal_grandfather_arabic": "الاسم الشخصي للجد من الأم بالعربية",
            "maternal_grandfather_latin": "الاسم الشخصي للجد من الأم بالفرنسية"
        }
        إذا لم تجد معلومة، اترك قيمتها فارغة "".
        """
        
        response = model.generate_content([prompt] + uploaded_files)
        
        result_text = response.text.strip()
        if result_text.startswith("```json"):
            result_text = result_text.replace("```json", "").replace("```", "").strip()
            
        data = json.loads(result_text)
        print("✅ تم استخراج البيانات وتحليلها بنجاح!")
        return data

    except Exception as e:
        print(f"❌ حدث خطأ أثناء الاتصال بالذكاء الاصطناعي: {e}")
        return None
        
    finally:
        for f in uploaded_files:
            try: genai.delete_file(f.name)
            except Exception: pass
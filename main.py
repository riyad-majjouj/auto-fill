import customtkinter as ctk
import threading
import sys
from tkinter import filedialog
from gemini_extractor import extract_data_from_documents
from web_filler import start_auto_fill

# === استدعاء نظام التراخيص ===
import license_manager

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class PrintRedirector:
    """كلاس لتوجيه أوامر print لتظهر داخل واجهة البرنامج (TextBox)"""
    def __init__(self, textbox):
        self.textbox = textbox

    def write(self, text):
        if text.strip():  
            self.textbox.configure(state="normal")
            self.textbox.insert("end", text + "\n")
            self.textbox.see("end") 
            self.textbox.configure(state="disabled")

    def flush(self):
        pass

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Auto-Filler Pro (Live Mode)")
        self.geometry("650x550")
        
        self.title_label = ctk.CTkLabel(self, text="المساعد الرقمي الذكي", text_color="#00ffcc", font=("Arial", 22, "bold"))
        self.title_label.pack(pady=10)

        self.site_label = ctk.CTkLabel(self, text="اختر الموقع المراد تعبئته:", font=("Arial", 14))
        self.site_label.pack(pady=(5, 0))
        
        self.site_var = ctk.StringVar(value="البطاقة الوطنية (CNIE)")
        self.site_menu = ctk.CTkOptionMenu(self, variable=self.site_var, values=["البطاقة الوطنية (CNIE)", "جواز السفر (Passeport)"], font=("Arial", 14), fg_color="#b35900", button_color="#cc6600", command=self.on_site_change)
        self.site_menu.pack(pady=5)

        self.mode_label = ctk.CTkLabel(self, text="نوع العملية (خاص بالبطاقة الوطنية فقط):", font=("Arial", 14))
        self.mode_label.pack(pady=(5, 0))
        
        self.mode_var = ctk.StringVar(value="أول مرة (First Time)")
        self.mode_menu = ctk.CTkOptionMenu(self, variable=self.mode_var, values=["أول مرة (First Time)", "تجديد البطاقة (Renewal)"], font=("Arial", 14))
        self.mode_menu.pack(pady=5)

        self.status_box = ctk.CTkTextbox(self, width=600, height=200, font=("Consolas", 13))
        self.status_box.pack(pady=10)
        self.status_box.insert("0.0", "البرنامج متصل بالذكاء الاصطناعي. اختر الموقع واضغط بدء...\n")
        self.status_box.configure(state="disabled")

        # توجيه مخرجات الطباعة (print) إلى صندوق النصوص
        sys.stdout = PrintRedirector(self.status_box)

        self.start_button = ctk.CTkButton(self, text="📂 اختيار الوثائق وبدء العمل", command=self.start_thread, font=("Arial", 16, "bold"), height=45)
        self.start_button.pack(pady=10)

        # ===============================================
        # نظام القفل والترخيص (License Manager Integration)
        # ===============================================
        if license_manager.verify_saved_key():
            # إذا كان المفتاح صالحاً، لا تفعل شيئاً (البرنامج يعمل طبيعياً)
            pass 
        else:
            # إذا لم يكن هناك مفتاح صالح، ابدأ مؤقت الفترة التجريبية (5 ثواني)
            license_manager.start_trial_timer(self, self.lock_application)

    def lock_application(self):
        """دالة تقييد الواجهة وإظهار نافذة الشراء"""
        # 1. تعطيل جميع أزرار التفاعل في الواجهة
        self.start_button.configure(state="disabled")
        self.site_menu.configure(state="disabled")
        self.mode_menu.configure(state="disabled")
        print("\n🔒 انتهت الفترة التجريبية! يرجى الاشتراك للاستمرار...")
        
        def on_activation_success():
            # 2. إعادة تفعيل الأزرار بعد نجاح الشراء أو إدخال الكود الصحيح
            self.start_button.configure(state="normal")
            self.site_menu.configure(state="normal")
            
            # فحص حالة زر "نوع العملية" ليعود لشكله الصحيح حسب الموقع المختار
            self.on_site_change(self.site_var.get())
            
            self.focus_force() # إرجاع التركيز للنافذة الرئيسية
            print("✅ تم التفعيل بنجاح! يمكنك الآن استخدام البرنامج.")
            
        # إظهار نافذة التفعيل والدفع
        license_manager.LicenseDialog(self, on_activation_success)

    def on_site_change(self, choice):
        if "Passeport" in choice:
            self.mode_menu.configure(state="disabled")
            print("💡 تم تعطيل نوع العملية (لا نحتاجه في جواز السفر)")
        else:
            self.mode_menu.configure(state="normal")
            print("💡 تم تفعيل نوع العملية (للبطاقة الوطنية)")

    def start_thread(self):
        self.start_button.configure(state="disabled")
        threading.Thread(target=self.run_process, daemon=True).start()

    def run_process(self):
        try:
            selected_site = self.site_var.get()
            selected_mode = self.mode_var.get()
            
            print(f"🎯 الموقع الهدف: {selected_site}")
            
            # 1. فتح نافذة اختيار الوثائق
            print("📂 يرجى اختيار ملفات الوثائق (PDF أو صور)...")
            file_paths = filedialog.askopenfilenames(filetypes=[("Documents", "*.pdf *.jpg *.png *.jpeg")])
            
            if not file_paths:
                print("🛑 تم إلغاء العملية: لم يتم اختيار أي ملف.")
                return

            # 2. إرسال الوثائق للذكاء الاصطناعي
            extracted_data = extract_data_from_documents(list(file_paths))
            
            if extracted_data:
                print("🌐 جاري فتح المتصفح...")
                # 3. إرسال البيانات المستخرجة لمتصفح Playwright
                start_auto_fill(extracted_data, selected_site, selected_mode)
            else:
                print("❌ فشل استخراج البيانات. يرجى التأكد من جودة الصورة/الملف.")

        except Exception as e:
            print(f"⚠️ خطأ غير متوقع: {e}")
        finally:
            self.start_button.configure(state="normal")

if __name__ == "__main__":
    app = App()
    app.mainloop()
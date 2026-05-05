import os
import uuid
import platform
import subprocess
import requests
import threading
import time
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk # أضفنا هذه لدعم توافق النوافذ
import webbrowser

# رابط السيرفر
SERVER_URL = "http://localhost:3000/api"

KEY_FILE = "license_autofiller.dat" 

# ==========================================
# المفتاح الخاص (أوفلاين)
MASTER_KEY = "AUTOFILLER-VIP-2024"
# ==========================================

APP_NAME = "AutoFillerPro"
APP_PRICE = "15.00"

def get_hwid():
    try:
        if platform.system() == "Windows":
            hwid = subprocess.check_output('wmic csproduct get uuid').decode().split('\n')[1].strip()
            return hwid
    except: pass
    mac = ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff) for ele in range(0,8*6,8)][::-1])
    return f"{platform.node()}-{mac}"

def verify_saved_key():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "r") as f:
            key = f.read().strip()
            
        if key == MASTER_KEY:
            return True
            
        if key:
            try:
                hwid = get_hwid()
                res = requests.post(f"{SERVER_URL}/activate", json={"key": key, "hwid": hwid, "appName": APP_NAME}, timeout=5)
                data = res.json()
                if data.get('success'):
                    return True 
            except: pass 
    return False

def save_key(key):
    with open(KEY_FILE, "w") as f:
        f.write(key)

class LicenseDialog:
    def __init__(self, parent_root, on_success_callback):
        self.parent_root = parent_root 
        
        # استخدام Toplevel الخاص بـ CustomTkinter إذا كان الجذر كذلك
        self.top = ctk.CTkToplevel(parent_root) if isinstance(parent_root, ctk.CTk) else tk.Toplevel(parent_root)
        self.top.title("⚠️ تفعيل النسخة المدفوعة")
        self.top.geometry("400x460")
        
        self.top.protocol("WM_DELETE_WINDOW", self.disable_close)
        
        # توافقية اللون مع CustomTkinter
        try: self.top.configure(bg="#1a1a1a")
        except: pass

        self.top.transient(parent_root)
        self.top.grab_set()
        
        self.parent_root.bind("<Map>", self.on_restore)

        self.on_success_callback = on_success_callback
        self.hwid = get_hwid()
        self.current_order_id = None 

        tk.Button(self.top, text="➖ تصغير البرنامج", bg="#333333", fg="white", font=("Segoe UI", 9), bd=0, command=self.minimize_app).pack(anchor="ne", padx=10, pady=5)

        tk.Label(self.top, text="💰 اشترك الآن للاستمرار", font=("Segoe UI", 16, "bold"), bg="#1a1a1a", fg="#22c55e").pack(pady=10)
        tk.Label(self.top, text="سعر الاشتراك: 15 دولار / شهرياً", bg="#1a1a1a", fg="white", font=("Segoe UI", 11)).pack()

        self.pay_btn = tk.Button(self.top, text="💳 شراء الآن عبر PayPal", bg="#0070ba", fg="white", font=("Segoe UI", 12, "bold"), command=self.start_paypal_payment)
        self.pay_btn.pack(pady=15, fill="x", padx=40)

        tk.Label(self.top, text="أدخل مفتاح الترخيص (أو المفتاح الخاص):", bg="#1a1a1a", fg="gray", font=("Segoe UI", 10)).pack(pady=10)
        
        self.key_entry = tk.Entry(self.top, font=("Segoe UI", 14), justify="center")
        self.key_entry.pack(pady=5, padx=40, fill="x")

        self.verify_btn = tk.Button(self.top, text="🔐 تفعيل البرنامج", bg="#6366f1", fg="white", font=("Segoe UI", 12, "bold"), command=self.verify_key)
        self.verify_btn.pack(pady=10, fill="x", padx=40)

    def minimize_app(self):
        self.top.grab_release() 
        self.parent_root.iconify()

    def on_restore(self, event):
        if event.widget == self.parent_root and self.parent_root.state() == 'normal':
            self.top.grab_set() 
            self.top.lift()     

    def disable_close(self):
        if messagebox.askyesno("إغلاق البرنامج", "هل أنت متأكد أنك تريد إغلاق البرنامج بالكامل؟", parent=self.top):
            self.parent_root.destroy() 

    def start_paypal_payment(self):
        self.pay_btn.config(text="جاري الاتصال بـ PayPal...", state=tk.DISABLED)
        try:
            payload = {"price": APP_PRICE, "appName": APP_NAME}
            res = requests.post(f"{SERVER_URL}/create-paypal-order", json=payload, timeout=10)
            data = res.json()
            
            if data.get('success'):
                approval_url = data.get('approvalUrl')
                self.current_order_id = data.get('orderID')
                webbrowser.open(approval_url)
                self.pay_btn.config(text="🔄 التحقق من حالة الدفع", bg="#f59e0b", command=self.retry_verification, state=tk.NORMAL)
                self.minimize_app()
                
                if messagebox.askyesno("تأكيد الدفع", "تم فتح صفحة الدفع في متصفحك.\nهل أكملت الدفع بنجاح؟", parent=self.top):
                    self.check_payment_status()
            else:
                messagebox.showerror("خطأ", "فشل في إنشاء رابط الدفع.", parent=self.top)
                self.pay_btn.config(text="💳 شراء الآن عبر PayPal", bg="#0070ba", state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror("خطأ بالاتصال", "تأكد من تشغيل سيرفر الباك إند", parent=self.top)
            self.pay_btn.config(text="💳 شراء الآن عبر PayPal", bg="#0070ba", state=tk.NORMAL)

    def retry_verification(self):
        if self.current_order_id: self.check_payment_status()
        else: messagebox.showwarning("خطأ", "لا يوجد طلب دفع حالي.", parent=self.top)

    def check_payment_status(self):
        self.pay_btn.config(text="جاري التحقق...", state=tk.DISABLED)
        try:
            res = requests.post(f"{SERVER_URL}/verify-payment", json={"orderID": self.current_order_id, "appName": APP_NAME}, timeout=10)
            data = res.json()
            if data.get('success'):
                license_key = data.get('licenseKey')
                self.key_entry.delete(0, tk.END)
                self.key_entry.insert(0, license_key)
                self.top.clipboard_clear()
                self.top.clipboard_append(license_key)
                self.pay_btn.config(text="✅ تم الدفع بنجاح", bg="#22c55e", state=tk.DISABLED)
                messagebox.showinfo("شكراً لك!", "تم تأكيد الدفع بنجاح!\nتم وضع مفتاح الترخيص في الخانة، اضغط 'تفعيل البرنامج' الآن.", parent=self.top)
            else:
                messagebox.showwarning("لم يتم الدفع", "لم نتمكن من العثور على دفعة مكتملة. حاول مجدداً.", parent=self.top)
                self.pay_btn.config(text="🔄 التحقق من حالة الدفع", bg="#f59e0b", state=tk.NORMAL)
        except:
            messagebox.showerror("خطأ", "حدث خطأ أثناء التحقق من الدفع.", parent=self.top)
            self.pay_btn.config(text="🔄 التحقق من حالة الدفع", bg="#f59e0b", state=tk.NORMAL)

    def verify_key(self):
        key = self.key_entry.get().strip()
        if not key: return
        
        if key == MASTER_KEY:
            save_key(key)
            messagebox.showinfo("تفعيل خاص", "✅ تم التفعيل باستخدام المفتاح الشامل بنجاح!", parent=self.top)
            self.top.destroy()
            self.on_success_callback()
            return

        self.verify_btn.config(text="جاري التفعيل...", state=tk.DISABLED)
        try:
            res = requests.post(f"{SERVER_URL}/activate", json={"key": key, "hwid": self.hwid, "appName": APP_NAME}, timeout=5)
            data = res.json()
            if data.get('success'):
                save_key(key) 
                messagebox.showinfo("تم التفعيل", "تم تفعيل البرنامج بنجاح! شكراً لثقتك.", parent=self.top)
                self.top.destroy()
                self.on_success_callback() 
            else:
                messagebox.showerror("خطأ", data.get('message'), parent=self.top)
        except:
            messagebox.showerror("خطأ بالاتصال", "السيرفر لا يستجيب، تأكد من الإنترنت.", parent=self.top)
        finally:
            if hasattr(self, 'verify_btn') and self.verify_btn.winfo_exists():
                self.verify_btn.config(text="🔐 تفعيل البرنامج", state=tk.NORMAL)

def start_trial_timer(root, lock_ui_callback):
    def timer():
        time.sleep(5)
        # استخدام after الخاص بـ CustomTkinter
        if hasattr(root, 'after'): root.after(0, lock_ui_callback)
    threading.Thread(target=timer, daemon=True).start()
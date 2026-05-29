import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import json
import webbrowser
import urllib.request
import threading

# --- 1. VERİTABANI İŞLEMLERİ (SQL) ---

def veritabani_kurulum():
    baglanti = sqlite3.connect("wordy.db")
    imlec = baglanti.cursor()
    
    # 📁 ÇALIŞMA ALANI (WORKSPACE) TABLOSU
    imlec.execute('''
        CREATE TABLE IF NOT EXISTS workspaces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad TEXT UNIQUE NOT NULL
        )
    ''')
    imlec.execute("INSERT OR IGNORE INTO workspaces (ad) VALUES ('Ana Çalışma Alanı')")

    imlec.execute('''
        CREATE TABLE IF NOT EXISTS kelimeler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kelime TEXT NOT NULL,
            kategori TEXT NOT NULL
        )
    ''')
    
    # 🌙 Tema ayarlarını tutacağımız tablo
    imlec.execute('''
        CREATE TABLE IF NOT EXISTS ayarlar (
            anahtar TEXT PRIMARY KEY,
            deger TEXT NOT NULL
        )
    ''')
    
    # Eski verileri korumak için güvenli sütun ekleme (Migration)
    try:
        imlec.execute("ALTER TABLE kelimeler ADD COLUMN workspace TEXT DEFAULT 'Ana Çalışma Alanı'")
    except sqlite3.OperationalError:
        pass # Eğer sütun zaten varsa hata vermez, sessizce geçer
        
    baglanti.commit()
    baglanti.close()

def ayari_getir_sql(anahtar):
    baglanti = sqlite3.connect("wordy.db")
    imlec = baglanti.cursor()
    imlec.execute("SELECT deger FROM ayarlar WHERE anahtar = ?", (anahtar,))
    sonuc = imlec.fetchone()
    baglanti.close()
    return sonuc[0] if sonuc else None

def ayar_kaydet_sql(anahtar, deger):
    baglanti = sqlite3.connect("wordy.db")
    imlec = baglanti.cursor()
    imlec.execute("INSERT OR REPLACE INTO ayarlar (anahtar, deger) VALUES (?, ?)", (anahtar, deger))
    baglanti.commit()
    baglanti.close()

def kelime_var_mi_sql(kelime, workspace):
    """Aynı çalışma alanında aynı kelime var mı diye kontrol eder."""
    baglanti = sqlite3.connect("wordy.db")
    imlec = baglanti.cursor()
    imlec.execute("SELECT id FROM kelimeler WHERE kelime = ? AND workspace = ? COLLATE NOCASE", (kelime, workspace))
    sonuc = imlec.fetchone()
    baglanti.close()
    return sonuc is not None

def calisma_alanlarini_getir_sql():
    baglanti = sqlite3.connect("wordy.db")
    imlec = baglanti.cursor()
    imlec.execute("SELECT ad FROM workspaces ORDER BY id ASC")
    veriler = imlec.fetchall()
    baglanti.close()
    return veriler

def calisma_alani_ekle_sql(ad):
    baglanti = sqlite3.connect("wordy.db")
    imlec = baglanti.cursor()
    try:
        imlec.execute("INSERT INTO workspaces (ad) VALUES (?)", (ad,))
        baglanti.commit()
        basarili = True
    except sqlite3.IntegrityError:
        basarili = False # Bu isimde bir alan zaten var
    baglanti.close()
    return basarili

def calisma_alani_sil_sql(ad):
    baglanti = sqlite3.connect("wordy.db")
    imlec = baglanti.cursor()
    imlec.execute("DELETE FROM kelimeler WHERE workspace = ?", (ad,))
    imlec.execute("DELETE FROM workspaces WHERE ad = ?", (ad,))
    baglanti.commit()
    baglanti.close()

def kelime_ekle_sql(kelime, kategori, workspace):
    baglanti = sqlite3.connect("wordy.db")
    imlec = baglanti.cursor()
    imlec.execute("INSERT INTO kelimeler (kelime, kategori, workspace) VALUES (?, ?, ?)", (kelime, kategori, workspace))
    baglanti.commit()
    baglanti.close()

def kelimeleri_getir_sql(workspace):
    baglanti = sqlite3.connect("wordy.db")
    imlec = baglanti.cursor()
    imlec.execute("SELECT id, kelime, kategori FROM kelimeler WHERE workspace = ? ORDER BY id DESC", (workspace,))
    veriler = imlec.fetchall()
    baglanti.close()
    return veriler

def kelimeleri_ara_sql(arama_metni, workspace):
    baglanti = sqlite3.connect("wordy.db")
    imlec = baglanti.cursor()
    sorgu_metni = f"%{arama_metni}%"
    imlec.execute("SELECT id, kelime, kategori FROM kelimeler WHERE workspace = ? AND (kelime LIKE ? OR kategori LIKE ?) ORDER BY id DESC", (workspace, sorgu_metni, sorgu_metni))
    veriler = imlec.fetchall()
    baglanti.close()
    return veriler

def kategorileri_getir_sql(workspace):
    baglanti = sqlite3.connect("wordy.db")
    imlec = baglanti.cursor()
    imlec.execute("SELECT kategori FROM kelimeler WHERE workspace = ?", (workspace,))
    veriler = imlec.fetchall()
    baglanti.close()
    
    benzersiz_etiketler = set()
    for satir in veriler:
        kategoriler_str = satir[0]
        for etiket in kategoriler_str.split(','):
            temiz_etiket = etiket.strip()
            if temiz_etiket:
                benzersiz_etiketler.add(temiz_etiket)
    return sorted(list(benzersiz_etiketler))

def kelimeleri_kategori_filtrele_sql(kategori, workspace):
    baglanti = sqlite3.connect("wordy.db")
    imlec = baglanti.cursor()
    imlec.execute("SELECT id, kelime, kategori FROM kelimeler WHERE workspace = ? ORDER BY id DESC", (workspace,))
    veriler = imlec.fetchall()
    baglanti.close()
    
    filtrelenmis_veriler = []
    for satir in veriler:
        id, kelime, kategori_str = satir
        etiketler = [e.strip() for e in kategori_str.split(',')]
        if kategori in etiketler:
            filtrelenmis_veriler.append(satir)
    return filtrelenmis_veriler

def kelime_sil_sql(kelime_id):
    baglanti = sqlite3.connect("wordy.db")
    imlec = baglanti.cursor()
    imlec.execute("DELETE FROM kelimeler WHERE id = ?", (kelime_id,))
    baglanti.commit()
    baglanti.close()

def kelime_guncelle_sql(kelime_id, yeni_kelime, yeni_kategori):
    baglanti = sqlite3.connect("wordy.db")
    imlec = baglanti.cursor()
    imlec.execute("UPDATE kelimeler SET kelime = ?, kategori = ? WHERE id = ?", (yeni_kelime, yeni_kategori, kelime_id))
    baglanti.commit()
    baglanti.close()

def kelimeleri_kategoriye_gore_sil_sql(hedef_kategori, workspace):
    baglanti = sqlite3.connect("wordy.db")
    imlec = baglanti.cursor()
    imlec.execute("SELECT id, kategori FROM kelimeler WHERE workspace = ?", (workspace,))
    veriler = imlec.fetchall()
    
    silinecek_adet = 0
    for satir in veriler:
        k_id, kat_str = satir
        etiketler = [e.strip() for e in kat_str.split(',')]
        if hedef_kategori in etiketler:
            imlec.execute("DELETE FROM kelimeler WHERE id = ?", (k_id,))
            silinecek_adet += 1
            
    baglanti.commit()
    baglanti.close()
    return silinecek_adet

# --- 2. ARAYÜZ (GUI) İŞLEMLERİ (Python/Tkinter) ---

class KelimeUygulamasi:
    def __init__(self, pencere):
        self.pencere = pencere
        self.pencere.title("Wordy")
        
        # --- ÖZELLİK DEĞİŞKENLERİ ---
        self.her_zaman_ustte = False
        self.sayfa_no = 1
        self.sayfa_basina_kayit = 50
        self.aktif_filtre_kategori = None
        self.aktif_workspace = "Ana Çalışma Alanı"

        veritabani_kurulum()
        
        # 🌙 Tema ve Ayar Sistemi Değişkenleri
        self.tema_modu = ayari_getir_sql("tema") or "Aydınlık"
        self.oto_kayit_aktif = (ayari_getir_sql("oto_kayit") == "1")
        self.tema_ayarla()

        # --- MODERN TASARIM AYARLARI ---
        self.font_main = ("Segoe UI", 10)
        self.font_bold = ("Segoe UI", 10, "bold")

        # 📌 Ana pencereyi ekranın ortasında başlat
        self.pencere_ortala(self.pencere, 900, 700)
        self.baslat_arayuz()

    def pencere_ortala(self, pencere, genislik, yukseklik):
        """Pencereyi ekranın tam ortasında açmak için gerekli matematiği hesaplar."""
        pencere.update_idletasks()
        ekran_g = pencere.winfo_screenwidth()
        ekran_y = pencere.winfo_screenheight()
        x = (ekran_g - genislik) // 2
        y = (ekran_y - yukseklik) // 2
        pencere.geometry(f"{genislik}x{yukseklik}+{x}+{y}")
        
        # 🛡️ YENİLİK: Eğer alt pencere açılıyorsa ve ana ekran sabitliyse, alt pencere de üstte kalmalı.
        if pencere != self.pencere:
            pencere.transient(self.pencere) # Ana pencereye ait olduğunu belirt
            if self.her_zaman_ustte:
                pencere.attributes('-topmost', True)

    def tema_ayarla(self):
        """Seçili temaya göre renk paletini belirler."""
        if self.tema_modu == "Karanlık":
            self.bg_color = "#111827"       
            self.card_bg = "#1F2937"        
            self.text_fg = "#F9FAFB"        
            self.header_bg = "#374151"      
            self.btn_neutral_bg = "#374151" 
            self.btn_neutral_fg = "#F9FAFB"
            self.tag_bg = "#1E3A8A"         
            self.tag_fg = "#BFDBFE"
        else:
            self.bg_color = "#F3F4F6"
            self.card_bg = "#FFFFFF"
            self.text_fg = "#374151"
            self.header_bg = "#E5E7EB"
            self.btn_neutral_bg = "#E5E7EB"
            self.btn_neutral_fg = "#374151"
            self.tag_bg = "#DBEAFE"
            self.tag_fg = "#1E40AF"
        
        self.pencere.configure(bg=self.bg_color)

    def baslat_arayuz(self):
        for widget in self.pencere.winfo_children():
            widget.destroy()
            
        self.arayuz_olustur()
        self.workspaceleri_guncelle()
        self.listeyi_guncelle()
        self.kategorileri_guncelle()

    def tema_degistir(self):
        self.tema_modu = "Karanlık" if self.tema_modu == "Aydınlık" else "Aydınlık"
        ayar_kaydet_sql("tema", self.tema_modu)
        self.tema_ayarla()
        self.baslat_arayuz()

    def modern_btn(self, parent, text, bg_color, fg_color, cmd, font=None, width=None):
        if font is None: font = self.font_main
        btn = tk.Button(parent, text=text, command=cmd, bg=bg_color, fg=fg_color, font=font,
                        relief="flat", borderwidth=0, cursor="hand2", padx=12, pady=6)
        if width: btn.config(width=width)
        return btn

    def arayuz_olustur(self):
        ws_cercevesi = tk.Frame(self.pencere, bg=self.header_bg, pady=8, padx=20)
        ws_cercevesi.pack(fill=tk.X)
        
        tk.Label(ws_cercevesi, text="📁 Çalışma Alanı:", font=self.font_bold, bg=self.header_bg, fg=self.text_fg).pack(side=tk.LEFT)
        
        self.workspace_combo = ttk.Combobox(ws_cercevesi, state="readonly", font=self.font_main, width=25)
        self.workspace_combo.pack(side=tk.LEFT, padx=10)
        self.workspace_combo.bind("<<ComboboxSelected>>", self.workspace_degisti)
        
        self.modern_btn(ws_cercevesi, "+ Yeni Alan", "#3B82F6", "white", self.yeni_workspace_penceresi).pack(side=tk.LEFT, padx=5)
        self.modern_btn(ws_cercevesi, "🗑️ Alanı Sil", "#EF4444", "white", self.workspace_sil).pack(side=tk.LEFT, padx=5)

        # ⚙️ ℹ️ Hakkında & Ayarlar Butonu
        self.modern_btn(ws_cercevesi, "ℹ️ Hakkında & Ayarlar", "#6366F1", "white", self.ayarlar_ve_hakkinda_penceresi).pack(side=tk.RIGHT, padx=5)

        kontrol_cercevesi = tk.Frame(self.pencere, bg=self.card_bg, padx=15, pady=15)
        kontrol_cercevesi.pack(fill=tk.X, padx=20, pady=(15, 10))

        sol_panel = tk.Frame(kontrol_cercevesi, bg=self.card_bg)
        sol_panel.pack(side=tk.LEFT)

        ekle_btn = self.modern_btn(sol_panel, "+ Yeni Kelime Ekle", "#3B82F6", "white", self.yeni_kelime_penceresi, self.font_bold)
        ekle_btn.pack(side=tk.LEFT, padx=(0, 15))

        sag_panel = tk.Frame(kontrol_cercevesi, bg=self.card_bg)
        sag_panel.pack(side=tk.RIGHT)

        tk.Label(sag_panel, text="Ara:", font=self.font_bold, bg=self.card_bg, fg=self.text_fg).pack(side=tk.LEFT, padx=5)
        self.arama_girisi = ttk.Entry(sag_panel, width=20, font=self.font_main)
        self.arama_girisi.pack(side=tk.LEFT, padx=8)
        
        # Canlı Arama
        self.arama_girisi.bind("<KeyRelease>", lambda event: self.listeyi_guncelle(arama_sifirlama=False))
        self.arama_girisi.bind("<Return>", lambda event: self.listeyi_guncelle())
        
        ara_btn = self.modern_btn(sag_panel, "Bul", "#6B7280", "white", self.listeyi_guncelle)
        ara_btn.pack(side=tk.LEFT, padx=2)

        temizle_btn = self.modern_btn(sag_panel, "Tümünü Göster", "#9CA3AF", "white", self.aramayi_temizle)
        temizle_btn.pack(side=tk.LEFT, padx=2)

        self.kategori_cercevesi = tk.Frame(self.pencere, bg=self.bg_color)
        self.kategori_cercevesi.pack(fill=tk.X, padx=20, pady=5)

        liste_cercevesi = tk.Frame(self.pencere, bg=self.bg_color)
        liste_cercevesi.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        baslik_frame = tk.Frame(liste_cercevesi, bg=self.header_bg, pady=8)
        baslik_frame.pack(fill=tk.X, pady=(0, 5))
        tk.Label(baslik_frame, text="Kelime", width=20, font=self.font_bold, bg=self.header_bg, fg=self.text_fg, anchor="w").pack(side=tk.LEFT, padx=15)
        tk.Label(baslik_frame, text="Kategori (Tag)", width=20, font=self.font_bold, bg=self.header_bg, fg=self.text_fg, anchor="w").pack(side=tk.LEFT, padx=15)
        tk.Label(baslik_frame, text="İşlemler", font=self.font_bold, bg=self.header_bg, fg=self.text_fg).pack(side=tk.RIGHT, padx=45)

        self.canvas = tk.Canvas(liste_cercevesi, bg=self.bg_color, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(liste_cercevesi, orient="vertical", command=self.canvas.yview, width=12)
        
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.bg_color)

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        def configure_canvas(event):
            self.canvas.itemconfig(self.canvas_window, width=event.width)
        self.canvas.bind('<Configure>', configure_canvas)

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.sayfalama_cercevesi = tk.Frame(self.pencere, bg=self.bg_color)
        self.sayfalama_cercevesi.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        self.onceki_sayfa_btn = self.modern_btn(self.sayfalama_cercevesi, "◀ Önceki", "#9CA3AF", "white", self.onceki_sayfa)
        self.onceki_sayfa_btn.pack(side=tk.LEFT)
        
        self.sayfa_bilgisi_lbl = tk.Label(self.sayfalama_cercevesi, text="Sayfa: 1", font=self.font_bold, bg=self.bg_color, fg=self.text_fg)
        self.sayfa_bilgisi_lbl.pack(side=tk.LEFT, padx=15)
        
        self.sonraki_sayfa_btn = self.modern_btn(self.sayfalama_cercevesi, "Sonraki ▶", "#9CA3AF", "white", self.sonraki_sayfa)
        self.sonraki_sayfa_btn.pack(side=tk.LEFT)

    def workspaceleri_guncelle(self):
        alanlar = calisma_alanlarini_getir_sql()
        isimler = [a[0] for a in alanlar]
        self.workspace_combo['values'] = isimler
        if self.aktif_workspace in isimler:
            self.workspace_combo.set(self.aktif_workspace)
        else:
            self.workspace_combo.current(0)
            self.aktif_workspace = self.workspace_combo.get()

    def workspace_degisti(self, event=None):
        self.aktif_workspace = self.workspace_combo.get()
        self.sayfa_no = 1
        self.aktif_filtre_kategori = None
        if hasattr(self, 'arama_girisi'):
            self.arama_girisi.delete(0, tk.END)
        self.listeyi_guncelle()
        self.kategorileri_guncelle()

    def yeni_workspace_penceresi(self):
        ws_pencere = tk.Toplevel(self.pencere)
        ws_pencere.title("Yeni Çalışma Alanı")
        self.pencere_ortala(ws_pencere, 300, 150)
        ws_pencere.configure(bg=self.bg_color)
        ws_pencere.grab_set()

        icerik = tk.Frame(ws_pencere, bg=self.card_bg, padx=20, pady=20)
        icerik.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        tk.Label(icerik, text="Alan Adı (Örn: İş, İngilizce):", font=self.font_bold, bg=self.card_bg, fg=self.text_fg).pack(anchor="w")
        isim_girisi = ttk.Entry(icerik, font=self.font_main)
        isim_girisi.pack(fill=tk.X, pady=(5, 10))
        isim_girisi.focus()

        def kaydet(event=None):
            ad = isim_girisi.get().strip()
            if not ad: return
            if calisma_alani_ekle_sql(ad):
                self.aktif_workspace = ad
                self.workspaceleri_guncelle()
                self.workspace_degisti()
                ws_pencere.destroy()
                messagebox.showinfo("Başarılı", f"'{ad}' çalışma alanı oluşturuldu!")
            else:
                messagebox.showwarning("Hata", "Bu isimde bir çalışma alanı zaten var!", parent=ws_pencere)

        self.modern_btn(icerik, "Oluştur", "#3B82F6", "white", kaydet).pack(fill=tk.X)
        ws_pencere.bind("<Return>", kaydet)

    def workspace_sil(self):
        if len(self.workspace_combo['values']) <= 1:
            messagebox.showwarning("Hata", "Sistemde en az bir çalışma alanı bulunmak zorundadır!")
            return
            
        ad = self.aktif_workspace
        cevap = messagebox.askyesno("Kritik Onay", f"DİKKAT!\n'{ad}' çalışma alanı ve içindeki TÜM kelimeler kalıcı olarak silinecek.\nBunu onaylıyor musunuz?")
        if cevap:
            calisma_alani_sil_sql(ad)
            self.aktif_workspace = "Ana Çalışma Alanı" 
            self.workspaceleri_guncelle()
            self.workspace_degisti()
            messagebox.showinfo("Başarılı", "Çalışma alanı ve içerisindeki tüm veriler silindi.")
            self.otomatik_yedek_al()

    def ustte_tut_gecis(self):
        """Uygulamayı ve açık olan Ayarlar penceresini Her Zaman Üstte durumuna getirir/çıkarır."""
        self.her_zaman_ustte = not self.her_zaman_ustte
        self.pencere.attributes('-topmost', self.her_zaman_ustte)
        
        if hasattr(self, 'ayarlar_pin_btn') and self.ayarlar_pin_btn.winfo_exists():
            ayarlar_win = self.ayarlar_pin_btn.winfo_toplevel() # Ayarlar penceresinin kendisini bul
            if self.her_zaman_ustte:
                self.ayarlar_pin_btn.config(bg="#FCD34D", text="📌 Sabitlendi", fg="#92400E") 
                ayarlar_win.attributes('-topmost', True) # 🛡️ Ayarlar menüsünü de anında üste çek
            else:
                self.ayarlar_pin_btn.config(bg=getattr(self, 'btn_neutral_bg', "#E5E7EB"), text="📌 Sabitle", fg=getattr(self, 'btn_neutral_fg', "#374151"))
                ayarlar_win.attributes('-topmost', False) # Üstten çıkar

    def ayarlar_ve_hakkinda_penceresi(self):
        win = tk.Toplevel(self.pencere)
        win.title("ℹ️ Hakkında & Ayarlar")
        self.pencere_ortala(win, 350, 560) 
        win.configure(bg=self.bg_color)
        win.grab_set()

        icerik = tk.Frame(win, bg=self.card_bg, padx=20, pady=20)
        icerik.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # --- HAKKINDA BÖLÜMÜ ---
        tk.Label(icerik, text="Wordy", font=("Segoe UI", 12, "bold"), bg=self.card_bg, fg=self.text_fg).pack(pady=(0, 5))
        tk.Label(icerik, text="Kelimelerinizi ve etiketlerinizi\nçalışma alanlarına bölerek güvenle\nyönetmenizi sağlayan masaüstü aracı.", 
                 font=self.font_main, bg=self.card_bg, fg=self.text_fg, justify="center").pack(pady=(0, 10))
        
        info_frame = tk.Frame(icerik, bg=self.card_bg)
        info_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 📌 YENİLİK: Versiyon Kontrol Etiketi (Değişebilir Tasarım)
        versiyon_lbl = tk.Label(info_frame, text="Versiyon 1.0 (Kontrol ediliyor...)", font=self.font_main, bg=self.card_bg, fg=self.text_fg)
        versiyon_lbl.pack()
        
        # 🛡️ YENİLİK: Uygulamayı dondurmamak için arkaplanda (Thread) kontrol başlatıyoruz
        threading.Thread(target=self.versiyon_kontrol, args=(versiyon_lbl,), daemon=True).start()

        tk.Label(info_frame, text="Geliştirici: furkanyasarr0", font=self.font_main, bg=self.card_bg, fg="#3B82F6").pack()
        repo_lbl = tk.Label(info_frame, text="Repo: github.com/furkanyasarr0/wordy", font=self.font_main, bg=self.card_bg, fg="#10B981", cursor="hand2")
        repo_lbl.pack()
        
        # 🌐 YENİLİK: Linke tıklayınca kopyalamak yerine tarayıcıda doğrudan aç
        repo_lbl.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/furkanyasarr0/wordy"))

        tk.Frame(icerik, bg=self.header_bg, height=2).pack(fill=tk.X, pady=10) # Ayırıcı Çizgi

        # --- AYARLAR BÖLÜMÜ ---
        tk.Label(icerik, text="⚙️ Arayüz Ayarları", font=self.font_bold, bg=self.card_bg, fg=self.text_fg).pack(anchor="w", pady=(0, 5))
        
        tema_ikon = "🌙 Gece Modu" if self.tema_modu == "Aydınlık" else "☀️ Gündüz Modu"
        self.ayarlar_tema_btn = self.modern_btn(icerik, tema_ikon, "#8B5CF6", "white", lambda: [self.tema_degistir(), win.destroy()])
        self.ayarlar_tema_btn.pack(fill=tk.X, pady=2)

        pin_bg = "#FCD34D" if self.her_zaman_ustte else getattr(self, 'btn_neutral_bg', "#E5E7EB")
        pin_fg = "#92400E" if self.her_zaman_ustte else getattr(self, 'btn_neutral_fg', "#374151")
        pin_metin = "📌 Sabitlendi" if self.her_zaman_ustte else "📌 Sabitle"
        self.ayarlar_pin_btn = self.modern_btn(icerik, pin_metin, pin_bg, pin_fg, self.ustte_tut_gecis)
        self.ayarlar_pin_btn.pack(fill=tk.X, pady=2)

        tk.Label(icerik, text="💾 Veri & Yedekleme", font=self.font_bold, bg=self.card_bg, fg=self.text_fg).pack(anchor="w", pady=(10, 5))
        
        oto_bg = "#10B981" if getattr(self, 'oto_kayit_aktif', False) else getattr(self, 'btn_neutral_bg', "#E5E7EB")
        oto_fg = "white" if getattr(self, 'oto_kayit_aktif', False) else getattr(self, 'btn_neutral_fg', "#374151")
        oto_metin = "✅ Oto Kayıt: Aktif" if getattr(self, 'oto_kayit_aktif', False) else "❌ Oto Kayıt: Kapalı"
        self.ayarlar_oto_btn = self.modern_btn(icerik, oto_metin, oto_bg, oto_fg, self.oto_kayit_gecis)
        self.ayarlar_oto_btn.pack(fill=tk.X, pady=2)

        self.modern_btn(icerik, "📥 İçe Aktar", "#10B981", "white", lambda: [win.destroy(), self.verileri_ice_aktar()]).pack(fill=tk.X, pady=2)
        self.modern_btn(icerik, "📤 Dışa Aktar", "#F59E0B", "white", lambda: [win.destroy(), self.verileri_disa_aktar()]).pack(fill=tk.X, pady=2)

    def oto_kayit_gecis(self):
        self.oto_kayit_aktif = not self.oto_kayit_aktif
        ayar_kaydet_sql("oto_kayit", "1" if self.oto_kayit_aktif else "0")
        if hasattr(self, 'ayarlar_oto_btn') and self.ayarlar_oto_btn.winfo_exists():
            if self.oto_kayit_aktif:
                self.ayarlar_oto_btn.config(bg="#10B981", fg="white", text="✅ Oto Kayıt: Aktif")
            else:
                self.ayarlar_oto_btn.config(bg=getattr(self, 'btn_neutral_bg', "#E5E7EB"), fg=getattr(self, 'btn_neutral_fg', "#374151"), text="❌ Oto Kayıt: Kapalı")

    def versiyon_kontrol(self, label_widget):
        """Kendi GitHub deponuzdan güncel versiyon numarasını okur."""
        try:
            # 🚀 ÖNEMLİ: Kendi reponuzda 'version.txt' dosyası oluşturup içine '1.0' yazın.
            url = "https://raw.githubusercontent.com/furkanyasarr0/Wordy/main/version.txt"
            req = urllib.request.Request(url, headers={'Cache-Control': 'no-cache'})
            with urllib.request.urlopen(req, timeout=3) as response:
                guncel_versiyon = response.read().decode('utf-8').strip()
                
            mevcut_versiyon = "1.0"
            
            # Eğer reponuzdaki txt dosyasındaki versiyon, uygulamadakinden farklıysa uyar
            if guncel_versiyon and guncel_versiyon != mevcut_versiyon:
                label_widget.config(text=f"Versiyon {mevcut_versiyon} (Yeni Sürüm Var: {guncel_versiyon})", fg="#F59E0B") # Turuncu
            else:
                label_widget.config(text=f"Versiyon {mevcut_versiyon} (Güncel)", fg="#10B981") # Yeşil
        except Exception:
            # İnternet yoksa veya txt dosyası henüz repoda oluşturulmadıysa sessizce 1.0 yaz
            label_widget.config(text="Versiyon 1.0", fg=self.text_fg)

    def otomatik_yedek_al(self):
        if getattr(self, 'oto_kayit_aktif', False):
            try:
                veriler = kelimeleri_getir_sql(self.aktif_workspace)
                json_verisi = [{"id": s[0], "kelime": s[1], "kategori": s[2]} for s in veriler]
                dosya_adi = f"auto_backup_{self.aktif_workspace.replace(' ', '_')}.json"
                with open(dosya_adi, mode='w', encoding='utf-8') as dosya:
                    json.dump(json_verisi, dosya, ensure_ascii=False, indent=4)
            except Exception:
                pass 

    def kategorileri_guncelle(self):
        for widget in self.kategori_cercevesi.winfo_children():
            widget.destroy()
            
        kategoriler = kategorileri_getir_sql(self.aktif_workspace)
        if not kategoriler: return

        tk.Label(self.kategori_cercevesi, text="Kategoriler:", font=self.font_bold, bg=self.bg_color, fg=self.text_fg).pack(side=tk.LEFT, padx=(0, 10))
        self.modern_btn(self.kategori_cercevesi, "Tümü", self.btn_neutral_bg, self.btn_neutral_fg, lambda: self.listeyi_guncelle()).pack(side=tk.LEFT, padx=3)

        for kat_adi in kategoriler:
            self.modern_btn(self.kategori_cercevesi, kat_adi, self.btn_neutral_bg, self.btn_neutral_fg, lambda k=kat_adi: self.listeyi_guncelle(kategori_filtresi=k)).pack(side=tk.LEFT, padx=3)

        tk.Label(self.kategori_cercevesi, text="|", font=self.font_main, bg=self.bg_color, fg="#9CA3AF").pack(side=tk.LEFT, padx=5)
        self.modern_btn(self.kategori_cercevesi, "🧹 Kategori Temizle", "#FEE2E2", "#DC2626", self.toplu_kategori_sil_penceresi).pack(side=tk.LEFT, padx=3)

    def toplu_kategori_sil_penceresi(self):
        kategoriler = kategorileri_getir_sql(self.aktif_workspace)
        if not kategoriler:
            messagebox.showinfo("Bilgi", "Silinecek kategori bulunmuyor.")
            return
            
        sil_pencere = tk.Toplevel(self.pencere)
        sil_pencere.title("Toplu Kategori Temizliği")
        self.pencere_ortala(sil_pencere, 350, 200) 
        sil_pencere.configure(bg=self.bg_color)
        sil_pencere.grab_set()
        
        icerik = tk.Frame(sil_pencere, bg=self.card_bg, padx=20, pady=20)
        icerik.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        tk.Label(icerik, text="Silinecek Kategoriyi Seçin:", font=self.font_bold, bg=self.card_bg, fg=self.text_fg).pack(anchor="w", pady=(0, 5))
        
        secili_kategori = tk.StringVar()
        kategori_isimleri = [k for k in kategoriler]
        acilir_menu = ttk.Combobox(icerik, textvariable=secili_kategori, values=kategori_isimleri, state="readonly", font=self.font_main)
        acilir_menu.pack(fill=tk.X, pady=(0, 15))
        if kategori_isimleri: acilir_menu.current(0)
        
        def onayli_sil():
            hedef = secili_kategori.get()
            if not hedef: return
            cevap = messagebox.askyesno("Kritik Onay", f"DİKKAT!\n'{hedef}' etiketine sahip TÜM kelimeler silinecek.\nBunu onaylıyor musunuz?", parent=sil_pencere)
            if cevap:
                silinen_adet = kelimeleri_kategoriye_gore_sil_sql(hedef, self.aktif_workspace)
                self.listeyi_guncelle()
                self.kategorileri_guncelle()
                self.otomatik_yedek_al()
                sil_pencere.destroy()
                messagebox.showinfo("Temizlik Tamam", f"'{hedef}' kategorisindeki {silinen_adet} adet kelime başarıyla silindi.")
                
        self.modern_btn(icerik, "Seçili Kategoriyi Tamamen Sil", "#EF4444", "white", onayli_sil, self.font_bold).pack(fill=tk.X)

    def yeni_kelime_penceresi(self):
        ekle_pencere = tk.Toplevel(self.pencere)
        ekle_pencere.title("Yeni Kelime Ekle")
        self.pencere_ortala(ekle_pencere, 350, 250) 
        ekle_pencere.configure(bg=self.bg_color)
        ekle_pencere.grab_set() 

        icerik = tk.Frame(ekle_pencere, bg=self.card_bg, padx=20, pady=20)
        icerik.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        tk.Label(icerik, text="Eklenecek Kelime:", font=self.font_bold, bg=self.card_bg, fg=self.text_fg).pack(anchor="w", pady=(0, 5))
        kelime_girisi = ttk.Entry(icerik, width=40, font=self.font_main)
        kelime_girisi.pack(pady=(0, 15))
        kelime_girisi.focus()

        tk.Label(icerik, text="Kategori / Etiket (Tag):", font=self.font_bold, bg=self.card_bg, fg=self.text_fg).pack(anchor="w", pady=(0, 5))
        kategori_girisi = ttk.Entry(icerik, width=40, font=self.font_main)
        kategori_girisi.pack(pady=(0, 15))

        def kaydet(event=None): 
            yeni_kelime = kelime_girisi.get().strip()
            yeni_kategori = kategori_girisi.get().strip()
            if not yeni_kelime or not yeni_kategori:
                messagebox.showwarning("Eksik Bilgi", "Lütfen hem kelimeyi hem de kategoriyi doldurun!", parent=ekle_pencere)
                return
            
            # 🛡️ ÖZELLİK 2: Çift Kayıt Kontrolü Sistemi
            if kelime_var_mi_sql(yeni_kelime, self.aktif_workspace):
                messagebox.showwarning("Kayıtlı", f"'{yeni_kelime}' bu çalışma alanında zaten ekli!", parent=ekle_pencere)
                return

            kelime_ekle_sql(yeni_kelime, yeni_kategori, self.aktif_workspace)
            self.listeyi_guncelle()
            self.kategorileri_guncelle() 
            self.otomatik_yedek_al()
            ekle_pencere.destroy()

        self.modern_btn(icerik, "Kelimeyi Ekle", "#3B82F6", "white", kaydet, self.font_bold).pack(fill=tk.X, pady=(5, 0))
        ekle_pencere.bind("<Return>", kaydet)

    def aramayi_temizle(self):
        self.arama_girisi.delete(0, tk.END)
        self.listeyi_guncelle()

    def onceki_sayfa(self):
        if self.sayfa_no > 1:
            self.sayfa_no -= 1
            self.listeyi_guncelle(self.aktif_filtre_kategori, sayfa_degisimi=True)

    def sonraki_sayfa(self):
        self.sayfa_no += 1
        self.listeyi_guncelle(self.aktif_filtre_kategori, sayfa_degisimi=True)

    def listeyi_guncelle(self, kategori_filtresi=None, sayfa_degisimi=False, arama_sifirlama=True):
        """arama_sifirlama eklendi ki canlı arama (live search) yaparken yazılan harf silinmesin."""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
            
        if not sayfa_degisimi:
            self.sayfa_no = 1
            
        self.aktif_filtre_kategori = kategori_filtresi
        arama_metni = getattr(self, 'arama_girisi', None)
        
        if kategori_filtresi:
            veriler = kelimeleri_kategori_filtrele_sql(kategori_filtresi, self.aktif_workspace)
            if self.arama_girisi and arama_sifirlama: self.arama_girisi.delete(0, tk.END)
        elif arama_metni and arama_metni.get().strip():
            veriler = kelimeleri_ara_sql(arama_metni.get().strip(), self.aktif_workspace)
        else:
            veriler = kelimeleri_getir_sql(self.aktif_workspace)

        toplam_kayit = len(veriler)
        baslangic = (self.sayfa_no - 1) * self.sayfa_basina_kayit
        bitis = baslangic + self.sayfa_basina_kayit
        gosterilecek_veriler = veriler[baslangic:bitis]
        
        if hasattr(self, 'sayfa_bilgisi_lbl'):
            toplam_sayfa = (toplam_kayit // self.sayfa_basina_kayit) + (1 if toplam_kayit % self.sayfa_basina_kayit > 0 else 0)
            if toplam_sayfa == 0: toplam_sayfa = 1
            
            self.sayfa_bilgisi_lbl.config(text=f"Sayfa: {self.sayfa_no} / {toplam_sayfa}  (Bulunan: {toplam_kayit})")
            
            if self.sayfa_no <= 1:
                self.onceki_sayfa_btn.config(state=tk.DISABLED, bg="#D1D5DB", cursor="arrow")
            else:
                self.onceki_sayfa_btn.config(state=tk.NORMAL, bg="#9CA3AF", cursor="hand2")
                
            if self.sayfa_no >= toplam_sayfa:
                self.sonraki_sayfa_btn.config(state=tk.DISABLED, bg="#D1D5DB", cursor="arrow")
            else:
                self.sonraki_sayfa_btn.config(state=tk.NORMAL, bg="#9CA3AF", cursor="hand2")

        for satir in gosterilecek_veriler:
            kelime_id, kelime, kategori = satir
            
            satir_frame = tk.Frame(self.scrollable_frame, bg=self.card_bg, pady=10)
            satir_frame.pack(fill=tk.X, pady=3)

            tk.Label(satir_frame, text=kelime, width=20, font=self.font_main, bg=self.card_bg, fg=self.text_fg, anchor="w").pack(side=tk.LEFT, padx=15)
            
            kat_frame = tk.Frame(satir_frame, bg=self.card_bg, width=200, height=30)
            kat_frame.pack_propagate(False) 
            kat_frame.pack(side=tk.LEFT, padx=15, fill=tk.Y)
            
            etiketler = [e.strip() for e in kategori.split(',') if e.strip()]
            for etiket in etiketler:
                kat_label = tk.Label(kat_frame, text=f" {etiket} ", font=("Segoe UI", 8, "bold"), bg=self.tag_bg, fg=self.tag_fg, relief="flat")
                kat_label.pack(side=tk.LEFT, padx=2, pady=2)

            buton_frame = tk.Frame(satir_frame, bg=self.card_bg)
            buton_frame.pack(side=tk.RIGHT, padx=15)

            def action_btn(parent, text, bg, cmd):
                return tk.Button(parent, text=text, command=cmd, bg=bg, fg="white", font=("Segoe UI", 9, "bold"),
                                 relief="flat", borderwidth=0, cursor="hand2", padx=10, pady=4, width=6)

            action_btn(buton_frame, "Kopyala", "#10B981", lambda k=kelime: self.kelime_kopyala(k)).pack(side=tk.LEFT, padx=3)
            action_btn(buton_frame, "Düzenle", "#F59E0B", lambda i=kelime_id, k=kelime, c=kategori: self.kelime_duzenle(i, k, c)).pack(side=tk.LEFT, padx=3)
            action_btn(buton_frame, "Sil", "#EF4444", lambda i=kelime_id, k=kelime: self.kelime_sil(i, k)).pack(side=tk.LEFT, padx=3)

    def kelime_kopyala(self, secili_kelime):
        self.pencere.clipboard_clear()
        self.pencere.clipboard_append(secili_kelime)
        self.pencere.update() 

    def kelime_sil(self, kelime_id, secili_kelime):
        cevap = messagebox.askyesno("Silme Onayı", f"'{secili_kelime}' kelimesini silmek istediğinize emin misiniz?")
        if cevap: 
            kelime_sil_sql(kelime_id)
            self.listeyi_guncelle()
            self.kategorileri_guncelle() 
            self.otomatik_yedek_al()

    def kelime_duzenle(self, kelime_id, mevcut_kelime, mevcut_kategori):
        duzenle_pencere = tk.Toplevel(self.pencere)
        duzenle_pencere.title("Kelime Düzenle")
        self.pencere_ortala(duzenle_pencere, 350, 250) 
        duzenle_pencere.configure(bg=self.bg_color)
        duzenle_pencere.grab_set() 

        icerik = tk.Frame(duzenle_pencere, bg=self.card_bg, padx=20, pady=20)
        icerik.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        tk.Label(icerik, text="Yeni Kelime:", font=self.font_bold, bg=self.card_bg, fg=self.text_fg).pack(anchor="w", pady=(0, 5))
        yeni_kelime_girisi = ttk.Entry(icerik, width=40, font=self.font_main)
        yeni_kelime_girisi.insert(0, mevcut_kelime)
        yeni_kelime_girisi.pack(pady=(0, 15))

        tk.Label(icerik, text="Yeni Kategori / Tag:", font=self.font_bold, bg=self.card_bg, fg=self.text_fg).pack(anchor="w", pady=(0, 5))
        yeni_kategori_girisi = ttk.Entry(icerik, width=40, font=self.font_main)
        yeni_kategori_girisi.insert(0, mevcut_kategori)
        yeni_kategori_girisi.pack(pady=(0, 15))

        def kaydet():
            guncel_k = yeni_kelime_girisi.get().strip()
            guncel_kat = yeni_kategori_girisi.get().strip()
            if not guncel_k or not guncel_kat:
                messagebox.showwarning("Eksik Bilgi", "Alanlar boş bırakılamaz!", parent=duzenle_pencere)
                return
                
            kelime_guncelle_sql(kelime_id, guncel_k, guncel_kat)
            self.listeyi_guncelle()
            self.kategorileri_guncelle()
            self.otomatik_yedek_al()
            duzenle_pencere.destroy()
            messagebox.showinfo("Başarılı", "Kelime başarıyla güncellendi!")

        self.modern_btn(icerik, "Değişiklikleri Kaydet", "#F59E0B", "white", kaydet, self.font_bold).pack(fill=tk.X, pady=(5, 0))

    def verileri_disa_aktar(self):
        dosya_yolu = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Dosyaları", "*.json"), ("Tüm Dosyalar", "*.*")],
            title="Yedek Al (Dışa Aktar)",
            initialfile=f"backup_{self.aktif_workspace}.json"
        )
        if not dosya_yolu: return

        try:
            veriler = kelimeleri_getir_sql(self.aktif_workspace)
            json_verisi = [{"id": satir[0], "kelime": satir[1], "kategori": satir[2]} for satir in veriler]
            with open(dosya_yolu, mode='w', encoding='utf-8') as dosya:
                json.dump(json_verisi, dosya, ensure_ascii=False, indent=4)
            messagebox.showinfo("Başarılı", f"Verileriniz güvenle dışa aktarıldı!\n\nDosya: {dosya_yolu}")
        except Exception as e:
            messagebox.showerror("Hata", f"Dışa aktarılırken bir sorun oluştu:\n{e}")

    def verileri_ice_aktar(self):
        dosya_yolu = filedialog.askopenfilename(
            filetypes=[("JSON Dosyaları", "*.json"), ("Tüm Dosyalar", "*.*")],
            title="Yedekten Yükle (İçe Aktar)"
        )
        if not dosya_yolu: return

        try:
            eklenen_adet = 0
            with open(dosya_yolu, mode='r', encoding='utf-8') as dosya:
                json_verisi = json.load(dosya)

                if isinstance(json_verisi, list):
                    for satir in json_verisi:
                        kelime = satir.get("kelime", "").strip()
                        kategori = satir.get("kategori", "").strip()
                        
                        if kelime and kategori:
                            if not kelime_var_mi_sql(kelime, self.aktif_workspace):
                                kelime_ekle_sql(kelime, kategori, self.aktif_workspace)
                                eklenen_adet += 1
                else:
                    messagebox.showwarning("Hata", "Seçilen dosya geçerli bir yedekleme formatında değil.")
                    return

            self.listeyi_guncelle()
            self.kategorileri_guncelle() 
            self.otomatik_yedek_al()
            messagebox.showinfo("Başarılı", f"{eklenen_adet} adet yeni kelime '{self.aktif_workspace}' alanına başarıyla aktarıldı!")
        except json.JSONDecodeError:
            messagebox.showerror("Hata", "Dosya bozuk veya geçerli bir JSON dosyası değil.")
        except Exception as e:
            messagebox.showerror("Hata", f"İçe aktarılırken bir sorun oluştu:\n{e}")

if __name__ == "__main__":
    ana_pencere = tk.Tk()
    uygulama = KelimeUygulamasi(ana_pencere)
    ana_pencere.mainloop()
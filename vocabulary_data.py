"""
Novaboard - MEB 8. ve 9. Sınıf Müfredatına Uygun B1 Seviyesi Kelime Havuzu.
Her kayıt: {"word": İngilizce kelime, "type": tür etiketi, "options": [doğru_anlam, çeldirici_1, çeldirici_2, çeldirici_3]}
Not: options[0] her zaman doğru cevaptır; soru sorulurken şıklar karıştırılır.
"""

B1_VOCABULARY = [
    # --- Ünite: Friendship & Personal Qualities (Arkadaşlık & Kişilik) ---
    {"word": "Friendship", "type": "İsim (Noun)", "options": ["Arkadaşlık, dostluk", "Düşmanlık", "Yalnızlık", "Kıskançlık"]},
    {"word": "Honest", "type": "Sıfat (Adjective)", "options": ["Dürüst, doğru sözlü", "Yalancı", "Korkak", "Cimri"]},
    {"word": "Generous", "type": "Sıfat (Adjective)", "options": ["Cömert, eli açık", "Bencil", "Kaba", "Tembel"]},
    {"word": "Support", "type": "Fiil / İsim", "options": ["Desteklemek", "Engel olmak", "Yalnız bırakmak", "Kızdırmak"]},
    {"word": "Trust", "type": "Fiil / İsim", "options": ["Güvenmek", "Şüphelenmek", "Korkmak", "Reddetmek"]},
    {"word": "Count on", "type": "Deyimsel Fiil", "options": ["Güvenmek, bel bağlamak", "Vazgeçmek", "Unutmak", "Kavga etmek"]},
    {"word": "Invite", "type": "Fiil (Verb)", "options": ["Davet etmek", "Kovmak", "Yasaklamak", "Cezalandırmak"]},
    {"word": "Accept", "type": "Fiil (Verb)", "options": ["Kabul etmek", "Reddetmek", "Ertelemek", "Şikayet etmek"]},
    {"word": "Refuse", "type": "Fiil (Verb)", "options": ["Reddetmek", "Kabul etmek", "Özür dilemek", "Tebrik etmek"]},
    {"word": "Apologize", "type": "Fiil (Verb)", "options": ["Özür dilemek", "Suçlamak", "Kızmak", "Gülmek"]},
    {"word": "Promise", "type": "Fiil / İsim", "options": ["Söz vermek", "Unutmak", "Yalan söylemek", "Şüphe etmek"]},
    {"word": "Secret", "type": "İsim / Sıfat", "options": ["Sır, gizli", "Haber", "Duyuru", "Plan"]},

    # --- Ünite: Teen Life & Daily Routine (Genç Yaşamı & Rutinler) ---
    {"word": "Exciting", "type": "Sıfat (Adjective)", "options": ["Heyecan verici", "Sıkıcı", "Yorucu", "Korkunç"]},
    {"word": "Prefer", "type": "Fiil (Verb)", "options": ["Tercih etmek", "Vazgeçmek", "Nefret etmek", "Zorunda olmak"]},
    {"word": "Habit", "type": "İsim (Noun)", "options": ["Alışkanlık", "Kural", "Yasak", "Ceza"]},
    {"word": "Confident", "type": "Sıfat (Adjective)", "options": ["Özgüvenli", "Utangaç", "Korkak", "Kararsız"]},
    {"word": "Patient", "type": "Sıfat (Adjective)", "options": ["Sabırlı", "Aceleci", "Öfkeli", "Tembel"]},
    {"word": "Polite", "type": "Sıfat (Adjective)", "options": ["Kibar, nazik", "Kaba", "Saygısız", "Bencil"]},
    {"word": "Spend", "type": "Fiil (Verb)", "options": ["Harcamak", "Kazanmak", "Biriktirmek", "Ödünç almak"]},
    {"word": "Save", "type": "Fiil (Verb)", "options": ["Biriktirmek, kurtarmak", "Harcamak", "Kaybetmek", "Yok etmek"]},

    # --- Ünite: In The Kitchen & Food (Mutfakta & Yemekler) ---
    {"word": "Recipe", "type": "İsim (Noun)", "options": ["Yemek tarifi", "Menü", "Fatura", "Liste"]},
    {"word": "Ingredient", "type": "İsim (Noun)", "options": ["Malzeme, içindekiler", "Yemek tabağı", "Baharat kutusu", "Fırın"]},
    {"word": "Prepare", "type": "Fiil (Verb)", "options": ["Hazırlamak", "Yıkamak", "Bitirmek", "Tüketmek"]},
    {"word": "Delicious", "type": "Sıfat (Adjective)", "options": ["Lezzetli", "Tatsız", "Bayat", "Acı"]},
    {"word": "Boil", "type": "Fiil (Verb)", "options": ["Kaynatmak, haşlamak", "Kızartmak", "Dondurmak", "Doğramak"]},
    {"word": "Chop", "type": "Fiil (Verb)", "options": ["Doğramak", "Karıştırmak", "Pişirmek", "Dökmek"]},

    # --- Ünite: On The Phone & Communication (Telefonda & İletişim) ---
    {"word": "Available", "type": "Sıfat (Adjective)", "options": ["Müsait, uygun", "Meşgul", "Uzak", "Kapalı"]},
    {"word": "Connect", "type": "Fiil (Verb)", "options": ["Bağlanmak", "Ayrılmak", "Kapatmak", "İptal etmek"]},
    {"word": "Leave a message", "type": "İfade (Phrase)", "options": ["Mesaj bırakmak", "Geri aramak", "Telefonu kapatmak", "Meşgule atmak"]},
    {"word": "Hang up", "type": "Deyimsel Fiil", "options": ["Telefonu kapatmak", "Cevap vermek", "Mesaj yazmak", "Bekletmek"]},
    {"word": "Hold on", "type": "Deyimsel Fiil", "options": ["Hatta beklemek", "Telefonu açmak", "Numarayı silmek", "Konuşmak"]},

    # --- Ünite: The Internet & Technology (İnternet & Teknoloji) ---
    {"word": "Download", "type": "Fiil (Verb)", "options": ["İndirmek", "Yüklemek", "Silmek", "Paylaşmak"]},
    {"word": "Upload", "type": "Fiil (Verb)", "options": ["Yüklemek", "İndirmek", "Kapatmak", "Aramak"]},
    {"word": "Search", "type": "Fiil / İsim", "options": ["Aramak, araştırmak", "Kaydetmek", "Gizlemek", "Yazmak"]},
    {"word": "Account", "type": "İsim (Noun)", "options": ["Hesap", "Şifre", "Adres", "Telefon"]},
    {"word": "Device", "type": "İsim (Noun)", "options": ["Cihaz, alet", "Program", "Kablo", "Ekran"]},

    # --- Ünite: Adventures & Sports (Maceralar & Spor) ---
    {"word": "Dangerous", "type": "Sıfat (Adjective)", "options": ["Tehlikeli", "Güvenli", "Kolay", "Sıkıcı"]},
    {"word": "Explore", "type": "Fiil (Verb)", "options": ["Keşfetmek", "Kaybolmak", "Korkmak", "Dönmek"]},
    {"word": "Equipment", "type": "İsim (Noun)", "options": ["Ekipman, teçhizat", "Ödül", "Kurallar", "Sporcu"]},
    {"word": "Brave", "type": "Sıfat (Adjective)", "options": ["Cesur", "Korkak", "Çekingen", "Sessiz"]},
    {"word": "Challenge", "type": "İsim / Fiil", "options": ["Meydan okuma", "Kolaylık", "Mola", "Ödül"]},

    # --- Ünite: Tourism & Travel (Turizm & Seyahat) ---
    {"word": "Attraction", "type": "İsim (Noun)", "options": ["Turistik yer", "Havalimanı", "Bilet gişesi", "Otel odası"]},
    {"word": "Destination", "type": "İsim (Noun)", "options": ["Varış noktası", "Kalkış saati", "Bilet", "Yolculuk"]},
    {"word": "Ancient", "type": "Sıfat (Adjective)", "options": ["Antik, tarihi", "Modern", "Yeni", "Geçici"]},
    {"word": "Tradition", "type": "İsim (Noun)", "options": ["Gelenek, görenek", "Kanun", "Moda", "Yenilik"]},
    {"word": "Crowded", "type": "Sıfat (Adjective)", "options": ["Kalabalık", "Tenha", "Sessiz", "Temiz"]},

    # --- Ünite: Chores & Responsibilities (Ev İşleri & Sorumluluklar) ---
    {"word": "Responsible", "type": "Sıfat (Adjective)", "options": ["Sorumlu, mesul", "Tembel", "Masum", "Uzak"]},
    {"word": "Rule", "type": "İsim (Noun)", "options": ["Kural", "Öneri", "Oyun", "Tavsiye"]},
    {"word": "Tidy", "type": "Sıfat / Fiil", "options": ["Düzenli", "Dağınık", "Kirli", "Eski"]},
    {"word": "Dust", "type": "Fiil / İsim", "options": ["Toz almak", "Yıkamak", "Süpürmek", "Boyamak"]},

    # --- Ünite: Science & Inventions (Bilim & İcatlar) ---
    {"word": "Scientist", "type": "İsim (Noun)", "options": ["Bilim insanı", "Öğrenci", "Mühendis", "Doktor"]},
    {"word": "Discover", "type": "Fiil (Verb)", "options": ["Keşfetmek", "Kaybetmek", "Gizlemek", "Bozmak"]},
    {"word": "Invent", "type": "Fiil (Verb)", "options": ["İcat etmek", "Kopyalamak", "Satın almak", "Yıkmak"]},
    {"word": "Experiment", "type": "İsim (Noun)", "options": ["Deney", "Sınav", "Ders kitabı", "Ödev"]},
    {"word": "Achieve", "type": "Fiil (Verb)", "options": ["Başarmak", "Yenilmek", "Vazgeçmek", "Unutmak"]},
    {"word": "Improve", "type": "Fiil (Verb)", "options": ["Geliştirmek", "Bozmak", "Duraklatmak", "Zayıflatmak"]},

    # --- Ünite: Natural Forces & Environment (Doğal Afetler & Çevre) ---
    {"word": "Disaster", "type": "İsim (Noun)", "options": ["Afet, felaket", "Kutlama", "Fırsat", "Başarı"]},
    {"word": "Earthquake", "type": "İsim (Noun)", "options": ["Deprem", "Sel", "Fırtına", "Yangın"]},
    {"word": "Survive", "type": "Fiil (Verb)", "options": ["Hayatta kalmak", "Yenilmek", "Kaybolmak", "Terk etmek"]},
    {"word": "Environment", "type": "İsim (Noun)", "options": ["Çevre, doğa", "Bina", "Yol", "Şehir"]},
    {"word": "Pollution", "type": "İsim (Noun)", "options": ["Kirlilik", "Temizlik", "Geri dönüşüm", "Tasarruf"]},
    {"word": "Protect", "type": "Fiil (Verb)", "options": ["Korumak", "Zarar vermek", "Yok etmek", "Yıkmak"]},
    {"word": "Recycle", "type": "Fiil (Verb)", "options": ["Geri dönüştürmek", "Çöpe atmak", "Yakmak", "İsraf etmek"]},
    {"word": "Waste", "type": "Fiil / İsim", "options": ["İsraf etmek, atık", "Tasarruf etmek", "Kazanmak", "Korumak"]},

    # --- Ünite: Health & Emergency (Sağlık & Acil Durum) ---
    {"word": "Emergency", "type": "İsim (Noun)", "options": ["Acil durum", "Tatil", "Randevu", "Tören"]},
    {"word": "Injury", "type": "İsim (Noun)", "options": ["Yaralanma", "Tedavi", "İlaç", "Sağlık"]},
    {"word": "Treatment", "type": "İsim (Noun)", "options": ["Tedavi", "Hastalık", "Ameliyat", "Kaza"]},
    {"word": "Medicine", "type": "İsim (Noun)", "options": ["İlaç, tıp", "Zehir", "Yara bandı", "Hastane"]},
    {"word": "Healthy", "type": "Sıfat (Adjective)", "options": ["Sağlıklı", "Hasta", "Yorgun", "Zayıf"]},

    # --- Ek B1 Müfredat Kelimeleri ---
    {"word": "Opportunity", "type": "İsim (Noun)", "options": ["Fırsat, olanak", "Tehlike", "Zorunluluk", "Gecikme"]},
    {"word": "Experience", "type": "İsim / Fiil", "options": ["Deneyim, tecrübe", "Teori", "Rüya", "Gelecek"]},
    {"word": "Decision", "type": "İsim (Noun)", "options": ["Karar", "Şüphe", "Tavsiye", "Dilek"]},
    {"word": "Advice", "type": "İsim (Noun)", "options": ["Tavsiye, öğüt", "Emir", "Yasak", "Eleştiri"]},
    {"word": "Explain", "type": "Fiil (Verb)", "options": ["Açıklamak", "Soru sormak", "Gizlemek", "İtiraz etmek"]},
    {"word": "Notice", "type": "Fiil / İsim", "options": ["Fark etmek", "Gözden kaçırmak", "İptal etmek", "Yalanlamak"]},
    {"word": "Remember", "type": "Fiil (Verb)", "options": ["Hatırlamak", "Unutmak", "Şaşırmak", "Korkmak"]},
    {"word": "Forget", "type": "Fiil (Verb)", "options": ["Unutmak", "Hatırlamak", "Öğrenmek", "Sevmek"]},
    {"word": "Borrow", "type": "Fiil (Verb)", "options": ["Ödünç almak", "Ödünç vermek", "Satın almak", "Hediye etmek"]},
    {"word": "Lend", "type": "Fiil (Verb)", "options": ["Ödünç vermek", "Ödünç almak", "Kaybetmek", "Satmak"]},
    {"word": "Careful", "type": "Sıfat (Adjective)", "options": ["Dikkatli", "Dikkatsiz", "Aceleci", "Korkak"]},
    {"word": "Curious", "type": "Sıfat (Adjective)", "options": ["Meraklı", "İlgisiz", "Sıkılmış", "Uykulu"]},
    {"word": "Useful", "type": "Sıfat (Adjective)", "options": ["Yararlı, faydalı", "Gereksiz", "Zararlı", "Eski"]},
    {"word": "Difficult", "type": "Sıfat (Adjective)", "options": ["Zor, güç", "Kolay", "Basit", "Hafif"]},
    {"word": "Necessary", "type": "Sıfat (Adjective)", "options": ["Gerekli, zorunlu", "İsteğe bağlı", "Faydasız", "Zararlı"]},
    {"word": "Famous", "type": "Sıfat (Adjective)", "options": ["Ünlü, meşhur", "Bilinmeyen", "Sıradan", "Yabancı"]},
    {"word": "Safe", "type": "Sıfat (Adjective)", "options": ["Güvenli, emin", "Tehlikeli", "Korkunç", "Zorlu"]},
]


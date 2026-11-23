# SYSTEM DESIGN & ARCHITECTURE RULES (Developer-Grade / Anti-AI Specification)

Bu doküman, projenin tüm kullanıcı arayüzü (UI), ses mimarisi ve etkileşim bileşenleri için bağlayıcı mühendislik standartlarını tanımlar. Tüm yeni özellikler ve refactoring işlemleri **Claude Code, Linear ve Raycast** kalitesinde yüksek yoğunluklu, mekanik ve profesyonel bir araç (developer-grade utility) hissi vermelidir.

---

## 1. UI & Görsel Mimari (Anti-AI Tasarım Kuralları)

### 1.1 Renk Paleti (Monokrom & Tek Vurgu)
- **Yasaklı Öğeler:** Mor/pembe/mavi AI gradientleri, parlak neon gölgeler (`drop-shadow`), glassmorphism (bulanık cam) ve dekoratif emoji yığınları kesinlikle kullanılmaz.
- **Zemin Katmanları (Zinc / Carbon Monokrom):**
  - Ana Zemin (`bg_main`): `#09090b` (Zinc 950)
  - Yan Panel & Kart Zemini (`bg_sidebar`, `bg_card`): `#121214` (Carbon 900)
  - İç Yüzey & Girdi Zemini (`bg_card_inner`, `input_bg`): `#18181b` (Zinc 900)
  - Etkileşim / Hover (`bg_hover`): `#27272a` (Zinc 800)
- **İşlevsel Vurgu Rengi (Functional Accent):**
  - Birincil Vurgu (`accent`): Keskin Zümrüt `#10b981` (veya Terminal Amber `#f59e0b`)
  - Durum Renkleri: Başarı `#10b981` (`bg: #052e16`), Uyarı `#f59e0b` (`bg: #451a03`), Hata/Silme `#ef4444` (`bg: #450a0a`).

### 1.2 Kenarlıklar ve Geometri
- Kalın gölgeler yerine `1px` inceliğinde, keskin ve düşük kontrastlı kenarlıklar (`#27272a` / `border-zinc-800/80`) kullanılır.
- Köşe yuvarlaklıkları minimumda tutulur (`4px` – `6px`, `rounded-sm` / `rounded-md`).

### 1.3 Tipografi
- **Monospace Zorunluluğu:** Tüm sayısal veriler, sayaçlar, sıra numaraları, gecikme (`latency`) ölçümleri, durum rozetleri (`[READY]`, `[PICKED]`, `[EXEMPT]`), diff satırları ve mikro loglar için monospaced font (`JetBrains Mono`, `Fira Code`, `Consolas` veya `DejaVu Sans Mono`) kullanılır.
- **Başlık ve Kontroller:** Sıkı harf aralığına sahip temiz sans-serif (`Inter`, `Geist`, `Segoe UI`) tercih edilir.

### 1.4 Bilgi Yoğunluğu (High Information Density)
- Gereksiz boşluklar (padding/margin) daraltılır; satır yükseklikleri kompakt (`26px` – `32px`) tutulur.
- Kullanıcı bir sohbet botuyla değil, yüksek hassasiyetli bir IDE / Terminal kontrol paneliyle etkileşime giriyormuş hissi almalıdır.

---

## 2. Ses Mimarisi (Sıfır Latanslı Mekanik Sesler)

- **Yasaklı Öğeler:** Hazır `.mp3`/`.wav` bildirim dosyaları, bilimkurgu efektleri veya tiz PC buzzer bipleri kullanılmaz.
- **Gerçek Zamanlı Sentezleme (Real-Time Synthesis):**
  - Masaüstünde (`sound_effects.py`) PCM dalga sentezi, web/tarayıcı katmanında (`soundEngine.ts`) **Web Audio API** kullanılarak sıfır gecikmeyle üretilir:
    1. **Stream / Yazım & Seçim Tıkırtısı (`play_tick` / `playStreamTick`):** `150Hz – 380Hz` bandında çok kısa (`12ms – 22ms`), düşük genlikli mekanik anahtar / röle darbesi (impulse).
    2. **Onay / Tamamlanma Sesi (`play_reveal` / `playConfirmClick`):** Tiz zil yerine fiziksel bir mekanik anahtarın kapanma hissi veren kısa, tok ve kuru `"click/thud"` (`180Hz -> 95Hz` + `320Hz` transient).
    3. **Hata / Uyarı Sesi (`play_error` / `playErrorTone`):** Rahatsız edici alarm yerine düşük frekanslı (`140Hz -> 110Hz`), kısa mekanik uyarı darbesi.
- **Hızlı Ses Anahtarı:** Arayüzün durum çubuğunda tek tıkla sesi açıp kapatan minimalist `AUDIO: ON` / `AUDIO: OFF` anahtarı her zaman görünür olmalıdır.

---

## 3. Claude Code Tarzı Ajan & Mühendislik Bileşenleri

- **Context & Telemetry Status Bar:** Alt durum çubuğunda aktif veri bağlamı (`CTX`), kayıt/token yoğunluğu, son işlem gecikmesi (`LATENCY: X.Xms`) ve hızlı `AUDIO: ON/OFF` kontrolü yer alır.
- **Minimalist Diff Görüntüleyici:** Toplu veri veya liste değişikliklerinde satır numaralı, `+` (yeşil `#052e16` zemin / `#4ade80` metin) ve `-` (kırmızı `#450a0a` zemin / `#f87171` metin) vurgulu Git Diff önizlemesi sunulur.
- **Komut & Akış Logları (Micro-Logs):** Dönen yükleme ikonları yerine durum çubuğunda monospaced mikro log satırları (`> Reading roster...`, `> Computing diff...`, `> Selecting candidate...`) gösterilir.

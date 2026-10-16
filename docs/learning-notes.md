# Learning Notes: invoice-to-emissions

Bu dosya, projeyi yaparken öğrendiğim komutları ve kavramları topladığım çalışma günlüğüm.
Gizli bilgi (anahtar, şifre, gerçek veri) buraya yazılmaz.

## Her oturumun başlangıcı

1. Terminali aç
2. `conda activate invoice-emissions` (satır başında `(invoice-emissions)` görünmeli)
3. `cd ~/projects/invoice-to-emissions`
4. `pwd` ile yerimi, `git status` ile durumu kontrol et

## Terminal komutları

| Komut | Ne yapar |
|---|---|
| `pwd` | Şu anki klasörü gösterir |
| `ls` / `ls -a` | Dosyaları listeler / gizlileri de gösterir |
| `cd klasör` / `cd ..` | Klasöre girer / bir üste çıkar |
| `mkdir -p yol` | Klasör açar, iç içe olanları birden |
| `touch dosya` | Boş dosya oluşturur |
| `head -5 dosya` | Dosyanın ilk 5 satırını gösterir |
| `open dosya` | Dosyayı Mac'in varsayılan uygulamasında açar |
| `cat > dosya << 'BİTİŞ'` | Yapıştırdığım metni dosyaya yazar (üzerine yazar) |
| `cat >> dosya << 'BİTİŞ'` | Metni dosyanın sonuna ekler |
| `history 1` | Yazdığım tüm komutların listesi |

Dikkat: `>` dosyanın üzerine yazar. Bitiş kelimesi tırnak içinde olmalı, metnin içinde de geçmemeli.

## Conda ve pip

| Komut | Ne yapar |
|---|---|
| `conda create -n isim python=3.11` | Ortam oluşturur (bir kez) |
| `conda activate isim` | Ortamı açar (her yeni terminalde) |
| `conda env list` | Ortamları listeler |
| `pip install paket` | Kütüphane kurar |
| `pip install -r requirements.txt` | Listedeki tüm kütüphaneleri kurar |

Dikkat: `(base)` yazıyorsa yanlış ortamdayım. Yeni kütüphane kurarsam `requirements.txt`'ye de eklemeliyim.

## Git komutları

| Komut | Ne yapar |
|---|---|
| `git config --global user.name "..."` | Adımı tanıtır (bir kez) |
| `git clone adres` | Repoyu indirir |
| `git checkout -b isim` | Yeni branch açar ve ona geçer |
| `git checkout isim` | Var olan branch'e geçer |
| `git branch` | Branch'leri listeler |
| `git status` | Ne değişti? (en sık kullanılan) |
| `git add .` | Değişiklikleri commit'e hazırlar |
| `git commit -m "mesaj"` | Kaydı alır (yalnızca bilgisayarımda) |
| `git push` | Commit'leri GitHub'a gönderir (şimdilik GitHub Desktop) |
| `git pull` | GitHub'daki yenilikleri indirir |
| `git log --oneline --all --graph` | Tüm geçmişi çizerek gösterir |
| `git diff` | Satır satır değişiklikleri gösterir |

Kurallar:
- Commit'ten önce `git status` bak. `.env`, `venv` ya da gerçek veri görünüyorsa commit etme.
- Commit mesajı kısa ve emir kipinde: `Add invoice schema with validation and tests`
- Önce `add`, sonra `commit`.
- Uzun çıktılardan `q` tuşuyla çıkılır.

## Git iş akışı (her iş için)

1. `git checkout main` ve `git pull` (güncel başla)
2. `git checkout -b feature/isim` (yeni branch)
3. Kodu yaz, `pytest` çalıştır
4. `git status`, `git add .`, `git commit -m "..."`
5. GitHub Desktop ile push (Publish branch)
6. GitHub'da Pull Request aç, açıklamaya `Closes #issue-numarası` yaz
7. Merge et, branch'i sil
8. Terminalde `git checkout main` ve `git pull`

## Python ve pytest

- `pytest`: `tests/` içindeki `test_*.py` dosyalarını bulur ve `test_` ile başlayan fonksiyonları çalıştırır.
- `assert koşul`: Koşul yanlışsa test başarısız olur.
- `with pytest.raises(Hata):` Bu blokta hata çıkması gerekir. Çıkarsa test geçer.
- Hata mesajlarında en önemli satır genelde en sondaki satırdır.
- Pydantic: `InvoiceData(**veri)` ile veriyi doğrularım. Hatalıysa `ValidationError` fırlatır.

```python
from src.schema import InvoiceData

inv = InvoiceData(
    invoice_type="electricity",
    period_start="2025-03-01",
    period_end="2025-03-31",
    quantity=1200,
    unit="kWh",
)
```

## Projedeki dosyalar

| Dosya | Ne işe yarar |
|---|---|
| `data/emission_factors.csv` | Kaynaklı emisyon faktörleri (UK DESNZ 2025) |
| `scripts/generate_invoices.py` | 16 sentetik fatura PDF'i ve ground truth üretir |
| `tests/ground_truth.csv` | Her faturanın doğru cevabı (doğruluk ölçümünün temeli) |
| `src/schema.py` | Fatura verisinin şeması ve doğrulama kuralları |
| `tests/test_factors.py` | Faktör tablosu kontrolü |
| `tests/test_ground_truth.py` | Ground truth ve faktör tablosu uyumu |
| `tests/test_schema.py` | Şema doğrulama testleri |
| `requirements.txt` | Gerekli kütüphaneler |

## Hata ve çözüm tablosu

| Hata | Sebep | Çözüm |
|---|---|---|
| `fatal: not a git repository` | Proje klasöründe değilim | `cd ~/projects/invoice-to-emissions` |
| `pytest: command not found` | Ortam açık değil | `conda activate invoice-emissions` |
| Satır başı `(base)` | Yanlış ortam | `conda activate invoice-emissions` |
| `ModuleNotFoundError` | Paket kurulu değil ya da yanlış ortam | Ortamı kontrol et, `pip install paket` |
| `nothing added to commit` | `git add` yapılmadı | `git add .` sonra commit |
| `403` (push/clone) | Kimlik doğrulama | GitHub Desktop ile gönder |
| `code: command not found` | VS Code komutu kurulu değil | Metin editörü olarak Jupyter ya da VS Code kur |
| CSV'de `ParserError` | Fazla virgül ya da tırnak sorunu | Metni çift tırnak içine al, ondalıkta nokta kullan |
| `Already up to date` ama dosya yok | PR henüz merge edilmedi | GitHub'da PR'ı kontrol et |

## Çalışma günlüğü

### Aşama 0: Hazırlık (Ekim 2026)
- Repo açıldı (public, MIT lisans), klonlandı, conda ortamı kuruldu
- Proje iskeleti commit'lendi, ilk Pull Request merge edildi
- Terminalden push 403 verdi, GitHub Desktop ile çözüldü
- Öğrendim: branch, commit, merge, Pull Request mantığı

### Aşama 1: Veri (Ekim 2026)
- Emisyon faktörü tablosu dolduruldu (UK DESNZ 2025: elektrik, doğalgaz kWh ve m3, dizel, benzin)
- 16 sentetik fatura ve ground truth üretildi, test yazıldı
- Öğrendim: faktör yılı aktivite yılıyla eşleşmeli, ondalıkta nokta kullanılmalı, ground truth tek kaynaktan üretilmeli
- PR #6 merge edildi

### Aşama 2: Şema ve hesaplama çekirdeği (9 Ekim 2026, devam ediyor)
- Pydantic şeması (`src/schema.py`) ve 5 test yazıldı, `7 passed`
- Sırada: `src/factors.py` (faktör eşleştirme, MWh'dan kWh'a dönüşüm) ve `src/calculate.py`

## Yeni günlük girişi şablonu

- Tarih ve aşama:
- Ne yaptım:
- Hangi hatayı aldım ve nasıl çözdüm:
- Öğrendiğim yeni komut ya da kavram:
- Sıradaki iş:

### Aşama 2: faktör eşleştirme (tarih)
- Ne yaptım:
- Öğrendiğim:

### Aşama 2 tamamlandı (9 Ekim 2026)
- Yazdıklarım: `src/factors.py` (faktör bulma, MWh'dan kWh'a dönüşüm), `src/calculate.py` (miktar x faktör, kg ve ton), `scripts/calculate_all.py` (16 fatura için toplu hesap)
- Testler: şema, faktör eşleştirme, hesaplama, altın değer testi (1000 kWh = 177 kg), toplam 18 test
- Öğrendiklerim:
  - Belirsiz ya da eksik faktörde sessiz tahmin yerine hata fırlatılır
  - Ondalık sayıları `pytest.approx` ile karşılaştır
  - Script'leri proje kökünden `python -m scripts.isim` ile çalıştır, aksi halde `src` bulunamaz
  - Üretilen çıktı klasörü (`output/`) commit'lenmez, `.gitignore`'a eklenir
  - `git add` ile dosya adı verirken dosyalar var olmalı
  - PR açıklamasındaki `Closes #N` numarası issue sayfasındaki gerçek numara olmalı
- Doğrulama: 4 faturayı Excel'de elle hesapladım, sonuçlar scriptle uyuştu (uyuşmadıysa buraya sebebini yaz)
- Sıradaki: Aşama 3, metin çıkarma (pdfplumber) ve regex ile alan çıkarma

### Aşama 3a: regex ile bilgi çıkarma (Ekim 2026)
- Yazdıklarım: `src/extract_rules.py` (PDF'ten metin okuma, regex ile alan çıkarma), `scripts/evaluate_rules.py` (alan bazında doğruluk ölçümü)
- Sonuç: 16 sentetik faturada tüm alanlarda 16/16 doğruluk
- Öğrendiklerim:
  - Önce ham metne bak, sonra regex yaz
  - Sayıyı değil etiketi çapa olarak ara
  - Bulamazsan tahmin etme, `None` döndür
  - %100 skor şüphelidir: kendi şablonuma göre yazdığım kuralı kendi şablonumda test ettim (döngüsel değerlendirme)
  - Kuralları geliştirdiğim veri ile test ettiğim veriyi ayrı tut
  - `ModuleNotFoundError` olunca önce dosya var mı (`ls`) diye bak
- Regex'in sınırı: farklı etiket ya da yazım gelince hiçbir alanı bulamıyor (denedim: "Energy used this month")
- Sıradaki: bilerek zor bir fatura seti, sonra yerel LLM (Ollama)

### Aşama 3a devamı: zor fatura seti (Ekim 2026)
- Yazdıklarım: `scripts/generate_messy_invoices.py` (13 elle tasarlanmış fatura, her birinde tek bir çarpıklık), `tests/ground_truth_messy.csv`
- Ölçüm scriptini güçlendirdim: `argparse` ile set seçimi, hataları `missed` (bulamadı) ve `wrong` (yanlış buldu) diye ayırdım
- Öğrendiklerim:
  - Ölçmeden önce tahmin yaz, sonra sonuçla karşılaştır
  - Zor seti yalnızca ölçmek için kullan, kuralları ona göre düzeltme
  - Eksik veri güvenli bir hatadır, yanlış veri tehlikeli bir hatadır (sessizce rapora girer)
  - Her test faturasına tek bir çarpıklık koyarsam hatanın nedenini bulmak kolaylaşır
  - Kontrol örneği (standart fatura) setin kendisinin bozuk olmadığını gösterir
  - `git branch -d` yalnızca merge edilmiş branch'i siler, `-D` kontrolü atlar
- Sonuç: 1/13 fatura tam doğru, alan bazında 89/117 doğru, 25 missed, 3 wrong (sessiz yanlışlar: #3 tutar, #9 tedarikçi, #10 miktar)
- Sıradaki: hataları analiz et, sonra yerel LLM (Ollama) ile aynı iki sette ölçüm

### Aşama 3b: yerel LLM ile bilgi çıkarma (Ekim 2026)
- Yazdıklarım: `src/extract_llm.py` (Ollama ile çıkarma, Pydantic şeması), `tests/test_extract_llm.py` (modeli taklit eden testler), `scripts/evaluate.py` (`--method rules|llm`, kritik alan ve süre ölçütleri), `scripts/debug_llm.py` (modelin ham cevabını gösterir), `docs/llm-experiments.md` (deney günlüğü)
- Kurulum: Ollama uygulaması ve `llama3.2:3b` modeli (2 GB). Python tarafında ayrıca `ollama` kütüphanesi gerekti: uygulama ile kütüphane iki ayrı parça
- Sonuçlar (kolay set, 16 fatura): ilk hali 0/16 tam doğru. Şemada tüm alanları zorunlu ama `null` olabilir yapınca 14/16 (kritik alanlar 15/16, 1 sessiz yanlış), fatura başına yaklaşık 3,7 sn
- Regex (zor set, 13 fatura): 1/13 tam doğru, kritik alanlar 5/13, 1 sessiz yanlış
- Teşhisler:
  - Model `Optional` alanları `null` yazmak yerine JSON'dan hiç yazmıyordu (anahtar yoktu). Sebep: şemada alanlar zorunlu değildi
  - Kontrollü deneyle (tedarikçi adını "RoadStar Petrol" yerine "RoadStar Fuels" yaptım) modelin yakıt cinsini tedarikçi adından çıkardığını kanıtladım
  - `01/02/2025` tarihini 2 Ocak okudu (gün ile ay yer değiştirdi)
- Öğrendiklerim:
  - Önce modelin ham cevabına bak, sonra düzelt: teşhis tahminimi çürüttü
  - Opsiyonel alan ile `null` değer farklı şeyler. Zorunlu ama `null` olabilir yapınca model karar vermek zorunda kalır
  - Tek değişiklik, tek ölçüm; her deneyi `docs/llm-experiments.md` dosyasına yaz
  - Kontrollü deney: tek şeyi değiştir (tedarikçi adı), sonucu karşılaştır
  - Modeli testte taklit et (mock), kendi kodunu test et
  - Geliştirme seti ile final sınavını ayrı tut: zor seti LLM ile henüz ölçmedim
  - Yer tutuculu komutu sonuç gelmeden çalıştırma, komut bitmeden yeni komut yapıştırma
  - `git checkout REF -- yol` dosyaları aynı anda commit'e hazır hale getirir, karışık commit buradan çıktı
- Sıradaki: Deney 2 (yakıt cinsini ürün satırından belirlet), Deney 3 (tarihi modele yazıldığı gibi okutup kodda çevir), zor sette final ölçüm, sonra hibrit mantık

## Ek komutlar (Aşama 3)

Ollama:
- `ollama --version`, `ollama list`, `ollama pull model`: kurulumu ve indirilen modelleri gösterir/indirir
- `ollama run model "soru"`: modele terminalden soru sorar (`/bye` ile çıkılır)
- `ollama ps`: bellekte yüklü modeli gösterir
- `curl http://localhost:11434`: "Ollama is running" yazarsa sunucu açık
- `open -a Ollama`: Ollama uygulamasını açar

Terminal:
- `komut | tee dosya`: çıktıyı hem ekrana hem dosyaya yazar
- `komut | grep METİN`: yalnızca o metni içeren satırları gösterir (`grep -n` satır numarasıyla)
- `sed -i '' 's#eski#yeni#' dosya`: dosyada bul-değiştir (macOS)
- `time komut`: komutun süresini ölçer
- `uname -m`: `arm64` ise Apple Silicon
- `which python`: hangi Python'un çalıştığını gösterir (ortam doğru mu?)
- `python -m scripts.isim`: script'i proje kökünden çalıştırır

Git:
- `git fetch`: GitHub'daki yenilikleri öğrenir ama dosyalara dokunmaz (`git pull` ise indirip uygular)
- `git restore --staged .`: commit'e hazırlananları geri çeker, dosyalara dokunmaz
- `git mv eski yeni`: dosyayı geçmişi koruyarak yeniden adlandırır
- `git checkout REF -- yol`: başka bir branch'ten dosya getirir ve commit'e hazır hale de getirir
- `git branch -a`: GitHub'daki branch'ler dahil hepsini listeler
- `git branch --show-current`: bulunduğum branch'i yazar
- `git --no-pager diff --staged --stat`: commit'e hazır değişikliklerin özeti (sayfalayıcı yok)

Ek hatalar:
- `unknown option staged` ya da `not a git repository`: proje klasöründe değilim, satır başında `(invoice-emissions)` ve klasör adına bak
- `ModuleNotFoundError: ollama`: Python kütüphanesi kurulu değil (`python -m pip install ollama`)
- `Connection refused`: Ollama kapalı, `open -a Ollama`
- Satır başında `heredoc>` ya da `dquote>`: komut bitmemiş ya da tırnak açık kalmış, `Ctrl+C` ile çık
- Ekranın altında `:` ve takılma: Git sayfalayıcısı, `q` ile çık

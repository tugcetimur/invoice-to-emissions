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

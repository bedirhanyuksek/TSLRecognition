# TIDSignRN Proje Durumu ve To-Do Listesi

Bu dosya, proje başka bir araçta veya başka bir hesapta devam ettirilebilsin diye tutulur. Yeni bir aşamaya başlamadan önce bu dosyayı ve son git commit'lerini kontrol et.

## Mevcut Durum

- Proje klasörü: `<repo-root>`
- Avatar Unity proje klasörü: `<unity-project>`
- Mobil uygulama: React Native Android prototipi
- Backend: FastAPI, repo içindeki `server/` klasöründe
- Model çalıştırma şekli: İlk prototipte model telefonda değil, Mac üzerindeki FastAPI backend'de çalışıyor
- Canlı tahmin akışı: Telefon kamerasından kısa frame pencereleri alınır, backend'e gönderilir, backend MediaPipe landmark çıkarır, sign gate + 226 sınıflı TCN model ile tahmin döner
- Backend manuel URL örneği: `http://<backend-host>:8000`
- Son commit: `b964783 Add live prediction stabilization`

## Kullanılan Modeller

- Kelime modeli: `server/models/landmark_tcn_full.pt`
- İşaret var/yok modeli: `server/models/sign_gate.pt`
- MediaPipe model dosyası: `server/models/holistic_landmarker.task`
- Sınıf listesi: `server/models/SignList_ClassId_TR_EN.csv`
- Sınıf metrikleri: `server/models/class_metrics.csv`

Not: `.pt` model dosyaları git'e girmemeli. `server/models/*.pt` gitignore içinde kalmalı.

## Backend Başlatma

```bash
cd <repo-root>
PYTHONPATH=server .venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Backend kontrol:

```bash
curl http://127.0.0.1:8000/health
```

Telefonla aynı Wi-Fi'da test için Mac IP'sini bul:

```bash
ifconfig | grep 'inet '
```

Uygulamadaki backend URL alanına şuna benzer adres gir:

```text
http://MAC_WIFI_IP:8000
```

Örnek:

```text
http://<backend-host>:8000
```

## Mobil Uygulamayı Çalıştırma

```bash
cd <repo-root>
npx react-native run-android
```

Statik kontroller:

```bash
npm run lint
npx tsc --noEmit
```

Android build kontrol:

```bash
cd <repo-root>/android
./gradlew assembleDebug
```

## Tamamlanan Checkpoint'ler

- [x] React Native Android prototipi oluşturuldu
  - Commit: `2be18b5 Create TID translator React Native prototype`
  - Canlı, Avatar, Geçmiş, Ayarlar ekranları eklendi
  - UI ilk prototip olarak düzenlendi

- [x] Backend iskeleti eklendi
  - Commit: `2ac8e3e Add inference backend skeleton`
  - `server/` altında FastAPI yapısı kuruldu
  - `GET /health` ve temel prediction endpoint yapısı hazırlandı

- [x] Model metadata ve model yükleme bağlandı
  - Commit: `d2236b0 Wire model metadata and loading`
  - TCN kelime modeli ve sign gate modeli okunabilir hale getirildi
  - Model config/metrics/class sayısı doğrulandı

- [x] MediaPipe landmark extraction eklendi
  - Commit: `370e7ca Add MediaPipe landmark extraction`
  - Gelen frame'lerden MediaPipe Holistic landmark çıkarma backend'e bağlandı
  - Landmark çıkarılamazsa tahmin üretmeme mantığı eklendi

- [x] Gerçek inference akışı eklendi
  - Commit: `38f64a4 Add sign gate and word inference`
  - Akış: frame -> landmark -> sign gate -> kelime modeli
  - Response alanları: `hasSign`, `gloss`, `display`, `confidence`, `top5`

- [x] React Native uygulama backend'e bağlandı
  - Commit: `37723ed Connect app to inference backend`
  - Ayarlar ekranına backend URL alanı eklendi
  - Backend test akışı eklendi
  - `src/services/inferenceService.ts` eklendi

- [x] Dinamik backend keşfi denendi
  - Commit: `cd64f35 Add dynamic backend discovery`
  - NetInfo ve subnet tarama ile backend bulma eklendi
  - Bazı Wi-Fi ağlarında otomatik bulma güvenilir çalışmayabilir

- [x] Canlı frame penceresi inference akışı eklendi
  - Commit: `280b044 Add live frame sequence inference`
  - VisionCamera ile kısa frame pencereleri alınıp backend'e gönderildi
  - Bu teknik olarak canlı akışın örneklenmiş frame penceresidir

- [x] Android native Wi-Fi IP fallback eklendi
  - Commit: `b92885e Add native Wi-Fi IP discovery fallback`
  - NetInfo IP vermezse Android native module ile Wi-Fi IP okunmaya çalışılıyor
  - Buna rağmen bazı ağlarda manuel URL daha güvenilir

- [x] Canlı tahmin stabilizasyonu eklendi
  - Commit: `b964783 Add live prediction stabilization`
  - Anlık tahmin ile kabul edilen gloss ayrıldı
  - Rastgele tek seferlik tahminlerin listeye eklenmesi azaltıldı
  - Top1-top2 farkı, güven eşiği ve kısa pencere tutarlılığı eklendi
  - TTS sadece anlamlı cümle oluşunca çalışacak şekilde korundu

## Mevcut Davranış ve Bilinen Sınırlar

- [x] Kamera preview Android cihazda çalışıyor
- [x] TTS çalışıyor
- [x] Backend manuel URL ile çalışıyor
- [x] Model canlı frame pencerelerinden tahmin üretiyor
- [x] Rastgele kelime birikmesini azaltan stabilizasyon eklendi
- [ ] Otomatik backend bulma her Wi-Fi'da güvenilir değil
- [ ] Model bazı kelimeleri, özellikle `ben`, mevcut canlı kamera koşullarında zor algılıyor
- [ ] Model izole kelime tanıma modelidir; doğal cümle çevirisi sınırlı kural tabanlıdır
- [ ] Telefon üzerinde on-device model çalıştırma henüz yapılmadı
- [ ] Unity'nin React Native içine entegrasyonu henüz başlamadı
- [x] Ayrı Unity avatar prototip projesi oluşturuldu

## Sıradaki Kısa Vadeli İşler

- [ ] Canlı stabilizasyonu gerçek cihazda test et
  - Backend URL'yi manuel gir
  - `Ayarlar > Güven eşiği` başlangıç: `%70`
  - Çok az kelime kabul ederse `%60-65` dene
  - Rastgele kelime hâlâ girerse `%75-80` dene

- [ ] Canlı ekrandaki durum mesajlarını kullanıcı açısından iyileştir
  - `Stabil değil: 1/3`
  - `Güven düşük`
  - `Kararsız tahmin`
  - `Kabul edildi`
  - Bu mesajlar teknik ama test için faydalı; final UI'da sadeleştirilebilir

- [ ] `ben seni seviyorum` senaryosunu özel test et
  - Beklenen gloss sırası: `ben`, `sen`, `sevmek`
  - Beklenen doğal çıktı: `Ben seni seviyorum.`
  - TTS sadece bu cümle oluşunca otomatik okumalı

- [ ] Yanlış kelime eklenirse hızlı düzeltme UX'i iyileştir
  - `Geri Al` çalışıyor
  - Gerekirse her gloss chip'e silme özelliği ekle

- [ ] Backend URL deneyimini sadeleştir
  - Otomatik bulma başarısız olursa kullanıcıya Mac IP örneği göster
  - Okul Wi-Fi'sinde cihaz izolasyonu varsa hotspot/ev Wi-Fi uyarısı göster

## Orta Vadeli İşler

- [ ] Canlı tahmin parametrelerini ayarlardan yönetilebilir yap
  - Stabil pencere sayısı
  - Gerekli tekrar sayısı
  - Top1-top2 minimum farkı
  - Aynı kelime tekrar davranışı

- [ ] Backend performansını ölç
  - Bir frame penceresi kaç ms sürüyor?
  - MediaPipe landmark çıkarma kaç ms?
  - Model inference kaç ms?
  - Telefon -> backend network gecikmesi kaç ms?

- [ ] Canlı frame örnekleme hızını optimize et
  - Mevcut akış kısa snapshot pencereleri alıyor
  - Gerekirse frame sayısı, çözünürlük ve JPEG kalite oranı ayarlanacak
  - Hedef: daha akıcı canlı tahmin, daha az gecikme

- [ ] Modelin zorlandığı kelimeleri raporla
  - `ben`, `sen`, `sevmek` için ayrı test notu çıkar
  - Yanlış gelen top5 alternatiflerini kaydet
  - Bu liste sonraki fine-tune için kullanılacak

- [ ] Kişisel veri/fine-tune planı hazırla
  - `ben`, `sen`, `sevmek` gibi kritik kelimeler için 20-50 örnek
  - Telefon kamerasına benzer açı ve mesafe
  - İşaret yok / geçiş anları için negatif örnekler

## Unity / Avatar Aşaması

- [x] Unity tarafı için yeni, ayrı proje aç
  - Mevcut eski Unity projesine dokunma
  - Avatar işi ayrı Unity projesinde yürüsün
  - Proje: `<unity-project>`
  - Commit: `9b25a71 Create TID avatar Unity prototype`

- [x] İlk avatar yaklaşımını seç
  - İlk prototip: hazır ücretsiz humanoid avatar + elle hazırlanmış/indirilmiş animasyon klipleri
  - Daha sonra: daha düzgün rig, blend tree veya gesture timeline
  - Şu an placeholder humanoid avatar ve basit procedural hareketler var

- [x] İlk avatar kelime setini küçük tut
  - `ben`
  - `sen`
  - `sevmek`
  - `yardim`
  - `doktor`
  - `istemek`

- [x] Metinden gloss'a basit kural tabanlı dönüşüm kullan
  - Örnek: `ben seni seviyorum` -> `ben sen sevmek`
  - Uygulamadaki `src/utils/translation.ts` ile uyumlu kal
  - Unity tarafında `GlossAvatarController.cs` içinde ilk kural seti eklendi

- [x] Avatar ekranında ilk demo akışını kur
  - Kullanıcı metin yazar
  - Metin gloss dizisine çevrilir
  - Avatar sırayla gloss animasyonlarını oynatır
  - Sahne: `<unity-project>/Assets/TIDAvatar/Scenes/AvatarPrototype.unity`

- [ ] React Native ile Unity entegrasyon stratejisini belirle
  - Seçenek 1: Unity sahnesini ayrı Android Activity olarak açmak
  - Seçenek 2: Unity output'u React Native içine native module olarak gömmek
  - İlk hedef: çalışan prototip, mimari kusursuzluk değil

## Daha Sonraki Model Aşaması

- [ ] 226 sınıflı mevcut TCN modeli için canlı kullanım raporu çıkar
  - Hangi kelimeler iyi?
  - Hangi kelimeler kötü?
  - Rastgele tahminler hangi durumda artıyor?

- [ ] Kişisel fine-tune veya ek eğitim verisi toplama
  - Telefon kamerası ile gerçek kullanım koşullarında kayıt
  - Özellikle başarısız kelimeler ve işaret yok anları

- [ ] On-device çalıştırma araştırması
  - PyTorch -> ONNX -> Core ML / TFLite dönüşüm
  - MediaPipe landmark çıkarma mobilde
  - React Native ile native inference entegrasyonu
  - Bu, prototip çalıştıktan sonra yapılmalı

- [ ] Cümle anlamlandırma sistemini geliştirme
  - İlk aşama: kural tabanlı gloss -> Türkçe cümle
  - Sonra: küçük lokal mapping / template sistemi
  - Daha sonra: gerekirse LLM veya daha gelişmiş dil modeli entegrasyonu

## Test Planı

- [ ] Backend health
  - `GET /health` `ok: true` dönmeli
  - `word_model`, `sign_gate`, `class_names`, `holistic_model` true olmalı

- [ ] Backend prediction
  - Landmark çıkarılamayan görüntüde tahmin üretmemeli
  - İşaret yoksa `hasSign=false` dönmeli
  - İşaret varsa `top5` dolu dönmeli

- [ ] Mobil uygulama
  - Kamera preview açılmalı
  - Ön/arka kamera geçişi çalışmalı
  - Backend URL yanlışsa app çökmemeli
  - Backend URL doğruysa canlı tahmin başlamalı
  - Gloss listesine sadece stabil tahminler eklenmeli
  - TTS sadece anlamlı cümle oluşunca otomatik çalışmalı

## Git Kullanımı

Her büyük adımdan sonra:

```bash
git status --short
npm run lint
npx tsc --noEmit
git add .
git commit -m "Kisa ve net commit mesaji"
```

Model ağırlıklarını yanlışlıkla stage etme:

```bash
git status --short
```

`server/models/*.pt` dosyaları commit'e girmemeli.

## Yeni Araçta Devam Etmek İçin İlk Komutlar

```bash
cd <repo-root>
git status --short
git log --oneline -n 5
npm run lint
npx tsc --noEmit
```

Backend'i aç:

```bash
PYTHONPATH=server .venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Mobil uygulamayı aç:

```bash
npx react-native run-android
```

## Kısa Karar Notları

- Şu an model eğitmeye geri dönülmeyecek; önce uygulama prototipi ve avatar akışı ilerletilecek.
- Canlı tanımada ana problem sadece model değil, aynı zamanda canlı akış stabilizasyonu ve kamera koşulları.
- Unity yalnızca avatar/işaret üretimi tarafında kullanılacak; normal kamera çeviri uygulaması React Native tarafında kalacak.
- Backend prototip için kabul edilebilir; final ürün için on-device optimizasyon ayrıca ele alınacak.

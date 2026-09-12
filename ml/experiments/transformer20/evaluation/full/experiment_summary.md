# AUTSL 20 Sinif Full Train Transformer Deneyi

Tarih: 2026-06-14 17:44

## Deney Ozeti

Bu deneyde AUTSL veri setinden secilen 20 Turk Isaret Dili sinifi uzerinde
MediaPipe Holistic ile cikarilan el ve ust govde landmarklari kullanilarak
Transformer Encoder tabanli bir siniflandirma modeli egitilmistir.

Bu deney, onceki 20 sinif subset deneyinden farkli olarak secilen 20 sinif
icin mevcut tum train orneklerini kullanmaktadir.

## Veri

- Sinif sayisi: 20
- Train video sayisi: 2450
- Validation video sayisi: 237
- Girdi temsili: 64 frame x 204 landmark ozelligi
- Landmark kaynagi: MediaPipe Holistic
- Kullanilan landmarklar: ust govde pose, sol el ve sag el

## Model

- Mimari: Landmark tabanli Transformer Encoder
- Epoch ust siniri: 120
- Early stopping patience: 15
- Batch size: 64
- Learning rate: 0.0003
- En iyi model validation accuracy iyilestiginde kaydedilmistir.

## Sonuc

- Validation accuracy: 0.8017 (%80.17)

## Onceki Deneylerle Karsilastirma

| Deney | Train Kapsami | Validation Accuracy |
|---|---:|---:|
| 20 sinif kucuk subset | 25 train/sinif | %53.10 |
| 20 sinif 100 train/sinif | 100 train/sinif | %72.15 |
| 20 sinif full train | 2450 train video | %80.17 |

## En Basarili Siniflar

| Sinif | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| arkadas | 0.933 | 1.000 | 0.966 | 14 |
| akraba | 1.000 | 0.909 | 0.952 | 11 |
| acikmak | 1.000 | 0.846 | 0.917 | 13 |
| ayni | 1.000 | 0.818 | 0.900 | 11 |
| agac | 0.857 | 0.923 | 0.889 | 13 |
| anne | 0.909 | 0.833 | 0.870 | 12 |
| abla | 0.786 | 0.917 | 0.846 | 12 |
| afiyet_olsun | 0.722 | 1.000 | 0.839 | 13 |

## En Zayif Siniflar

| Sinif | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| akilli | 0.750 | 0.250 | 0.375 | 12 |
| ayna | 0.438 | 0.778 | 0.560 | 9 |
| aglamak | 0.750 | 0.545 | 0.632 | 11 |
| agir | 0.833 | 0.625 | 0.714 | 8 |
| acele | 0.625 | 0.909 | 0.741 | 11 |
| alisveris | 0.667 | 0.909 | 0.769 | 11 |
| ataturk | 0.833 | 0.714 | 0.769 | 14 |
| aile | 1.000 | 0.667 | 0.800 | 12 |

## Yorum

Full train deneyinde validation accuracy %80 seviyesine ulasmistir. Bu sonuc,
train ornek sayisinin artirilmasinin model performansina belirgin katkı
sagladigini gostermektedir. Onceki 100 train/sinif deneyinde elde edilen
%72.15 basarim, full train kullanildiginda %80.17 seviyesine cikmistir.

Sinif bazli sonuclarda arkadas, akraba, acikmak ve ayni gibi isaretlerde
yuksek F1 skorlari elde edilmistir. Buna karsilik akilli, ayna ve aglamak
siniflari daha dusuk performans gostermistir. Bu durum, bazi isaretlerin
landmark temsiliyle daha zor ayrildigini veya bu siniflarin benzer hareket
kaliplarina sahip oldugunu dusundurmektedir.

Bu deney, mobil cihazda calisabilecek hafif bir TID isaret tanima modeli
icin guclu bir baseline olarak degerlendirilebilir. Sonraki asamalarda
landmark normalizasyonu, veri artirma, farkli model mimarileriyle karsilastirma
ve sinif sayisinin 50/100/226 seviyelerine genisletilmesi planlanabilir.

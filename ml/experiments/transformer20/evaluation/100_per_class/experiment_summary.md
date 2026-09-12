# AUTSL 20 Sinif Transformer Deneyi

Tarih: 2026-06-14 16:05

## Deney Ozeti

Bu deneyde AUTSL veri setinden secilen 20 Turk Isaret Dili sinifi uzerinde
MediaPipe Holistic ile cikarilan el ve ust govde landmarklari kullanilarak
Transformer Encoder tabanli bir siniflandirma modeli egitilmistir.

## Veri

- Sinif sayisi: 20
- Train video sayisi: 2000
- Validation video sayisi: 237
- Her train sinifi icin ornek sayisi: 100
- Validation sinif dagilimi veri setindeki mevcut eslesmelere gore degismektedir.
- Girdi temsili: 64 frame x 204 landmark ozelligi

## Model

- Mimari: Landmark tabanli Transformer Encoder
- Girdi: MediaPipe Holistic pose + sol el + sag el landmark zaman serisi
- Epoch ust siniri: 120
- Early stopping patience: 15
- Batch size: 64
- Learning rate: 0.0003
- En iyi model validation accuracy iyilestiginde kaydedilmistir.

## Sonuc

- Validation accuracy: 0.7215 (%72.15)

## En Basarili Siniflar

| Sinif | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| acikmak | 0.929 | 1.000 | 0.963 | 13 |
| akraba | 0.846 | 1.000 | 0.917 | 11 |
| ayni | 1.000 | 0.818 | 0.900 | 11 |
| agir | 0.800 | 1.000 | 0.889 | 8 |
| abla | 1.000 | 0.750 | 0.857 | 12 |
| agac | 0.846 | 0.846 | 0.846 | 13 |
| acele | 0.818 | 0.818 | 0.818 | 11 |
| agabey | 0.846 | 0.786 | 0.815 | 14 |

## En Zayif Siniflar

| Sinif | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| akilli | 0.500 | 0.083 | 0.143 | 12 |
| akilsiz | 0.375 | 0.273 | 0.316 | 11 |
| ayna | 0.385 | 0.556 | 0.455 | 9 |
| aglamak | 0.409 | 0.818 | 0.545 | 11 |
| ataturk | 0.700 | 0.500 | 0.583 | 14 |
| anne | 0.700 | 0.583 | 0.636 | 12 |
| afiyet_olsun | 0.571 | 0.923 | 0.706 | 13 |
| ayakkabi | 0.692 | 0.750 | 0.720 | 12 |

## Yorum

Elde edilen sonuc, landmark tabanli Transformer mimarisinin AUTSL uzerinde
izole isaret tanima gorevinde anlamli bir ogrenme gerceklestirdigini
gostermektedir. 20 sinifli deneyde rastgele tahmin basarimi yaklasik %5 iken,
model validation setinde bunun belirgin sekilde uzerinde bir basarim elde
etmistir.

Bazi siniflarda F1 skorunun yuksek olmasi, el ve ust govde hareketlerinin
bu isaretler icin ayirt edici oldugunu gostermektedir. Buna karsilik akilli,
akilsiz ve ayna gibi siniflarda performansin dusuk kalmasi, bu isaretlerin
landmark temsiliyle daha zor ayirt edildigini veya validation ornek sayisinin
sinirli olmasinin sonuclari etkiledigini gostermektedir.

Bu deney, proje kapsaminda mobil uygulamaya aktarilabilecek hafif bir model
mimarisi icin baslangic baseline'i olarak degerlendirilebilir. Sonraki
calismalarda landmark normalizasyonu, veri artirma, daha genis sinif sayisi
ve LSTM/GRU gibi baseline modellerle karsilastirma yapilmasi planlanmaktadir.

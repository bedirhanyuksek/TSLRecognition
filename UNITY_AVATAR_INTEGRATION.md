# Unity Avatar Android Entegrasyonu

Bu dosya React Native uygulamasındaki Avatar ekranını Unity avatar prototipine bağlamak için izlenecek sırayı tutar.

## Mevcut Durum

- React Native tarafında `TidUnityAvatar` native modülü eklendi.
- `Avatar` ekranındaki `Oynat` butonu artık `src/services/avatarService.ts` üzerinden Unity modülünü çağırıyor.
- Unity tarafında `UnityAppBridge` objesi ve `PlayGlossCsv`, `PlayText`, `Stop` metodları hazırlandı.
- Unity Library henüz Android projesine export edilmediği için uygulamada şu an `Unity export henuz Android projesine bagli degil` mesajı görünmesi normaldir.

## Akış

React Native:

```text
AvatarScreen > Oynat > avatarService.playUnityGlosses(["ben", "sen", "sevmek"])
```

Android native:

```text
TidUnityAvatarModule.playGlosses("ben,sen,sevmek")
```

Unity:

```text
UnityPlayer.UnitySendMessage("UnityAppBridge", "PlayGlossCsv", "ben,sen,sevmek")
```

## Unity Tarafında Yapılacaklar

1. Unity projesini aç:

```text
<unity-project>
```

2. Üst menüden tekrar çalıştır:

```text
TIDAvatar > Kontrollü Clip Sistemini Kur
```

3. Sahne içinde `UnityAppBridge` objesinin oluştuğunu kontrol et.

4. Android build target seç:

```text
File > Build Profiles > Android > Switch Platform
```

5. Export ayarları:

```text
Export Project: açık
Development Build: ilk test için açık olabilir
Scenes In Build: Assets/TIDAvatar/Scenes/AvatarPrototype.unity
```

6. Export hedef klasörü:

```text
<repo-root>/android/unityExport
```

Export sonrası beklenen klasör:

```text
<repo-root>/android/unityExport/unityLibrary
```

Local Android ve Unity yolları tracked Gradle dosyalarında tutulmaz. Örnek dosyayı
kopyalayıp kendi makinenizdeki yolları tanımlayın:

```bash
cp android/local.properties.example android/local.properties
```

`android/local.properties` Git tarafından ignore edilir.

## React Native Android Tarafında Sonraki Adım

Unity export alındıktan sonra Gradle bağlantısı yapılacak:

- `android/settings.gradle` içine `unityLibrary` include edilecek.
- `android/app/build.gradle` içine `implementation project(':unityLibrary')` eklenecek.
- Gerekirse Unity’nin `launcher` modülü kullanılmayacak, sadece `unityLibrary` bağlanacak.

Bu adım Unity export klasörü oluşmadan yapılmamalı; aksi halde Android build bozulur.

## Test Sırası

1. React Native uygulamayı çalıştır.
2. Avatar sekmesine git.
3. `ben seni seviyorum` yaz.
4. `İşarete Çevir` butonuna bas.
5. `Oynat` butonuna bas.
6. Beklenen: Unity ekranı açılır ve sırayla gloss animasyonları oynar.

## Not

İlk entegrasyon gömülü React Native view olarak değil, Unity Activity açma şeklinde yapılacak. Bu daha hızlı ve daha az riskli prototip yoludur. Daha sonra gerekiyorsa Avatar ekranının içine gömülü Unity view yapılabilir.

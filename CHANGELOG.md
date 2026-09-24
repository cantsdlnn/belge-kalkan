# Değişiklik günlüğü

## 2.1.0

- Otomatik maske kutuları OCR satırının tamamı yerine algılanan hassas değere daraltıldı.
- Çevredeki belge rengini örnekleyen doğal arka plan dolgusu varsayılan yapıldı.
- Siyah şerit, arayüzde isteğe bağlı maske stili olarak korundu.
- Arka plan örnekleme, çoklu bulgu alt-kutuları ve maske stili API doğrulaması test edildi.

## 2.0.0

- PNG, JPEG, WEBP, TIFF ve taranmış PDF desteği eklendi.
- RapidOCR ve ONNX Runtime ile yerel OCR eklendi.
- Otomatik maske kutularını seçme/kaldırma ve elle kutu çizme arayüzü eklendi.
- Maskelenmiş PNG ve düzleştirilmiş PDF çıktısı eklendi.
- Dosya boyutu, sayfa sayısı, çözünürlük ve belge eşleme kontrolleri eklendi.
- Görsel/PDF işleme ve eski PDF metin katmanının kaldırılması test edildi.

## 1.0.0

- T.C. kimlik, Türkiye IBAN'ı, e-posta ve telefon için metin algılayıcıları eklendi.
- Etiket, maske ve HMAC token modları eklendi.
- FastAPI, CLI, test, CI ve Docker desteği yayımlandı.

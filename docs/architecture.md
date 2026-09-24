# Mimari

```text
Metin ───────────────► deterministik algılayıcılar ──► güvenli metin

Görsel / PDF ─► doğrulanmış sayfa görüntüsü ─► yerel OCR ─► algılayıcılar
                         │                                  │
                         ▼                                  ▼
                 kullanıcı önizlemesi ◄────────────── maske kutuları
                         │
                         ▼
              kullanıcı onayı + elle alan ─► PNG / düzleştirilmiş PDF
```

`detectors.py` yalnız bulgu üretir. `service.py` maskeleme politikasını ve kanıt manifestini uygular. `api.py` ham bulgu değerlerini serileştirmeyen HTTP sınırıdır. Ayrım sayesinde algoritma web sunucusundan bağımsız test edilebilir.

`documents.py`, yüklemeyi doğrular ve PDF sayfalarını 150 DPI RGB görüntülere çevirir. RapidOCR adaptörü satır metni, güven skoru ve poligon üretir; algılayıcılar hassas satırları işaretler. API ham OCR metnini ayrı bir JSON alanı olarak döndürmez. Tarayıcı, otomatik kutuların seçimini ve kullanıcının çizdiği ek kutuları gönderir. Çıktı PDF ise özgün belge nesneleri kopyalanmaz; maskelenmiş sayfa görüntüleriyle yeni bir PDF oluşturulur. Uygulama kalıcı dosya veya veri tabanı oluşturmaz; multipart çerçevesinin istek süresindeki geçici alan davranışı dağıtım katmanında ayrıca yönetilir.

Metin akışındaki manifest; girdi ve çıktının SHA-256 özetini, kural sürümünü ve tür bazında sayıları içerir. Özellikle ham eşleşmeyi içermez. Bu kayıt, metnin kendisini yeniden saklamadan hangi işlem sürümünün kullanıldığını karşılaştırmaya yarar.

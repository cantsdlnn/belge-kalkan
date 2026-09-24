# Gereksinimler ve kabul ölçütleri

1. Geçerli T.C. kimlik numarası ve Türkiye IBAN'ı sağlama toplamıyla doğrulanmalı.
2. E-posta ve Türkiye mobil telefon biçimleri bulunmalı.
3. API bulgular içinde ham kişisel veriyi yeniden göndermemeli.
4. Etiket ve son dört haneyi koruyan maske seçenekleri deterministik olmalı.
5. Manifest ham değer içermeden kural sürümü, tür sayıları ve içerik özetlerini göstermeli.
6. Boş metin ve 100.000 karakter üzerindeki istekler API sınırında reddedilmeli.
7. PNG, JPEG, WEBP, TIFF ve PDF yüklemeleri kalıcı depoya yazılmadan işlenmeli; 10 MB, 10 sayfa, 30 megapiksel ve 20.000 piksel kenar sınırları uygulanmalı.
8. OCR harici bir servise istek göndermeden yerel ONNX modeliyle çalışmalı.
9. Otomatik bölgeler kullanıcıya görünür kutularla sunulmalı; seçim kaldırma ve elle bölge ekleme desteklenmeli.
10. Maskelenmiş PDF özgün metin katmanını taşımayan yeni bir belgeden oluşmalı.
11. Tarama API'si ham OCR metnini ayrı veri alanı olarak döndürmemeli ve yanıtta `no-store` önbellek politikası kullanmalı.

Kabul: test paketi en az %85 satır kapsamıyla geçer; örnek metinde dört veri türü maskelenir, görselde seçilen alanın pikseli siyaha döner ve yeniden oluşturulan PDF'de eski seçilebilir metin katmanı bulunmaz.

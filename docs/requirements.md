# Gereksinimler ve kabul ölçütleri

1. Geçerli T.C. kimlik numarası ve Türkiye IBAN'ı sağlama toplamıyla doğrulanmalı.
2. E-posta ve Türkiye mobil telefon biçimleri bulunmalı.
3. API bulgular içinde ham kişisel veriyi yeniden göndermemeli.
4. Etiket ve son dört haneyi koruyan maske seçenekleri deterministik olmalı.
5. Manifest ham değer içermeden kural sürümü, tür sayıları ve içerik özetlerini göstermeli.
6. Boş metin ve 100.000 karakter üzerindeki istekler API sınırında reddedilmeli.

Kabul: test paketi en az %85 satır kapsamıyla geçer; örnek metinde dört veri türü maskelenir ve yanıtta kaynak değerlerden hiçbiri bulunmaz.


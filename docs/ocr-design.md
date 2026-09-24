# OCR tasarımı ve insan kontrolü

## Neden yerel OCR?

Belge daha maskelenmeden önce en hassas hâlindedir. Bu nedenle uygulama yüklenen görseli üçüncü taraf OCR veya üretken yapay zekâ API'sine göndermez. RapidOCR, ONNX Runtime üzerinde aynı makinede çalışır. FastAPI katmanı kalıcı kayıt oluşturmaz ve tarama yanıtını `Cache-Control: no-store` ile döndürür. Multipart web çatısı büyük yüklemeleri istek süresince işletim sisteminin geçici alanına taşıyabileceğinden, kurumsal dağıtımda geçici dizin şifreleme ve temizleme politikası ayrıca belirlenmelidir.

## Veri akışı

1. Dosya imzası, boyutu, sayfa sayısı ve görüntü çözünürlüğü doğrulanır.
2. PDF sayfaları 150 DPI RGB görüntüye dönüştürülür.
3. OCR motoru her yazı satırı için poligon, metin ve güven skoru üretir.
4. Metin; T.C. kimlik, IBAN, e-posta ve telefon algılayıcılarından geçer.
5. Algılanan değerin karakter aralığı, OCR satır poligonu içinde yaklaşık bir alt-kutuya dönüştürülür; böylece satır etiketi ve komşu bilgi gereksiz yere kapanmaz.
6. API, bulunan ham OCR metnini ayrı bir JSON alanında döndürmeden yalnız tür, güven ve kutu koordinatını verir.
7. Kullanıcı otomatik kutuları kontrol eder, kaldırır veya elle yeni kutu çizer.
8. Varsayılan dolgu, kutunun hemen dışındaki piksellerin kanal bazlı medyanıyla belirlenir. Kullanıcı isterse siyah şerit seçebilir. Her iki yöntemde de kaynak pikseller değiştirilir; PDF bu yeni sayfa görüntülerinden baştan oluşturulur.

## Bilinçli sınırlar

- OCR küçük, eğik, gölgeli, el yazısı veya düşük kontrastlı metni kaçırabilir.
- OCR'nin yanlış okuduğu bir rakam checksum doğrulamasını geçemeyebilir; bu durumda otomatik kutu oluşmaz.
- Karakter aralığını satır poligonuna orantılayan alt-kutu, değişken genişlikli veya eğik yazıda yaklaşık sonuç verir.
- Dokulu, desenli veya renk geçişli zeminde tek renk arka plan dolgusu çevreden ayırt edilebilir.
- Ad, adres ve bağlama bağlı kişisel veriler deterministik algılayıcıların kapsamı dışındadır.
- Güven skoru, metnin doğru olduğuna dair garanti değildir.

Bu nedenlerle ürün akışı “otomatik tara → insan doğrulasın → maskeli çıktıyı yeniden açıp kontrol et” biçiminde tasarlanmıştır.

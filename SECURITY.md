# Güvenlik politikası

Güvenlik açığını herkese açık issue açmadan `tasdelennusretcan58@gmail.com` adresine bildirebilirsiniz.

## Güvenlik sınırları

- Uygulama istek gövdesini, yüklenen belgeyi, OCR metnini veya maskelenmiş çıktıyı kalıcı depoya yazmaz. Web çatısı büyük multipart yüklemeleri istek süresince işletim sisteminin geçici alanına taşıyabilir; dağıtım ortamının geçici dosya politikası ayrıca sınırlandırılmalıdır.
- Yüklemeler 10 MB, PDF'ler 10 sayfa, görseller 30 megapiksel ve tek kenar 20.000 piksel ile sınırlandırılır; parolalı PDF ve çok kareli görsel reddedilir.
- Tek taramada 5.000 OCR satırı ve 500 maske alanı sınırı uygulanır; sınırı aşan belgeler sessizce kırpılmak yerine bölünerek yeniden yüklenmek üzere reddedilir.
- Tarama yanıtları `Cache-Control: no-store` ile döner. Önizleme, kullanıcının kendi belgesini tarayıcıya geri taşır; HTTPS kullanılmadan ağ üzerinden çalıştırılmamalıdır.
- Maskelenmiş PDF özgün sayfaların görüntü olarak yeniden oluşturulmasıyla üretilir; eski seçilebilir metin katmanı çıktıya kopyalanmaz.
- Örnek dağıtım tek kullanıcıya yönelik yerel kullanım içindir. İnternete açılacaksa TLS, kimlik doğrulama, istek boyutu ve hız sınırı ters proxy katmanında ayrıca yapılandırılmalıdır.
- `token` modu CLI/çekirdek servis düzeyinde vardır; gizli anahtar API üzerinden kabul edilmez.
- OCR ve desen tabanlı tespit eksiksiz DLP garantisi vermez. Kullanıcı otomatik kutuları kontrol etmeli, gerekirse elle alan eklemeli ve çıktıyı paylaşmadan önce yeniden açıp doğrulamalıdır.

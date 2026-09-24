# Güvenlik politikası

Güvenlik açığını herkese açık issue açmadan `tasdelennusretcan58@gmail.com` adresine bildirebilirsiniz.

## Güvenlik sınırları

- Sunucu istek gövdesini, bulunan ham değerleri veya maskelenmiş metni kalıcı olarak kaydetmez.
- Örnek dağıtım tek kullanıcıya yönelik yerel kullanım içindir. İnternete açılacaksa TLS, kimlik doğrulama, istek boyutu ve hız sınırı ters proxy katmanında ayrıca yapılandırılmalıdır.
- `token` modu CLI/çekirdek servis düzeyinde vardır; gizli anahtar API üzerinden kabul edilmez.
- Desen tabanlı tespit eksiksiz DLP garantisi vermez. Çıktı paylaşılmadan önce insan kontrolü gerekir.


# BelgeKalkan

[![CI](https://github.com/cantsdlnn/belge-kalkan/actions/workflows/ci.yml/badge.svg)](https://github.com/cantsdlnn/belge-kalkan/actions/workflows/ci.yml)

[English summary](README.en.md)

Türkçe metinlerdeki T.C. kimlik numarası, Türkiye IBAN'ı, e-posta ve mobil telefon gibi kişisel verileri **harici bir yapay zekâ servisine göndermeden** bulup maskeleyen küçük bir web servisi ve komut satırı aracı.

![BelgeKalkan arayüzü](docs/assets/belge-kalkan.png)

## Neden bu proje?

Hata kaydı, destek talebi veya örnek veri paylaşılırken gerçek kişisel bilgiler kolayca metinde kalabiliyor. BelgeKalkan paylaşım öncesinde otomatik bir ilk kontrol sağlar; T.C. kimlik ve IBAN adaylarını yalnız desenle değil sağlama toplamıyla doğrular, işlem kaydında ham değeri tutmaz ve son kararı kullanıcıya bırakır.

## Öne çıkan özellikler

- T.C. kimlik numarası için resmî sağlama algoritması
- Türkiye IBAN'ı için ISO 13616 mod-97 kontrolü
- E-posta ve Türkiye mobil telefon biçimleri
- Etiket, maske ve çekirdek serviste HMAC tabanlı kararlı token üretimi
- Ham değer içermeyen işlem manifesti ve içerik özetleri
- FastAPI arayüzü, OpenAPI belgesi ve aynı çekirdeği kullanan CLI
- Çakışan eşleşmeleri deterministik çözme
- Test, kapsam eşiği, Ruff ve GitHub Actions CI
- Çok aşamalı olmayan, ayrıcalıksız kullanıcıyla çalışan Docker imajı

## Hızlı başlangıç

Python 3.11 veya üzeri gerekir.

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]"
uvicorn belgekalkan.api:app --reload
```

Ardından `http://127.0.0.1:8000` adresini açın. API belgesi `/docs` yolundadır.

CLI örneği:

```bash
belge-kalkan ornek.txt --output guvenli.txt --manifest islem.json --mode label
```

## Test

```bash
ruff check .
pytest
```

Testler checksum doğrulamasını, yanlış pozitiflerin elenmesini, çakışma çözümünü, maskeleme modlarını ve API'nin ham değeri yanıtta tekrar etmemesini kapsar.

## Güvenlik ve dürüst sınırlar

BelgeKalkan deterministik bir ön kontrol aracıdır; bağlamı anlayan eksiksiz bir veri kaybı önleme ürünü değildir. Ad, adres ve serbest biçimli hassas içerik gibi her kişisel veriyi bulamaz. Çıktı paylaşılmadan önce insan tarafından kontrol edilmelidir.

Web katmanı veri tabanı kullanmaz ve uygulama kodu istek içeriğini loglamaz. İnternete açık dağıtım için TLS, kimlik doğrulama, hız sınırı ve altyapı logları ayrıca ele alınmalıdır. Ayrıntı: [SECURITY.md](SECURITY.md).

## Proje belgeleri

- [Gereksinimler ve kabul ölçütleri](docs/requirements.md)
- [Mimari](docs/architecture.md)
- [Yapay zekâ kullanım beyanı](AI_USAGE.md)

## AI kullanımı

Üretken yapay zekâyı tasarım seçeneklerini karşılaştırma, sınır durumlarını bulma, testleri genişletme ve dokümantasyon incelemesi için kullandım. Kural uygulaması, gizlilik sınırları ve nihai doğrulama sorumluluğu bana aittir. Uygulamanın çalışma zamanında yapay zekâ servisi kullanılmaz.

## Lisans

[MIT](LICENSE)

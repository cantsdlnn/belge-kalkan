# Mimari

```text
Tarayıcı / CLI
      │
      ▼
FastAPI sınırı ──► deterministik algılayıcılar ──► çakışma çözümü
                                                    │
                                                    ▼
                    güvenli çıktı ◄── maskeleme + değersiz manifest
```

`detectors.py` yalnız bulgu üretir. `service.py` maskeleme politikasını ve kanıt manifestini uygular. `api.py` ham bulgu değerlerini serileştirmeyen HTTP sınırıdır. Ayrım sayesinde algoritma web sunucusundan bağımsız test edilebilir.

Manifest; girdi ve çıktının SHA-256 özetini, kural sürümünü ve tür bazında sayıları içerir. Özellikle ham eşleşmeyi içermez. Bu kayıt, belgenin kendisini yeniden saklamadan hangi işlem sürümünün kullanıldığını karşılaştırmaya yarar.


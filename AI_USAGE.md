# Yapay zekâ kullanım beyanı

Bu projeyi geliştirirken üretken yapay zekâyı gereksinimleri sınır durumlarına dönüştürmek, alternatif API tasarımlarını karşılaştırmak, test senaryolarını genişletmek ve dokümantasyonu gözden geçirmek için eşli geliştirme aracı olarak kullandım.

T.C. kimlik ve IBAN doğrulama kurallarını kaynak kod düzeyinde inceledim; hangi verinin API yanıtında gösterilmeyeceğine, çakışan bulguların nasıl çözüleceğine ve ürünün hangi iddialarda bulunamayacağına ben karar verdim. Testleri çalıştırmak, başarısız sonuçları incelemek ve son doğrulamayı yapmak benim sorumluluğumdaydı.

Uygulamanın çalışma zamanında üretken yapay zekâ veya harici model servisi kullanılmaz. Görselden yazı bölgesi çıkarmak için cihazda çalışan RapidOCR/ONNX modeli kullanılır; bulunan metindeki kişisel veri sınıflandırması ise sürümlenmiş ve deterministik kurallarla yapılır. OCR sonucunun eksik olabileceği kabul edildiği için nihai maske seçimi kullanıcıya gösterilir.

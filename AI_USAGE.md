# Yapay zekâ kullanım beyanı

Bu projeyi geliştirirken üretken yapay zekâyı gereksinimleri sınır durumlarına dönüştürmek, alternatif API tasarımlarını karşılaştırmak, test senaryolarını genişletmek ve dokümantasyonu gözden geçirmek için eşli geliştirme aracı olarak kullandım.

T.C. kimlik ve IBAN doğrulama kurallarını kaynak kod düzeyinde inceledim; hangi verinin API yanıtında gösterilmeyeceğine, çakışan bulguların nasıl çözüleceğine ve ürünün hangi iddialarda bulunamayacağına ben karar verdim. Testleri çalıştırmak, başarısız sonuçları incelemek ve son doğrulamayı yapmak benim sorumluluğumdaydı.

Uygulamanın çalışma zamanında üretken yapay zekâ veya harici model servisi kullanılmaz. Tespitler sürümlenmiş ve deterministik kurallarla yapılır.


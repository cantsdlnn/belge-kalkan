const source = document.querySelector('#source');
const result = document.querySelector('#result');
const stats = document.querySelector('#stats');
const sampleText = `Başvuru sahibi 10000000146 T.C. kimlik numarasıyla kayıtlıdır.
İletişim: ornek.kisi@example.com / +90 555 123 45 67
Ödeme hesabı: TR33 0006 1005 1978 6457 8413 26`;

source.value = sampleText;

document.querySelector('#sample').addEventListener('click', () => { source.value = sampleText; source.focus(); });
document.querySelector('#copy').addEventListener('click', async () => {
  await navigator.clipboard.writeText(result.textContent);
});
document.querySelector('#redact').addEventListener('click', async () => {
  if (!source.value.trim()) { stats.textContent = 'Önce bir metin girin.'; return; }
  stats.textContent = 'Taranıyor…';
  const response = await fetch('/api/redact', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({text: source.value, mode: document.querySelector('#mode').value})
  });
  if (!response.ok) { stats.textContent = 'İşlem tamamlanamadı.'; return; }
  const data = await response.json();
  result.textContent = data.redacted_text;
  const chips = Object.entries(data.manifest.counts).map(([key,value]) => `<span>${key.toUpperCase()} · ${value}</span>`).join('');
  stats.innerHTML = chips || '<span>Bulgu yok</span>';
});

document.querySelector('#redact').click();

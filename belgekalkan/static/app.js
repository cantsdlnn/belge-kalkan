const source = document.querySelector('#source');
const result = document.querySelector('#result');
const stats = document.querySelector('#stats');
const sampleText = `Başvuru sahibi 10000000146 T.C. kimlik numarasıyla kayıtlıdır.
İletişim: ornek.kisi@example.com / +90 555 123 45 67
Ödeme hesabı: TR33 0006 1005 1978 6457 8413 26`;

source.value = sampleText;

document.querySelectorAll('.mode-tab').forEach((button) => {
  button.addEventListener('click', () => {
    document.querySelectorAll('.mode-tab').forEach((item) => item.classList.toggle('active', item === button));
    document.querySelectorAll('.mode-panel').forEach((panel) => { panel.hidden = panel.id !== button.dataset.target; });
  });
});

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

const fileInput = document.querySelector('#documentFile');
const fileName = document.querySelector('#fileName');
const scanButton = document.querySelector('#scanDocument');
const documentStatus = document.querySelector('#documentStatus');
const review = document.querySelector('#documentReview');
const pagePreviews = document.querySelector('#pagePreviews');
const documentStats = document.querySelector('#documentStats');
const manualButton = document.querySelector('#manualMode');
const toggleAllButton = document.querySelector('#toggleAll');
const maskStyle = document.querySelector('#maskStyle');
let selectedFile = null;
let scanState = null;
let regions = [];
let manualMode = false;

function setSelectedFile(file) {
  selectedFile = file || null;
  fileName.textContent = selectedFile ? `${selectedFile.name} · ${(selectedFile.size / 1024 / 1024).toFixed(2)} MB` : 'Dosya seç veya buraya bırak';
  review.hidden = true;
  documentStatus.textContent = '';
}

fileInput.addEventListener('change', () => setSelectedFile(fileInput.files[0]));
const dropZone = document.querySelector('.drop-zone');
dropZone.addEventListener('dragover', (event) => { event.preventDefault(); dropZone.classList.add('dragging'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragging'));
dropZone.addEventListener('drop', (event) => {
  event.preventDefault(); dropZone.classList.remove('dragging');
  const file = event.dataTransfer.files[0];
  if (file) setSelectedFile(file);
});

function errorMessage(data, fallback) {
  return typeof data?.detail === 'string' ? data.detail : fallback;
}

scanButton.addEventListener('click', async () => {
  if (!selectedFile) { documentStatus.textContent = 'Önce bir dosya seçin.'; return; }
  scanButton.disabled = true;
  documentStatus.textContent = 'Belge belleğe alınıyor ve yerel OCR modeli çalışıyor… İlk tarama biraz sürebilir.';
  review.hidden = true;
  const form = new FormData(); form.append('file', selectedFile);
  try {
    const response = await fetch('/api/document/scan', { method:'POST', body:form });
    const data = await response.json();
    if (!response.ok) throw new Error(errorMessage(data, 'Belge taranamadı.'));
    scanState = data;
    regions = data.regions.map((region) => ({...region, selected:true, manual:false}));
    manualMode = false; manualButton.classList.remove('active');
    renderReview();
    review.hidden = false;
    documentStatus.textContent = data.summary.region_count
      ? `${data.summary.page_count} sayfa tarandı. Kalıcı dosya oluşturulmadı.`
      : `${data.summary.page_count} sayfa tarandı; otomatik alan bulunamadı. Gerekirse elle alan ekleyin.`;
  } catch (error) {
    documentStatus.textContent = error.message || 'Belge taranamadı.';
  } finally {
    scanButton.disabled = false;
  }
});

function regionLabel(region) {
  return region.manual ? 'ELLE' : region.kinds.map((kind) => kind.toUpperCase()).join(' + ');
}

function createRegionElement(region, page) {
  const button = document.createElement('button');
  button.type = 'button'; button.className = `region ${region.selected ? 'selected' : ''} ${region.manual ? 'manual-region' : ''}`;
  button.dataset.id = region.id; button.dataset.label = regionLabel(region);
  button.title = region.manual ? 'Elle eklenen maske' : `${regionLabel(region)} · OCR güveni %${Math.round(region.confidence * 100)}`;
  button.style.left = `${region.x / page.width * 100}%`;
  button.style.top = `${region.y / page.height * 100}%`;
  button.style.width = `${region.width / page.width * 100}%`;
  button.style.height = `${region.height / page.height * 100}%`;
  button.addEventListener('click', (event) => {
    event.stopPropagation(); region.selected = !region.selected;
    button.classList.toggle('selected', region.selected); updateReviewSummary();
  });
  return button;
}

function addManualDrawing(stage, page) {
  let start = null; let draft = null;
  stage.addEventListener('pointerdown', (event) => {
    if (!manualMode || event.target.closest('.region')) return;
    const rect = stage.getBoundingClientRect();
    start = { x:Math.max(0, Math.min(rect.width, event.clientX - rect.left)), y:Math.max(0, Math.min(rect.height, event.clientY - rect.top)), rect };
    draft = document.createElement('div'); draft.className = 'draft-region';
    draft.style.left = `${start.x}px`; draft.style.top = `${start.y}px`; stage.append(draft);
    stage.setPointerCapture(event.pointerId);
  });
  stage.addEventListener('pointermove', (event) => {
    if (!start || !draft) return;
    const endX = Math.max(0, Math.min(start.rect.width, event.clientX - start.rect.left));
    const endY = Math.max(0, Math.min(start.rect.height, event.clientY - start.rect.top));
    draft.style.left = `${Math.min(start.x,endX)}px`; draft.style.top = `${Math.min(start.y,endY)}px`;
    draft.style.width = `${Math.abs(endX-start.x)}px`; draft.style.height = `${Math.abs(endY-start.y)}px`;
  });
  stage.addEventListener('pointerup', (event) => {
    if (!start || !draft) return;
    const endX = Math.max(0, Math.min(start.rect.width, event.clientX - start.rect.left));
    const endY = Math.max(0, Math.min(start.rect.height, event.clientY - start.rect.top));
    const left = Math.min(start.x,endX), top = Math.min(start.y,endY);
    const width = Math.abs(endX-start.x), height = Math.abs(endY-start.y);
    draft.remove();
    if (width >= 8 && height >= 8) {
      const region = {
        id:`manual-${page.number}-${Date.now()}`, page:page.number,
        x:left/start.rect.width*page.width, y:top/start.rect.height*page.height,
        width:width/start.rect.width*page.width, height:height/start.rect.height*page.height,
        kinds:['manual'], confidence:1, selected:true, manual:true,
      };
      regions.push(region); stage.append(createRegionElement(region,page)); updateReviewSummary();
    }
    start = null; draft = null;
  });
}

function renderReview() {
  pagePreviews.innerHTML = '';
  for (const page of scanState.pages) {
    const card = document.createElement('article'); card.className = 'page-card';
    const title = document.createElement('h3'); title.textContent = `Sayfa ${page.number + 1} · ${page.width} × ${page.height}`;
    const stage = document.createElement('div'); stage.className = `page-stage ${manualMode ? 'manual' : ''}`; stage.dataset.page = page.number;
    const image = document.createElement('img'); image.src = page.image; image.alt = `Belge önizlemesi, sayfa ${page.number + 1}`; image.draggable = false;
    stage.append(image);
    regions.filter((region) => region.page === page.number).forEach((region) => stage.append(createRegionElement(region,page)));
    addManualDrawing(stage,page); card.append(title,stage); pagePreviews.append(card);
  }
  updateReviewSummary();
}

function updateReviewSummary() {
  if (!scanState) return;
  const selected = regions.filter((region) => region.selected).length;
  const manual = regions.filter((region) => region.manual).length;
  const summary = scanState.summary;
  const lowConfidence = summary.low_confidence_count ? `<span>${summary.low_confidence_count} DÜŞÜK OCR</span>` : '';
  documentStats.innerHTML = `<span>${summary.page_count} SAYFA</span><span>${summary.region_count} OTOMATİK</span>${lowConfidence}<span>${manual} ELLE</span><span>${selected} SEÇİLİ</span>`;
  toggleAllButton.textContent = selected ? 'Tümünü kaldır' : 'Tümünü seç';
}

toggleAllButton.addEventListener('click', () => {
  const shouldSelect = !regions.some((region) => region.selected);
  regions.forEach((region) => { region.selected = shouldSelect; }); renderReview();
});
manualButton.addEventListener('click', () => {
  manualMode = !manualMode; manualButton.classList.toggle('active', manualMode);
  manualButton.textContent = manualMode ? 'Elle ekleme açık' : '+ Elle alan ekle';
  document.querySelectorAll('.page-stage').forEach((stage) => stage.classList.toggle('manual', manualMode));
});

document.querySelector('#downloadRedacted').addEventListener('click', async (event) => {
  const downloadButton = event.currentTarget;
  const selected = regions.filter((region) => region.selected);
  if (!selected.length) { documentStatus.textContent = 'İndirmeden önce en az bir alan seçin.'; return; }
  const pages = new Map(scanState.pages.map((page) => [page.number,page]));
  const boxes = selected.map((region) => ({
    page:region.page, x:region.x, y:region.y, width:region.width, height:region.height,
    preview_width:pages.get(region.page).width, preview_height:pages.get(region.page).height,
  }));
  const form = new FormData();
  form.append('file',selectedFile); form.append('regions',JSON.stringify(boxes)); form.append('fingerprint',scanState.fingerprint);
  form.append('mask_style',maskStyle.value);
  documentStatus.textContent = 'Maskeli çıktı bellekte oluşturuluyor…';
  downloadButton.disabled = true;
  try {
    const response = await fetch('/api/document/redact',{method:'POST',body:form});
    if (!response.ok) {
      const data = await response.json(); throw new Error(errorMessage(data,'Maskeli çıktı oluşturulamadı.'));
    }
    const blob = await response.blob();
    const disposition = response.headers.get('Content-Disposition') || '';
    const match = disposition.match(/filename\*=UTF-8''([^;]+)/i);
    const name = match ? decodeURIComponent(match[1]) : 'belge-maskeli';
    const url = URL.createObjectURL(blob); const link = document.createElement('a');
    link.href = url; link.download = name; document.body.append(link); link.click(); link.remove();
    const styleLabel = maskStyle.value === 'background' ? 'arka plan rengiyle' : 'siyah şeritle';
    URL.revokeObjectURL(url); documentStatus.textContent = `${selected.length} alan ${styleLabel} maskelendi ve dosya indirildi.`;
  } catch (error) {
    documentStatus.textContent = error.message || 'Maskeli çıktı oluşturulamadı.';
  } finally {
    downloadButton.disabled = false;
  }
});

document.querySelector('#redact').click();
if (window.location.hash === '#document') {
  document.querySelector('[data-target="documentMode"]').click();
}

// 转换台交互：方向 / 模式开关、上传、XMind→预览、CSV→分隔符→下载
document.addEventListener('DOMContentLoaded', () => {
  const state = { dir: 'x2c', mode: 'single', file: null };
  const $ = (s) => document.querySelector(s);
  const dropzone = $('#dropzone'), fileInput = $('#file');
  const convertBtn = $('#convert-btn'), convertLabel = $('#convert-label');
  const dropTitle = $('#drop-title'), dropSub = $('#drop-sub'), outChips = $('#out-chips');

  const COPY = {
    x2c: { accept: '.xmind', label: '转换为测试用例',
           title: '点击或拖拽上传 .xmind 文件', sub: '解析思维导图结构，生成结构化测试用例',
           src: 'XMind', tgt: '用例表格', chips: ['禅道 CSV', 'TestLink XML'] },
    c2x: { accept: '.csv', label: '转换为 XMind',
           title: '点击或拖拽上传禅道导出的 .csv', sub: '还原为可在 XMind 中打开的思维导图',
           src: '禅道 CSV', tgt: 'XMind', chips: ['XMind 思维导图 (.xmind)'] },
  };

  function applyDir() {
    const c = COPY[state.dir];
    fileInput.setAttribute('accept', c.accept);
    convertLabel.textContent = c.label;
    if (dropTitle) dropTitle.textContent = c.title;
    if (dropSub) dropSub.textContent = c.sub;
    const sEl = document.querySelector('[data-flow-src]'); if (sEl) sEl.textContent = c.src;
    const tEl = document.querySelector('[data-flow-tgt]'); if (tEl) tEl.textContent = c.tgt;
    if (outChips) outChips.innerHTML = c.chips.map(
      (l) => `<span class="out-chip">${l}</span>`).join('');
    state.file = null; resetDropzone();
  }

  function resetDropzone() {
    if (dropTitle) dropTitle.textContent = COPY[state.dir].title;
  }

  // 分段开关
  document.querySelector('[data-toggle="dir"]').addEventListener('click', (e) => {
    const btn = e.target.closest('[data-dir]'); if (!btn) return;
    state.dir = btn.dataset.dir;
    document.querySelectorAll('[data-toggle="dir"] .seg__btn').forEach(
      (b) => b.classList.toggle('seg__btn--on', b === btn));
    applyDir();
  });
  document.querySelector('[data-toggle="mode"]').addEventListener('click', (e) => {
    const btn = e.target.closest('[data-mode]'); if (!btn) return;
    state.mode = btn.dataset.mode;
    document.querySelectorAll('[data-toggle="mode"] .seg__btn').forEach(
      (b) => b.classList.toggle('seg__btn--on', b === btn));
    document.querySelector('#single-panel').hidden = state.mode !== 'single';
    document.querySelector('#batch-panel').hidden = state.mode !== 'batch';
  });

  // 选择文件
  const extOk = (name) => name.toLowerCase().endsWith(COPY[state.dir].accept);
  dropzone.addEventListener('click', () => fileInput.click());
  fileInput.addEventListener('change', () => {
    if (fileInput.files && fileInput.files[0]) setFile(fileInput.files[0]);
  });
  ['dragover', 'dragenter'].forEach((ev) => dropzone.addEventListener(ev, (e) => {
    e.preventDefault(); dropzone.classList.add('dropzone--over');
  }));
  ['dragleave', 'drop'].forEach((ev) => dropzone.addEventListener(ev, (e) => {
    e.preventDefault(); dropzone.classList.remove('dropzone--over');
  }));
  dropzone.addEventListener('drop', (e) => {
    const f = e.dataTransfer.files && e.dataTransfer.files[0];
    if (f) setFile(f);
  });
  function setFile(f) {
    if (!extOk(f.name)) { alert('请上传 ' + COPY[state.dir].accept + ' 文件'); return; }
    state.file = f;
    if (dropTitle) dropTitle.textContent = '已选择：' + f.name;
  }

  // 转换
  convertBtn.addEventListener('click', async () => {
    if (!state.file) { dropzone.classList.add('dropzone--over');
      setTimeout(() => dropzone.classList.remove('dropzone--over'), 600); return; }
    const fd = new FormData(); fd.append('file', state.file);
    convertBtn.disabled = true;
    try {
      const r = await fetch('/api/upload', { method: 'POST', body: fd });
      const body = await r.json();
      if (!body.success) { alert(body.message || '上传失败'); return; }
      const name = encodeURIComponent(body.filename);
      if (state.dir === 'x2c') { window.location = '/preview/' + name; }
      else { openSepModal(body.filename); }
    } catch (err) { alert('上传失败，请重试'); }
    finally { convertBtn.disabled = false; }
  });

  // CSV → XMind 分隔符弹窗（照原型 sep 逻辑）
  function openSepModal(filename) {
    const base = '/' + encodeURIComponent(filename) + '/to/xmind-from-csv';
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.innerHTML = `
      <div class="modal">
        <div class="modal__title serif">选择标题分隔符</div>
        <div class="modal__divider"></div>
        <p style="font-size:13px;color:var(--text-2);margin:0 0 14px;">用例标题将按勾选的符号拆成 XMind 层级，任一符号都作为切分点。</p>
        <label class="modal__check"><input type="checkbox" class="sep-opt" value=" " checked><span>空格</span></label>
        <label class="modal__check"><input type="checkbox" class="sep-opt" value=">"><span>&gt; 大于号</span></label>
        <label class="modal__check"><input type="checkbox" class="sep-opt" value="-"><span>- 连字符</span></label>
        <label class="modal__check"><span>自定义</span><input type="text" id="sep-custom" maxlength="10" class="modal__input" style="width:160px;"></label>
        <p style="font-size:12px;color:var(--text-4);margin:10px 0 0;">不勾选任何符号则不拆分，每条用例直接挂在模块下。</p>
        <div class="modal__actions" style="margin-top:20px;">
          <button class="btn btn--outline" id="sep-cancel">取消</button>
          <button class="btn btn--ink" id="sep-confirm">下载</button>
        </div>
      </div>`;
    document.body.appendChild(overlay);
    const close = () => overlay.remove();
    overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });
    overlay.querySelector('#sep-cancel').addEventListener('click', close);
    overlay.querySelector('#sep-confirm').addEventListener('click', () => {
      const seps = Array.from(overlay.querySelectorAll('.sep-opt:checked')).map((c) => c.value);
      const custom = overlay.querySelector('#sep-custom').value;
      if (custom) seps.push(custom);
      const url = seps.length === 0 ? base + '?flat=1'
        : base + '?' + seps.map((s) => 'sep=' + encodeURIComponent(s)).join('&');
      close(); window.location = url;
    });
  }

  applyDir();
});

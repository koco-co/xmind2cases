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
    // 批量仅支持 XMind → 用例：锁定方向开关到 x2c
    const dirSeg = document.querySelector('[data-toggle="dir"]');
    if (state.mode === 'batch') {
      if (state.dir !== 'x2c') {
        state.dir = 'x2c';
        document.querySelectorAll('[data-toggle="dir"] .seg__btn').forEach(
          (b) => b.classList.toggle('seg__btn--on', b.dataset.dir === 'x2c'));
        applyDir();
      }
      dirSeg.classList.add('seg--locked');
    } else {
      dirSeg.classList.remove('seg--locked');
    }
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
      // 不论 XMind 还是 CSV，上传成功后都进预览页（恢复历史落点）。
      // CSV 预览页自带「下载 XMind」+ 分隔符弹窗（见 preview.html is_csv 分支）。
      window.location = '/preview/' + encodeURIComponent(body.filename);
    } catch (err) { alert('上传失败，请重试'); }
    finally { convertBtn.disabled = false; }
  });

  /* ===== 批量转换（仅 XMind → 用例）===== */
  const batchDropzone = $('#batch-dropzone');
  const batchInput = $('#batch-file');
  const batchQueueEl = $('#batch-queue');
  const batchActions = $('#batch-actions');
  const batchRunBtn = $('#batch-run');
  const batchRunLabel = $('#batch-run-label');
  const batchZipBtn = $('#batch-zip');
  const fmtToggle = document.querySelector('[data-toggle="fmt"]');
  const BATCH_MAX = 20;
  let batchFmt = 'zentao';
  let batchSeq = 0;
  let batchRunning = false;
  const queue = []; // {id, file, name, status, output}

  const STATUS = {
    queued: { label: '排队中', cls: 'queued' },
    converting: { label: '转换中', cls: 'converting' },
    done: { label: '完成', cls: 'done' },
    failed: { label: '失败', cls: 'failed' },
  };
  const esc = (s) => String(s).replace(/[&<>"]/g,
    (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

  function batchAdd(files) {
    for (const f of files) {
      if (!f.name.toLowerCase().endsWith('.xmind')) continue;
      if (queue.length >= BATCH_MAX) { alert('单批最多 ' + BATCH_MAX + ' 个文件'); break; }
      queue.push({ id: ++batchSeq, file: f, name: f.name, status: 'queued', output: null });
    }
    renderQueue();
  }

  function renderQueue() {
    const has = queue.length > 0;
    batchQueueEl.hidden = !has;
    batchActions.hidden = !has;
    batchQueueEl.innerHTML = queue.map((it) => {
      const s = STATUS[it.status];
      let action;
      if (it.status === 'done' && it.output) {
        action = `<a class="bq-action bq-action--dl" href="/uploads/${encodeURIComponent(it.output)}" download>下载</a>`;
      } else if (it.status === 'converting') {
        action = '<span class="bq-action bq-action--mute">…</span>';
      } else {
        action = `<a class="bq-action" data-remove="${it.id}">移除</a>`;
      }
      return `<div class="bq-row">
        <div class="bq-file">
          <span class="bq-icon"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#8A887E" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><path d="M14 2v6h6"></path></svg></span>
          <div class="bq-meta"><div class="bq-name" title="${esc(it.name)}">${esc(it.name)}</div><div class="bq-sub">XMind → 用例 · ${s.label}</div></div>
        </div>
        <span class="bq-badge bq-badge--${s.cls}"><span class="bq-dot"></span>${s.label}</span>
        ${action}
      </div>`;
    }).join('');
    const pending = queue.filter((it) => it.status === 'queued' || it.status === 'failed').length;
    batchRunLabel.textContent = pending ? `全部转换（${pending}）` : '全部转换';
    batchRunBtn.disabled = batchRunning || pending === 0;
    batchZipBtn.hidden = !queue.some((it) => it.status === 'done');
  }

  batchDropzone.addEventListener('click', () => batchInput.click());
  batchInput.addEventListener('change', () => {
    if (batchInput.files && batchInput.files.length) batchAdd(Array.from(batchInput.files));
    batchInput.value = '';
  });
  ['dragover', 'dragenter'].forEach((ev) => batchDropzone.addEventListener(ev, (e) => {
    e.preventDefault(); batchDropzone.classList.add('dropzone--over');
  }));
  ['dragleave', 'drop'].forEach((ev) => batchDropzone.addEventListener(ev, (e) => {
    e.preventDefault(); batchDropzone.classList.remove('dropzone--over');
  }));
  batchDropzone.addEventListener('drop', (e) => {
    const fs = e.dataTransfer.files;
    if (fs && fs.length) batchAdd(Array.from(fs));
  });

  batchQueueEl.addEventListener('click', (e) => {
    const rm = e.target.closest('[data-remove]');
    if (!rm) return;
    const i = queue.findIndex((it) => it.id === +rm.dataset.remove);
    if (i >= 0) queue.splice(i, 1);
    renderQueue();
  });

  // 切换目标格式：已转换/失败项重置为排队，确保整批统一格式
  fmtToggle.addEventListener('click', (e) => {
    if (batchRunning) return;
    const btn = e.target.closest('[data-fmt]'); if (!btn || btn.dataset.fmt === batchFmt) return;
    batchFmt = btn.dataset.fmt;
    document.querySelectorAll('[data-toggle="fmt"] .seg__btn').forEach(
      (b) => b.classList.toggle('seg__btn--on', b === btn));
    queue.forEach((it) => {
      if (it.status === 'done' || it.status === 'failed') { it.status = 'queued'; it.output = null; }
    });
    renderQueue();
  });

  // 全部转换：串行逐个上传 + 转换，实时翻状态，失败不阻断其余
  batchRunBtn.addEventListener('click', async () => {
    if (batchRunning) return;
    const pending = queue.filter((it) => it.status === 'queued' || it.status === 'failed');
    if (pending.length === 0) return;
    batchRunning = true;
    batchInput.disabled = true;
    renderQueue();
    try {
      for (const it of pending) {
        if (!queue.includes(it)) continue; // 运行中被移除的项跳过
        it.status = 'converting'; it.output = null; renderQueue();
        try {
          const fd = new FormData();
          fd.append('file', it.file);
          fd.append('format', batchFmt);
          const r = await fetch('/api/batch/convert', { method: 'POST', body: fd });
          const body = await r.json();
          if (body.success) { it.status = 'done'; it.output = body.output_filename; }
          else { it.status = 'failed'; }
        } catch (err) { it.status = 'failed'; }
        renderQueue();
      }
    } finally {
      batchRunning = false;
      batchInput.disabled = false;
      renderQueue();
    }
  });

  // 打包 ZIP 下载全部已成功项
  batchZipBtn.addEventListener('click', async () => {
    const files = queue.filter((it) => it.status === 'done' && it.output).map((it) => it.output);
    if (files.length === 0) return;
    batchZipBtn.disabled = true;
    try {
      const r = await fetch('/api/batch/zip', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ files }),
      });
      if (!r.ok) { alert('打包失败'); return; }
      const blob = await r.blob();
      const cd = r.headers.get('Content-Disposition') || '';
      const star = /filename\*=(?:UTF-8'')?([^;]+)/i.exec(cd);
      const plain = /filename="?([^";]+)"?/i.exec(cd);
      let fname = '用例批量.zip';
      if (star) fname = decodeURIComponent(star[1].trim());
      else if (plain) fname = plain[1].trim();
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = fname;
      document.body.appendChild(a); a.click(); a.remove();
      URL.revokeObjectURL(a.href);
    } catch (err) { alert('打包失败，请重试'); }
    finally { batchZipBtn.disabled = false; }
  });

  applyDir();
});

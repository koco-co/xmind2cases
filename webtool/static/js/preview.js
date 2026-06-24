/**
 * 预览页面列自定义交互脚本 v2
 * 保留既有数据流（init/fetchPage/renderPagination/doExport/saveCurrentTemplate/
 * debounceSave/handleDrag*/swapColumnOrder/getColumnValueRaw/escapeHtml）
 * 替换渲染层为 v2 markup (renderTable/renderCell)
 * 新增 priorityMeta/fetchHealth/renderHealth
 */

const DEFAULT_COLUMNS = [
  { id: 'suite', name: '所属模块', order: 1, is_custom: false, rich_text_break: false, empty_check: false },
  { id: 'name', name: '用例标题', order: 2, is_custom: false, rich_text_break: false, empty_check: false },
  { id: 'preconditions', name: '前置条件', order: 3, is_custom: false, rich_text_break: false, empty_check: false },
  { id: 'steps', name: '步骤', order: 4, is_custom: false, rich_text_break: false, empty_check: false },
  { id: 'expectedresults', name: '预期', order: 5, is_custom: false, rich_text_break: false, empty_check: false },
  { id: 'importance', name: '优先级', order: 6, is_custom: false, rich_text_break: false, empty_check: false },
];

const HEADER_COLOR_PRESETS = ['#FAF8F2', '#f8fafc', '#e0f2fe', '#f0fdf4', '#fefce8', '#fef3c7', '#fce7f3', '#ede9fe', '#f3e8ff', '#fae8ff'];

/* ─── 优先级元数据 ─── */
const PRIORITY = {
  1: { label: 'P1', cls: 'p1' },
  2: { label: 'P2', cls: 'p2' },
  3: { label: 'P3', cls: 'p3' },
  4: { label: 'P4', cls: 'p4' },
};
function priorityMeta(importance) {
  const n = parseInt(importance, 10);
  return PRIORITY[n] || PRIORITY[4];
}

const ColumnManager = {
  currentTemplate: null,
  templates: [],
  lastTemplateId: null,
  testcases: [],
  total: 0,
  page: 1,
  pageSize: 20,
  filename: '',
  editMode: false,
  priorityCounts: { '1': 0, '2': 0, '3': 0, '4': 0 },
  _saveTimer: null,
  _draggedColumn: null,
  emptyCells: [],

  escapeHtml(str) {
    if (str === null || str === undefined) return '';
    const div = document.createElement('div');
    div.textContent = String(str);
    return div.innerHTML;
  },

  /* ─── init ─── */
  async init() {
    try {
      this.filename = document.body.dataset.filename || '';
      this.total = parseInt(document.body.dataset.total || '0', 10);
      if (!this.filename) { console.error('未找到文件名'); return; }

      const response = await fetch('/api/templates');
      const result = await response.json();
      if (result.success) {
        this.templates = result.data.templates || [];
        this.lastTemplateId = result.data.last_template_id;
        const tpl = this.templates.find(t => t.id === this.lastTemplateId)
          || this.templates[0]
          || null;
        this.currentTemplate = tpl;
      }

      // 更新模版名称显示
      const tplNameEl = document.getElementById('pv-tpl-name');
      if (tplNameEl && this.currentTemplate) tplNameEl.textContent = this.currentTemplate.name;

      // 体检（全量）→ health bar → 首页数据
      await this.fetchHealth();
      this.renderHealth();
      await this.fetchPage();
      this.bindEvents();
    } catch (error) {
      console.error('ColumnManager 初始化失败:', error);
    }
  },

  /* ─── 体检摘要（全量）：total + 优先级分布 + 空值 ─── */
  async fetchHealth() {
    const tplId = this.currentTemplate && this.currentTemplate.id;
    const q = tplId ? `?template_id=${tplId}` : '';
    try {
      const r = await fetch(`/api/preview/${encodeURIComponent(this.filename)}/empty-cells${q}`);
      const res = await r.json();
      if (res.success) {
        this.emptyCells = res.data.empty_cells || [];
        this.total = res.data.total != null ? res.data.total : this.total;
        this.priorityCounts = res.data.priority_counts || { '1': 0, '2': 0, '3': 0, '4': 0 };
      }
    } catch (e) {
      this.emptyCells = [];
      this.priorityCounts = { '1': 0, '2': 0, '3': 0, '4': 0 };
    }
  },

  /* ─── 体检栏渲染 ─── */
  renderHealth() {
    const el = document.getElementById('health');
    if (!el) return;
    const pc = this.priorityCounts || { '1': 0, '2': 0, '3': 0, '4': 0 };
    const empty = (this.emptyCells || []).length;

    // 优先级颜色与原型 --p* 变量对应
    const priColors = [
      ['1', 'var(--p1-fg)'],
      ['2', 'var(--p2-fg)'],
      ['3', 'var(--p3-fg)'],
      ['4', 'var(--p4-fg)'],
    ];
    const dots = priColors
      .filter(([k]) => pc[k] > 0)
      .map(([k, c]) =>
        `<span class="health__pri"><span class="pri-dot" style="background:${c}"></span>${priorityMeta(k).label} · ${pc[k]}</span>`
      ).join('');

    el.innerHTML = `
      <div class="health__brand">
        <div class="health__icon-wrap">
          <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="#5E7355" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><path d="M22 4L12 14.01l-3-3"></path></svg>
        </div>
        <div>
          <div class="health__t">用例体检</div>
          <div class="health__s">导出前自动检查质量</div>
        </div>
      </div>
      <span class="health__div"></span>
      <div class="health__count"><span class="serif">${this.total}</span> 条用例</div>
      ${empty > 0 ? `
        <div class="health__warn">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><path d="M12 9v4M12 17h.01"></path></svg>
          ${empty} 处待补充
        </div>` : ''}
      <div class="health__pris"><span class="health__pris-label">优先级</span>${dots}</div>`;
  },

  /* ─── 分页数据拉取 ─── */
  async fetchPage() {
    try {
      const url = `/api/preview/${encodeURIComponent(this.filename)}/cases?page=${this.page}&page_size=${this.pageSize}`;
      const response = await fetch(url);
      const result = await response.json();
      if (result.success) {
        this.testcases = result.data.testcases || [];
        // 使用 fetchHealth 拿到的 total，避免覆盖
        const serverTotal = result.data.total || 0;
        if (serverTotal > this.total) this.total = serverTotal;
        this.page = result.data.page || 1;
        this.pageSize = result.data.page_size || this.pageSize;
        this.renderTable();
        this.renderPagination();
      }
    } catch (error) {
      console.error('获取数据失败:', error);
    }
  },

  /* ─── 表格渲染（v2）─── */
  renderTable() {
    const table = document.getElementById('case-table');
    if (!table) return;

    const cols = [...((this.currentTemplate && this.currentTemplate.columns) || DEFAULT_COLUMNS)]
      .sort((a, b) => (a.order || 0) - (b.order || 0));
    const headerColor = (this.currentTemplate && this.currentTemplate.header_color) || '#FAF8F2';
    const start = (this.page - 1) * this.pageSize;
    const emptySet = new Set((this.emptyCells || []).map((c) => `${c.colId}:${c.rowIndex}`));
    const edit = !!this.editMode;

    const thead = table.querySelector('thead tr');
    thead.innerHTML =
      `<th class="col-th idx-th" style="background:${headerColor}">序号</th>` +
      cols.map((col) => `
        <th class="col-th" data-col-id="${this.escapeHtml(col.id)}"
            ${edit ? 'draggable="true"' : ''}
            style="background:${headerColor}">
          <div class="col-th__inner">
            ${edit ? '<span class="drag-handle" title="拖动调整列顺序"><svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><circle cx="9" cy="6" r="1.6"></circle><circle cx="15" cy="6" r="1.6"></circle><circle cx="9" cy="12" r="1.6"></circle><circle cx="15" cy="12" r="1.6"></circle><circle cx="9" cy="18" r="1.6"></circle><circle cx="15" cy="18" r="1.6"></circle></svg></span>' : ''}
            <span class="col-title">${this.escapeHtml(col.name)}</span>
            ${edit && col.type !== 'index' ? `
              <span class="col-actions">
                <button class="edit-col col-action-btn" title="编辑列"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4z"></path></svg></button>
                <button class="add-col col-action-btn" title="新增列"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M5 12h14"></path></svg></button>
                ${col.is_custom ? '<button class="del-col col-action-btn" title="删除列"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18M8 6V4h8v2M6 6l1 14h10l1-14"></path></svg></button>' : ''}
              </span>` : ''}
          </div>
        </th>`).join('') +
      (edit ? '<th class="col-th op-th">操作</th>' : '');

    const tbody = table.querySelector('tbody');
    tbody.innerHTML = this.testcases.map((tc, i) => {
      const gi = start + i;
      return `<tr>
        <td class="idx-cell"><span class="serif">${gi + 1}</span></td>
        ${cols.map((col) => `<td data-col-id="${this.escapeHtml(col.id)}" data-row="${gi}">${this.renderCell(tc, col, gi, emptySet)}</td>`).join('')}
        ${edit ? `<td class="op-cell"><button class="del-row btn--disabled" title="暂未上线" disabled><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18M8 6V4h8v2M6 6l1 14h10l1-14"></path></svg></button></td>` : ''}
      </tr>`;
    }).join('');
  },

  /* ─── 单元格渲染（v2）─── */
  renderCell(tc, col, rowIndex, emptySet) {
    if (col.type === 'index') return '';

    if (col.id === 'importance' || col.type === 'priority') {
      const m = priorityMeta(tc.importance || 4);
      return `<span class="pri-badge pri-badge--${m.cls}">${m.label}</span>`;
    }

    if (col.id === 'steps' || col.type === 'steps') {
      const steps = tc.steps || [];
      if (steps.length === 0) return '<span class="cell-text"></span>';
      return `<ol class="steps-list">${steps.map((s, i) =>
        `<li><span class="step-n">${i + 1}</span>${this.escapeHtml(s.actions || '')}</li>`
      ).join('')}</ol>`;
    }

    if (col.id === 'expectedresults') {
      const steps = tc.steps || [];
      if (steps.length === 0) return '<span class="cell-text"></span>';
      return `<ol class="steps-list steps-list--exp">${steps.map((s, i) =>
        `<li><span class="step-n">${i + 1}</span>${this.escapeHtml(s.expectedresults || '')}</li>`
      ).join('')}</ol>`;
    }

    const raw = this.getColumnValueRaw(tc, col, rowIndex);
    const isEmpty = emptySet.has(`${col.id}:${rowIndex}`);
    if (isEmpty && col.empty_check) {
      return `<span class="empty-chip"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><path d="M12 9v4M12 17h.01"></path></svg>待补充</span>`;
    }

    const tooLong = col.id === 'name' && (tc.name || '').length > 100;
    return `<span class="cell-text${tooLong ? ' cell-text--long' : ''}">${this.escapeHtml(raw)}</span>${
      tooLong ? '<span class="cell-warn">标题过长</span>' : ''}`;
  },

  /* ─── 分页渲染（v2 原型风格）─── */
  renderPagination() {
    const bar = document.getElementById('pagination-bar');
    if (!bar) return;

    const totalPages = Math.max(1, Math.ceil(this.total / this.pageSize));
    const start = (this.page - 1) * this.pageSize + 1;
    const end = Math.min(this.page * this.pageSize, this.total);

    const pageSizeOptions = [10, 20, 50, 100].map(n =>
      `<option value="${n}" ${this.pageSize === n ? 'selected' : ''}>${n}</option>`
    ).join('');

    bar.innerHTML = `
      <div class="pager__left">
        <span class="pager__label">每页</span>
        <select class="pager__size-sel" id="page-size-select">${pageSizeOptions}</select>
        <span class="pager__label">条 · 共 ${this.total} 条（第 ${start}–${end}）</span>
      </div>
      <div class="pager__right">
        <button class="pager__btn" data-page="1" title="首页" ${this.page <= 1 ? 'disabled' : ''}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 17l-5-5 5-5M18 17l-5-5 5-5"></path></svg>
        </button>
        <button class="pager__btn" data-page="${this.page - 1}" title="上一页" ${this.page <= 1 ? 'disabled' : ''}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"></path></svg>
        </button>
        ${this.buildPageNums(totalPages)}
        <button class="pager__btn" data-page="${this.page + 1}" title="下一页" ${this.page >= totalPages ? 'disabled' : ''}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18l6-6-6-6"></path></svg>
        </button>
        <button class="pager__btn" data-page="${totalPages}" title="末页" ${this.page >= totalPages ? 'disabled' : ''}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 17l5-5-5-5M6 17l5-5-5-5"></path></svg>
        </button>
      </div>`;

    bar.querySelectorAll('.pager__btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const p = parseInt(btn.dataset.page, 10);
        if (!isNaN(p) && p >= 1 && p <= totalPages) {
          this.page = p;
          this.fetchPage();
        }
      });
    });

    bar.querySelector('#page-size-select')?.addEventListener('change', (e) => {
      this.pageSize = parseInt(e.target.value, 10);
      this.page = 1;
      this.fetchPage();
    });
  },

  buildPageNums(totalPages) {
    if (totalPages <= 7) {
      return Array.from({ length: totalPages }, (_, i) => i + 1).map(p =>
        `<button class="pager__btn${p === this.page ? ' pager__btn--on' : ''}" data-page="${p}">${p}</button>`
      ).join('');
    }
    // Ellipsis logic
    const pages = new Set([1, 2, this.page - 1, this.page, this.page + 1, totalPages - 1, totalPages]);
    const sorted = [...pages].filter(p => p >= 1 && p <= totalPages).sort((a, b) => a - b);
    let html = '';
    let prev = 0;
    for (const p of sorted) {
      if (prev && p - prev > 1) html += '<span class="pager__ellipsis">…</span>';
      html += `<button class="pager__btn${p === this.page ? ' pager__btn--on' : ''}" data-page="${p}">${p}</button>`;
      prev = p;
    }
    return html;
  },

  /* ─── 原始值取值（保留既有）─── */
  getColumnValueRaw(testcase, column, rowIndex) {
    const colId = column.id;
    const isCustom = column.is_custom || false;
    const defaultValue = column.default_value || '';

    if (isCustom) {
      const values = column.values || {};
      return values[rowIndex] !== undefined ? values[rowIndex] : defaultValue;
    }

    switch (colId) {
      case 'suite': return testcase.suite || '';
      case 'name': return testcase.name || '';
      case 'preconditions': return testcase.preconditions || '';
      case 'steps':
        return (testcase.steps || []).map(s => s.actions || '').join('\n');
      case 'expectedresults':
        return (testcase.steps || []).map(s => s.expectedresults || '').join('\n');
      case 'importance': return String(testcase.importance || '');
      default: return defaultValue;
    }
  },

  /* ─── 事件绑定 ─── */
  bindEvents() {
    // 导出按钮
    document.querySelectorAll('.export-btn').forEach(btn => {
      btn.addEventListener('click', () => this.openExportModal(btn.dataset.type));
    });

    // 模版设置
    const tplSettingsBtn = document.getElementById('tpl-settings-btn');
    if (tplSettingsBtn) {
      tplSettingsBtn.addEventListener('click', () => this.openTemplateSettingsModal());
    }

    // 编辑模式切换（Task 6 完整实现，这里只做骨架）
    const editToggle = document.getElementById('edit-toggle');
    if (editToggle) {
      editToggle.addEventListener('click', () => {
        this.editMode = !this.editMode;
        editToggle.textContent = this.editMode ? '退出编辑' : '编辑模式';
        editToggle.classList.toggle('btn--ink', this.editMode);
        editToggle.classList.toggle('btn--outline', !this.editMode);
        const banner = document.getElementById('edit-banner');
        if (banner) {
          if (this.editMode) {
            banner.hidden = false;
            banner.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M12 16v-4M12 8h.01"></path></svg>
              编辑模式：拖动表头可调整列顺序，点击 ✎ 改列、＋ 加列；单元格可直接修改。`;
          } else {
            banner.hidden = true;
          }
        }
        this.renderTable();
      });
    }

    // 拖拽（保留既有逻辑）
    const table = document.getElementById('case-table');
    if (!table) return;
    const thead = table.querySelector('thead');
    if (thead) {
      thead.addEventListener('dragstart', (e) => this.handleDragStart(e));
      thead.addEventListener('dragover', (e) => this.handleDragOver(e));
      thead.addEventListener('dragleave', (e) => this.handleDragLeave(e));
      thead.addEventListener('drop', (e) => this.handleDrop(e));
      thead.addEventListener('dragend', (e) => this.handleDragEnd(e));

      thead.addEventListener('click', (e) => {
        const editBtn = e.target.closest('.edit-col');
        const addBtn = e.target.closest('.add-col');
        const deleteBtn = e.target.closest('.del-col');
        const titleSpan = e.target.closest('.col-title');

        if (editBtn) {
          const th = editBtn.closest('th');
          const colId = th?.dataset?.colId;
          if (colId) this.openEditColumnModal(colId);
        }
        if (addBtn) {
          const th = addBtn.closest('th');
          const colId = th?.dataset?.colId;
          if (colId) this.openAddColumnModal(colId);
        }
        if (deleteBtn) {
          const th = deleteBtn.closest('th');
          const colId = th?.dataset?.colId;
          if (colId) this.deleteColumn(colId);
        }
        if (titleSpan && !editBtn && !addBtn && !deleteBtn) {
          const th = titleSpan.closest('th');
          const colId = th?.dataset?.colId;
          if (colId) this.editColumnTitleInline(colId, titleSpan);
        }
      });
    }

    const tbody = table.querySelector('tbody');
    if (tbody) {
      tbody.addEventListener('dblclick', (e) => {
        const cell = e.target.closest('td[data-col-id]');
        if (!cell) return;
        const colId = cell.dataset.colId;
        const col = this.currentTemplate?.columns?.find(c => c.id === colId);
        if (col && col.is_custom) {
          const row = parseInt(cell.dataset.row, 10);
          this.editCell(colId, row, cell);
        }
      });
    }
  },

  /* ─── 拖拽（保留既有）─── */
  handleDragStart(e) {
    const th = e.target.closest('th[data-col-id]');
    if (!th) return;
    this._draggedColumn = th.dataset.colId;
    th.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
  },

  handleDragOver(e) {
    e.preventDefault();
    const th = e.target.closest('th[data-col-id]');
    if (!th || th.dataset.colId === this._draggedColumn) return;
    th.classList.add('drag-over');
    e.dataTransfer.dropEffect = 'move';
  },

  handleDragLeave(e) {
    const th = e.target.closest('th[data-col-id]');
    if (th) th.classList.remove('drag-over');
  },

  handleDrop(e) {
    e.preventDefault();
    const th = e.target.closest('th[data-col-id]');
    if (!th || !this._draggedColumn) return;
    const targetColId = th.dataset.colId;
    if (targetColId !== this._draggedColumn) {
      this.swapColumnOrder(this._draggedColumn, targetColId);
    }
    th.classList.remove('drag-over');
  },

  handleDragEnd(e) {
    const th = e.target.closest('th[data-col-id]');
    if (th) th.classList.remove('dragging');
    this._draggedColumn = null;
    document.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over'));
  },

  swapColumnOrder(colId1, colId2) {
    if (!this.currentTemplate) return;
    const columns = this.currentTemplate.columns;
    const col1 = columns.find(c => c.id === colId1);
    const col2 = columns.find(c => c.id === colId2);
    if (!col1 || !col2) return;
    const tempOrder = col1.order;
    col1.order = col2.order;
    col2.order = tempOrder;
    this.renderTable();
    this.debounceSave();
  },

  debounceSave() {
    if (this._saveTimer) clearTimeout(this._saveTimer);
    this._saveTimer = setTimeout(() => this.saveCurrentTemplate(), 1000);
  },

  async saveCurrentTemplate() {
    if (!this.currentTemplate?.id) return;
    try {
      const response = await fetch(`/api/templates/${this.currentTemplate.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          columns: this.currentTemplate.columns,
          header_color: this.currentTemplate.header_color || '#FAF8F2',
        }),
      });
      const result = await response.json();
      if (result.success) {
        // 模版变化后重新拉体检（全量）
        await this.fetchHealth();
        this.renderHealth();
        this.renderTable();
      } else {
        console.error('保存模版失败:', result.message);
      }
    } catch (error) {
      console.error('保存模版失败:', error);
    }
  },

  /* ─── 通用弹窗（保留既有逻辑，markup 适配 theme.css .modal*）─── */
  showModal(title, fields, onConfirm) {
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    const fieldsHtml = fields.map(f => {
      if (f.type === 'color') {
        return `<div class="modal__field">
          <label class="modal__label">${this.escapeHtml(f.label)}</label>
          <input type="color" id="modal-${f.id}" value="${this.escapeHtml(f.value || '#FAF8F2')}" class="modal__input" style="height:44px;">
          <input type="text" id="modal-${f.id}-text" value="${this.escapeHtml(f.value || '#FAF8F2')}" class="modal__input" style="margin-top:6px;">
        </div>`;
      } else if (f.type === 'checkbox') {
        return `<div class="modal__field">
          <label class="modal__check">
            <input type="checkbox" id="modal-${f.id}" ${f.value ? 'checked' : ''}>
            <span>
              <span style="font-size:13px;font-weight:500;color:var(--text);">${this.escapeHtml(f.label)}</span>
              ${f.desc ? `<span style="display:block;font-size:12px;color:var(--text-3);margin-top:2px;">${this.escapeHtml(f.desc)}</span>` : ''}
            </span>
          </label>
        </div>`;
      } else {
        return `<div class="modal__field">
          <label class="modal__label">${this.escapeHtml(f.label)}</label>
          <input type="text" id="modal-${f.id}" value="${this.escapeHtml(f.value || '')}" placeholder="${this.escapeHtml(f.placeholder || '')}" class="modal__input">
        </div>`;
      }
    }).join('');

    overlay.innerHTML = `
      <div class="modal">
        <div class="modal__title">${this.escapeHtml(title)}</div>
        <div class="modal__divider"></div>
        ${fieldsHtml}
        <div class="modal__actions">
          <button class="btn btn--outline" id="modal-cancel">取消</button>
          <button class="btn btn--ink" id="modal-confirm">确定</button>
        </div>
      </div>`;

    document.body.appendChild(overlay);

    const closeModal = () => document.body.removeChild(overlay);

    overlay.querySelector('#modal-cancel').addEventListener('click', closeModal);
    overlay.addEventListener('click', (e) => { if (e.target === overlay) closeModal(); });

    overlay.querySelector('#modal-confirm').addEventListener('click', () => {
      const data = {};
      fields.forEach(f => {
        const input = overlay.querySelector(`#modal-${f.id}`);
        if (f.type === 'color') {
          data[f.id] = input ? input.value : (f.value || '#FAF8F2');
        } else if (f.type === 'checkbox') {
          data[f.id] = input ? input.checked : false;
        } else {
          data[f.id] = input ? input.value.trim() : '';
        }
      });
      closeModal();
      onConfirm(data);
    });

    const firstInput = overlay.querySelector('input[type="text"]');
    if (firstInput) firstInput.focus();
  },

  /* ─── 模版设置弹窗（保留既有逻辑，markup 适配 theme.css）─── */
  openTemplateSettingsModal() {
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay template-settings-modal';
    overlay.innerHTML = `
      <div class="modal" style="min-width:480px;">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
          <div class="modal__title" style="margin:0;">模版设置</div>
          <button type="button" class="btn btn--outline" id="tpl-add-btn" style="font-size:13px;">+ 新建模版</button>
        </div>
        <div class="modal__divider"></div>
        <div id="tpl-settings-message" style="display:none;font-size:13px;color:var(--p1-fg);margin-bottom:10px;"></div>
        <div class="template-settings-list" style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:18px;"></div>
        <div class="modal__actions">
          <button class="btn btn--outline" id="tpl-settings-close">关闭</button>
          <button class="btn btn--ink" id="tpl-settings-apply">应用</button>
        </div>
      </div>`;

    const listEl = overlay.querySelector('.template-settings-list');
    const renderList = () => {
      listEl.innerHTML = this.templates.map(tpl => {
        const bg = tpl.header_color || '#FAF8F2';
        return `
          <label class="tpl-settings-item" style="background:${bg}">
            <input type="radio" name="tpl-apply" value="${tpl.id}" ${tpl.id === this.currentTemplate?.id ? 'checked' : ''} style="display:none;">
            <span class="tpl-name" style="font-size:13px;font-weight:500;color:var(--text);">${this.escapeHtml(tpl.name)}</span>
            <button type="button" class="edit-tpl-btn tpl-action-btn" data-id="${tpl.id}" title="编辑">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4z"></path></svg>
            </button>
            <button type="button" class="delete-tpl-btn tpl-action-btn" data-id="${tpl.id}" title="删除" ${this.templates.length <= 1 ? 'disabled' : ''}>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18M8 6V4h8v2M6 6l1 14h10l1-14"></path></svg>
            </button>
          </label>`;
      }).join('');
    };
    renderList();
    document.body.appendChild(overlay);

    overlay.addEventListener('click', (e) => { if (e.target === overlay) document.body.removeChild(overlay); });

    overlay.querySelector('#tpl-add-btn').addEventListener('click', async (e) => {
      e.preventDefault();
      const msgEl = overlay.querySelector('#tpl-settings-message');
      msgEl.style.display = 'none';
      try {
        const response = await fetch('/api/templates', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: '未命名模版',
            columns: this.currentTemplate ? JSON.parse(JSON.stringify(this.currentTemplate.columns)) : JSON.parse(JSON.stringify(DEFAULT_COLUMNS)),
            header_color: this.currentTemplate?.header_color || '#FAF8F2',
          }),
        });
        const result = await response.json();
        if (result.success) {
          const listRes = await fetch('/api/templates');
          const listResult = await listRes.json();
          if (listResult.success) {
            this.templates = listResult.data.templates || [];
            renderList();
          }
        } else {
          msgEl.textContent = result.message || '模版名称已存在';
          msgEl.style.display = 'block';
        }
      } catch (error) {
        msgEl.textContent = '创建失败，请重试';
        msgEl.style.display = 'block';
      }
    });

    listEl.addEventListener('click', (e) => {
      const editBtn = e.target.closest('.edit-tpl-btn');
      const deleteBtn = e.target.closest('.delete-tpl-btn');
      const item = e.target.closest('.tpl-settings-item');
      if (editBtn) {
        e.preventDefault();
        const id = parseInt(editBtn.dataset.id, 10);
        document.body.removeChild(overlay);
        this.openTemplateEditModal(id, () => this.openTemplateSettingsModal());
        return;
      }
      if (deleteBtn && !deleteBtn.disabled) {
        e.preventDefault();
        const id = parseInt(deleteBtn.dataset.id, 10);
        if (this.templates.length <= 1) return;
        if (!confirm('确定删除该模版？')) return;
        fetch(`/api/templates/${id}`, { method: 'DELETE' }).then(() => {
          this.templates = this.templates.filter(p => p.id !== id);
          if (this.currentTemplate?.id === id) this.currentTemplate = this.templates[0];
          renderList();
          this.renderTable();
        });
        return;
      }
      if (item) {
        const radio = item.querySelector('input[type="radio"]');
        if (radio) radio.checked = true;
        listEl.querySelectorAll('.tpl-settings-item').forEach(el => el.classList.remove('tpl-settings-item--on'));
        item.classList.add('tpl-settings-item--on');
      }
    });

    overlay.querySelector('#tpl-settings-close').addEventListener('click', () => document.body.removeChild(overlay));

    overlay.querySelector('#tpl-settings-apply').addEventListener('click', () => {
      const radio = overlay.querySelector('input[name="tpl-apply"]:checked');
      if (radio) {
        const templateId = parseInt(radio.value, 10);
        const tpl = this.templates.find(t => t.id === templateId);
        if (tpl) {
          this.currentTemplate = tpl;
          const tplNameEl = document.getElementById('pv-tpl-name');
          if (tplNameEl) tplNameEl.textContent = tpl.name;
          this.fetchHealth().then(() => { this.renderHealth(); this.renderTable(); });
        }
      }
      document.body.removeChild(overlay);
    });
  },

  /* ─── 模版编辑弹窗（保留既有逻辑）─── */
  openTemplateEditModal(templateId, onClose) {
    const tpl = this.templates.find(t => t.id === templateId);
    if (!tpl) return;

    const columns = JSON.parse(JSON.stringify(tpl.columns || []));
    const sortedColumns = [...columns].sort((a, b) => (a.order || 0) - (b.order || 0));
    const defaultColIds = ['suite', 'name', 'preconditions', 'steps', 'expectedresults', 'importance'];
    let headerColor = tpl.header_color || '#FAF8F2';

    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay template-edit-modal';
    overlay.innerHTML = `
      <div class="modal" style="min-width:520px;max-height:90vh;overflow-y:auto;">
        <div class="modal__title">编辑模版</div>
        <div class="modal__divider"></div>
        <div id="tpl-edit-message" style="display:none;font-size:13px;color:var(--p1-fg);margin-bottom:10px;"></div>
        <div class="modal__field">
          <label class="modal__label">模版名称</label>
          <input type="text" id="tpl-edit-name" value="${this.escapeHtml(tpl.name)}" placeholder="模版名称" maxlength="20" class="modal__input">
        </div>
        <div class="modal__field">
          <label class="modal__label">标题行字段</label>
          <div class="tpl-edit-columns-list" style="border:1px solid var(--border);border-radius:10px;padding:12px;max-height:240px;overflow-y:auto;"></div>
          <div style="margin-top:10px;display:flex;gap:8px;">
            <button type="button" class="btn btn--outline tpl-add-column-btn" style="font-size:13px;">+ 新增字段</button>
            <button type="button" class="btn btn--outline tpl-restore-default-btn" style="font-size:13px;">恢复默认</button>
          </div>
        </div>
        <div class="modal__field">
          <label class="modal__label">标题行颜色</label>
          <div class="color-swatch-grid" style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px;"></div>
          <input type="text" id="tpl-edit-header-color-text" value="${headerColor}" placeholder="#FAF8F2" class="modal__input">
        </div>
        <div class="modal__actions">
          <button class="btn btn--outline" id="tpl-edit-cancel">取消</button>
          <button class="btn btn--ink" id="tpl-edit-save">保存</button>
        </div>
      </div>`;

    const listEl = overlay.querySelector('.tpl-edit-columns-list');
    const swatchGrid = overlay.querySelector('.color-swatch-grid');
    const colorText = overlay.querySelector('#tpl-edit-header-color-text');

    const renderColorSwatches = () => {
      swatchGrid.innerHTML = HEADER_COLOR_PRESETS.map(c =>
        `<button type="button" class="swatch${c === headerColor ? ' swatch--on' : ''}" data-color="${c}" style="background:${c}" title="${c}"></button>`
      ).join('');
    };
    renderColorSwatches();

    swatchGrid.addEventListener('click', (e) => {
      const btn = e.target.closest('.swatch');
      if (btn) { headerColor = btn.dataset.color; colorText.value = headerColor; renderColorSwatches(); }
    });
    colorText.addEventListener('input', () => {
      const v = (colorText.value || '').trim();
      if (/^#[0-9a-fA-F]{6}$/.test(v)) { headerColor = v; renderColorSwatches(); }
    });

    const renderColumnRow = (col, index) => {
      const isDefault = defaultColIds.includes(col.id);
      const row = document.createElement('div');
      row.className = 'tpl-edit-column-row tpl-col-collapsed';
      row.dataset.colId = col.id;
      row.dataset.index = String(index);

      const header = document.createElement('div');
      header.className = 'tpl-col-header';
      header.style.cssText = 'display:flex;align-items:center;gap:8px;cursor:pointer;padding:6px 0;';
      const toggleIcon = document.createElement('span');
      toggleIcon.className = 'tpl-col-toggle';
      toggleIcon.style.color = 'var(--text-3)';
      toggleIcon.innerHTML = '<svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>';
      const nameSpan = document.createElement('span');
      nameSpan.style.cssText = 'font-size:13px;font-weight:500;color:var(--text);';
      nameSpan.textContent = col.name || '未命名';
      header.appendChild(toggleIcon);
      header.appendChild(nameSpan);
      if (!isDefault) {
        const delBtn = document.createElement('button');
        delBtn.type = 'button';
        delBtn.className = 'tpl-col-delete';
        delBtn.style.cssText = 'margin-left:auto;background:none;border:none;cursor:pointer;color:var(--text-3);padding:4px;';
        delBtn.title = '删除';
        delBtn.innerHTML = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18M8 6V4h8v2M6 6l1 14h10l1-14"></path></svg>';
        delBtn.addEventListener('click', (e) => { e.stopPropagation(); });
        header.appendChild(delBtn);
      }
      row.appendChild(header);

      const body = document.createElement('div');
      body.className = 'tpl-col-body';
      body.style.cssText = 'display:none;padding:8px 0 4px 22px;';

      const nameField = document.createElement('div');
      nameField.style.marginBottom = '8px';
      nameField.innerHTML = '<label style="font-size:12px;color:var(--text-3);display:block;margin-bottom:4px;">字段名</label>';
      const nameInput = document.createElement('input');
      nameInput.type = 'text';
      nameInput.className = 'tpl-col-name modal__input';
      nameInput.style.cssText = 'padding:7px 10px;font-size:13px;';
      nameInput.placeholder = '字段名';
      nameInput.value = col.name || '';
      nameField.appendChild(nameInput);
      body.appendChild(nameField);

      if (col.is_custom) {
        const defField = document.createElement('div');
        defField.style.marginBottom = '8px';
        defField.innerHTML = '<label style="font-size:12px;color:var(--text-3);display:block;margin-bottom:4px;">默认值</label>';
        const defInput = document.createElement('input');
        defInput.type = 'text';
        defInput.className = 'tpl-col-default modal__input';
        defInput.style.cssText = 'padding:7px 10px;font-size:13px;';
        defInput.placeholder = '可选';
        defInput.value = col.default_value || '';
        defField.appendChild(defInput);
        body.appendChild(defField);
      }

      const optsField = document.createElement('div');
      optsField.style.cssText = 'display:flex;flex-direction:column;gap:8px;';
      optsField.innerHTML = `
        <label class="modal__check">
          <input type="checkbox" class="tpl-col-rich-text-break-input" ${col.rich_text_break ? 'checked' : ''}>
          <span><span style="font-size:13px;font-weight:500;color:var(--text);">富文本换行处理</span><span style="display:block;font-size:12px;color:var(--text-3);">导出时将换行符转为 HTML 换行标签</span></span>
        </label>
        <label class="modal__check">
          <input type="checkbox" class="tpl-col-empty-check-input" ${col.empty_check ? 'checked' : ''}>
          <span><span style="font-size:13px;font-weight:500;color:var(--text);">空值校验处理</span><span style="display:block;font-size:12px;color:var(--text-3);">当该列存在空值时显示提醒</span></span>
        </label>`;
      body.appendChild(optsField);
      row.appendChild(body);

      header.addEventListener('click', (e) => {
        if (e.target.closest('.tpl-col-delete')) return;
        const collapsed = body.style.display === 'none';
        body.style.display = collapsed ? 'block' : 'none';
        toggleIcon.innerHTML = collapsed
          ? '<svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>'
          : '<svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>';
      });

      return row;
    };

    const syncColumnsFromDOM = () => {
      listEl.querySelectorAll('.tpl-edit-column-row').forEach((row) => {
        const colId = row.dataset?.colId;
        const col = sortedColumns.find(c => c.id === colId);
        if (col) {
          const nameInput = row.querySelector('.tpl-col-name');
          const defaultInput = row.querySelector('.tpl-col-default');
          const richTextInput = row.querySelector('.tpl-col-rich-text-break-input');
          const emptyCheckInput = row.querySelector('.tpl-col-empty-check-input');
          if (nameInput) col.name = (nameInput.value || '').trim() || col.name;
          if (col.is_custom && defaultInput) col.default_value = (defaultInput.value || '').trim();
          if (richTextInput) col.rich_text_break = richTextInput.checked;
          if (emptyCheckInput) col.empty_check = emptyCheckInput.checked;
        }
      });
    };

    const refreshColumnList = (opts = {}) => {
      if (opts.skipSync !== true) syncColumnsFromDOM();
      listEl.innerHTML = '';
      sortedColumns.forEach((col, i) => listEl.appendChild(renderColumnRow(col, i)));
    };
    refreshColumnList({ skipSync: true });

    listEl.addEventListener('click', (e) => {
      const delBtn = e.target.closest('.tpl-col-delete');
      if (!delBtn) return;
      e.stopPropagation();
      const row = delBtn.closest('.tpl-edit-column-row');
      const colId = row?.dataset?.colId;
      if (!colId || defaultColIds.includes(colId)) return;
      const idx = sortedColumns.findIndex(c => c.id === colId);
      if (idx >= 0) { sortedColumns.splice(idx, 1); refreshColumnList(); }
    });

    overlay.querySelector('.tpl-add-column-btn').addEventListener('click', () => {
      const customColumns = sortedColumns.filter(c => c.is_custom);
      const maxNum = customColumns.reduce((max, c) => {
        const m = (c.id || '').match(/^custom_(\d+)$/);
        return Math.max(max, m ? parseInt(m[1]) : 0);
      }, 0);
      sortedColumns.push({
        id: `custom_${maxNum + 1}`,
        name: '未命名字段',
        order: sortedColumns.length + 1,
        is_custom: true,
        default_value: '',
        rich_text_break: false,
        empty_check: false,
        values: {},
      });
      refreshColumnList();
    });

    overlay.querySelector('.tpl-restore-default-btn').addEventListener('click', () => {
      sortedColumns.length = 0;
      DEFAULT_COLUMNS.forEach((c, i) => sortedColumns.push({ ...c, order: i + 1, rich_text_break: false, empty_check: false }));
      headerColor = '#FAF8F2';
      colorText.value = headerColor;
      renderColorSwatches();
      refreshColumnList({ skipSync: true });
    });

    const closeAndReturn = () => {
      document.body.removeChild(overlay);
      if (typeof onClose === 'function') onClose();
    };

    overlay.querySelector('#tpl-edit-cancel').addEventListener('click', closeAndReturn);
    overlay.addEventListener('click', (e) => { if (e.target === overlay) closeAndReturn(); });

    overlay.querySelector('#tpl-edit-save').addEventListener('click', async () => {
      const msgEl = overlay.querySelector('#tpl-edit-message');
      msgEl.style.display = 'none';
      const nameInput = overlay.querySelector('#tpl-edit-name');
      const name = (nameInput?.value || '').trim() || tpl.name;
      syncColumnsFromDOM();
      overlay.querySelectorAll('.tpl-edit-column-row').forEach((row, i) => {
        const colId = row.dataset?.colId;
        const col = sortedColumns.find(c => c.id === colId);
        if (col) col.order = i + 1;
      });
      const finalHeaderColor = (colorText.value || '').trim() || headerColor;
      if (!/^#[0-9a-fA-F]{6}$/.test(finalHeaderColor)) {
        msgEl.textContent = '请输入有效的十六进制颜色（如 #FAF8F2）';
        msgEl.style.display = 'block';
        return;
      }
      try {
        const response = await fetch(`/api/templates/${templateId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, columns: sortedColumns, header_color: finalHeaderColor }),
        });
        const result = await response.json();
        if (result.success) {
          tpl.name = name;
          tpl.columns = sortedColumns;
          tpl.header_color = finalHeaderColor;
          this.currentTemplate = tpl;
          const tplNameEl = document.getElementById('pv-tpl-name');
          if (tplNameEl) tplNameEl.textContent = tpl.name;
          await this.fetchHealth();
          this.renderHealth();
          this.renderTable();
          closeAndReturn();
        } else {
          msgEl.textContent = result.message || '保存失败';
          msgEl.style.display = 'block';
        }
      } catch (error) {
        msgEl.textContent = '保存失败，请重试';
        msgEl.style.display = 'block';
      }
    });

    document.body.appendChild(overlay);
    overlay.querySelector('#tpl-edit-name')?.focus();
  },

  openAddColumnModal(afterColId) {
    this.showModal('新增列', [
      { id: 'name', label: '列名称', value: '未命名字段', placeholder: '未命名字段' },
      { id: 'default_value', label: '默认值', value: '', placeholder: '可选，为空则留空' },
      { id: 'rich_text_break', type: 'checkbox', label: '富文本换行处理', value: false, desc: '导出时将换行符转为 HTML 换行标签' },
      { id: 'empty_check', type: 'checkbox', label: '空值校验处理', value: false, desc: '当该列存在空值时显示提醒' },
    ], async (data) => {
      await this.addColumn(data.name || '未命名字段', data.default_value || '', data.rich_text_break || false, data.empty_check || false, afterColId);
    });
  },

  openEditColumnModal(colId) {
    if (!this.currentTemplate) return;
    const column = this.currentTemplate.columns.find(c => c.id === colId);
    if (!column) return;
    this.showModal('编辑列', [
      { id: 'name', label: '列名称', value: column.name },
      { id: 'default_value', label: '默认值', value: column.default_value || '', placeholder: '自定义列可设置' },
      { id: 'rich_text_break', type: 'checkbox', label: '富文本换行处理', value: !!column.rich_text_break, desc: '导出时将换行符转为 HTML 换行标签' },
      { id: 'empty_check', type: 'checkbox', label: '空值校验处理', value: !!column.empty_check, desc: '当该列存在空值时显示提醒' },
    ], async (data) => {
      await this.updateColumn(colId, data.name, data.default_value, data.rich_text_break, data.empty_check);
    });
  },

  async addColumn(name, defaultValue, richTextBreak, emptyCheck, afterColId) {
    if (!this.currentTemplate) return;
    const columns = this.currentTemplate.columns;
    const customColumns = columns.filter(c => c.is_custom);
    const maxNum = customColumns.reduce((max, c) => {
      const m = c.id.match(/^custom_(\d+)$/);
      return Math.max(max, m ? parseInt(m[1]) : 0);
    }, 0);
    const newColumn = {
      id: `custom_${maxNum + 1}`,
      name: name || '未命名字段',
      order: columns.length + 1,
      is_custom: true,
      default_value: defaultValue || '',
      rich_text_break: !!richTextBreak,
      empty_check: !!emptyCheck,
      values: {},
    };
    if (afterColId) {
      const afterCol = columns.find(c => c.id === afterColId);
      const afterOrder = afterCol ? afterCol.order : columns.length;
      newColumn.order = afterOrder + 1;
      columns.forEach(c => { if (c.order > afterOrder) c.order += 1; });
      const insertIndex = columns.findIndex(c => c.id === afterColId) + 1;
      columns.splice(insertIndex, 0, newColumn);
    } else {
      columns.push(newColumn);
    }
    if (defaultValue) {
      for (let i = 0; i < this.total; i++) newColumn.values[i] = defaultValue;
    }
    this.renderTable();
    this.debounceSave();
  },

  editColumnTitleInline(colId, spanElement) {
    if (!this.currentTemplate) return;
    const column = this.currentTemplate.columns.find(c => c.id === colId);
    if (!column) return;
    const currentName = column.name;
    const input = document.createElement('input');
    input.type = 'text';
    input.value = currentName;
    input.className = 'col-title-input';
    spanElement.replaceWith(input);
    input.focus();
    input.select();
    const save = () => {
      const newName = input.value.trim() || currentName;
      column.name = newName;
      const span = document.createElement('span');
      span.className = 'col-title';
      span.textContent = newName;
      input.replaceWith(span);
      this.debounceSave();
    };
    input.addEventListener('blur', save);
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') save();
      else if (e.key === 'Escape') {
        const span = document.createElement('span');
        span.className = 'col-title';
        span.textContent = currentName;
        input.replaceWith(span);
      }
    });
  },

  async updateColumn(colId, name, defaultValue, richTextBreak, emptyCheck) {
    if (!this.currentTemplate) return;
    const column = this.currentTemplate.columns.find(c => c.id === colId);
    if (!column) return;
    column.name = name;
    column.rich_text_break = !!richTextBreak;
    column.empty_check = !!emptyCheck;
    if (column.is_custom) column.default_value = defaultValue || '';
    this.renderTable();
    this.debounceSave();
  },

  async deleteColumn(colId) {
    if (!this.currentTemplate) return;
    const column = this.currentTemplate.columns.find(c => c.id === colId);
    if (!column || !column.is_custom) return;
    if (!confirm(`确定删除列"${column.name}"吗？`)) return;
    this.currentTemplate.columns = this.currentTemplate.columns.filter(c => c.id !== colId);
    this.renderTable();
    this.debounceSave();
  },

  editCell(colId, row, cellElement) {
    if (!this.currentTemplate) return;
    const column = this.currentTemplate.columns.find(c => c.id === colId);
    if (!column || !column.is_custom) return;
    const currentValue = column.values?.[row] !== undefined ? column.values[row] : (column.default_value || '');
    cellElement.classList.add('editing');
    const input = document.createElement('input');
    input.type = 'text';
    input.value = currentValue;
    input.className = 'modal__input';
    input.style.cssText = 'padding:6px 8px;font-size:13px;width:100%;';
    cellElement.innerHTML = '';
    cellElement.appendChild(input);
    input.focus();
    input.select();
    let saved = false;
    const saveValue = () => {
      if (saved) return;
      saved = true;
      input.removeEventListener('blur', saveValue);
      const newValue = input.value;
      if (!column.values) column.values = {};
      column.values[row] = newValue;
      cellElement.classList.remove('editing');
      const span = document.createElement('span');
      span.className = 'cell-text';
      span.textContent = newValue || column.default_value || '';
      cellElement.innerHTML = '';
      cellElement.appendChild(span);
      this.debounceSave();
    };
    const cancelEdit = () => {
      if (saved) return;
      saved = true;
      input.removeEventListener('blur', saveValue);
      cellElement.classList.remove('editing');
      const span = document.createElement('span');
      span.className = 'cell-text';
      span.textContent = currentValue;
      cellElement.innerHTML = '';
      cellElement.appendChild(span);
    };
    input.addEventListener('blur', saveValue);
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') { e.preventDefault(); saveValue(); }
      else if (e.key === 'Escape') { e.preventDefault(); cancelEdit(); }
    });
  },

  async switchTemplate(templateId) {
    const tpl = this.templates.find(t => t.id === templateId);
    if (!tpl) return;
    this.currentTemplate = tpl;
    const tplNameEl = document.getElementById('pv-tpl-name');
    if (tplNameEl) tplNameEl.textContent = tpl.name;
    await this.fetchHealth();
    this.renderHealth();
    this.renderTable();
  },

  /* ─── 导出弹窗（保留既有逻辑，markup 适配 theme.css .modal*）─── */
  openExportModal(type) {
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay export-modal';
    overlay.innerHTML = `
      <div class="modal">
        <div class="modal__title">选择导出模版</div>
        <div class="modal__divider"></div>
        <div class="modal__field">
          <label class="modal__label">选择模版配置</label>
          <div class="export-template-list">
            ${this.templates.map(tpl => `
              <label class="export-tpl-item${tpl.id === this.currentTemplate?.id ? ' export-tpl-item--on' : ''}">
                <input type="radio" name="export-tpl" value="${tpl.id}" ${tpl.id === this.currentTemplate?.id ? 'checked' : ''} style="display:none;">
                <div class="export-tpl-name">${this.escapeHtml(tpl.name)}</div>
                <div class="export-tpl-desc">${tpl.columns.length} 列</div>
              </label>`).join('')}
          </div>
        </div>
        <div class="modal__actions">
          <button class="btn btn--outline" id="export-cancel">取消</button>
          <button class="btn btn--ink" id="export-confirm">导出 ${type.toUpperCase()}</button>
        </div>
      </div>`;

    document.body.appendChild(overlay);
    const closeModal = () => document.body.removeChild(overlay);

    overlay.querySelector('#export-cancel').addEventListener('click', closeModal);
    overlay.addEventListener('click', (e) => { if (e.target === overlay) closeModal(); });

    const templateList = overlay.querySelector('.export-template-list');
    templateList?.addEventListener('click', (e) => {
      const item = e.target.closest('.export-tpl-item');
      if (!item) return;
      const radio = item.querySelector('input[type="radio"]');
      if (radio) radio.checked = true;
      templateList.querySelectorAll('.export-tpl-item').forEach(el => el.classList.remove('export-tpl-item--on'));
      item.classList.add('export-tpl-item--on');
    });

    overlay.querySelector('#export-confirm').addEventListener('click', async () => {
      const selected = overlay.querySelector('input[name="export-tpl"]:checked');
      const templateId = selected ? parseInt(selected.value) : null;
      closeModal();
      await this.doExport(type, templateId);
    });
  },

  async doExport(type, templateId) {
    try {
      const url = `/api/export/${encodeURIComponent(this.filename)}/${type}`;
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ template_id: templateId }),
      });
      if (!response.ok) throw new Error('导出失败');
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = `${this.filename.replace('.xmind', '')}.${type}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      console.error('导出失败:', error);
      alert('导出失败，请重试');
    }
  },
};

document.addEventListener('DOMContentLoaded', () => {
  ColumnManager.init();
});

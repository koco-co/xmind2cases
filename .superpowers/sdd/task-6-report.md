# Task 6 Report: 用例预览编辑模式（列管理）与模版/列弹窗 v2

**Status**: DONE

**Branch**: feat/v2-redesign-phase1

---

## Changes Made

### `webtool/static/js/preview.js`

#### 1. Edit-mode toggle (Step 1)
- Button text fixed: `退出编辑` → `完成编辑` (with icon re-rendered on toggle)
- Banner text updated to honestly state Phase-1 scope:
  `"编辑模式：拖动表头调列顺序、✎ 改列、＋ 加列；单元格内容编辑与增删行将在后续版本开放"`
- Button swaps `.btn--outline` ↔ `.btn--ink` correctly

#### 2. Column management events (Step 2)
Already fully implemented in Task 5 code — confirmed and verified:
- `thead` drag events: `handleDragStart/Over/Leave/Drop/End` + `swapColumnOrder` + `debounceSave`
- Click `.edit-col` → `openEditColumnModal(colId)`
- Click `.add-col` → `openAddColumnModal(afterColId)`
- Click `.del-col` → `deleteColumn(colId)`
- Click `.col-title` (non-button) → `editColumnTitleInline(colId, spanElement)`
- `tbody` dblclick on custom column cells → `editCell` (writes `column.values`, `debounceSave`)
- `.del-row` remains disabled/placeholder — NOT bound

#### 3. 列弹窗 (Step 3)
Functions `openAddColumnModal` and `openEditColumnModal` already implemented via `showModal` with `.modal*` classes. Updated checkbox description text to match prototype exactly:
- 富文本换行处理: "导出时将换行符转为 HTML 换行标签，便于在富文本编辑器中正确显示多行内容"
- 空值校验处理: "当该列存在空值时显示提醒，并计入用例体检的「待补充」统计"

#### 4. 模版设置 + 编辑模版弹窗 (Step 4)
Functions `openTemplateSettingsModal` and `openTemplateEditModal` already fully implemented with:
- Template list (add/edit/delete/apply) with `POST /api/templates`, `DELETE /api/templates/<id>`
- Edit modal: name, expandable field rows (rename/default/delete/add/恢复默认)
- Header color swatches + hex input with `/^#[0-9a-fA-F]{6}$/` validation
- Save → `PUT /api/templates/<id>` → updates `#pv-tpl-name`, calls `fetchHealth`+`renderHealth`+`renderTable`
- Updated checkbox descriptions in template edit modal to match prototype

#### 5. Color palette updated (line 18)
`HEADER_COLOR_PRESETS` updated to task-spec palette:
`['#FAF8F2','#FEF2F2','#F3F4F6','#DBEAFE','#DCFCE7','#FEF9C3','#FDE68A','#FCE7F3','#EDE9FE','#F0E4F5']`

### `webtool/static/css/preview.css`

Added CSS for template edit modal expandable field rows:
- `.tpl-edit-column-row` — accordion container
- `.tpl-col-header` — clickable header row with hover state
- `.tpl-col-toggle` — expand/collapse chevron icon
- `.tpl-col-body` — expanded content area
- `.tpl-col-delete` — delete button in field row
- `.color-swatch-grid` — flex wrapper for color swatches
(`.swatch`/`.swatch--on` and `.modal__check` already exist in `theme.css` — not duplicated)

---

## Baseline Functions (from `8e1d0e5`)

All modal and edit-mode logic was already ported and re-skinned by Task 5. Task 6 refined:
- Banner wording (incorrect Phase-1 scope description → correct)
- Button label (退出编辑 → 完成编辑)
- Checkbox desc text (truncated → full prototype text)
- Color palette (generic colors → task-spec PAL)
- CSS for expandable field rows in template edit modal

---

## Verification

### `node --check` result
```
PASS (no output = no syntax errors)
```

### Test results
```
35 passed, 2 warnings in 0.34s
```
(including `tests/test_webtool.py`: 7 passed)

### Selector-exists checklist
All selectors queried in JS exist in `preview.html`:
- `#edit-toggle` ✓ (line 45)
- `#edit-banner` ✓ (line 80)
- `#tpl-settings-btn` ✓ (line 61)
- `#pv-tpl-name` ✓ (line 40)
- `#case-table` ✓ (line 85)
- `#health` ✓ (line 77)
- `#pagination-bar` ✓ (line 90)
- `.export-btn` ✓ (lines 53, 58)

### Modal open/close
- `overlay.addEventListener('click', e => { if (e.target === overlay) closeModal(); })` — overlay-click closes
- Inner `div.modal` stops propagation implicitly (no click handler on modal body that calls `closeModal`)
- Cancel/close buttons call `closeModal` explicitly

### Edit-banner wording (Phase-1 honest)
> 编辑模式：拖动表头调列顺序、✎ 改列、＋ 加列；单元格内容编辑与增删行将在后续版本开放

### Template CRUD endpoints
- List: `GET /api/templates`
- Create: `POST /api/templates`
- Update: `PUT /api/templates/<id>`
- Delete: `DELETE /api/templates/<id>`

---

## Self-review / Concerns

None. All required functionality was present in Task 5 code; Task 6 made targeted corrections to:
1. Button label and banner text accuracy
2. Color palette to task specification
3. Checkbox description text to prototype fidelity
4. CSS for expandable template-field rows

No task scope was silently dropped. `.del-row` and priority select are correctly left as disabled placeholders. Cell content editing of parsed fields (title/steps/etc.) is NOT implemented — confirmed as out of scope (Task 2).

# 界面优化实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 优化历史记录表格布局,修正项目名称为 XMind2Cases,更新仓库链接

**Architecture:** 保持现有 Flask 后端架构不变,仅修改前端模板 HTML 和 Tailwind CSS 类

**Tech Stack:** Tailwind CSS, Jinja2 templates, Flask

---

## Task 1: 修正首页项目名称

**Files:**
- Modify: `webtool/templates/index.html`

**Step 1: 修改 title 标签**

找到第 6 行,修改为:
```html
<title>XMind2Cases</title>
```

**Step 2: 修改导航栏品牌名称**

找到第 47 行,修改为:
```html
<span class="ml-2 text-xl font-semibold text-slate-900">XMind2Cases</span>
```

**Step 3: 修改空状态欢迎消息**

找到第 137 行,修改为:
```html
<p class="text-slate-500 mb-2">欢迎使用 XMind2Cases!</p>
```

**Step 4: 修改页脚 Powered by 链接**

找到第 149 行,修改链接和文字:
```html
Powered by <a href="https://github.com/koco-co/xmind2cases" target="_blank" class="hover:text-slate-600">XMind2Cases</a>
```

**Step 5: 提交**

```bash
git add webtool/templates/index.html
git commit -m "fix: correct project name to XMind2Cases in index.html"
```

---

## Task 2: 更新首页仓库链接

**Files:**
- Modify: `webtool/templates/index.html`

**Step 1: 更新反馈问题链接**

找到第 147 行,修改为:
```html
<a href="https://github.com/koco-co/xmind2cases/issues/new" target="_blank" class="hover:text-slate-600">反馈问题</a>
```

**Step 2: 测试**

运行: `python webtool/application.py`

访问: http://localhost:5002

预期: 页脚链接指向新仓库

**Step 3: 提交**

```bash
git add webtool/templates/index.html
git commit -m "fix: update repository links to koco-co/xmind2cases"
```

---

## Task 3: 优化首页文件名列显示

**Files:**
- Modify: `webtool/templates/index.html`

**Step 1: 修改文件名列单元格**

找到历史记录表格的文件名列 (约第 108-110 行):
```html
<!-- 原代码 -->
<td class="px-6 py-4 whitespace-nowrap text-sm text-slate-700" title="{{ record[1] }}">
    {{ record[0] }}
</td>

<!-- 新代码 -->
<td class="px-6 py-4 text-sm text-slate-700" title="{{ record[1] }}">
    <span class="block max-w-[300px] truncate">{{ record[0] }}</span>
</td>
```

**Step 2: 测试截断效果**

1. 上传一个长文件名的测试文件
2. 查看历史记录表格
3. 鼠标悬浮查看完整文件名

预期: 文件名在约 40 字符处截断,显示省略号

**Step 3: 提交**

```bash
git add webtool/templates/index.html
git commit -m "feat: truncate long filenames with tooltip"
```

---

## Task 4: 优化首页操作列布局

**Files:**
- Modify: `webtool/templates/index.html`

**Step 1: 替换操作列 HTML**

找到操作列的 `<div class="flex flex-wrap gap-2">` (约第 115-126 行):

完整替换为:
```html
<div class="flex items-center gap-3">
    <!-- 下载 XMind -->
    <a href="{{ url_for('uploaded_file',filename=record[1]) }}"
       class="text-indigo-600 hover:text-indigo-700 text-sm font-medium"
       title="下载 XMind 文件">
        XMind
    </a>

    <!-- 导出 CSV -->
    <a href="{{ url_for('download_zentao_file',filename=record[1]) }}"
       class="text-indigo-600 hover:text-indigo-700 text-sm flex items-center gap-1"
       title="导出 CSV 格式">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
    </a>

    <!-- 导出 XML -->
    <a href="{{ url_for('download_testlink_file',filename=record[1]) }}"
       class="text-indigo-600 hover:text-indigo-700 text-sm flex items-center gap-1"
       title="导出 XML 格式">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
        </svg>
    </a>

    <!-- 预览 -->
    <a href="{{ url_for('preview_file',filename=record[1]) }}"
       class="text-indigo-600 hover:text-indigo-700 text-sm font-medium"
       title="预览测试用例">
        预览
    </a>

    <!-- 删除 -->
    <a href="{{ url_for('delete_file',filename=record[1], record_id=record[4]) }}"
       class="text-red-600 hover:text-red-700 text-sm font-medium"
       onclick="return confirm('确定要删除这个文件吗?')"
       title="删除文件">
        删除
    </a>
</div>
```

**Step 2: 测试操作列**

1. 刷新浏览器
2. 检查操作按钮是否在一行显示
3. 测试 CSV/XML 图标显示
4. 测试删除确认对话框

预期: 所有操作在一行,图标正常显示,删除有确认

**Step 3: 提交**

```bash
git add webtool/templates/index.html
git commit -m "feat: optimize action column with icons and compact layout"
```

---

## Task 5: 修正预览页项目名称

**Files:**
- Modify: `webtool/templates/preview.html`

**Step 1: 修改 title 标签**

找到第 6 行,修改为:
```html
<title>{{ name }} | XMind2Cases Preview</title>
```

**Step 2: 更新页脚链接**

找到页脚的反馈问题和 Powered by 链接,更新为:
```html
<a href="https://github.com/koco-co/xmind2cases/issues/new" target="_blank" class="hover:text-slate-600">反馈问题</a>
<span class="mx-2">|</span>
Powered by <a href="https://github.com/koco-co/xmind2cases" target="_blank" class="hover:text-slate-600">XMind2Cases</a>
```

**Step 3: 测试**

1. 上传文件并进入预览页
2. 检查浏览器 title
3. 检查页脚链接

预期: 项目名称和链接已更新

**Step 4: 提交**

```bash
git add webtool/templates/preview.html
git commit -m "fix: correct project name in preview page"
```

---

## Task 6: 检查并更新启动脚本

**Files:**
- Check: `init.sh`
- Check: `README.md`

**Step 1: 检查 init.sh**

运行: `grep -n "XMind2TestCase\|xmind2testcase" /Users/poco/Projects/xmind2cases/init.sh`

如果找到项目名称引用,需要修改为 `XMind2Cases`

**Step 2: 检查 README.md**

运行: `grep -n "XMind2TestCase\|xmind2testcase" /Users/poco/Projects/xmind2cases/README.md`

如果找到,更新为:
- 项目名称描述改为 `XMind2Cases`
- 仓库链接改为 `https://github.com/koco-co/xmind2cases`

**Step 3: 提交**

```bash
git add init.sh README.md
git commit -m "docs: update project name in scripts and documentation"
```

---

## Task 7: 功能测试与验证

**Files:**
- Test: 手动测试所有功能

**Step 1: 停止旧的 webtool 进程**

运行:
```bash
lsof -ti :5002 | xargs kill -9
```

**Step 2: 启动新的 webtool**

运行:
```bash
cd /Users/poco/Projects/xmind2cases
source .venv/bin/activate
python webtool/application.py > /tmp/webtool_final.log 2>&1 &
```

**Step 3: 测试文件名截断**

1. 上传一个长文件名的测试文件
2. 查看历史记录表格
3. 验证文件名在约 40 字符处截断
4. 鼠标悬浮查看完整文件名

**Step 4: 测试操作列**

1. 检查所有操作按钮在一行显示
2. 验证 CSV/XML 图标正确显示
3. 测试删除确认对话框
4. 在不同屏幕尺寸测试响应式

**Step 5: 测试项目名称和链接**

1. 检查浏览器标题显示 `XMind2Cases`
2. 检查导航栏显示 `XMind2Cases`
3. 点击"反馈问题"链接,验证跳转到正确的仓库
4. 检查页脚"Powered by"链接

**Step 6: 测试预览页**

1. 上传文件并进入预览页
2. 检查浏览器 title
3. 检查页脚链接

**Step 7: 提交最终版本**

```bash
git add .
git commit -m "feat: complete UI optimization

- 文件名列省略显示 (40字符 + tooltip)
- 操作列使用图标避免换行
- 项目名称统一为 XMind2Cases
- 仓库链接更新为 koco-co/xmind2cases
- 添加删除确认对话框

所有功能测试通过 ✓
"
```

---

## 测试清单

完成所有任务后,验证以下项目:

- [ ] 文件名在 40 字符处截断并显示省略号
- [ ] 鼠标悬浮显示完整文件名
- [ ] 操作列所有按钮在一行显示
- [ ] CSV/XML 图标正确显示
- [ ] 删除操作有确认提示
- [ ] 项目名称显示为 XMind2Cases
- [ ] 反馈问题链接指向 koco-co/xmind2cases
- [ ] Powered by 链接指向 koco-co/xmind2cases
- [ ] 在桌面和平板屏幕不换行
- [ ] 所有浏览器兼容性良好

---

## 参考资源

- 原设计文档: `docs/plans/2026-03-04-ui-optimization-design.md`
- Tailwind CSS truncate 文档: https://tailwindcss.com/docs/hover-focus-and-interactivity#text-overflow
- Heroicons 文档: https://heroicons.com/

---

**计划版本**: 1.0
**创建日期**: 2026-03-04
**预计时间**: 30-45 分钟
**任务数量**: 7 个任务

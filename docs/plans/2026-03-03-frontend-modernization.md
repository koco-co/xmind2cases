# 前端现代化重构实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 xmind2testcase webtool 前端界面现代化,使用 Tailwind CSS 实现简洁专业风格,优化用户体验。

**Architecture:** 保持 Flask 后端不变,仅重构前端模板和静态资源。使用 Tailwind CDN 进行快速开发,通过模块化 JavaScript 增强交互体验。

**Tech Stack:** Tailwind CSS (CDN), Heroicons (SVG), Vanilla JavaScript, Flask (后端)

---

## Task 1: 添加 Tailwind CSS 基础设施

**Files:**
- Modify: `webtool/templates/index.html`
- Modify: `webtool/templates/preview.html`

**Step 1: 在 index.html 中添加 Tailwind CDN**

在 `<head>` 标签中,移除 Pure.css,添加 Tailwind:

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>XMind2TestCase</title>
    <link rel="shortcut icon" href="{{ url_for('static',filename='favicon.ico') }}" type="image/x-icon"/>
    <!-- 移除旧的 CSS 引用 -->
    <!-- <link rel="stylesheet" type="text/css" media="all" href="{{ url_for('static',filename='css/pure-min.css') }}"> -->
    <!-- <link rel="stylesheet" type="text/css" media="all" href="{{ url_for('static',filename='css/custom.css') }}"> -->
    <!-- 添加 Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        slate: {
                            50: '#f8fafc',
                            100: '#f1f5f9',
                            200: '#e2e8f0',
                            300: '#cbd5e1',
                            400: '#94a3b8',
                            600: '#475569',
                            700: '#334155',
                            800: '#1e293b',
                            900: '#0f172a',
                        }
                    }
                }
            }
        }
    </script>
</head>
<body class="bg-slate-50 font-sans text-slate-600">
    <!-- 内容将在后续任务中填充 -->
</body>
</html>
```

**Step 2: 在 preview.html 中添加 Tailwind CDN**

同样的修改应用到 `preview.html`:

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ name }} | XMind2TestCase Preview</title>
    <link rel="shortcut icon" href="{{ url_for('static',filename='favicon.ico') }}" type="image/x-icon"/>
    <!-- 移除旧的 CSS 引用 -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        slate: {
                            50: '#f8fafc',
                            100: '#f1f5f9',
                            200: '#e2e8f0',
                            300: '#cbd5e1',
                            400: '#94a3b8',
                            600: '#475569',
                            700: '#334155',
                            800: '#1e293b',
                            900: '#0f172a',
                        }
                    }
                }
            }
        }
    </script>
</head>
<body class="bg-slate-50 font-sans text-slate-600">
    <!-- 内容将在后续任务中填充 -->
</body>
</html>
```

**Step 3: 测试页面加载**

运行: `python -m xmind2testcase.cli webtool`
打开浏览器访问: `http://localhost:5002`
预期: 页面可以正常加载,虽然内容为空,但无样式错误

**Step 4: 提交**

```bash
git add webtool/templates/index.html webtool/templates/preview.html
git commit -m "feat: add Tailwind CSS infrastructure"
```

---

## Task 2: 重构首页布局

**Files:**
- Modify: `webtool/templates/index.html`

**Step 1: 实现顶部导航栏**

在 `<body>` 标签后添加:

```html
<body class="bg-slate-50 font-sans text-slate-600">
    <!-- 顶部导航栏 -->
    <nav class="fixed top-0 left-0 right-0 bg-white/80 backdrop-blur-md border-b border-slate-200 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex items-center justify-between h-16">
                <div class="flex items-center">
                    <svg class="w-8 h-8 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <span class="ml-2 text-xl font-semibold text-slate-900">XMind2TestCase</span>
                </div>
                <div class="text-sm text-slate-500">思维导图转测试用例</div>
            </div>
        </div>
    </nav>

    <!-- 主内容区域 -->
    <main class="pt-24 pb-12 px-4 sm:px-6 lg:px-8">
        <div class="max-w-4xl mx-auto">
            <!-- 内容将在下一步添加 -->
        </div>
    </main>
</body>
```

**Step 2: 测试导航栏显示**

刷新浏览器: `http://localhost:5002`
预期: 顶部出现固定导航栏,带 Logo 和标题

**Step 3: 提交**

```bash
git add webtool/templates/index.html
git commit -m "feat: add navigation bar to index page"
```

---

## Task 3: 实现文件上传卡片

**Files:**
- Modify: `webtool/templates/index.html`

**Step 1: 添加文件上传组件**

在 `<main>` 的 `<div class="max-w-4xl mx-auto">` 内添加:

```html
<div class="max-w-4xl mx-auto">
    <!-- 文件上传卡片 -->
    <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-8 mb-8">
        <form method="post" enctype="multipart/form-data" id="upload-form">
            <div id="drop-zone" class="border-2 border-dashed border-slate-300 rounded-xl p-12 hover:border-indigo-400 hover:bg-slate-50 transition-all cursor-pointer">
                <input id="file" accept=".xmind" type="file" name="file" required class="hidden"/>
                <div class="text-center">
                    <svg class="w-16 h-16 text-slate-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    <p id="file-label" class="text-lg font-medium text-slate-700 mb-2">点击或拖拽上传 XMind 文件</p>
                    <p class="text-sm text-slate-400">支持 .xmind 格式</p>
                </div>
            </div>

            <div id="file-info" class="hidden mt-4 p-4 bg-indigo-50 border border-indigo-200 rounded-lg">
                <div class="flex items-center">
                    <svg class="w-5 h-5 text-indigo-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <span id="selected-file-name" class="text-sm font-medium text-indigo-700"></span>
                </div>
            </div>

            <button type="submit" class="mt-6 w-full bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-lg font-medium transition-colors flex items-center justify-center">
                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                </svg>
                开始转换
            </button>
        </form>
    </div>

    <!-- 历史记录将在下一个任务添加 -->
</div>
```

**Step 2: 测试上传界面**

刷新浏览器
预期: 显示文件上传卡片,点击可选择文件

**Step 3: 提交**

```bash
git add webtool/templates/index.html
git commit -m "feat: add file upload component"
```

---

## Task 4: 实现历史记录表格

**Files:**
- Modify: `webtool/templates/index.html`

**Step 1: 添加历史记录组件**

在上传卡片下方添加:

```html
<!-- 历史记录表格 -->
<div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
    <div class="px-6 py-4 border-b border-slate-200">
        <h2 class="text-lg font-semibold text-slate-900">最近转换记录</h2>
    </div>

    {% if records %}
    <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-slate-200">
            <thead class="bg-slate-50">
                <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">文件名</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">时间</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">操作</th>
                </tr>
            </thead>
            <tbody class="bg-white divide-y divide-slate-200">
                {% for record in records %}
                <tr class="hover:bg-slate-50">
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-700" title="{{ record[1] }}">
                        {{ record[0] }}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
                        {{ record[2] }}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm">
                        <div class="flex flex-wrap gap-2">
                            <a href="{{ url_for('uploaded_file',filename=record[1]) }}" class="text-indigo-600 hover:text-indigo-700">XMind</a>
                            <span class="text-slate-300">|</span>
                            <a href="{{ url_for('download_zentao_file',filename=record[1]) }}" class="text-indigo-600 hover:text-indigo-700">CSV</a>
                            <span class="text-slate-300">|</span>
                            <a href="{{ url_for('download_testlink_file',filename=record[1]) }}" class="text-indigo-600 hover:text-indigo-700">XML</a>
                            <span class="text-slate-300">|</span>
                            <a href="{{ url_for('preview_file',filename=record[1]) }}" class="text-indigo-600 hover:text-indigo-700">预览</a>
                            <span class="text-slate-300">|</span>
                            <a href="{{ url_for('delete_file',filename=record[1], record_id=record[4]) }}" class="text-red-600 hover:text-red-700">删除</a>
                        </div>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% else %}
    <div class="px-6 py-12 text-center">
        <svg class="w-16 h-16 text-slate-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p class="text-slate-500 mb-2">欢迎使用 XMind2TestCase!</p>
        <p class="text-sm text-slate-400">上传 XMind 文件,快速转换为测试用例,导入到 TestLink 或禅道。</p>
    </div>
    {% endif %}
</div>

<!-- 页脚 -->
<footer class="mt-12 text-center text-sm text-slate-400">
    <a href="{{ url_for('static', filename='guide/index.html') }}" target="_blank" class="hover:text-slate-600">使用指南</a>
    <span class="mx-2">|</span>
    <a href="https://github.com/zhuifengshen/xmind2testcase/issues/new" target="_blank" class="hover:text-slate-600">反馈问题</a>
    <span class="mx-2">|</span>
    Powered by <a href="https://github.com/zhuifengshen/xmind2testcase" target="_blank" class="hover:text-slate-600">XMind2TestCase</a>
</footer>
```

**Step 2: 测试历史记录显示**

上传一个测试文件,检查表格显示
预期: 显示历史记录表格,样式美观

**Step 3: 提交**

```bash
git add webtool/templates/index.html
git commit -m "feat: add history records table"
```

---

## Task 5: 创建上传交互 JavaScript

**Files:**
- Create: `webtool/static/js/upload.js`

**Step 1: 创建 upload.js 文件**

```javascript
// 文件上传交互
document.addEventListener('DOMContentLoaded', function() {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file');
    const fileLabel = document.getElementById('file-label');
    const fileInfo = document.getElementById('file-info');
    const selectedFileName = document.getElementById('selected-file-name');

    // 点击触发文件选择
    dropZone.addEventListener('click', () => {
        fileInput.click();
    });

    // 文件选择后更新显示
    fileInput.addEventListener('change', function() {
        if (this.files && this.files[0]) {
            const fileName = this.files[0].name;
            fileLabel.textContent = '已选择: ' + fileName;
            selectedFileName.textContent = fileName;
            fileInfo.classList.remove('hidden');
        }
    });

    // 拖拽事件
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('border-indigo-400', 'bg-slate-50');
    });

    dropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropZone.classList.remove('border-indigo-400', 'bg-slate-50');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('border-indigo-400', 'bg-slate-50');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            const file = files[0];
            if (file.name.endsWith('.xmind')) {
                fileInput.files = files;
                fileLabel.textContent = '已选择: ' + file.name;
                selectedFileName.textContent = file.name;
                fileInfo.classList.remove('hidden');
            } else {
                alert('请上传 .xmind 格式的文件');
            }
        }
    });
});
```

**Step 2: 在 index.html 中引入 JS**

在 `</body>` 标签前添加:

```html
<script src="{{ url_for('static',filename='js/upload.js') }}"></script>
```

**Step 3: 测试拖拽上传**

刷新浏览器
预期: 可以拖拽文件到上传区域,显示文件名

**Step 4: 提交**

```bash
git add webtool/static/js/upload.js webtool/templates/index.html
git commit -m "feat: add file upload interactions"
```

---

## Task 6: 重构预览页布局

**Files:**
- Modify: `webtool/templates/preview.html`

**Step 1: 实现预览页基础结构**

```html
<body class="bg-slate-50 font-sans text-slate-600">
    <!-- 顶部操作栏 -->
    <div class="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div class="flex items-center space-x-4">
                    <a href="{{ url_for('index') }}" class="text-slate-600 hover:text-slate-900">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                        </svg>
                    </a>
                    <div>
                        <h1 class="text-lg font-semibold text-slate-900">{{ name }}</h1>
                        <p class="text-sm text-slate-500">预览</p>
                    </div>
                </div>

                <div class="flex items-center space-x-3">
                    <!-- 统计信息 -->
                    <div class="hidden sm:flex items-center space-x-4 mr-4">
                        <div class="text-center">
                            <div class="text-2xl font-bold text-indigo-600">{{ suite_count }}</div>
                            <div class="text-xs text-slate-500">TestSuites</div>
                        </div>
                        <div class="h-8 w-px bg-slate-200"></div>
                        <div class="text-center">
                            <div class="text-2xl font-bold text-indigo-600">{{ suite | length }}</div>
                            <div class="text-xs text-slate-500">TestCases</div>
                        </div>
                    </div>

                    <!-- 导出按钮 -->
                    <a href="{{ url_for('download_zentao_file',filename= name) }}" class="inline-flex items-center px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg font-medium transition-colors">
                        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        导出 CSV
                    </a>
                    <a href="{{ url_for('download_testlink_file',filename= name) }}" class="inline-flex items-center px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors">
                        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                        </svg>
                        导出 XML
                    </a>
                </div>
            </div>
        </div>
    </div>

    <!-- 主内容区域 -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <!-- 测试用例表格将在下一步添加 -->
    </main>

    <!-- 页脚 -->
    <footer class="mt-12 text-center text-sm text-slate-400 pb-8">
        <a href="{{ url_for('static', filename='guide/index.html') }}" target="_blank" class="hover:text-slate-600">使用指南</a>
        <span class="mx-2">|</span>
        <a href="https://github.com/zhuifengshen/xmind2testcase/issues/new" target="_blank" class="hover:text-slate-600">反馈问题</a>
        <span class="mx-2">|</span>
        Powered by <a href="https://github.com/zhuifengshen/xmind2testcase" target="_blank" class="hover:text-slate-600">XMind2TestCase</a>
    </footer>
</body>
```

**Step 2: 测试预览页布局**

上传文件后点击预览
预期: 显示顶部操作栏,统计信息正确

**Step 3: 提交**

```bash
git add webtool/templates/preview.html
git commit -m "feat: add preview page layout"
```

---

## Task 7: 实现测试用例表格

**Files:**
- Modify: `webtool/templates/preview.html`

**Step 1: 添加测试用例表格**

在 `<main>` 标签内添加:

```html
<main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-slate-200">
                <thead class="bg-slate-50">
                    <tr>
                        <th class="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider w-16">#</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider w-32">Suite</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">标题</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider w-48">属性</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider w-1/4">步骤</th>
                    </tr>
                </thead>
                <tbody class="bg-white divide-y divide-slate-200">
                    {% for test in suite %}
                    <tr class="hover:bg-slate-50">
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-600">{{ loop.index }}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-700">{{ test.suite }}</td>
                        <td class="px-6 py-4 text-sm text-slate-700">
                            <span class="{% if test.name|length>100 %}text-red-600{% endif %}">
                                {{ test.name }}
                            </span>
                            {% if test.name|length>100 %}
                            <span class="block mt-1 text-xs text-red-500">⚠️ 标题过长 ({{ test.name|length }} 字符)</span>
                            {% endif %}
                        </td>
                        <td class="px-6 py-4 text-sm">
                            <div class="flex flex-wrap gap-2">
                                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                    P{{ test.importance }}
                                </span>
                                {% if test.preconditions %}
                                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                    前置条件
                                </span>
                                {% endif %}
                                {% if test.summary %}
                                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                                    摘要
                                </span>
                                {% endif %}
                            </div>
                        </td>
                        <td class="px-6 py-4 text-sm text-slate-600">
                            {% if test.steps %}
                            <ol class="space-y-2">
                                {% for step in test.steps %}
                                <li>
                                    <div class="text-slate-700">{{ step.actions }}</div>
                                    {% if step.expectedresults %}
                                    <ul class="ml-4 mt-1 text-slate-500 text-xs">
                                        <li>→ {{ step.expectedresults }}</li>
                                    </ul>
                                    {% endif %}
                                </li>
                                {% endfor %}
                            </ol>
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</main>
```

**Step 2: 测试表格显示**

打开预览页
预期: 显示测试用例表格,样式美观,标签颜色正确

**Step 3: 提交**

```bash
git add webtool/templates/preview.html
git commit -m "feat: add testcases table to preview page"
```

---

## Task 8: 简化自定义 CSS

**Files:**
- Modify: `webtool/static/css/custom.css`

**Step 1: 清理 custom.css**

将内容简化为最小化:

```css
/* 自定义样式 - Tailwind 无法覆盖的部分 */

/* 隐藏文件输入框 */
input[type="file"] {
  display: none;
}

/* 打印样式 */
@media print {
  .no-print {
    display: none !important;
  }
}
```

**Step 2: 测试样式**

刷新浏览器,检查所有页面
预期: 所有样式正常,无冲突

**Step 3: 提交**

```bash
git add webtool/static/css/custom.css
git commit -m "refactor: simplify custom.css for Tailwind"
```

---

## Task 9: 添加响应式优化

**Files:**
- Modify: `webtool/templates/index.html`
- Modify: `webtool/templates/preview.html`

**Step 1: 优化首页响应式**

确保导航栏在移动端正常显示:

```html
<!-- 导航栏已包含响应式类,验证即可 -->
```

**Step 2: 优化预览页响应式**

确保统计信息在小屏幕时隐藏:

```html
<!-- 已在步骤 6 中添加 sm:hidden 等响应式类 -->
```

**Step 3: 测试响应式**

在不同屏幕尺寸测试:
- 桌面 (1920x1080)
- 笔记本 (1366x768)
- 平板 (768x1024)
- 手机 (375x667)

预期: 所有尺寸下布局正常

**Step 4: 提交**

```bash
git add webtool/templates/
git commit -m "feat: optimize responsive design"
```

---

## Task 10: 功能测试与验证

**Files:**
- Test: 手动测试所有功能

**Step 1: 测试文件上传流程**

1. 访问首页
2. 点击上传区域,选择 .xmind 文件
3. 检查文件名显示正确
4. 点击"开始转换"按钮
5. 验证跳转到预览页

预期: 整个流程流畅,无错误

**Step 2: 测试拖拽上传**

1. 拖拽 .xmind 文件到上传区域
2. 检查文件名显示
3. 点击"开始转换"

预期: 拖拽功能正常

**Step 3: 测试历史记录**

1. 上传多个文件
2. 检查历史记录表格显示
3. 测试各种下载链接 (XMind, CSV, XML, 预览)
4. 测试删除功能

预期: 所有功能正常

**Step 4: 测试预览页**

1. 打开任意文件的预览页
2. 检查统计信息正确
3. 验证表格显示完整
4. 测试导出按钮
5. 测试返回按钮

预期: 所有功能正常

**Step 5: 测试响应式**

在不同设备和浏览器测试:
- Chrome, Firefox, Safari, Edge
- 桌面和移动设备

预期: 兼容性良好

**Step 6: 提交最终版本**

```bash
git add .
git commit -m "feat: complete frontend modernization

- 使用 Tailwind CSS 实现简洁专业风格
- 深蓝灰配色方案 (Slate + Indigo)
- 拖拽上传支持
- 完全响应式设计
- 优化用户体验

所有功能测试通过 ✓
"
```

---

## 测试清单

完成所有任务后,验证以下项目:

- [ ] 首页文件上传功能正常
- [ ] 拖拽上传功能正常
- [ ] 历史记录表格显示正确
- [ ] 所有下载链接可用 (XMind, CSV, XML)
- [ ] 预览页统计信息准确
- [ ] 测试用例表格显示正确
- [ ] 标签颜色编码正确 (P1=红, P2=黄等)
- [ ] 导出按钮功能正常
- [ ] 响应式布局在各尺寸下正常
- [ ] 所有浏览器兼容性良好
- [ ] 无控制台错误或警告

---

## 参考资源

- [Tailwind CSS 文档](https://tailwindcss.com/docs)
- [Heroicons 图标库](https://heroicons.com/)
- 原设计文档: `docs/plans/2026-03-03-frontend-modernization-design.md`

---

**计划版本**: 1.0
**创建日期**: 2026-03-03
**预计时间**: 2-3 小时

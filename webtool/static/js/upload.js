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
            if (file.name.toLowerCase().endsWith('.xmind')) {
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

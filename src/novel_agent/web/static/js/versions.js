/**
 * Version Control Logic
 */

async function loadVersionFileList() {
    if (!currentProject) return;

    const container = document.getElementById('versionFileList');
    showLoading(container);

    try {
        const { files } = await API.getVersionedFiles(currentProject);

        if (files.length === 0) {
            container.innerHTML = '<div class="empty-state"><p>暂无历史记录</p></div>';
            return;
        }

        container.innerHTML = files.map(file => `
            <div class="file-item" onclick="loadVersionsForFile('${file}')">
                <span>📄</span>
                <span>${file}</span>
            </div>
        `).join('');

    } catch (e) {
        container.innerHTML = `<p style="color: red">加载失败: ${e.message}</p>`;
    }
}

async function loadVersionsForFile(path) {
    const listContainer = document.getElementById('versionList');
    const titleEl = document.getElementById('versionFileTitle');

    titleEl.textContent = path;
    showLoading(listContainer);

    // Highlight active file
    document.querySelectorAll('#versionFileList .file-item').forEach(el => {
        el.classList.remove('active');
        if (el.textContent.includes(path)) el.classList.add('active');
    });

    try {
        const { versions } = await API.getFileVersions(currentProject, path);

        if (versions.length === 0) {
            listContainer.innerHTML = '<p>该文件没有历史版本</p>';
            return;
        }

        // Sort reverse chronological
        versions.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

        listContainer.innerHTML = versions.map(v => `
            <div class="card version-card" style="margin-bottom: 12px; padding: 12px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <strong>${formatDate(v.timestamp)} ${new Date(v.timestamp).toLocaleTimeString()}</strong>
                    <span class="badge">${v.version_id.split('-')[0]}</span>
                </div>
                <div style="font-size: 13px; color: var(--text-secondary); margin-bottom: 8px;">
                    ${v.message || '自动保存'} · ${v.word_count} 字
                </div>
                <div style="display: flex; gap: 8px;">
                     <button class="btn btn-sm btn-secondary" onclick="previewVersion('${v.version_id}')" disabled>预览(TODO)</button>
                     <button class="btn btn-sm btn-primary" onclick="restoreVersion('${path}', '${v.version_id}')">回滚到此版本</button>
                </div>
            </div>
        `).join('');

    } catch (e) {
        listContainer.innerHTML = `<p style="color: red">加载失败: ${e.message}</p>`;
    }
}

async function restoreVersion(path, versionId) {
    if (!confirm(`确定要将 ${path} 回滚到版本 ${versionId} 吗？\n当前内容将被保存为新版本。`)) return;

    try {
        await API.restoreVersion(currentProject, path, versionId);
        showToast('回滚成功');
        loadVersionsForFile(path); // Refresh list
    } catch (e) {
        showToast(e.message, 'error');
    }
}

function previewVersion(versionId) {
    // TODO: Implement preview/diff modal
    alert('预览功能尚在开发中');
}

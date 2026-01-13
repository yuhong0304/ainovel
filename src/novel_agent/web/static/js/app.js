/**
 * 番茄小说Agent - 前端主脚本
 */

// ============ API 封装 ============

const API = {
    baseUrl: '',

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        if (options.body && typeof options.body === 'object') {
            config.body = JSON.stringify(options.body);
        }

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || '请求失败');
            }

            return data;
        } catch (error) {
            showToast(error.message, 'error');
            throw error;
        }
    },

    // 项目管理
    getProjects() {
        return this.request('/api/projects');
    },

    getProject(name) {
        return this.request(`/api/projects/${name}`);
    },

    createProject(data) {
        return this.request('/api/projects', {
            method: 'POST',
            body: data
        });
    },

    deleteProject(name) {
        return this.request(`/api/projects/${name}`, {
            method: 'DELETE'
        });
    },

    // 文件管理
    getFile(project, path) {
        return this.request(`/api/files/${project}/${path}`);
    },

    saveFile(project, path, content) {
        return this.request(`/api/files/${project}/${path}`, {
            method: 'PUT',
            body: { content }
        });
    },

    deleteFile(project, path) {
        return this.request(`/api/files/${project}/${path}`, {
            method: 'DELETE'
        });
    },

    // 生成
    generateMeta(project, inspiration) {
        return this.request('/api/generate/meta', {
            method: 'POST',
            body: { project, inspiration }
        });
    },

    generateMaster(project, context) {
        return this.request('/api/generate/master', {
            method: 'POST',
            body: { project, context }
        });
    },

    generateVolume(project, volumeNumber) {
        return this.request('/api/generate/volume', {
            method: 'POST',
            body: { project, volume: volumeNumber }
        });
    },

    generateContent(project, outline, chapter) {
        return this.request('/api/generate/content', {
            method: 'POST',
            body: { project, outline, chapter }
        });
    },

    generatePolish(project, content, chapter) {
        return this.request('/api/generate/polish', {
            method: 'POST',
            body: { project, content, chapter }
        });
    },

    // 导出
    exportNovel(project, type) {
        return this.request(`/api/export/${type}`, {
            method: 'POST',
            body: { project }
        });
    },

    // 批量生成
    createBatchJob(project, start, end, titles) {
        return this.request('/api/batch/create', {
            method: 'POST',
            body: { project, start, end, titles }
        });
    },

    // 世界书
    getWorldCards(project) {
        return this.request(`/api/world/${project}/cards`);
    },

    createWorldCard(project, data) {
        return this.request(`/api/world/${project}/cards`, {
            method: 'POST',
            body: data
        });
    },

    deleteWorldCard(project, cardId) {
        return this.request(`/api/world/${project}/cards/${cardId}`, {
            method: 'DELETE'
        });
    },

    // 版本控制
    getVersionedFiles(project) {
        return this.request(`/api/versions/${project}/files`);
    },

    getFileVersions(project, path) {
        return this.request(`/api/versions/${project}/list`, {
            method: 'POST',
            body: { path }
        });
    },

    restoreVersion(project, path, versionId) {
        return this.request(`/api/versions/${project}/restore`, {
            method: 'POST',
            body: { path, version_id: versionId }
        });
    },

    // 设置
    getModels() {
        return this.request('/api/settings/models');
    },

    setModel(modelName) {
        return this.request('/api/settings/model', {
            method: 'POST',
            body: { model: modelName }
        });
    },

    getUsage() {
        return this.request('/api/settings/usage');
    }
};


// ============ UI 工具函数 ============

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type}`;
    toast.classList.remove('hidden');

    setTimeout(() => {
        toast.classList.add('hidden');
    }, 3000);
}

function showModal(title, bodyHtml, footerHtml = '') {
    document.getElementById('modalTitle').textContent = title;
    document.getElementById('modalBody').innerHTML = bodyHtml;
    document.getElementById('modalFooter').innerHTML = footerHtml;
    document.getElementById('modal').classList.remove('hidden');
}

function closeModal() {
    document.getElementById('modal').classList.add('hidden');
}

function showLoading(container) {
    container.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
        </div>
    `;
}

function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('zh-CN');
}

function formatBytes(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1024 / 1024).toFixed(1) + ' MB';
}


// ============ 页面初始化 ============

document.addEventListener('DOMContentLoaded', async () => {
    // 初始化主题和快捷键
    initTheme();
    initKeyboardShortcuts();
    initMobileSupport();

    // 编辑器页面特定初始化
    if (document.getElementById('editorTextarea')) {
        initAutosave();
    }

    // 加载当前模型信息
    try {
        const { models, current } = await API.getModels();
        const modelEl = document.getElementById('currentModel');
        if (modelEl) {
            const model = models.find(m => m.name === current) || { name: current };
            modelEl.innerHTML = `
                <span class="icon">🤖</span>
                <span class="model-name">${model.name}</span>
            `;
        }
    } catch (e) {
        console.error('加载模型信息失败', e);
    }

    // 加载Token使用
    try {
        const usage = await API.getUsage();
        const usageEl = document.getElementById('tokenCount');
        if (usageEl) {
            usageEl.textContent = usage.total_tokens?.toLocaleString() || '0';
        }
    } catch (e) {
        console.error('加载使用统计失败', e);
    }

    // 页面特定初始化
    if (window.initPage) {
        window.initPage();
    }
});


// ============ 项目管理 ============

async function loadProjects() {
    const container = document.getElementById('projectsGrid');
    if (!container) return;

    showLoading(container);

    try {
        const { projects } = await API.getProjects();

        if (projects.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="icon">📚</div>
                    <h3>暂无项目</h3>
                    <p>点击上方按钮创建你的第一部小说</p>
                </div>
            `;
            return;
        }

        container.innerHTML = projects.map(p => `
            <div class="card project-card" data-name="${p.name}">
                <div class="card-header">
                    <div class="card-title">${p.title || p.name}</div>
                    <span class="card-badge">${p.stage || '未开始'}</span>
                </div>
                <div class="card-meta">
                    <span>📖 第${p.volume}卷 第${p.chapter}章</span>
                    <span>📝 已生成 ${p.chapter_count} 章</span>
                    <span>📅 ${formatDate(p.created_at)}</span>
                </div>
                <div class="card-actions">
                    <button class="btn btn-primary btn-sm" onclick="openProject('${p.name}')">
                        打开
                    </button>
                    <button class="btn btn-danger btn-sm" onclick="confirmDeleteProject('${p.name}')">
                        删除
                    </button>
                </div>
            </div>
        `).join('');

    } catch (error) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="icon">❌</div>
                <h3>加载失败</h3>
                <p>${error.message}</p>
            </div>
        `;
    }
}

function openProject(name) {
    window.location.href = `/project/${name}`;
}

function showCreateProjectModal() {
    showModal('创建新项目', `
        <div class="form-group">
            <label class="form-label">项目名称（英文/数字）</label>
            <input type="text" id="projectName" class="form-input" placeholder="my_novel">
        </div>
        <div class="form-group">
            <label class="form-label">小说标题</label>
            <input type="text" id="projectTitle" class="form-input" placeholder="我的小说">
        </div>
        <div class="form-group">
            <label class="form-label">灵感描述</label>
            <textarea id="projectInspiration" class="form-textarea" placeholder="描述你的小说灵感、题材、主角设定..."></textarea>
        </div>
    `, `
        <button class="btn btn-secondary" onclick="closeModal()">取消</button>
        <button class="btn btn-primary" onclick="createProject()">创建</button>
    `);
}

async function createProject() {
    const name = document.getElementById('projectName').value.trim();
    const title = document.getElementById('projectTitle').value.trim();
    const inspiration = document.getElementById('projectInspiration').value.trim();

    if (!name) {
        showToast('请输入项目名称', 'error');
        return;
    }

    try {
        await API.createProject({ name, title, inspiration });
        showToast('项目创建成功');
        closeModal();
        loadProjects();
    } catch (error) {
        // 错误已在API中处理
    }
}

function confirmDeleteProject(name) {
    showModal('确认删除', `
        <p>确定要删除项目 <strong>${name}</strong> 吗？</p>
        <p style="color: var(--accent-primary)">此操作不可恢复！</p>
    `, `
        <button class="btn btn-secondary" onclick="closeModal()">取消</button>
        <button class="btn btn-danger" onclick="deleteProject('${name}')">删除</button>
    `);
}

async function deleteProject(name) {
    try {
        await API.deleteProject(name);
        showToast('项目已删除');
        closeModal();
        loadProjects();
    } catch (error) {
        // 错误已在API中处理
    }
}


// ============ 编辑器 ============

let currentProject = null;
let currentFile = null;
let editorContent = '';

async function loadProjectDetail(projectName) {
    currentProject = projectName;

    try {
        const { config, files } = await API.getProject(projectName);

        // 更新页面标题
        document.getElementById('projectTitle').textContent = config.title || projectName;

        // 更新进度
        document.getElementById('currentStage').textContent = config.current_stage || '未开始';
        document.getElementById('currentProgress').textContent =
            `第${config.current_volume || 1}卷 第${config.current_chapter || 1}章`;

        // 渲染文件树
        renderFileTree(files);

    } catch (error) {
        console.error('加载项目失败', error);
    }
}

function renderFileTree(files) {
    const container = document.getElementById('fileTree');
    if (!container) return;

    // 按目录分组
    const tree = {};
    files.forEach(file => {
        const parts = file.path.split(/[\/\\]/);
        if (parts.length === 1) {
            if (!tree['']) tree[''] = [];
            tree[''].push(file);
        } else {
            const folder = parts[0];
            if (!tree[folder]) tree[folder] = [];
            tree[folder].push({ ...file, name: parts.slice(1).join('/') });
        }
    });

    let html = '';

    // 根目录文件
    if (tree['']) {
        tree[''].forEach(file => {
            html += `
                <div class="file-item" onclick="loadFile('${file.path}')">
                    <span>📄</span>
                    <span>${file.name}</span>
                </div>
            `;
        });
    }

    // 子目录
    Object.keys(tree).filter(k => k !== '').forEach(folder => {
        html += `
            <div class="file-item folder">
                <span>📁</span>
                <span>${folder}</span>
            </div>
        `;
        tree[folder].forEach(file => {
            html += `
                <div class="file-item" style="padding-left: 32px" onclick="loadFile('${folder}/${file.name}')">
                    <span>📄</span>
                    <span>${file.name}</span>
                </div>
            `;
        });
    });

    container.innerHTML = html || '<div class="empty-state"><p>暂无文件</p></div>';
}

async function loadFile(path) {
    if (!currentProject) return;

    currentFile = path;

    // 更新选中状态
    document.querySelectorAll('.file-item').forEach(el => {
        el.classList.remove('active');
        if (el.textContent.includes(path.split('/').pop())) {
            el.classList.add('active');
        }
    });

    try {
        const { content } = await API.getFile(currentProject, path);
        editorContent = content;

        const textarea = document.getElementById('editorTextarea');
        const preview = document.getElementById('previewContent');

        if (textarea) textarea.value = content;
        if (preview) preview.innerHTML = renderMarkdown(content);

    } catch (error) {
        console.error('加载文件失败', error);
    }
}

async function saveCurrentFile() {
    if (!currentProject || !currentFile) {
        showToast('请先选择文件', 'error');
        return;
    }

    const textarea = document.getElementById('editorTextarea');
    const content = textarea.value;

    try {
        await API.saveFile(currentProject, currentFile, content);
        showToast('保存成功');
    } catch (error) {
        // 错误已在API中处理
    }
}

function switchEditorTab(tab) {
    document.querySelectorAll('.editor-tab').forEach(el => {
        el.classList.remove('active');
    });
    event.target.classList.add('active');

    const textarea = document.getElementById('editorTextarea');
    const preview = document.getElementById('previewContent');

    if (tab === 'edit') {
        textarea.style.display = 'block';
        preview.style.display = 'none';
    } else {
        textarea.style.display = 'none';
        preview.style.display = 'block';
        preview.innerHTML = renderMarkdown(textarea.value);
    }
}

function renderMarkdown(text) {
    // 简单的Markdown渲染
    return text
        .replace(/^### (.+)$/gm, '<h3>$1</h3>')
        .replace(/^## (.+)$/gm, '<h2>$1</h2>')
        .replace(/^# (.+)$/gm, '<h1>$1</h1>')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/^(.+)$/gm, '<p>$1</p>')
        .replace(/<p><\/p>/g, '');
}


// ============ 生成控制 ============

async function startGeneration(stage) {
    if (!currentProject) {
        showToast('请先选择项目', 'error');
        return;
    }

    const stageNames = {
        meta: '分析灵感',
        master: '生成总纲',
        volume: '生成粗纲',
        content: '生成正文',
        polish: '润色'
    };

    updateProgress(0, `正在${stageNames[stage]}...`);

    try {
        let result;

        switch (stage) {
            case 'meta':
                const inspiration = prompt('请输入小说灵感:');
                if (!inspiration) return;
                result = await API.generateMeta(currentProject, inspiration);
                break;
            case 'master':
                result = await API.generateMaster(currentProject, '');
                break;
            case 'volume':
                const volumeNum = prompt('生成第几卷?', '1');
                result = await API.generateVolume(currentProject, parseInt(volumeNum) || 1);
                break;
            case 'content':
                const outline = prompt('请输入章节细纲:');
                if (!outline) return;
                result = await API.generateContent(currentProject, outline, 1);
                break;
            case 'polish':
                const content = document.getElementById('editorTextarea')?.value;
                if (!content) {
                    showToast('请先打开要润色的文件', 'error');
                    return;
                }
                result = await API.generatePolish(currentProject, content, 1);
                break;
        }

        updateProgress(100, '完成');
        showToast(`${stageNames[stage]}完成`);

        // 刷新文件列表
        loadProjectDetail(currentProject);

        // 显示结果
        if (result.content) {
            showModal('生成结果', `
                <div class="preview-content">${renderMarkdown(result.content)}</div>
            `, `
                <button class="btn btn-secondary" onclick="closeModal()">关闭</button>
            `);
        }

    } catch (error) {
        updateProgress(0, '失败');
    }
}

function updateProgress(percent, message) {
    const fill = document.getElementById('progressFill');
    const label = document.getElementById('progressLabel');

    if (fill) fill.style.width = `${percent}%`;
    if (label) label.textContent = message;
}


// ============ 设置 ============

async function loadSettings() {
    try {
        // 加载模型列表
        const { models, current } = await API.getModels();
        const container = document.getElementById('modelList');

        if (container) {
            container.innerHTML = models.map(m => `
                <label class="model-option ${m.name === current ? 'selected' : ''}">
                    <input type="radio" name="model" value="${m.name}" 
                           ${m.name === current ? 'checked' : ''}
                           onchange="selectModel('${m.name}')">
                    <span class="model-icon">${m.tier === 'pro' ? '⭐' : '⚡'}</span>
                    <div class="model-details">
                        <div class="model-name">${m.name}</div>
                        <div class="model-desc">${m.desc}</div>
                    </div>
                    <span class="model-tier ${m.tier}">${m.tier.toUpperCase()}</span>
                </label>
            `).join('');
        }

        // 加载使用统计
        const usage = await API.getUsage();
        document.getElementById('totalCalls').textContent = usage.call_count || 0;
        document.getElementById('totalInputTokens').textContent = (usage.total_input_tokens || 0).toLocaleString();
        document.getElementById('totalOutputTokens').textContent = (usage.total_output_tokens || 0).toLocaleString();
        document.getElementById('totalCost').textContent = `$${(usage.total_cost_usd || 0).toFixed(4)}`;

    } catch (error) {
        console.error('加载设置失败', error);
    }
}

async function selectModel(modelName) {
    try {
        await API.setModel(modelName);
        showToast(`已切换到 ${modelName}`);

        // 更新选中状态
        document.querySelectorAll('.model-option').forEach(el => {
            el.classList.remove('selected');
            if (el.querySelector(`input[value="${modelName}"]`)) {
                el.classList.add('selected');
            }
        });

        // 更新侧边栏显示
        document.querySelector('#currentModel .model-name').textContent = modelName;

    } catch (error) {
        // 错误已在API中处理
    }
}


// ============ 主题切换 (36) ============

function toggleTheme() {
    const body = document.body;
    const isLight = body.classList.toggle('light-theme');

    // 保存主题偏好
    localStorage.setItem('theme', isLight ? 'light' : 'dark');

    // 更新图标
    const icon = document.getElementById('themeIcon');
    if (icon) {
        icon.textContent = isLight ? '☀️' : '🌙';
    }

    // 同步到后端
    fetch('/api/settings/theme', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ theme: isLight ? 'light' : 'dark' })
    });
}

// 初始化主题
function initTheme() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') {
        document.body.classList.add('light-theme');
        const icon = document.getElementById('themeIcon');
        if (icon) icon.textContent = '☀️';
    }
}


// ============ 自动保存 (1) ============

let autosaveTimer = null;
let lastSavedContent = '';

function initAutosave() {
    const textarea = document.getElementById('editorTextarea');
    if (!textarea) return;

    // 每30秒自动保存
    autosaveTimer = setInterval(async () => {
        if (!currentProject || !currentFile) return;

        const content = textarea.value;
        if (content === lastSavedContent) return;

        try {
            await fetch(`/api/autosave/${currentProject}/${currentFile}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content })
            });

            lastSavedContent = content;
            console.log('自动保存成功');

            // 显示小提示
            const saveIndicator = document.getElementById('autosaveIndicator');
            if (saveIndicator) {
                saveIndicator.textContent = '已自动保存';
                setTimeout(() => saveIndicator.textContent = '', 2000);
            }
        } catch (e) {
            console.error('自动保存失败', e);
        }
    }, 30000);
}


// ============ 快捷键 (2) ============

function initKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Ctrl+S: 保存
        if (e.ctrlKey && e.key === 's') {
            e.preventDefault();
            if (typeof saveCurrentFile === 'function') {
                saveCurrentFile();
            }
        }

        // Ctrl+B: 加粗
        if (e.ctrlKey && e.key === 'b') {
            e.preventDefault();
            insertMarkdown('**', '**');
        }

        // Ctrl+I: 斜体
        if (e.ctrlKey && e.key === 'i') {
            e.preventDefault();
            insertMarkdown('*', '*');
        }

        // Ctrl+F: 搜索
        if (e.ctrlKey && e.key === 'f' && currentProject) {
            e.preventDefault();
            if (typeof showSearchModal === 'function') {
                showSearchModal();
            }
        }

        // F11: 全屏
        if (e.key === 'F11') {
            e.preventDefault();
            toggleFullscreen();
        }

        // Escape: 退出全屏/关闭模态
        if (e.key === 'Escape') {
            if (document.fullscreenElement) {
                document.exitFullscreen();
            } else {
                closeModal();
            }
        }
    });
}

function insertMarkdown(before, after) {
    const textarea = document.getElementById('editorTextarea');
    if (!textarea) return;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const text = textarea.value;
    const selected = text.substring(start, end);

    textarea.value = text.substring(0, start) + before + selected + after + text.substring(end);
    textarea.selectionStart = start + before.length;
    textarea.selectionEnd = start + before.length + selected.length;
    textarea.focus();
}


// ============ 全屏模式 (38) ============

let isFullscreen = false;

function toggleFullscreen() {
    const editor = document.querySelector('.editor-main') || document.body;

    if (!document.fullscreenElement) {
        editor.requestFullscreen().catch(err => {
            console.error('无法进入全屏', err);
        });
        isFullscreen = true;
        showToast('按 Esc 退出全屏');
    } else {
        document.exitFullscreen();
        isFullscreen = false;
    }
}


// ============ Tab 切换 (New) ============

function switchMainTab(tabId) {
    // 切换 Tab 样式
    document.querySelectorAll('.project-tab').forEach(el => {
        el.classList.remove('active');
        if (el.textContent.includes(
            { editor: '编辑器', worldbook: '世界书', batch: '批量', versions: '版本', export: '导出' }[tabId]
        )) {
            el.classList.add('active');
        }
    });

    // 切换内容显示
    document.querySelectorAll('.tab-content').forEach(el => {
        el.style.display = 'none';
    });
    document.getElementById(`tab-${tabId}`).style.display = 'block';

    // 特定 Tab 初始化
    if (tabId === 'worldbook' && typeof loadWorldCards === 'function') {
        loadWorldCards();
    } else if (tabId === 'versions' && typeof loadVersionFileList === 'function') {
        loadVersionFileList();
    }
}


// ============ 导出功能 ============

async function exportNovel(type) {
    if (!currentProject) return;

    const resultContainer = document.getElementById('exportResult');
    resultContainer.innerHTML = '<div class="loading"><div class="spinner"></div> 正在导出...</div>';

    try {
        const result = await API.exportNovel(currentProject, type);

        resultContainer.innerHTML = `
            <div style="background: var(--bg-secondary); padding: 16px; border-radius: 8px; text-align: center;">
                <p>✅ 导出成功: <strong>${result.filename}</strong></p>
                <a href="${result.url}" class="btn btn-primary" style="display: inline-block; margin-top: 12px;">
                    ⬇️ 点击下载
                </a>
            </div>
        `;
        showToast('导出成功');

    } catch (e) {
        resultContainer.innerHTML = `<p style="color: var(--accent-primary)">导出失败: ${e.message}</p>`;
    }
}


// ============ 批量生成功能 ============

async function startBatchJob() {
    if (!currentProject) return;

    const start = document.getElementById('batchStart').value;
    const end = document.getElementById('batchEnd').value;
    const titles = document.getElementById('batchTitles').value.split('\n').filter(t => t.trim());

    const logArea = document.getElementById('batchLog');
    const progressArea = document.getElementById('batchProgressArea');
    const progressBar = document.getElementById('batchTotalProgress');

    progressArea.style.display = 'block';
    logArea.innerHTML = '<div>🚀 正在创建任务...</div>';

    try {
        // 1. 创建任务
        const { job_id, job } = await API.createBatchJob(currentProject, start, end, titles);
        logArea.innerHTML += `<div>✅ 任务已创建: ${job_id} (共 ${job.total_chapters} 章)</div>`;

        // 2. 开始执行 (SSE)
        const response = await fetch('/api/batch/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ job_id })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const text = decoder.decode(value);
            const lines = text.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));

                        if (data.type === 'task_started') {
                            logArea.innerHTML += `<div>▶️ 开始生成: ${data.task.title}</div>`;
                        } else if (data.type === 'task_completed') {
                            logArea.innerHTML += `<div style="color: #4caf50">✅ 完成: ${data.task.title}</div>`;
                            progressBar.style.width = `${data.job_progress}%`;
                        } else if (data.type === 'task_failed') {
                            logArea.innerHTML += `<div style="color: var(--accent-primary)">❌ 失败: ${data.task.title} - ${data.task.error}</div>`;
                        } else if (data.type === 'job_completed') {
                            logArea.innerHTML += `<div style="margin-top: 10px; font-weight: bold;">🎉 所有任务完成！</div>`;
                            progressBar.style.width = '100%';
                            showToast('批量生成完成');
                        }

                        logArea.scrollTop = logArea.scrollHeight;

                    } catch (e) { }
                }
            }
        }

    } catch (e) {
        logArea.innerHTML += `<div style="color: var(--accent-primary)">❌ 错误: ${e.message}</div>`;
    }
}


// ============ 侧边栏折叠 (37) ============

function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const main = document.querySelector('.main-content');

    if (sidebar) {
        sidebar.classList.toggle('collapsed');
        if (main) {
            main.classList.toggle('expanded');
        }
    }
}


// ============ 字数目标进度 (5) ============

async function updateGoalProgress() {
    if (!currentProject) return;

    try {
        const goals = await API.request(`/api/goals/${currentProject}`);
        const stats = await API.request(`/api/statistics/${currentProject}`);

        const totalProgress = (stats.total_words / goals.total_goal * 100).toFixed(1);

        const progressEl = document.getElementById('goalProgress');
        if (progressEl) {
            progressEl.innerHTML = `
                <div style="font-size: 12px; color: var(--text-secondary);">
                    总目标: ${stats.total_words.toLocaleString()} / ${goals.total_goal.toLocaleString()} 字 (${totalProgress}%)
                </div>
                <div class="progress-bar" style="margin-top: 4px;">
                    <div class="progress-fill" style="width: ${Math.min(totalProgress, 100)}%"></div>
                </div>
            `;
        }
    } catch (e) {
        console.error('加载目标失败', e);
    }
}


// ============ 版本快照 (4) ============

async function saveVersion(filepath) {
    if (!currentProject || !filepath) return;

    try {
        await API.request(`/api/versions/${currentProject}/${filepath}`, {
            method: 'POST'
        });
        showToast('版本快照已保存');
    } catch (e) {
        showToast('保存版本失败', 'error');
    }
}

async function showVersions(filepath) {
    if (!currentProject || !filepath) return;

    const { versions } = await API.request(`/api/versions/${currentProject}/${filepath}`);

    let versionList = versions.length === 0
        ? '<p style="color: var(--text-secondary);">暂无版本历史</p>'
        : versions.map(v => `
            <div style="display: flex; justify-content: space-between; padding: 8px; background: var(--bg-primary); border-radius: 4px; margin-bottom: 4px;">
                <span>${v.name}</span>
                <span style="color: var(--text-muted);">${new Date(v.created).toLocaleString()}</span>
            </div>
        `).join('');

    showModal('版本历史', versionList, `
        <button class="btn btn-secondary" onclick="closeModal()">关闭</button>
        <button class="btn btn-primary" onclick="saveVersion('${filepath}')">保存当前版本</button>
    `);
}


// ============ 移动端适配 (39) ============

function initMobileSupport() {
    // 检测移动设备
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);

    if (isMobile) {
        document.body.classList.add('mobile');

        // 添加移动菜单按钮
        const menuBtn = document.createElement('button');
        menuBtn.className = 'mobile-menu-btn';
        menuBtn.innerHTML = '☰';
        menuBtn.onclick = toggleSidebar;
        document.body.appendChild(menuBtn);
    }
}


// ============ 阅读模式 (6) ============

function toggleReadingMode() {
    const container = document.querySelector('.editor-container');
    if (!container) return;

    container.classList.toggle('reading-mode');

    if (container.classList.contains('reading-mode')) {
        showToast('阅读模式开启，点击编辑器退出');
    }
}


// ============ 初始化函数声明（已在页面顶部统一调用）============


// ============ 语法高亮 (8) ============

function highlightSyntax(text) {
    // 对话高亮
    text = text.replace(/[""]([^""]+)[""]/g, '<span class="syntax-dialogue">"$1"</span>');

    // 心理活动高亮
    text = text.replace(/[（(]([^）)]+)[）)]/g, '<span class="syntax-thought">($1)</span>');

    return text;
}


// ============ 分屏对比 (7) ============

function showComparison(original, modified) {
    showModal('对比视图', `
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; max-height: 500px;">
            <div>
                <h4 style="margin-bottom: 8px; color: var(--accent-danger);">原文</h4>
                <div style="background: var(--bg-primary); padding: 12px; border-radius: 8px; max-height: 400px; overflow-y: auto;">
                    ${renderMarkdown(original)}
                </div>
            </div>
            <div>
                <h4 style="margin-bottom: 8px; color: var(--accent-success);">修改后</h4>
                <div style="background: var(--bg-primary); padding: 12px; border-radius: 8px; max-height: 400px; overflow-y: auto;">
                    ${renderMarkdown(modified)}
                </div>
            </div>
        </div>
    `, `
        <button class="btn btn-secondary" onclick="closeModal()">关闭</button>
    `);
}


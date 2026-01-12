/**
 * 工具箱页面脚本
 */

console.log('Tools V2 Script Loaded Successfully');
window.TOOLS_LOADED = true;

// Use window property to avoid "Identifier already declared" errors if script is double-loaded
window.currentProject = window.currentProject || '';

// 页面初始化
window.initPage = async function () {
    console.log('Tools page initializing...');
    try {
        // 加载项目列表
        const { projects } = await API.getProjects();
        const select = document.getElementById('currentProject');

        if (!select) {
            console.error('Project select element not found!');
            return;
        }

        // 清空现有选项
        select.innerHTML = '<option value="">选择项目...</option>';

        projects.forEach(p => {
            const option = document.createElement('option');
            option.value = p.name;
            option.textContent = p.title || p.name;
            select.appendChild(option);
        });

        select.onchange = () => {
            currentProject = select.value;
            console.log('Project switched to:', currentProject);
        };

        if (projects.length > 0) {
            select.value = projects[0].name;
            currentProject = projects[0].name;
            console.log('Default project selected:', currentProject);
        } else {
            console.log('No projects found.');
        }
    } catch (e) {
        console.error('Failed to init tools page:', e);
        showToast('初始化失败: ' + e.message, 'error');
    }
};

window.ensureProject = function () {
    if (!currentProject) {
        showToast('请先选择项目', 'error');
        return false;
    }
    return true;
}

// ============ 角色数据库 ============
async function showCharactersModal() {
    if (!window.ensureProject()) return;

    try {
        const { characters } = await API.request(`/api/characters/${currentProject}`);

        let charList = characters.length === 0
            ? '<p style="color: var(--text-secondary);">暂无角色</p>'
            : characters.map(c => `
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px; background: var(--bg-primary); border-radius: 8px; margin-bottom: 8px;">
                <div>
                    <strong>${c.name}</strong> 
                    <span class="card-badge" style="margin-left: 8px;">${c.role}</span>
                    <span style="color: var(--text-secondary); margin-left: 8px;">${c.personality || ''}</span>
                </div>
                <button class="btn btn-sm btn-danger" onclick="deleteCharacter(${c.id})">删除</button>
            </div>
        `).join('');

        showModal('👤 角色数据库', `
        <div style="margin-bottom: 16px;">
            ${charList}
        </div>
        <hr style="border-color: var(--border-color); margin: 16px 0;">
        <h4 style="margin-bottom: 12px;">添加角色</h4>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
            <input type="text" id="charName" class="form-input" placeholder="姓名">
            <select id="charRole" class="form-select">
                <option value="主角">主角</option>
                <option value="配角">配角</option>
                <option value="反派">反派</option>
                <option value="龙套">龙套</option>
            </select>
            <input type="text" id="charPersonality" class="form-input" placeholder="性格特点">
            <input type="text" id="charAppearance" class="form-input" placeholder="外貌特征">
        </div>
        <textarea id="charBackground" class="form-textarea" style="margin-top: 12px; min-height: 80px;" placeholder="背景故事..."></textarea>
    `, `
        <button class="btn btn-secondary" onclick="closeModal()">关闭</button>
        <button class="btn btn-primary" onclick="addCharacter()">添加角色</button>
    `);
    } catch (e) {
        showToast('加载角色失败', 'error');
    }
}

async function addCharacter() {
    const data = {
        name: document.getElementById('charName').value,
        role: document.getElementById('charRole').value,
        personality: document.getElementById('charPersonality').value,
        appearance: document.getElementById('charAppearance').value,
        background: document.getElementById('charBackground').value
    };

    if (!data.name) {
        showToast('请输入角色姓名', 'error');
        return;
    }

    try {
        await API.request(`/api/characters/${currentProject}`, {
            method: 'POST',
            body: data
        });

        showToast('角色添加成功');
        showCharactersModal();
    } catch (e) {
        // API wrapper handles toast usually, but safe to have try/catch
    }
}

async function deleteCharacter(id) {
    if (!confirm('确定要删除这个角色吗？')) return;
    try {
        await API.request(`/api/characters/${currentProject}/${id}`, { method: 'DELETE' });
        showToast('角色已删除');
        showCharactersModal();
    } catch (e) { }
}

// ============ 世界观设定 ============
async function showWorldbuildingModal() {
    if (!window.ensureProject()) return;

    try {
        const { settings, categories } = await API.request(`/api/worldbuilding/${currentProject}`);

        let settingsList = settings.length === 0
            ? '<p style="color: var(--text-secondary);">暂无设定</p>'
            : settings.map(s => `
            <div style="padding: 12px; background: var(--bg-primary); border-radius: 8px; margin-bottom: 8px;">
                <div style="display: flex; justify-content: space-between;">
                    <strong>${s.name}</strong>
                    <span class="card-badge">${s.category}</span>
                </div>
                <p style="color: var(--text-secondary); margin-top: 4px; font-size: 13px;">${s.description}</p>
            </div>
        `).join('');

        showModal('🌍 世界观设定', `
        <div style="margin-bottom: 16px; max-height: 300px; overflow-y: auto;">
            ${settingsList}
        </div>
        <hr style="border-color: var(--border-color); margin: 16px 0;">
        <h4 style="margin-bottom: 12px;">添加设定</h4>
        <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 12px;">
            <input type="text" id="settingName" class="form-input" placeholder="设定名称">
            <select id="settingCategory" class="form-select">
                ${categories.map(c => `<option value="${c}">${c}</option>`).join('')}
            </select>
        </div>
        <textarea id="settingDesc" class="form-textarea" style="margin-top: 12px;" placeholder="详细描述..."></textarea>
    `, `
        <button class="btn btn-secondary" onclick="closeModal()">关闭</button>
        <button class="btn btn-primary" onclick="addWorldbuilding()">添加设定</button>
    `);
    } catch (e) {
        showToast('加载世界观失败', 'error');
    }
}

async function addWorldbuilding() {
    const data = {
        name: document.getElementById('settingName').value,
        category: document.getElementById('settingCategory').value,
        description: document.getElementById('settingDesc').value
    };

    if (!data.name) {
        showToast('请输入设定名称', 'error');
        return;
    }

    try {
        await API.request(`/api/worldbuilding/${currentProject}`, {
            method: 'POST',
            body: data
        });

        showToast('设定添加成功');
        showWorldbuildingModal();
    } catch (e) { }
}

// ============ 伏笔管理 ============
async function showForeshadowingModal() {
    if (!window.ensureProject()) return;

    try {
        const { foreshadowing } = await API.request(`/api/foreshadowing/${currentProject}`);

        const statusColors = {
            '未回收': 'var(--accent-warning)',
            '部分回收': 'var(--accent-info)',
            '已回收': 'var(--accent-success)'
        };

        let foreList = foreshadowing.length === 0
            ? '<p style="color: var(--text-secondary);">暂无伏笔</p>'
            : foreshadowing.map(f => `
            <div style="padding: 12px; background: var(--bg-primary); border-radius: 8px; margin-bottom: 8px; border-left: 4px solid ${statusColors[f.status] || 'gray'};">
                <div style="display: flex; justify-content: space-between;">
                    <strong>${f.title}</strong>
                    <span style="font-size: 12px;">${f.status}</span>
                </div>
                <p style="color: var(--text-secondary); margin-top: 4px; font-size: 13px;">${f.description}</p>
                <div style="font-size: 12px; color: var(--text-muted); margin-top: 8px;">
                    埋设: ${f.planted_chapter || '未知'} | 计划回收: ${f.planned_payoff || '未定'}
                </div>
            </div>
        `).join('');

        showModal('🎯 伏笔管理', `
        <div style="margin-bottom: 16px; max-height: 300px; overflow-y: auto;">
            ${foreList}
        </div>
        <hr style="border-color: var(--border-color); margin: 16px 0;">
        <h4 style="margin-bottom: 12px;">添加伏笔</h4>
        <input type="text" id="foreTitle" class="form-input" placeholder="伏笔标题" style="margin-bottom: 12px;">
        <textarea id="foreDesc" class="form-textarea" placeholder="伏笔描述..."></textarea>
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; margin-top: 12px;">
            <input type="text" id="forePlanted" class="form-input" placeholder="埋设章节">
            <input type="text" id="forePlan" class="form-input" placeholder="计划回收">
            <select id="foreImportance" class="form-select">
                <option value="普通">普通</option>
                <option value="支线">支线</option>
                <option value="主线">主线</option>
            </select>
        </div>
    `, `
        <button class="btn btn-secondary" onclick="closeModal()">关闭</button>
        <button class="btn btn-primary" onclick="addForeshadowing()">添加伏笔</button>
    `);
    } catch (e) {
        showToast('加载伏笔失败', 'error');
    }
}

async function addForeshadowing() {
    const data = {
        title: document.getElementById('foreTitle').value,
        description: document.getElementById('foreDesc').value,
        planted_chapter: document.getElementById('forePlanted').value,
        planned_payoff: document.getElementById('forePlan').value,
        importance: document.getElementById('foreImportance').value
    };

    if (!data.title) {
        showToast('请输入伏笔标题', 'error');
        return;
    }

    try {
        await API.request(`/api/foreshadowing/${currentProject}`, {
            method: 'POST',
            body: data
        });

        showToast('伏笔添加成功');
        showForeshadowingModal();
    } catch (e) { }
}

// ============ 统计 ============
async function showStatisticsModal() {
    if (!window.ensureProject()) return;

    try {
        const stats = await API.request(`/api/statistics/${currentProject}`);

        // 词频排行
        const wordFreq = Object.entries(stats.word_frequency || {})
            .map(([word, count]) => `<span style="margin-right: 12px;">${word} (${count})</span>`)
            .join('');

        showModal('📊 写作统计', `
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px;">
            <div class="stat-card">
                <div class="stat-value">${stats.total_words?.toLocaleString() || 0}</div>
                <div class="stat-label">总字数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${stats.total_chapters || 0}</div>
                <div class="stat-label">章节数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${stats.avg_chapter_length?.toLocaleString() || 0}</div>
                <div class="stat-label">平均章节长度</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${stats.dialogue_ratio || 0}%</div>
                <div class="stat-label">对话比例</div>
            </div>
        </div>
        
        <h4 style="margin-bottom: 12px;">高频词汇</h4>
        <div style="padding: 16px; background: var(--bg-primary); border-radius: 8px; font-size: 14px;">
            ${wordFreq || '暂无数据'}
        </div>
        
        <h4 style="margin: 16px 0 12px;">章节详情</h4>
        <div style="max-height: 200px; overflow-y: auto;">
            ${(stats.chapters || []).map(c => `
                <div style="display: flex; justify-content: space-between; padding: 8px; border-bottom: 1px solid var(--border-color);">
                    <span>${c.name}</span>
                    <span>${c.words?.toLocaleString()} 字</span>
                </div>
            `).join('')}
        </div>
    `, `
        <button class="btn btn-secondary" onclick="closeModal()">关闭</button>
    `);
    } catch (e) {
        showToast('加载统计失败', 'error');
    }
}

// ============ 搜索替换 ============
async function showSearchModal() {
    if (!window.ensureProject()) return;

    showModal('🔍 搜索替换', `
        <div class="form-group">
            <label class="form-label">搜索内容</label>
            <input type="text" id="searchQuery" class="form-input" placeholder="输入要搜索的文本">
        </div>
        <div class="form-group">
            <label class="form-label">替换为（可选）</label>
            <input type="text" id="replaceText" class="form-input" placeholder="留空则仅搜索">
        </div>
        <div id="searchResults" style="max-height: 300px; overflow-y: auto;"></div>
    `, `
        <button class="btn btn-secondary" onclick="closeModal()">关闭</button>
        <button class="btn btn-secondary" onclick="doSearch()">搜索</button>
        <button class="btn btn-primary" onclick="doReplace()">替换全部</button>
    `);
}

async function doSearch() {
    const query = document.getElementById('searchQuery').value;
    if (!query) return;

    try {
        const { results } = await API.request(`/api/search/${currentProject}`, {
            method: 'POST',
            body: { query }
        });

        const resultsEl = document.getElementById('searchResults');
        resultsEl.innerHTML = results.length === 0
            ? '<p style="color: var(--text-secondary);">未找到匹配</p>'
            : results.map(r => `
            <div style="padding: 8px; background: var(--bg-primary); border-radius: 4px; margin-bottom: 4px; font-size: 13px;">
                <strong>${r.file}:${r.line}</strong>
                <span style="color: var(--text-secondary);">${r.context}</span>
            </div>
        `).join('');
    } catch (e) { }
}

async function doReplace() {
    const search = document.getElementById('searchQuery').value;
    const replace = document.getElementById('replaceText').value;

    if (!search) {
        showToast('请输入搜索内容', 'error');
        return;
    }

    try {
        const { replaced_count } = await API.request(`/api/replace/${currentProject}`, {
            method: 'POST',
            body: { search, replace }
        });

        showToast(`已替换 ${replaced_count} 处`);
    } catch (e) { }
}

// ============ 导出 ============
async function showExportModal() {
    if (!window.ensureProject()) return;

    showModal('📥 导出', `
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
            <button class="btn btn-secondary" style="padding: 24px;" onclick="exportTxt()">
                <div style="font-size: 32px; margin-bottom: 8px;">📄</div>
                导出TXT
            </button>
            <button class="btn btn-secondary" style="padding: 24px;" onclick="exportZip()">
                <div style="font-size: 32px; margin-bottom: 8px;">📦</div>
                打包ZIP
            </button>
        </div>
    `, `
        <button class="btn btn-secondary" onclick="closeModal()">关闭</button>
    `);
}

async function exportTxt() {
    try {
        const result = await API.request(`/api/export/${currentProject}/txt`);
        showToast(`已导出: ${result.size} 字`);
    } catch (e) { }
}

async function exportZip() {
    window.open(`/api/export/${currentProject}/zip`, '_blank');
    showToast('正在下载...');
}

// ============ 批量生成 ============
async function showBatchModal() {
    if (!window.ensureProject()) return;

    showModal('⚡ 批量生成', `
        <div class="form-group">
            <label class="form-label">起始章节</label>
            <input type="number" id="batchStart" class="form-input" value="1" min="1">
        </div>
        <div class="form-group">
            <label class="form-label">生成数量</label>
            <input type="number" id="batchCount" class="form-input" value="3" min="1" max="1">
        </div>
        <p style="color: var(--accent-warning); font-size: 13px;">
            ⚠️ 批量生成会消耗较多Token，请谨慎使用
        </p>
    `, `
        <button class="btn btn-secondary" onclick="closeModal()">取消</button>
        <button class="btn btn-primary" onclick="doBatchGenerate()">开始生成</button>
    `);
}

async function doBatchGenerate() {
    const start = parseInt(document.getElementById('batchStart').value);
    const count = parseInt(document.getElementById('batchCount').value);

    closeModal();
    showToast('批量生成已开始...');

    try {
        const result = await API.request('/api/batch/generate', {
            method: 'POST',
            body: { project: currentProject, start, count }
        });

        showToast(`成功生成 ${result.results.length} 章`);
    } catch (e) {
        showToast('生成失败', 'error');
    }
}

// ============ 历史 ============
async function showHistoryModal() {
    if (!window.ensureProject()) return;

    try {
        const { history } = await API.request(`/api/history/${currentProject}`);

        let histList = history.length === 0
            ? '<p style="color: var(--text-secondary);">暂无记录</p>'
            : history.reverse().map(h => `
            <div style="padding: 12px; background: var(--bg-primary); border-radius: 8px; margin-bottom: 8px;">
                <div style="display: flex; justify-content: space-between;">
                    <strong>${h.stage}</strong>
                    <span style="font-size: 12px; color: var(--text-muted);">${new Date(h.timestamp).toLocaleString()}</span>
                </div>
                <p style="color: var(--text-secondary); font-size: 13px; margin-top: 4px;">${h.preview}</p>
                <div style="font-size: 12px; color: var(--text-muted);">${h.length} 字</div>
            </div>
        `).join('');

        showModal('📜 生成历史', `
        <div style="max-height: 500px; overflow-y: auto;">
            ${histList}
        </div>
    `, `
        <button class="btn btn-secondary" onclick="closeModal()">关闭</button>
    `);
    } catch (e) {
        showToast('加载历史失败', 'error');
    }
}

// ============ 时间线 ============
async function showTimelineModal() {
    if (!window.ensureProject()) return;

    try {
        const { events } = await API.request(`/api/timeline/${currentProject}`);

        let timeline = events.length === 0
            ? '<p style="color: var(--text-secondary);">暂无事件</p>'
            : events.map(e => `
            <div style="display: flex; gap: 16px; margin-bottom: 16px;">
                <div style="width: 60px; text-align: right; color: var(--accent-secondary); font-weight: bold;">${e.time}</div>
                <div style="width: 2px; background: var(--accent-primary);"></div>
                <div style="flex: 1; padding: 12px; background: var(--bg-primary); border-radius: 8px;">
                    <strong>${e.title}</strong>
                    <p style="color: var(--text-secondary); font-size: 13px; margin-top: 4px;">${e.description}</p>
                </div>
            </div>
        `).join('');

        showModal('📅 时间线', `
        <div style="max-height: 400px; overflow-y: auto; margin-bottom: 16px;">
            ${timeline}
        </div>
        <hr style="border-color: var(--border-color); margin: 16px 0;">
        <h4 style="margin-bottom: 12px;">添加事件</h4>
        <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 12px;">
            <input type="text" id="eventTime" class="form-input" placeholder="时间点">
            <input type="text" id="eventTitle" class="form-input" placeholder="事件标题">
        </div>
        <textarea id="eventDesc" class="form-textarea" style="margin-top: 12px;" placeholder="事件描述..."></textarea>
    `, `
        <button class="btn btn-secondary" onclick="closeModal()">关闭</button>
        <button class="btn btn-primary" onclick="addTimelineEvent()">添加事件</button>
    `);
    } catch (e) {
        showToast('加载时间线失败', 'error');
    }
}

async function addTimelineEvent() {
    const data = {
        time: document.getElementById('eventTime').value,
        title: document.getElementById('eventTitle').value,
        description: document.getElementById('eventDesc').value
    };

    if (!data.title) {
        showToast('请输入事件标题', 'error');
        return;
    }

    try {
        await API.request(`/api/timeline/${currentProject}`, {
            method: 'POST',
            body: data
        });

        showToast('事件添加成功');
        showTimelineModal();
    } catch (e) { }
}

// Export to window explicitly
Object.assign(window, {
    showCharactersModal, addCharacter, deleteCharacter,
    showWorldbuildingModal, addWorldbuilding,
    showForeshadowingModal, addForeshadowing,
    showStatisticsModal,
    showSearchModal, doSearch, doReplace,
    showExportModal, exportTxt, exportZip,
    showBatchModal, doBatchGenerate,
    showHistoryModal,
    showTimelineModal, addTimelineEvent
});

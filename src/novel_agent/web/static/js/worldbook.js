/**
 * Worldbook Logic
 */

let currentCards = [];
let currentFilter = 'all';

async function loadWorldCards() {
    if (!currentProject) return;

    const container = document.getElementById('worldCardsGrid');
    showLoading(container);

    try {
        const { cards } = await API.getWorldCards(currentProject);
        currentCards = cards;
        renderCards();
    } catch (e) {
        container.innerHTML = `<p style="color: red">加载失败: ${e.message}</p>`;
    }
}

function renderCards() {
    const container = document.getElementById('worldCardsGrid');
    if (!container) return;

    let filtered = currentCards;
    if (currentFilter !== 'all') {
        filtered = currentCards.filter(c => c.card_type === currentFilter);
    }

    if (filtered.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>暂无卡片</p></div>';
        return;
    }

    container.innerHTML = filtered.map(card => `
        <div class="card world-card">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div>
                    <span class="card-badge ${card.card_type}">${card.card_type.toUpperCase()}</span>
                    <h4 style="margin: 8px 0;">${card.name}</h4>
                </div>
                <button class="btn btn-sm btn-text" onclick="deleteCard('${card.id}')" style="color: var(--accent-primary)">🗑️</button>
            </div>
            <p style="font-size: 13px; color: var(--text-secondary); display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;">
                ${card.description}
            </p>
            <div style="margin-top: 12px; font-size: 12px; color: var(--text-secondary);">
                ${Object.keys(card.attributes || {}).length} 个属性
            </div>
        </div>
    `).join('');
}

function filterCards(type) {
    currentFilter = type;

    // Update active button
    document.querySelectorAll('.filter-bar .btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.textContent.includes({ all: '全部', character: '角色', location: '地点', item: '物品', concept: '设定' }[type])) {
            btn.classList.add('active');
        }
    });

    if (type === 'all') {
        // Find button by text content match might be tricky if not exact, simplify:
        // Already handled logic above roughly. exact match preferred.
    }

    renderCards();
}

function showAddCardModal() {
    showModal('新建卡片', `
        <div class="form-group">
            <label class="form-label">名称</label>
            <input type="text" id="cardName" class="form-input">
        </div>
        <div class="form-group">
            <label class="form-label">类型</label>
            <select id="cardType" class="form-select">
                <option value="character">角色 (Character)</option>
                <option value="location">地点 (Location)</option>
                <option value="item">物品 (Item)</option>
                <option value="faction">势力 (Faction)</option>
                <option value="event">事件 (Event)</option>
                <option value="concept">设定 (Concept)</option>
            </select>
        </div>
        <div class="form-group">
            <label class="form-label">描述</label>
            <textarea id="cardDesc" class="form-textarea" style="min-height: 100px;"></textarea>
        </div>
    `, `
        <button class="btn btn-secondary" onclick="closeModal()">取消</button>
        <button class="btn btn-primary" onclick="submitNewCard()">创建</button>
    `);
}

async function submitNewCard() {
    const name = document.getElementById('cardName').value;
    const type = document.getElementById('cardType').value;
    const desc = document.getElementById('cardDesc').value;

    if (!name) return showToast('请输入名称', 'error');

    try {
        await API.createWorldCard(currentProject, {
            name,
            card_type: type,
            description: desc
        });
        showToast('创建成功');
        closeModal();
        loadWorldCards();
    } catch (e) {
        showToast(e.message, 'error');
    }
}

async function deleteCard(id) {
    if (!confirm('确定要删除这张卡片吗？')) return;

    try {
        await API.deleteWorldCard(currentProject, id);
        showToast('删除成功');
        loadWorldCards();
    } catch (e) {
        showToast(e.message, 'error');
    }
}

import { useEffect, useCallback } from 'react';

// 快捷键配置
const DEFAULT_SHORTCUTS = {
    'ctrl+s': { description: '保存', action: 'save' },
    'ctrl+z': { description: '撤销', action: 'undo' },
    'ctrl+shift+z': { description: '重做', action: 'redo' },
    'ctrl+f': { description: '搜索', action: 'search' },
    'ctrl+h': { description: '替换', action: 'replace' },
    'ctrl+g': { description: 'AI 生成', action: 'generate' },
    'ctrl+b': { description: '加粗', action: 'bold' },
    'ctrl+i': { description: '斜体', action: 'italic' },
    'escape': { description: '关闭面板', action: 'close' },
};

export function useKeyboardShortcuts(handlers = {}) {
    const handleKeyDown = useCallback((e) => {
        // 构建快捷键字符串
        const parts = [];
        if (e.ctrlKey || e.metaKey) parts.push('ctrl');
        if (e.shiftKey) parts.push('shift');
        if (e.altKey) parts.push('alt');

        // 获取按键
        let key = e.key.toLowerCase();
        if (key === ' ') key = 'space';
        if (!['control', 'shift', 'alt', 'meta'].includes(key)) {
            parts.push(key);
        }

        const shortcut = parts.join('+');

        // 查找匹配的处理函数
        const config = DEFAULT_SHORTCUTS[shortcut];
        if (config && handlers[config.action]) {
            e.preventDefault();
            handlers[config.action](e);
        }
    }, [handlers]);

    useEffect(() => {
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [handleKeyDown]);
}

// 获取所有快捷键列表
export function getShortcutsList() {
    return Object.entries(DEFAULT_SHORTCUTS).map(([key, config]) => ({
        key: key.toUpperCase().replace('CTRL', '⌘/Ctrl'),
        ...config
    }));
}

export default useKeyboardShortcuts;

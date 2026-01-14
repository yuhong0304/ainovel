import React, { useEffect, useState, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import client from '@/api/client';
import CardGrid from './worldbook/CardGrid';
import CardEditor from './worldbook/CardEditor';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import {
    Plus, Loader2, Book, Search, User, MapPin, Package,
    ScrollText, Sparkles, Filter, Download, Upload, X
} from 'lucide-react';

// 类别定义
const CATEGORIES = [
    { value: 'all', label: '全部', icon: Book },
    { value: 'character', label: '角色', icon: User },
    { value: 'location', label: '地点', icon: MapPin },
    { value: 'item', label: '物品', icon: Package },
    { value: 'lore', label: '设定', icon: ScrollText },
];

export default function Worldbook() {
    const { projectId } = useParams();
    const [cards, setCards] = useState([]);
    const [loading, setLoading] = useState(true);

    // UI 状态
    const [isEditorOpen, setIsEditorOpen] = useState(false);
    const [editingCard, setEditingCard] = useState(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedCategory, setSelectedCategory] = useState('all');
    const [isExtracting, setIsExtracting] = useState(false);

    // 获取卡片
    const fetchCards = async () => {
        try {
            const { data } = await client.get(`/api/world/${projectId}/cards`);
            setCards(data.cards || []);
        } catch (e) {
            console.error(e);
            toast.error('加载失败');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (projectId) fetchCards();
    }, [projectId]);

    // 过滤后的卡片
    const filteredCards = useMemo(() => {
        return cards.filter(card => {
            // 类别过滤
            if (selectedCategory !== 'all' && card.category !== selectedCategory) {
                return false;
            }
            // 搜索过滤
            if (searchQuery.trim()) {
                const query = searchQuery.toLowerCase();
                return (
                    card.name?.toLowerCase().includes(query) ||
                    card.content?.toLowerCase().includes(query) ||
                    card.tags?.some(t => t.toLowerCase().includes(query))
                );
            }
            return true;
        });
    }, [cards, selectedCategory, searchQuery]);

    // 类别统计
    const categoryCounts = useMemo(() => {
        const counts = { all: cards.length };
        CATEGORIES.forEach(cat => {
            if (cat.value !== 'all') {
                counts[cat.value] = cards.filter(c => c.category === cat.value).length;
            }
        });
        return counts;
    }, [cards]);

    const handleCreate = (category = 'character') => {
        setEditingCard({ category });
        setIsEditorOpen(true);
    };

    const handleEdit = (card) => {
        setEditingCard(card);
        setIsEditorOpen(true);
    };

    const handleDelete = async (id) => {
        if (!confirm("确定要删除这张卡片吗？")) return;
        try {
            await client.delete(`/api/world/${projectId}/cards/${id}`);
            setCards(prev => prev.filter(c => c.id !== id));
            toast.success('已删除');
        } catch (e) {
            toast.error('删除失败');
        }
    };

    const handleSave = async (cardData) => {
        try {
            if (cardData.id) {
                const { data } = await client.put(`/api/world/${projectId}/cards/${cardData.id}`, cardData);
                setCards(prev => prev.map(c => c.id === cardData.id ? data.card : c));
                toast.success('已更新');
            } else {
                const { data } = await client.post(`/api/world/${projectId}/cards`, cardData);
                setCards(prev => [...prev, data.card]);
                toast.success('已创建');
            }
            setIsEditorOpen(false);
        } catch (e) {
            toast.error('保存失败');
        }
    };

    // AI 自动提取设定
    const handleAutoExtract = async () => {
        setIsExtracting(true);
        try {
            const { data } = await client.post(`/api/world/${projectId}/extract`);
            if (data.extracted?.length > 0) {
                setCards(prev => [...prev, ...data.extracted]);
                toast.success(`从正文中提取了 ${data.extracted.length} 个设定`);
            } else {
                toast.info('未找到可提取的设定');
            }
        } catch (e) {
            toast.error('提取失败: ' + e.message);
        } finally {
            setIsExtracting(false);
        }
    };

    // 导出 JSON
    const handleExport = () => {
        const data = JSON.stringify(cards, null, 2);
        const blob = new Blob([data], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `worldbook_${projectId}.json`;
        a.click();
        URL.revokeObjectURL(url);
        toast.success('已导出');
    };

    // 导入 JSON
    const handleImport = (e) => {
        const file = e.target.files?.[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = async (event) => {
            try {
                const imported = JSON.parse(event.target.result);
                if (Array.isArray(imported)) {
                    // 批量创建
                    for (const card of imported) {
                        delete card.id; // 移除原 ID
                        await client.post(`/api/world/${projectId}/cards`, card);
                    }
                    fetchCards();
                    toast.success(`已导入 ${imported.length} 个卡片`);
                }
            } catch (err) {
                toast.error('导入失败: 无效的 JSON');
            }
        };
        reader.readAsText(file);
    };

    if (loading) {
        return (
            <div className="p-8 space-y-6">
                <div className="flex items-center justify-between">
                    <Skeleton className="h-10 w-48" />
                    <Skeleton className="h-10 w-32" />
                </div>
                <div className="flex gap-2">
                    {[1, 2, 3, 4, 5].map(i => <Skeleton key={i} className="h-8 w-16" />)}
                </div>
                <div className="grid grid-cols-3 gap-4">
                    {[1, 2, 3, 4, 5, 6].map(i => <Skeleton key={i} className="h-40" />)}
                </div>
            </div>
        );
    }

    return (
        <div className="h-full flex flex-col bg-background">
            {/* Header */}
            <div className="px-8 py-6 border-b">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-primary/10 rounded-lg text-primary">
                            <Book className="w-6 h-6" />
                        </div>
                        <div>
                            <h1 className="text-2xl font-bold">世界设定 (Worldbook)</h1>
                            <p className="text-muted-foreground text-sm">
                                共 {cards.length} 个设定
                            </p>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <Button variant="outline" size="sm" onClick={handleAutoExtract} disabled={isExtracting}>
                            {isExtracting ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <Sparkles className="w-4 h-4 mr-1" />}
                            AI 提取
                        </Button>
                        <Button variant="outline" size="sm" onClick={handleExport}>
                            <Download className="w-4 h-4 mr-1" />
                            导出
                        </Button>
                        <label>
                            <input type="file" accept=".json" onChange={handleImport} className="hidden" />
                            <Button variant="outline" size="sm" asChild>
                                <span><Upload className="w-4 h-4 mr-1" /> 导入</span>
                            </Button>
                        </label>
                        <Button onClick={() => handleCreate()} className="gap-2">
                            <Plus className="w-4 h-4" /> 新建设定
                        </Button>
                    </div>
                </div>

                {/* 搜索和筛选 */}
                <div className="flex items-center gap-4">
                    {/* 类别筛选 */}
                    <div className="flex items-center gap-1">
                        {CATEGORIES.map(cat => {
                            const Icon = cat.icon;
                            const isActive = selectedCategory === cat.value;
                            return (
                                <Button
                                    key={cat.value}
                                    variant={isActive ? 'default' : 'ghost'}
                                    size="sm"
                                    onClick={() => setSelectedCategory(cat.value)}
                                    className="gap-1.5"
                                >
                                    <Icon className="w-3.5 h-3.5" />
                                    {cat.label}
                                    <Badge variant="secondary" className="ml-1 text-xs">
                                        {categoryCounts[cat.value] || 0}
                                    </Badge>
                                </Button>
                            );
                        })}
                    </div>

                    <div className="flex-1" />

                    {/* 搜索框 */}
                    <div className="relative w-64">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                        <Input
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="搜索设定..."
                            className="pl-9 pr-8"
                        />
                        {searchQuery && (
                            <button
                                onClick={() => setSearchQuery('')}
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                            >
                                <X className="w-4 h-4" />
                            </button>
                        )}
                    </div>
                </div>
            </div>

            {/* Grid */}
            <div className="flex-1 overflow-y-auto bg-muted/10 p-6">
                {filteredCards.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
                        <Book className="w-12 h-12 mb-4 opacity-30" />
                        <p>{searchQuery ? '未找到匹配的设定' : '暂无设定，点击新建开始'}</p>
                    </div>
                ) : (
                    <CardGrid cards={filteredCards} onEdit={handleEdit} onDelete={handleDelete} />
                )}
            </div>

            {/* Editor Dialog */}
            <CardEditor
                isOpen={isEditorOpen}
                onClose={() => setIsEditorOpen(false)}
                onSave={handleSave}
                card={editingCard}
            />
        </div>
    );
}

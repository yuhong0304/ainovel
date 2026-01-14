import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const CARD_TYPES = [
    { value: 'character', label: '角色 (Character)' },
    { value: 'location', label: '地点 (Location)' },
    { value: 'item', label: '物品 (Item)' },
    { value: 'concept', label: '概念 (Concept)' },
    { value: 'event', label: '事件 (Event)' }
];

export default function CardEditor({ isOpen, onClose, onSave, card }) {
    const [formData, setFormData] = useState({
        name: '',
        card_type: 'character',
        description: '',
        content: ''
    });
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        if (isOpen) {
            if (card) {
                setFormData({
                    name: card.name || '',
                    card_type: (card.card_type || 'character').toLowerCase(),
                    description: card.description || '',
                    content: card.content || ''
                });
            } else {
                // Reset for new card
                setFormData({ name: '', card_type: 'character', description: '', content: '' });
            }
        }
    }, [isOpen, card]);

    const handleChange = (field, value) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    const handleSubmit = async () => {
        if (!formData.name) return alert("名称不能为空");

        try {
            setSaving(true);
            await onSave({ ...card, ...formData });
            onClose();
        } catch (e) {
            alert("保存失败: " + e.message);
        } finally {
            setSaving(false);
        }
    };

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="sm:max-w-[600px]">
                <DialogHeader>
                    <DialogTitle>{card ? "编辑卡片" : "新建卡片"}</DialogTitle>
                    <DialogDescription>
                        设定世界观元素，它们将被 AI 记忆并在写作时参考。
                    </DialogDescription>
                </DialogHeader>

                <div className="grid gap-4 py-4">
                    <div className="grid grid-cols-4 items-center gap-4">
                        <Label htmlFor="name" className="text-right">名称</Label>
                        <Input
                            id="name"
                            value={formData.name}
                            onChange={(e) => handleChange('name', e.target.value)}
                            className="col-span-3"
                            placeholder="如：林默"
                        />
                    </div>
                    <div className="grid grid-cols-4 items-center gap-4">
                        <Label htmlFor="type" className="text-right">类型</Label>
                        <Select
                            value={formData.card_type}
                            onValueChange={(v) => handleChange('card_type', v)}
                        >
                            <SelectTrigger className="col-span-3">
                                <SelectValue placeholder="选择类型" />
                            </SelectTrigger>
                            <SelectContent>
                                {CARD_TYPES.map(t => (
                                    <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>
                    <div className="grid grid-cols-4 items-center gap-4">
                        <Label htmlFor="desc" className="text-right">简述</Label>
                        <Textarea
                            id="desc"
                            value={formData.description}
                            onChange={(e) => handleChange('description', e.target.value)}
                            className="col-span-3 h-20"
                            placeholder="简短描述，用于快速检索"
                        />
                    </div>
                    <div className="grid grid-cols-4 items-center gap-4">
                        <Label htmlFor="content" className="text-right">详细设定</Label>
                        <Textarea
                            id="content"
                            value={formData.content}
                            onChange={(e) => handleChange('content', e.target.value)}
                            className="col-span-3 h-32 font-mono text-xs"
                            placeholder="详细设定内容，支持 Markdown"
                        />
                    </div>
                </div>

                <DialogFooter>
                    <Button variant="outline" onClick={onClose}>取消</Button>
                    <Button onClick={handleSubmit} disabled={saving}>
                        {saving ? "保存中..." : "保存设定"}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}

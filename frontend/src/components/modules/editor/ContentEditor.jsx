import React, { useEffect, useState } from 'react';
import { Button } from "@/components/ui/button";
import { Save, Sparkles, Wand2 } from 'lucide-react';

export default function ContentEditor({ chapterNum, content, onSave, onGenerate, isSaving, isGenerating }) {
    const [value, setValue] = useState(content || "");

    useEffect(() => {
        setValue(content || "");
    }, [content]);

    // Handle Ctrl+S
    useEffect(() => {
        const handleKeyDown = (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                e.preventDefault();
                onSave(value);
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [value, onSave]);

    if (!chapterNum) {
        return (
            <div className="h-full flex items-center justify-center text-muted-foreground bg-muted/10">
                请从左侧选择一个章节开始写作
            </div>
        );
    }

    return (
        <div className="flex flex-col h-full bg-background">
            {/* Toolbar */}
            <div className="h-14 border-b flex items-center justify-between px-6 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold text-sm">
                        {chapterNum}
                    </div>
                    <div className="text-sm font-medium">正文编辑</div>
                    {isGenerating && <span className="text-xs text-primary animate-pulse ml-2">正在撰写中...</span>}
                </div>
                <div className="flex items-center gap-2">
                    <Button
                        variant="outline"
                        size="sm"
                        className="gap-2 border-primary/20 hover:bg-primary/5 text-primary"
                        onClick={onGenerate}
                        disabled={isGenerating}
                    >
                        <Sparkles className="w-4 h-4" />
                        {isGenerating ? "生成中..." : "AI 续写/生成本章"}
                    </Button>

                    <div className="text-muted-foreground/20 text-xl font-thin mx-2">|</div>

                    <Button size="sm" onClick={() => onSave(value)} disabled={isSaving} className="gap-2 min-w-[80px]">
                        <Save className="w-4 h-4" />
                        {isSaving ? "保存中" : "保存"}
                    </Button>
                </div>
            </div>

            {/* Editor Area */}
            <div className="flex-1 overflow-auto relative group">
                <textarea
                    className="w-full h-full p-8 md:p-12 lg:px-24 bg-transparent resize-none focus:outline-none font-serif text-lg leading-relaxed text-foreground/90 selection:bg-primary/20"
                    value={value}
                    onChange={(e) => setValue(e.target.value)}
                    spellCheck={false}
                    placeholder="开始创作..."
                />

                {/* Status Bar */}
                <div className="absolute bottom-4 right-6 text-xs text-muted-foreground opacity-50 group-hover:opacity-100 transition-opacity bg-background/80 px-2 py-1 rounded-md pointer-events-none">
                    {value.length} 字 | Ln {value.split('\n').length}
                </div>
            </div>
        </div>
    );
}

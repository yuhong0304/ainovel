import React from 'react';
import { Button } from "@/components/ui/button";
import { Save, Wand2 } from 'lucide-react';

export default function StructureEditor({ content, onSave, isSaving, canGenerate, onGenerate, isGenerating }) {
    const [value, setValue] = React.useState(content || "");

    React.useEffect(() => {
        setValue(content || "");
    }, [content]);

    return (
        <div className="flex flex-col h-full bg-background">
            {/* Toolbar */}
            <div className="h-12 border-b flex items-center justify-between px-4 bg-muted/20">
                <div className="flex items-center gap-2">
                    <div className="text-sm font-medium opacity-70">Markdown 编辑器</div>
                    {isGenerating && <span className="text-xs text-primary animate-pulse">正在生成全书结构，请勿关闭页面...</span>}
                </div>
                <div className="flex items-center gap-2">
                    {canGenerate && (
                        <Button
                            size="sm"
                            variant="secondary"
                            className="h-8 gap-2 mr-2"
                            onClick={onGenerate}
                            disabled={isGenerating}
                        >
                            <Wand2 className="w-3 h-3" /> {isGenerating ? "生成中..." : "生成全书结构"}
                        </Button>
                    )}
                    <Button size="sm" variant="ghost" className="h-8 gap-2">
                        <Wand2 className="w-3 h-3" /> AI 润色
                    </Button>
                    <Button size="sm" onClick={() => onSave(value)} disabled={isSaving} className="h-8 gap-2">
                        <Save className="w-3 h-3" /> {isSaving ? "保存中..." : "保存"}
                    </Button>
                </div>
            </div>

            {/* Editor Area */}
            <div className="flex-1 overflow-auto p-0">
                <textarea
                    className="w-full h-full p-8 bg-transparent resize-none focus:outline-none font-mono text-sm leading-relaxed"
                    value={value}
                    onChange={(e) => setValue(e.target.value)}
                    spellCheck={false}
                />
            </div>
        </div>
    );
}

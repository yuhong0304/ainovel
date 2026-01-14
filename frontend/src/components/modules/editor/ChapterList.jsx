import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { FileText, Plus, Search } from 'lucide-react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function ChapterList({ chapters, selectedId, onSelect, onCreate }) {
    const [searchTerm, setSearchTerm] = useState("");

    const filteredChapters = (chapters || []).filter(c =>
        c.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        `Chapter ${c.chapter_num}`.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="w-64 border-r bg-card h-full flex flex-col">
            {/* Header */}
            <div className="p-4 border-b space-y-3">
                <div className="flex items-center justify-between">
                    <h3 className="font-semibold text-sm uppercase tracking-wider text-muted-foreground">章节列表</h3>
                    <Button size="icon" variant="ghost" className="h-6 w-6" onClick={onCreate}>
                        <Plus className="w-4 h-4" />
                    </Button>
                </div>
                <div className="relative">
                    <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                        placeholder="搜索章节..."
                        className="pl-8 h-9 text-xs"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
            </div>

            {/* List */}
            <div className="flex-1 overflow-y-auto py-2">
                {filteredChapters.map((chapter) => (
                    <div
                        key={chapter.chapter_num}
                        className={cn(
                            "flex items-center px-4 py-3 cursor-pointer hover:bg-accent transition-colors gap-3 border-l-2 border-transparent",
                            selectedId === chapter.chapter_num && "bg-accent/50 border-primary"
                        )}
                        onClick={() => onSelect(chapter.chapter_num)}
                    >
                        <div className={cn(
                            "w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-xs font-mono",
                            chapter.has_content ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground"
                        )}>
                            {chapter.chapter_num}
                        </div>
                        <div className="flex-1 min-w-0">
                            <div className="text-sm font-medium truncate">{chapter.title || `第 ${chapter.chapter_num} 章`}</div>
                            <div className="text-xs text-muted-foreground flex items-center gap-2">
                                <span>{chapter.word_count || 0} 字</span>
                            </div>
                        </div>
                    </div>
                ))}

                {filteredChapters.length === 0 && (
                    <div className="p-8 text-center text-xs text-muted-foreground">
                        {searchTerm ? "无匹配章节" : "暂无章节，点击 + 新建"}
                    </div>
                )}
            </div>
        </div>
    );
}

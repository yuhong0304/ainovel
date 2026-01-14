import React, { useEffect, useState, useCallback, useRef } from 'react';
import { useParams } from 'react-router-dom';
import client from '@/api/client';
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import SearchReplace from '@/components/SearchReplace';
import { useKeyboardShortcuts } from '@/hooks/use-keyboard-shortcuts';
import { toast } from "sonner";
import {
    ChevronRight, ChevronDown, FileText, BookOpen, Loader2, Save,
    Sparkles, Plus, FolderOpen, File, Wand2, RotateCcw, Check,
    Eye, EyeOff, Search, Undo2, Redo2, PenLine, AlignLeft
} from 'lucide-react';

// ============ 左侧：结构树组件 ============
function StructureTree({ structure, selectedId, onSelect, onAddVolume, onAddChapter }) {
    const [expandedVolumes, setExpandedVolumes] = useState(new Set([1]));

    const toggleVolume = (volNum, e) => {
        e.stopPropagation();
        setExpandedVolumes(prev => {
            const next = new Set(prev);
            if (next.has(volNum)) next.delete(volNum);
            else next.add(volNum);
            return next;
        });
    };

    const isSelected = (type, volNum = null, chapterNum = null) => {
        if (!selectedId) return false;
        if (selectedId.type !== type) return false;
        if (volNum !== null && selectedId.volNum !== volNum) return false;
        if (chapterNum !== null && selectedId.chapterNum !== chapterNum) return false;
        return true;
    };

    return (
        <div className="h-full flex flex-col">
            {/* 头部 */}
            <div className="px-4 py-3 border-b font-medium flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <BookOpen className="w-4 h-4" />
                    小说结构
                </div>
                <Button size="sm" variant="ghost" onClick={onAddVolume} className="h-7 px-2">
                    <Plus className="w-3 h-3" />
                </Button>
            </div>

            {/* 树形结构 */}
            <ScrollArea className="flex-1">
                <div className="p-3 space-y-1">
                    {/* 总纲入口 */}
                    <div
                        onClick={() => onSelect({ type: 'master' })}
                        className={`flex items-center gap-2 px-3 py-2.5 rounded-lg cursor-pointer transition-all ${isSelected('master')
                            ? 'bg-primary text-primary-foreground shadow-sm'
                            : 'hover:bg-muted'
                            }`}
                    >
                        <BookOpen className="w-4 h-4" />
                        <span className="font-medium">总纲</span>
                        <Badge variant="outline" className="ml-auto text-xs">
                            大纲
                        </Badge>
                    </div>

                    {/* 分卷列表 */}
                    {structure?.volumes?.map((vol) => (
                        <div key={vol.vol_num} className="space-y-1">
                            {/* 卷标题行 */}
                            <div
                                className={`flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-all ${isSelected('volume', vol.vol_num)
                                    ? 'bg-primary/10 text-primary'
                                    : 'hover:bg-muted'
                                    }`}
                            >
                                <button onClick={(e) => toggleVolume(vol.vol_num, e)} className="p-0.5">
                                    {expandedVolumes.has(vol.vol_num)
                                        ? <ChevronDown className="w-4 h-4" />
                                        : <ChevronRight className="w-4 h-4" />
                                    }
                                </button>
                                <FolderOpen className="w-4 h-4" />
                                <span
                                    className="flex-1"
                                    onClick={() => onSelect({ type: 'volume', volNum: vol.vol_num })}
                                >
                                    第 {vol.vol_num} 卷
                                </span>
                                <Badge variant="secondary" className="text-xs">
                                    {vol.scripts?.length || 0}章
                                </Badge>
                            </div>

                            {/* 展开的卷内容 */}
                            {expandedVolumes.has(vol.vol_num) && (
                                <div className="ml-4 pl-4 border-l-2 border-muted space-y-1">
                                    {/* 卷纲 */}
                                    <div
                                        onClick={() => onSelect({ type: 'volume_outline', volNum: vol.vol_num })}
                                        className={`flex items-center gap-2 px-3 py-1.5 rounded-md cursor-pointer text-sm ${isSelected('volume_outline', vol.vol_num)
                                            ? 'bg-primary/10 text-primary'
                                            : 'hover:bg-muted text-muted-foreground'
                                            }`}
                                    >
                                        <AlignLeft className="w-3 h-3" />
                                        <span>粗纲 / 卷纲</span>
                                    </div>

                                    {/* 章节列表 */}
                                    {vol.scripts?.map((script) => (
                                        <div
                                            key={script.script_num}
                                            onClick={() => onSelect({
                                                type: 'chapter',
                                                volNum: vol.vol_num,
                                                chapterNum: script.script_num,
                                                filename: script.filename
                                            })}
                                            className={`flex items-center gap-2 px-3 py-2 rounded-md cursor-pointer text-sm transition-all ${isSelected('chapter', vol.vol_num, script.script_num)
                                                ? 'bg-primary text-primary-foreground shadow-sm'
                                                : 'hover:bg-muted'
                                                }`}
                                        >
                                            <PenLine className="w-3 h-3" />
                                            <span className="flex-1">第 {script.script_num} 章</span>
                                            {script.word_count > 0 && (
                                                <span className="text-xs opacity-70">
                                                    {(script.word_count / 1000).toFixed(1)}k
                                                </span>
                                            )}
                                        </div>
                                    ))}

                                    {/* 添加章节按钮 */}
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        className="w-full justify-start text-muted-foreground h-8"
                                        onClick={() => onAddChapter(vol.vol_num)}
                                    >
                                        <Plus className="w-3 h-3 mr-2" />
                                        添加章节
                                    </Button>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </ScrollArea>
        </div>
    );
}

// ============ 主组件：写作工作室 ============
export default function WritingStudio() {
    const { projectId } = useParams();
    const [structure, setStructure] = useState(null);
    const [selectedId, setSelectedId] = useState({ type: 'master' });
    const [loading, setLoading] = useState(true);

    // 编辑器状态
    const [outlineContent, setOutlineContent] = useState('');
    const [chapterContent, setChapterContent] = useState('');
    const [contentLoading, setContentLoading] = useState(false);
    const [autoSaveStatus, setAutoSaveStatus] = useState('saved');
    const [generating, setGenerating] = useState(false);

    // UI 状态
    const [showPreview, setShowPreview] = useState(false);
    const [showSearch, setShowSearch] = useState(false);

    // 撤销/重做
    const [history, setHistory] = useState([]);
    const [historyIndex, setHistoryIndex] = useState(-1);

    // 自动保存计时器
    const saveTimerRef = useRef(null);

    // 加载结构
    useEffect(() => {
        async function fetchStructure() {
            try {
                const { data } = await client.get(`/api/project/${projectId}/structure`);
                setStructure(data);
            } catch (e) {
                toast.error('加载失败: ' + e.message);
            } finally {
                setLoading(false);
            }
        }
        if (projectId) fetchStructure();
    }, [projectId]);

    // 加载选中内容
    useEffect(() => {
        async function loadContent() {
            if (!selectedId || !structure) return;
            setContentLoading(true);

            try {
                if (selectedId.type === 'master') {
                    setOutlineContent(structure.master_outline || '');
                    setChapterContent('');
                } else if (selectedId.type === 'volume' || selectedId.type === 'volume_outline') {
                    const vol = structure.volumes?.find(v => v.vol_num === selectedId.volNum);
                    setOutlineContent(vol?.content || '');
                    setChapterContent('');
                } else if (selectedId.type === 'chapter') {
                    // 章节：同时加载章纲和正文
                    const vol = structure.volumes?.find(v => v.vol_num === selectedId.volNum);
                    const script = vol?.scripts?.find(s => s.script_num === selectedId.chapterNum);
                    setOutlineContent(script?.content || '');

                    // 加载正文
                    try {
                        const { data } = await client.get(`/api/project/${projectId}/chapter/${selectedId.chapterNum}`);
                        setChapterContent(data.content || '');
                    } catch {
                        setChapterContent('');
                    }
                }

                // 重置历史
                setHistory([]);
                setHistoryIndex(-1);
            } catch (e) {
                console.error(e);
            } finally {
                setContentLoading(false);
                setAutoSaveStatus('saved');
            }
        }
        loadContent();
    }, [selectedId, projectId]);

    // 自动保存
    const autoSave = useCallback(async () => {
        if (!selectedId) return;
        setAutoSaveStatus('saving');

        try {
            // 保存大纲
            if (selectedId.type === 'master') {
                await client.post(`/api/project/${projectId}/structure/node`, {
                    type: 'master', content: outlineContent
                });
            } else if (selectedId.type === 'volume' || selectedId.type === 'volume_outline') {
                const vol = structure?.volumes?.find(v => v.vol_num === selectedId.volNum);
                await client.post(`/api/project/${projectId}/structure/node`, {
                    type: 'volume', filename: vol?.filename, content: outlineContent
                });
            } else if (selectedId.type === 'chapter') {
                const vol = structure?.volumes?.find(v => v.vol_num === selectedId.volNum);
                const script = vol?.scripts?.find(s => s.script_num === selectedId.chapterNum);

                // 保存章纲
                await client.post(`/api/project/${projectId}/structure/node`, {
                    type: 'script', filename: script?.filename, content: outlineContent
                });

                // 保存正文
                if (chapterContent) {
                    await client.post(`/api/project/${projectId}/chapter/${selectedId.chapterNum}`, {
                        content: chapterContent
                    });
                }
            }

            setAutoSaveStatus('saved');
        } catch (e) {
            toast.error('保存失败');
            setAutoSaveStatus('unsaved');
        }
    }, [selectedId, projectId, outlineContent, chapterContent, structure]);

    // 防抖保存
    const scheduleAutoSave = useCallback(() => {
        setAutoSaveStatus('unsaved');
        if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
        saveTimerRef.current = setTimeout(autoSave, 2000);
    }, [autoSave]);

    // 内容变更处理
    const handleOutlineChange = (value) => {
        // 记录历史
        setHistory(prev => [...prev.slice(0, historyIndex + 1), { outline: outlineContent, chapter: chapterContent }]);
        setHistoryIndex(prev => prev + 1);

        setOutlineContent(value);
        scheduleAutoSave();
    };

    const handleChapterChange = (value) => {
        setHistory(prev => [...prev.slice(0, historyIndex + 1), { outline: outlineContent, chapter: chapterContent }]);
        setHistoryIndex(prev => prev + 1);

        setChapterContent(value);
        scheduleAutoSave();
    };

    // 撤销/重做
    const undo = useCallback(() => {
        if (historyIndex >= 0) {
            const prev = history[historyIndex];
            setOutlineContent(prev.outline);
            setChapterContent(prev.chapter);
            setHistoryIndex(i => i - 1);
        }
    }, [history, historyIndex]);

    const redo = useCallback(() => {
        if (historyIndex < history.length - 1) {
            const next = history[historyIndex + 1];
            setOutlineContent(next.outline);
            setChapterContent(next.chapter);
            setHistoryIndex(i => i + 1);
        }
    }, [history, historyIndex]);

    // AI 生成
    const handleGenerate = async () => {
        if (selectedId?.type !== 'chapter') {
            toast.error('请先选择一个章节');
            return;
        }
        if (!outlineContent.trim()) {
            toast.error('请先填写章纲');
            return;
        }

        setGenerating(true);
        setChapterContent('');

        try {
            const { data } = await client.post('/api/generate/stream', {
                project: projectId,
                stage: 'content',
                params: { outline: outlineContent, chapter_num: selectedId.chapterNum }
            });

            if (data.queue_id) {
                const eventSource = new EventSource(`/api/generate/progress/${data.queue_id}`);

                eventSource.onmessage = (event) => {
                    const msg = JSON.parse(event.data);
                    if (msg.type === 'chunk') {
                        setChapterContent(prev => prev + msg.content);
                    } else if (msg.type === 'complete') {
                        toast.success(`生成完成，共 ${msg.word_count} 字`);
                        eventSource.close();
                        setGenerating(false);
                    } else if (msg.type === 'error' || msg.type === 'done') {
                        eventSource.close();
                        setGenerating(false);
                    }
                };

                eventSource.onerror = () => {
                    eventSource.close();
                    setGenerating(false);
                };
            }
        } catch (e) {
            toast.error('生成失败: ' + e.message);
            setGenerating(false);
        }
    };

    // 添加卷
    const handleAddVolume = async () => {
        try {
            await client.post(`/api/project/${projectId}/structure/node`, {
                type: 'volume'
            });
            toast.success('已创建新卷');
            const { data } = await client.get(`/api/project/${projectId}/structure`);
            setStructure(data);
        } catch (e) {
            toast.error('创建失败: ' + (e.response?.data?.error || e.message));
        }
    };

    // 添加章节
    const handleAddChapter = async (volNum) => {
        try {
            await client.post(`/api/project/${projectId}/structure/node`, {
                type: 'script',
                vol_num: volNum
            });
            toast.success('已添加章节');
            const { data } = await client.get(`/api/project/${projectId}/structure`);
            setStructure(data);
        } catch (e) {
            toast.error('创建失败: ' + (e.response?.data?.error || e.message));
        }
    };

    // 快捷键
    useKeyboardShortcuts({
        save: () => autoSave(),
        undo: () => undo(),
        redo: () => redo(),
        search: () => setShowSearch(true),
        generate: () => handleGenerate(),
        close: () => setShowSearch(false),
    });

    // 搜索替换回调
    const handleSearchReplace = (newContent) => {
        if (selectedId?.type === 'chapter') {
            setChapterContent(newContent);
        } else {
            setOutlineContent(newContent);
        }
        scheduleAutoSave();
    };

    if (loading) {
        return (
            <div className="h-full flex">
                <div className="w-64 border-r p-4 space-y-3">
                    <Skeleton className="h-8 w-full" />
                    <Skeleton className="h-6 w-3/4" />
                    <Skeleton className="h-6 w-1/2" />
                </div>
                <div className="flex-1 p-8">
                    <Skeleton className="h-full w-full" />
                </div>
            </div>
        );
    }

    const isChapterMode = selectedId?.type === 'chapter';
    const wordCount = isChapterMode ? chapterContent.length : outlineContent.length;

    return (
        <div className="h-full flex bg-background">
            {/* 左侧结构树 */}
            <div className="w-64 border-r bg-card shrink-0">
                <StructureTree
                    structure={structure}
                    selectedId={selectedId}
                    onSelect={setSelectedId}
                    onAddVolume={handleAddVolume}
                    onAddChapter={handleAddChapter}
                />
            </div>

            {/* 右侧编辑区 */}
            <div className="flex-1 flex flex-col min-w-0 relative">
                {/* 工具栏 */}
                <div className="px-4 py-2 border-b flex items-center gap-2 bg-card">
                    <span className="font-medium text-sm">
                        {selectedId?.type === 'master' && '总纲'}
                        {selectedId?.type === 'volume' && `第 ${selectedId.volNum} 卷`}
                        {selectedId?.type === 'volume_outline' && `第 ${selectedId.volNum} 卷 - 粗纲`}
                        {selectedId?.type === 'chapter' && `第 ${selectedId.volNum} 卷 第 ${selectedId.chapterNum} 章`}
                    </span>

                    {/* 保存状态 */}
                    <Badge variant={autoSaveStatus === 'saved' ? 'outline' : 'secondary'} className="gap-1 text-xs">
                        {autoSaveStatus === 'saving' && <Loader2 className="w-3 h-3 animate-spin" />}
                        {autoSaveStatus === 'saved' && <Check className="w-3 h-3" />}
                        {autoSaveStatus === 'unsaved' && <RotateCcw className="w-3 h-3" />}
                        {autoSaveStatus === 'saving' ? '保存中' : autoSaveStatus === 'saved' ? '已保存' : '未保存'}
                    </Badge>

                    <div className="flex-1" />

                    {/* 字数 */}
                    <span className="text-xs text-muted-foreground">{wordCount} 字</span>

                    {/* 操作按钮 */}
                    <Button size="sm" variant="ghost" onClick={undo} disabled={historyIndex < 0}>
                        <Undo2 className="w-4 h-4" />
                    </Button>
                    <Button size="sm" variant="ghost" onClick={redo} disabled={historyIndex >= history.length - 1}>
                        <Redo2 className="w-4 h-4" />
                    </Button>
                    <Button size="sm" variant="ghost" onClick={() => setShowSearch(!showSearch)}>
                        <Search className="w-4 h-4" />
                    </Button>

                    {isChapterMode && (
                        <>
                            <Button size="sm" variant="ghost" onClick={() => setShowPreview(!showPreview)}>
                                {showPreview ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                            </Button>
                            <Button size="sm" onClick={handleGenerate} disabled={generating}>
                                {generating ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <Wand2 className="w-4 h-4 mr-1" />}
                                AI 生成
                            </Button>
                        </>
                    )}

                    <Button size="sm" variant="outline" onClick={autoSave}>
                        <Save className="w-4 h-4 mr-1" />
                        保存
                    </Button>
                </div>

                {/* 搜索替换面板 */}
                <SearchReplace
                    isOpen={showSearch}
                    onClose={() => setShowSearch(false)}
                    content={isChapterMode ? chapterContent : outlineContent}
                    onReplace={handleSearchReplace}
                />

                {/* 编辑区域 */}
                {contentLoading ? (
                    <div className="flex-1 p-4">
                        <Skeleton className="h-full w-full" />
                    </div>
                ) : (
                    <div className={`flex-1 flex min-h-0 ${isChapterMode ? 'divide-x' : ''}`}>
                        {/* 大纲/章纲编辑 */}
                        <div className={`flex flex-col ${isChapterMode ? 'w-1/3' : 'flex-1'}`}>
                            <div className="px-4 py-2 bg-muted/30 text-xs font-medium border-b flex items-center gap-2">
                                <AlignLeft className="w-3 h-3" />
                                {isChapterMode ? '章纲 / 细纲' : '大纲内容'}
                            </div>
                            <Textarea
                                value={outlineContent}
                                onChange={(e) => handleOutlineChange(e.target.value)}
                                placeholder={isChapterMode ? '在此输入本章的详细大纲，AI 将根据此生成正文...' : '在此输入大纲内容...'}
                                className="flex-1 resize-none rounded-none border-0 focus-visible:ring-0 font-mono text-sm leading-relaxed p-4"
                            />
                        </div>

                        {/* 正文编辑 (仅章节) */}
                        {isChapterMode && (
                            <div className="flex-1 flex flex-col">
                                <div className="px-4 py-2 bg-muted/30 text-xs font-medium border-b flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <PenLine className="w-3 h-3" />
                                        正文内容
                                    </div>
                                    {generating && (
                                        <Badge className="animate-pulse gap-1">
                                            <Sparkles className="w-3 h-3" />
                                            生成中...
                                        </Badge>
                                    )}
                                </div>
                                <Textarea
                                    value={chapterContent}
                                    onChange={(e) => handleChapterChange(e.target.value)}
                                    placeholder="正文内容，可由 AI 根据章纲自动生成..."
                                    className="flex-1 resize-none rounded-none border-0 focus-visible:ring-0 text-base leading-relaxed p-4"
                                    disabled={generating}
                                />
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

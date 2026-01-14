import React, { useEffect, useState, useCallback, useRef } from 'react';
import { useParams } from 'react-router-dom';
import client from '@/api/client';
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { toast } from "sonner";
import {
    ChevronRight, ChevronDown, FileText, BookOpen, Loader2, Save,
    Sparkles, Plus, FolderOpen, File, Wand2, RotateCcw, Check
} from 'lucide-react';

// ============ 章节树组件 ============
function ChapterTree({ structure, selectedId, onSelect }) {
    const [expandedVolumes, setExpandedVolumes] = useState(new Set([1]));

    const toggleVolume = (volNum) => {
        setExpandedVolumes(prev => {
            const next = new Set(prev);
            if (next.has(volNum)) next.delete(volNum);
            else next.add(volNum);
            return next;
        });
    };

    return (
        <ScrollArea className="h-full">
            <div className="p-4 space-y-1">
                {/* 总纲 */}
                <div
                    onClick={() => onSelect({ type: 'master' })}
                    className={`flex items-center gap-2 px-3 py-2 rounded-md cursor-pointer transition-colors ${selectedId?.type === 'master'
                            ? 'bg-primary/10 text-primary'
                            : 'hover:bg-muted'
                        }`}
                >
                    <BookOpen className="w-4 h-4" />
                    <span className="font-medium">总纲</span>
                </div>

                {/* 分卷 */}
                {structure?.volumes?.map((vol) => (
                    <div key={vol.vol_num}>
                        {/* 卷头 */}
                        <div
                            onClick={() => toggleVolume(vol.vol_num)}
                            className="flex items-center gap-2 px-3 py-2 rounded-md cursor-pointer hover:bg-muted"
                        >
                            {expandedVolumes.has(vol.vol_num)
                                ? <ChevronDown className="w-4 h-4" />
                                : <ChevronRight className="w-4 h-4" />
                            }
                            <FolderOpen className="w-4 h-4" />
                            <span>第 {vol.vol_num} 卷</span>
                            <Badge variant="outline" className="ml-auto text-xs">
                                {vol.scripts?.length || 0} 章
                            </Badge>
                        </div>

                        {/* 卷纲 */}
                        {expandedVolumes.has(vol.vol_num) && (
                            <div className="ml-6 space-y-1">
                                <div
                                    onClick={() => onSelect({ type: 'volume', volNum: vol.vol_num })}
                                    className={`flex items-center gap-2 px-3 py-1.5 rounded-md cursor-pointer text-sm ${selectedId?.type === 'volume' && selectedId?.volNum === vol.vol_num
                                            ? 'bg-primary/10 text-primary'
                                            : 'hover:bg-muted text-muted-foreground'
                                        }`}
                                >
                                    <FileText className="w-3 h-3" />
                                    <span>卷纲</span>
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
                                        className={`flex items-center gap-2 px-3 py-1.5 rounded-md cursor-pointer text-sm ${selectedId?.type === 'chapter' &&
                                                selectedId?.volNum === vol.vol_num &&
                                                selectedId?.chapterNum === script.script_num
                                                ? 'bg-primary/10 text-primary'
                                                : 'hover:bg-muted text-muted-foreground'
                                            }`}
                                    >
                                        <File className="w-3 h-3" />
                                        <span>第 {script.script_num} 章</span>
                                        {script.word_count > 0 && (
                                            <span className="ml-auto text-xs opacity-50">
                                                {script.word_count}字
                                            </span>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </ScrollArea>
    );
}

// ============ 联合编辑器 (章纲+正文) ============
function UnifiedEditor({
    projectId,
    selectedId,
    structure,
    onStructureChange
}) {
    const [outlineContent, setOutlineContent] = useState('');
    const [chapterContent, setChapterContent] = useState('');
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [generating, setGenerating] = useState(false);
    const [autoSaveStatus, setAutoSaveStatus] = useState('saved'); // 'saved', 'saving', 'unsaved'

    // 自动保存 Refs
    const outlineTimerRef = useRef(null);
    const chapterTimerRef = useRef(null);

    // 加载内容
    useEffect(() => {
        async function loadContent() {
            if (!selectedId) return;
            setLoading(true);

            try {
                if (selectedId.type === 'master') {
                    setOutlineContent(structure?.master_outline || '');
                    setChapterContent('');
                } else if (selectedId.type === 'volume') {
                    const vol = structure?.volumes?.find(v => v.vol_num === selectedId.volNum);
                    setOutlineContent(vol?.content || '');
                    setChapterContent('');
                } else if (selectedId.type === 'chapter') {
                    // 同时加载章纲和正文
                    const vol = structure?.volumes?.find(v => v.vol_num === selectedId.volNum);
                    const script = vol?.scripts?.find(s => s.script_num === selectedId.chapterNum);
                    setOutlineContent(script?.content || '');

                    // 加载正文
                    try {
                        const { data } = await client.get(
                            `/api/project/${projectId}/chapter/${selectedId.chapterNum}`
                        );
                        setChapterContent(data.content || '');
                    } catch (e) {
                        setChapterContent('');
                    }
                }
            } catch (e) {
                console.error(e);
            } finally {
                setLoading(false);
                setAutoSaveStatus('saved');
            }
        }
        loadContent();
    }, [selectedId, projectId]);

    // 自动保存函数
    const autoSaveOutline = useCallback(async (content) => {
        if (!selectedId) return;
        setAutoSaveStatus('saving');

        try {
            if (selectedId.type === 'master') {
                await client.post(`/api/project/${projectId}/structure/node`, {
                    type: 'master',
                    content
                });
            } else if (selectedId.type === 'volume') {
                const vol = structure?.volumes?.find(v => v.vol_num === selectedId.volNum);
                await client.post(`/api/project/${projectId}/structure/node`, {
                    type: 'volume',
                    filename: vol?.filename,
                    content
                });
            } else if (selectedId.type === 'chapter') {
                const vol = structure?.volumes?.find(v => v.vol_num === selectedId.volNum);
                const script = vol?.scripts?.find(s => s.script_num === selectedId.chapterNum);
                await client.post(`/api/project/${projectId}/structure/node`, {
                    type: 'script',
                    filename: script?.filename,
                    content
                });
            }
            setAutoSaveStatus('saved');
        } catch (e) {
            toast.error('自动保存失败');
            setAutoSaveStatus('unsaved');
        }
    }, [selectedId, projectId, structure]);

    const autoSaveChapter = useCallback(async (content) => {
        if (!selectedId || selectedId.type !== 'chapter') return;
        setAutoSaveStatus('saving');

        try {
            await client.post(`/api/project/${projectId}/chapter/${selectedId.chapterNum}`, {
                content
            });
            setAutoSaveStatus('saved');
        } catch (e) {
            toast.error('自动保存失败');
            setAutoSaveStatus('unsaved');
        }
    }, [selectedId, projectId]);

    // 处理纲要变化 (防抖自动保存)
    const handleOutlineChange = (value) => {
        setOutlineContent(value);
        setAutoSaveStatus('unsaved');

        if (outlineTimerRef.current) clearTimeout(outlineTimerRef.current);
        outlineTimerRef.current = setTimeout(() => {
            autoSaveOutline(value);
        }, 3000);
    };

    // 处理正文变化 (防抖自动保存)
    const handleChapterChange = (value) => {
        setChapterContent(value);
        setAutoSaveStatus('unsaved');

        if (chapterTimerRef.current) clearTimeout(chapterTimerRef.current);
        chapterTimerRef.current = setTimeout(() => {
            autoSaveChapter(value);
        }, 3000);
    };

    // AI 生成正文 (流式)
    const handleGenerateChapter = async () => {
        if (!outlineContent.trim()) {
            toast.error('请先填写章纲');
            return;
        }

        setGenerating(true);
        setChapterContent(''); // 清空准备流式填充

        try {
            // 创建流式任务
            const { data } = await client.post('/api/generate/stream', {
                project: projectId,
                stage: 'content',
                params: {
                    outline: outlineContent,
                    chapter_num: selectedId.chapterNum
                }
            });

            if (data.queue_id) {
                // 连接 SSE
                const eventSource = new EventSource(`/api/generate/progress/${data.queue_id}`);

                eventSource.onmessage = (event) => {
                    const msg = JSON.parse(event.data);

                    if (msg.type === 'chunk') {
                        setChapterContent(prev => prev + msg.content);
                    } else if (msg.type === 'complete') {
                        toast.success(`生成完成，共 ${msg.word_count} 字`);
                        eventSource.close();
                        setGenerating(false);
                        // 保存
                        autoSaveChapter(msg.content);
                    } else if (msg.type === 'error') {
                        toast.error(msg.message);
                        eventSource.close();
                        setGenerating(false);
                    } else if (msg.type === 'done') {
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

    // 手动保存
    const handleManualSave = async () => {
        setSaving(true);
        await autoSaveOutline(outlineContent);
        if (selectedId?.type === 'chapter') {
            await autoSaveChapter(chapterContent);
        }
        setSaving(false);
        toast.success('保存成功');
    };

    if (loading) {
        return (
            <div className="h-full flex items-center justify-center">
                <Loader2 className="animate-spin w-8 h-8 text-muted-foreground" />
            </div>
        );
    }

    const isChapter = selectedId?.type === 'chapter';
    const wordCount = chapterContent.length;
    const outlineWordCount = outlineContent.length;

    return (
        <div className="h-full flex flex-col">
            {/* 工具栏 */}
            <div className="px-4 py-3 border-b flex items-center justify-between bg-card">
                <div className="flex items-center gap-2">
                    <span className="font-medium">
                        {selectedId?.type === 'master' && '总纲'}
                        {selectedId?.type === 'volume' && `第 ${selectedId.volNum} 卷 - 卷纲`}
                        {selectedId?.type === 'chapter' && `第 ${selectedId.volNum} 卷 - 第 ${selectedId.chapterNum} 章`}
                    </span>

                    {/* 保存状态 */}
                    <Badge variant={autoSaveStatus === 'saved' ? 'outline' : 'secondary'} className="gap-1">
                        {autoSaveStatus === 'saving' && <Loader2 className="w-3 h-3 animate-spin" />}
                        {autoSaveStatus === 'saved' && <Check className="w-3 h-3" />}
                        {autoSaveStatus === 'unsaved' && <RotateCcw className="w-3 h-3" />}
                        {autoSaveStatus === 'saving' ? '保存中...' : autoSaveStatus === 'saved' ? '已保存' : '未保存'}
                    </Badge>
                </div>

                <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">
                        {isChapter ? `正文 ${wordCount} 字` : `${outlineWordCount} 字`}
                    </span>

                    <Button size="sm" variant="outline" onClick={handleManualSave} disabled={saving}>
                        <Save className="w-4 h-4 mr-1" />
                        保存
                    </Button>

                    {isChapter && (
                        <Button size="sm" onClick={handleGenerateChapter} disabled={generating}>
                            {generating ? (
                                <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                            ) : (
                                <Wand2 className="w-4 h-4 mr-1" />
                            )}
                            AI 生成
                        </Button>
                    )}
                </div>
            </div>

            {/* 编辑区域 */}
            <div className={`flex-1 overflow-hidden ${isChapter ? 'grid grid-cols-2' : ''}`}>
                {/* 纲要编辑 */}
                <div className={`flex flex-col ${isChapter ? 'border-r' : 'h-full'}`}>
                    <div className="px-4 py-2 border-b bg-muted/30 text-sm font-medium">
                        {selectedId?.type === 'master' && '总纲内容'}
                        {selectedId?.type === 'volume' && '粗纲 / 卷纲'}
                        {selectedId?.type === 'chapter' && '章纲 / 细纲'}
                    </div>
                    <Textarea
                        value={outlineContent}
                        onChange={(e) => handleOutlineChange(e.target.value)}
                        placeholder="在此输入纲要内容..."
                        className="flex-1 resize-none rounded-none border-0 focus-visible:ring-0 font-mono text-sm"
                    />
                </div>

                {/* 正文编辑 (仅章节) */}
                {isChapter && (
                    <div className="flex flex-col">
                        <div className="px-4 py-2 border-b bg-muted/30 text-sm font-medium flex items-center justify-between">
                            <span>正文内容</span>
                            {generating && (
                                <Badge className="animate-pulse">
                                    <Sparkles className="w-3 h-3 mr-1" />
                                    AI 生成中...
                                </Badge>
                            )}
                        </div>
                        <Textarea
                            value={chapterContent}
                            onChange={(e) => handleChapterChange(e.target.value)}
                            placeholder="在此输入或由 AI 生成正文..."
                            className="flex-1 resize-none rounded-none border-0 focus-visible:ring-0"
                            disabled={generating}
                        />
                    </div>
                )}
            </div>
        </div>
    );
}

// ============ 主组件 ============
export default function Editor() {
    const { projectId } = useParams();
    const [structure, setStructure] = useState(null);
    const [selectedId, setSelectedId] = useState({ type: 'master' });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchStructure() {
            try {
                const { data } = await client.get(`/api/project/${projectId}/structure`);
                setStructure(data);
            } catch (e) {
                console.error(e);
            } finally {
                setLoading(false);
            }
        }
        if (projectId) fetchStructure();
    }, [projectId]);

    if (loading) {
        return (
            <div className="h-full flex items-center justify-center">
                <Loader2 className="animate-spin w-8 h-8 text-muted-foreground" />
            </div>
        );
    }

    return (
        <div className="h-full flex">
            {/* 左侧: 章节树 */}
            <div className="w-64 border-r bg-card">
                <div className="px-4 py-3 border-b font-medium flex items-center gap-2">
                    <BookOpen className="w-4 h-4" />
                    章节大纲
                </div>
                <ChapterTree
                    structure={structure}
                    selectedId={selectedId}
                    onSelect={setSelectedId}
                />
            </div>

            {/* 右侧: 统一编辑器 */}
            <div className="flex-1">
                <UnifiedEditor
                    projectId={projectId}
                    selectedId={selectedId}
                    structure={structure}
                    onStructureChange={setStructure}
                />
            </div>
        </div>
    );
}

import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import client from '@/api/client';
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { Zap, Play, Pause, Square, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';

export default function BatchGenerate() {
    const { projectId } = useParams();
    const [config, setConfig] = useState({
        startChapter: 1,
        count: 5
    });
    const [isRunning, setIsRunning] = useState(false);
    const [progress, setProgress] = useState({ current: 0, total: 0, status: '' });
    const [logs, setLogs] = useState([]);
    const eventSourceRef = useRef(null);

    const addLog = (message, type = 'info') => {
        setLogs(prev => [...prev, { message, type, time: new Date().toLocaleTimeString() }]);
    };

    const handleStart = async () => {
        setIsRunning(true);
        setLogs([]);
        setProgress({ current: 0, total: config.count, status: '初始化中...' });
        addLog(`开始批量生成: 从第 ${config.startChapter} 章开始，共 ${config.count} 章`);

        try {
            // 创建批量任务
            const { data } = await client.post('/api/batch/create', {
                project: projectId,
                start_chapter: config.startChapter,
                count: config.count
            });

            if (data.task_id) {
                addLog(`任务创建成功: ${data.task_id}`, 'success');

                // 连接 SSE 获取进度
                connectSSE(data.task_id);
            }
        } catch (err) {
            addLog(`任务创建失败: ${err.response?.data?.error || err.message}`, 'error');
            setIsRunning(false);
        }
    };

    const connectSSE = (taskId) => {
        const eventSource = new EventSource(`/api/batch/progress/${taskId}`);
        eventSourceRef.current = eventSource;

        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);

            switch (data.type) {
                case 'progress':
                    setProgress({
                        current: data.current,
                        total: data.total,
                        status: data.message
                    });
                    addLog(data.message);
                    break;
                case 'complete':
                    addLog(`第 ${data.chapter} 章生成完成`, 'success');
                    break;
                case 'done':
                    addLog('批量生成完成！', 'success');
                    setIsRunning(false);
                    eventSource.close();
                    break;
                case 'error':
                    addLog(`错误: ${data.message}`, 'error');
                    setIsRunning(false);
                    eventSource.close();
                    break;
            }
        };

        eventSource.onerror = () => {
            addLog('连接断开', 'error');
            setIsRunning(false);
            eventSource.close();
        };
    };

    const handleStop = () => {
        if (eventSourceRef.current) {
            eventSourceRef.current.close();
        }
        setIsRunning(false);
        addLog('已停止生成', 'warning');
    };

    useEffect(() => {
        return () => {
            if (eventSourceRef.current) {
                eventSourceRef.current.close();
            }
        };
    }, []);

    const progressPercent = progress.total > 0
        ? Math.round((progress.current / progress.total) * 100)
        : 0;

    return (
        <div className="h-full flex flex-col bg-background">
            {/* Header */}
            <div className="px-8 py-6 border-b flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-primary/10 rounded-lg text-primary">
                        <Zap className="w-6 h-6" />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold">批量生成 (Batch)</h1>
                        <p className="text-muted-foreground text-sm">自动连续生成多个章节</p>
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-8">
                <div className="max-w-3xl mx-auto space-y-6">

                    {/* Config */}
                    <Card>
                        <CardHeader>
                            <CardTitle>生成配置</CardTitle>
                            <CardDescription>设置批量生成的参数</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label>起始章节</Label>
                                    <Input
                                        type="number"
                                        min={1}
                                        value={config.startChapter}
                                        onChange={e => setConfig(prev => ({ ...prev, startChapter: parseInt(e.target.value) || 1 }))}
                                        disabled={isRunning}
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label>生成数量</Label>
                                    <Input
                                        type="number"
                                        min={1}
                                        max={50}
                                        value={config.count}
                                        onChange={e => setConfig(prev => ({ ...prev, count: parseInt(e.target.value) || 1 }))}
                                        disabled={isRunning}
                                    />
                                </div>
                            </div>

                            <div className="flex gap-2 pt-4">
                                {!isRunning ? (
                                    <Button onClick={handleStart} className="flex-1 gap-2">
                                        <Play className="w-4 h-4" />
                                        开始生成
                                    </Button>
                                ) : (
                                    <Button onClick={handleStop} variant="destructive" className="flex-1 gap-2">
                                        <Square className="w-4 h-4" />
                                        停止
                                    </Button>
                                )}
                            </div>
                        </CardContent>
                    </Card>

                    {/* Progress */}
                    {(isRunning || progress.current > 0) && (
                        <Card>
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    {isRunning && <Loader2 className="w-4 h-4 animate-spin" />}
                                    生成进度
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="space-y-2">
                                    <div className="flex justify-between text-sm">
                                        <span>{progress.status}</span>
                                        <span>{progress.current} / {progress.total}</span>
                                    </div>
                                    <Progress value={progressPercent} />
                                </div>
                            </CardContent>
                        </Card>
                    )}

                    {/* Logs */}
                    {logs.length > 0 && (
                        <Card>
                            <CardHeader>
                                <CardTitle>日志</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="bg-muted rounded-lg p-4 max-h-64 overflow-y-auto font-mono text-sm space-y-1">
                                    {logs.map((log, idx) => (
                                        <div key={idx} className={`flex items-start gap-2 ${log.type === 'error' ? 'text-destructive' :
                                                log.type === 'success' ? 'text-green-500' :
                                                    log.type === 'warning' ? 'text-yellow-500' :
                                                        'text-muted-foreground'
                                            }`}>
                                            <span className="text-xs opacity-50">[{log.time}]</span>
                                            {log.type === 'success' && <CheckCircle2 className="w-4 h-4 mt-0.5" />}
                                            {log.type === 'error' && <AlertCircle className="w-4 h-4 mt-0.5" />}
                                            <span>{log.message}</span>
                                        </div>
                                    ))}
                                </div>
                            </CardContent>
                        </Card>
                    )}
                </div>
            </div>
        </div>
    );
}

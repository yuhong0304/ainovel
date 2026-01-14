import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import client from '@/api/client';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import useProjectStore from '@/store/useProjectStore';
import {
    BookOpen,
    PenTool,
    FileText,
    Coins,
    ArrowRight,
    Zap,
    Download,
    TrendingUp,
    Clock,
    Calendar,
    History,
    BarChart3
} from 'lucide-react';

// 简易柱状图组件
function MiniBarChart({ data }) {
    if (!data || data.length === 0) {
        return <div className="h-32 flex items-center justify-center text-muted-foreground text-sm">暂无数据</div>;
    }

    const maxValue = Math.max(...data.map(d => d.words));

    return (
        <div className="h-32 flex items-end gap-1">
            {data.slice(-14).map((d, idx) => {
                const height = maxValue > 0 ? (d.words / maxValue) * 100 : 0;
                const date = new Date(d.date);
                const dayLabel = date.getDate();

                return (
                    <div key={idx} className="flex-1 flex flex-col items-center gap-1">
                        <div
                            className="w-full bg-primary/80 rounded-t transition-all hover:bg-primary"
                            style={{ height: `${height}%`, minHeight: d.words > 0 ? '4px' : '0' }}
                            title={`${d.date}: ${d.words.toLocaleString()} 字`}
                        />
                        <span className="text-[10px] text-muted-foreground">{dayLabel}</span>
                    </div>
                );
            })}
        </div>
    );
}

export default function Dashboard() {
    const { projectId } = useParams();
    const navigate = useNavigate();
    const { currentProject } = useProjectStore();
    const [stats, setStats] = useState(null);
    const [dailyStats, setDailyStats] = useState([]);
    const [recentEdits, setRecentEdits] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchData() {
            try {
                const [statsRes, dailyRes, recentRes] = await Promise.all([
                    client.get(`/api/statistics/${projectId}`),
                    client.get(`/api/statistics/${projectId}/daily`),
                    client.get(`/api/statistics/${projectId}/recent`)
                ]);
                setStats(statsRes.data);
                setDailyStats(dailyRes.data.daily || []);
                setRecentEdits(recentRes.data.recent || []);
            } catch (e) {
                console.error(e);
            } finally {
                setLoading(false);
            }
        }
        if (projectId) fetchData();
    }, [projectId]);

    const quickActions = [
        {
            title: '继续写作',
            desc: '进入写作工作室',
            icon: PenTool,
            path: 'write',
            color: 'text-blue-500',
            bg: 'bg-blue-500/10'
        },
        {
            title: '批量生成',
            desc: 'AI 自动写作',
            icon: Zap,
            path: 'batch',
            color: 'text-yellow-500',
            bg: 'bg-yellow-500/10'
        },
        {
            title: '世界设定',
            desc: '管理角色地点',
            icon: BookOpen,
            path: 'world',
            color: 'text-green-500',
            bg: 'bg-green-500/10'
        },
        {
            title: '导出小说',
            desc: '下载成品',
            icon: Download,
            path: 'export',
            color: 'text-purple-500',
            bg: 'bg-purple-500/10'
        },
    ];

    const statCards = [
        {
            title: '当前进度',
            value: `第 ${currentProject?.current_volume || 1} 卷`,
            sub: `第 ${currentProject?.current_chapter || 1} 章`,
            icon: BookOpen,
            color: 'text-blue-500'
        },
        {
            title: '总字数',
            value: stats?.total_words?.toLocaleString() || '0',
            sub: '字',
            icon: FileText,
            color: 'text-green-500'
        },
        {
            title: 'Token 消耗',
            value: stats?.total_tokens?.toLocaleString() || '0',
            sub: 'tokens',
            icon: Coins,
            color: 'text-yellow-500'
        },
        {
            title: '预估成本',
            value: `$${stats?.estimated_cost?.toFixed(3) || '0.00'}`,
            sub: 'USD',
            icon: TrendingUp,
            color: 'text-purple-500'
        },
    ];

    // 计算写作进度
    const targetWords = currentProject?.target_words || 200000;
    const currentWords = stats?.total_words || 0;
    const progressPercent = Math.min(100, Math.round((currentWords / targetWords) * 100));

    // 格式化时间
    const formatTime = (isoStr) => {
        const date = new Date(isoStr);
        const now = new Date();
        const diff = now - date;

        if (diff < 60000) return '刚刚';
        if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`;
        if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`;
        return date.toLocaleDateString();
    };

    if (loading) {
        return (
            <div className="p-8 space-y-6">
                <Skeleton className="h-10 w-64" />
                <Skeleton className="h-32 w-full" />
                <div className="grid grid-cols-4 gap-4">
                    {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-24" />)}
                </div>
            </div>
        );
    }

    return (
        <div className="p-8 space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold tracking-tight">
                    {currentProject?.title || currentProject?.name || '项目概览'}
                </h1>
                <p className="text-muted-foreground mt-1">
                    {currentProject?.genre || '欢迎回来，继续你的创作之旅'}
                </p>
            </div>

            {/* Progress + Daily Chart */}
            <div className="grid gap-6 lg:grid-cols-2">
                {/* Progress Card */}
                <Card className="bg-gradient-to-br from-primary/10 via-primary/5 to-transparent border-primary/20">
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between mb-4">
                            <div>
                                <h3 className="font-semibold text-lg">写作进度</h3>
                                <p className="text-sm text-muted-foreground">
                                    目标: {targetWords.toLocaleString()} 字
                                </p>
                            </div>
                            <div className="text-right">
                                <div className="text-3xl font-bold text-primary">{progressPercent}%</div>
                                <p className="text-sm text-muted-foreground">
                                    {currentWords.toLocaleString()} / {targetWords.toLocaleString()}
                                </p>
                            </div>
                        </div>
                        <Progress value={progressPercent} className="h-3" />
                    </CardContent>
                </Card>

                {/* Daily Chart */}
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium flex items-center gap-2">
                            <BarChart3 className="w-4 h-4" />
                            近两周写作趋势
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <MiniBarChart data={dailyStats} />
                    </CardContent>
                </Card>
            </div>

            {/* Stats Grid */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                {statCards.map((stat, idx) => {
                    const Icon = stat.icon;
                    return (
                        <Card key={idx}>
                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                <CardTitle className="text-sm font-medium text-muted-foreground">
                                    {stat.title}
                                </CardTitle>
                                <Icon className={`w-4 h-4 ${stat.color}`} />
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold">{stat.value}</div>
                                <p className="text-xs text-muted-foreground">{stat.sub}</p>
                            </CardContent>
                        </Card>
                    );
                })}
            </div>

            {/* Quick Actions + Recent Edits */}
            <div className="grid gap-6 lg:grid-cols-3">
                {/* Quick Actions */}
                <div className="lg:col-span-2">
                    <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                        <Clock className="w-5 h-5" />
                        快捷操作
                    </h2>
                    <div className="grid gap-4 md:grid-cols-2">
                        {quickActions.map((action, idx) => {
                            const Icon = action.icon;
                            return (
                                <Card
                                    key={idx}
                                    className="cursor-pointer transition-all hover:shadow-lg hover:border-primary/50 group"
                                    onClick={() => navigate(`/project/${projectId}/${action.path}`)}
                                >
                                    <CardContent className="pt-6">
                                        <div className="flex items-center gap-4">
                                            <div className={`p-3 rounded-lg ${action.bg}`}>
                                                <Icon className={`w-5 h-5 ${action.color}`} />
                                            </div>
                                            <div className="flex-1">
                                                <h3 className="font-medium">{action.title}</h3>
                                                <p className="text-sm text-muted-foreground">{action.desc}</p>
                                            </div>
                                            <ArrowRight className="w-4 h-4 text-muted-foreground group-hover:text-primary group-hover:translate-x-1 transition-all" />
                                        </div>
                                    </CardContent>
                                </Card>
                            );
                        })}
                    </div>
                </div>

                {/* Recent Edits */}
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium flex items-center gap-2">
                            <History className="w-4 h-4" />
                            最近编辑
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <ScrollArea className="h-[200px]">
                            <div className="space-y-2">
                                {recentEdits.length === 0 ? (
                                    <p className="text-sm text-muted-foreground text-center py-4">暂无编辑记录</p>
                                ) : (
                                    recentEdits.map((edit, idx) => (
                                        <div key={idx} className="flex items-center gap-2 py-2 border-b border-border/50 last:border-0">
                                            <FileText className="w-4 h-4 text-muted-foreground" />
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm font-medium truncate">{edit.filename}</p>
                                                <p className="text-xs text-muted-foreground">{formatTime(edit.modified)}</p>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </ScrollArea>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}

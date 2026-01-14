import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import client from '@/api/client';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card";
import { BarChart3, FileText, Coins, TrendingUp, Clock, Loader2 } from 'lucide-react';

export default function Statistics() {
    const { projectId } = useParams();
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchStats() {
            try {
                const { data } = await client.get(`/api/statistics/${projectId}`);
                setStats(data);
            } catch (e) {
                console.error(e);
            } finally {
                setLoading(false);
            }
        }
        if (projectId) fetchStats();
    }, [projectId]);

    if (loading) {
        return (
            <div className="h-full flex items-center justify-center">
                <Loader2 className="animate-spin w-8 h-8 text-muted-foreground" />
            </div>
        );
    }

    const statCards = [
        {
            title: '总字数',
            value: stats?.total_words?.toLocaleString() || '0',
            icon: FileText,
            color: 'text-blue-500',
            bgColor: 'bg-blue-500/10'
        },
        {
            title: '章节数',
            value: stats?.chapter_count || '0',
            icon: BarChart3,
            color: 'text-green-500',
            bgColor: 'bg-green-500/10'
        },
        {
            title: 'Token 消耗',
            value: stats?.total_tokens?.toLocaleString() || '0',
            icon: Coins,
            color: 'text-yellow-500',
            bgColor: 'bg-yellow-500/10'
        },
        {
            title: '预估成本',
            value: `$${stats?.estimated_cost?.toFixed(4) || '0.00'}`,
            icon: TrendingUp,
            color: 'text-purple-500',
            bgColor: 'bg-purple-500/10'
        }
    ];

    return (
        <div className="h-full flex flex-col bg-background">
            {/* Header */}
            <div className="px-8 py-6 border-b flex items-center gap-3">
                <div className="p-2 bg-primary/10 rounded-lg text-primary">
                    <BarChart3 className="w-6 h-6" />
                </div>
                <div>
                    <h1 className="text-2xl font-bold">统计分析 (Statistics)</h1>
                    <p className="text-muted-foreground text-sm">查看写作进度和资源消耗</p>
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-8">
                <div className="max-w-4xl mx-auto space-y-6">

                    {/* Stat Cards */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {statCards.map((stat, idx) => {
                            const Icon = stat.icon;
                            return (
                                <Card key={idx}>
                                    <CardContent className="pt-6">
                                        <div className="flex items-center gap-4">
                                            <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                                                <Icon className={`w-5 h-5 ${stat.color}`} />
                                            </div>
                                            <div>
                                                <p className="text-sm text-muted-foreground">{stat.title}</p>
                                                <p className="text-2xl font-bold">{stat.value}</p>
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>
                            );
                        })}
                    </div>

                    {/* Chapter Stats */}
                    <Card>
                        <CardHeader>
                            <CardTitle>章节统计</CardTitle>
                            <CardDescription>各章节字数分布</CardDescription>
                        </CardHeader>
                        <CardContent>
                            {stats?.chapters?.length > 0 ? (
                                <div className="space-y-3">
                                    {stats.chapters.map((chapter, idx) => (
                                        <div key={idx} className="flex items-center gap-4">
                                            <span className="w-20 text-sm text-muted-foreground">
                                                第 {chapter.number} 章
                                            </span>
                                            <div className="flex-1 bg-muted rounded-full h-3 overflow-hidden">
                                                <div
                                                    className="bg-primary h-full rounded-full transition-all"
                                                    style={{
                                                        width: `${Math.min(100, (chapter.words / 5000) * 100)}%`
                                                    }}
                                                />
                                            </div>
                                            <span className="w-20 text-sm text-right">
                                                {chapter.words?.toLocaleString()} 字
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p className="text-muted-foreground text-center py-8">
                                    暂无章节数据
                                </p>
                            )}
                        </CardContent>
                    </Card>

                    {/* Recent Activity */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Clock className="w-4 h-4" />
                                最近活动
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            {stats?.recent_activity?.length > 0 ? (
                                <div className="space-y-2">
                                    {stats.recent_activity.map((activity, idx) => (
                                        <div key={idx} className="flex items-center gap-4 py-2 border-b last:border-0">
                                            <span className="text-xs text-muted-foreground w-32">
                                                {activity.time}
                                            </span>
                                            <span className="text-sm">{activity.action}</span>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p className="text-muted-foreground text-center py-4">
                                    暂无活动记录
                                </p>
                            )}
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}

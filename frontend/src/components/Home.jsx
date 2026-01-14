import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Plus, BookOpen, Clock, ArrowRight } from "lucide-react";
import useProjectStore from '@/store/useProjectStore';

export default function Home() {
    const navigate = useNavigate();
    const { projects, fetchProjects, isLoading } = useProjectStore();

    useEffect(() => {
        fetchProjects();
    }, []);

    return (
        <div className="min-h-screen bg-background text-foreground p-8">
            <div className="max-w-6xl mx-auto space-y-8">

                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-4xl font-extrabold tracking-tight lg:text-5xl">Novel Agent</h1>
                        <p className="mt-2 text-muted-foreground">AI 驱动的沉浸式小说创作工作台</p>
                    </div>
                    <Button onClick={() => navigate('/create')} size="lg" className="gap-2">
                        <Plus className="w-5 h-5" /> 新建项目
                    </Button>
                </div>

                {/* Project List */}
                <div>
                    <h2 className="text-2xl font-semibold mb-6 flex items-center gap-2">
                        <BookOpen className="w-6 h-6" /> 我的作品
                    </h2>

                    {isLoading ? (
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            {[1, 2, 3].map(i => (
                                <div key={i} className="h-48 rounded-xl bg-muted/50 animate-pulse" />
                            ))}
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {/* New Project Card (Quick Action) */}
                            <Card
                                className="flex flex-col items-center justify-center p-6 border-dashed cursor-pointer hover:bg-accent/50 transition-colors h-full min-h-[200px]"
                                onClick={() => navigate('/create')}
                            >
                                <div className="p-4 rounded-full bg-primary/10 text-primary mb-4">
                                    <Plus className="w-8 h-8" />
                                </div>
                                <h3 className="font-semibold text-lg">开启新篇章</h3>
                                <p className="text-sm text-muted-foreground mt-2">从一个灵感开始</p>
                            </Card>

                            {/* Existing Projects */}
                            {projects.map((project) => (
                                <Card key={project.name} className="flex flex-col hover:shadow-lg transition-shadow">
                                    <CardHeader>
                                        <CardTitle className="truncate">{project.title || project.name}</CardTitle>
                                        <CardDescription className="line-clamp-2">
                                            {project.summary || "暂无简介"}
                                        </CardDescription>
                                    </CardHeader>
                                    <CardContent className="flex-1">
                                        <div className="flex items-center text-sm text-muted-foreground gap-4">
                                            <div className="flex items-center gap-1">
                                                <BookOpen className="w-4 h-4" />
                                                <span>{project.current_volume || 1} 卷</span>
                                            </div>
                                            <div className="flex items-center gap-1">
                                                <Clock className="w-4 h-4" />
                                                <span>{new Date(project.modified || project.updated_at || Date.now()).toLocaleDateString()}</span>
                                            </div>
                                        </div>
                                    </CardContent>
                                    <CardFooter>
                                        <Button
                                            variant="ghost"
                                            className="w-full justify-between group"
                                            onClick={() => navigate(`/project/${project.name}`)}
                                        >
                                            继续创作
                                            <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
                                        </Button>
                                    </CardFooter>
                                </Card>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import useGenesisStore from '@/store/useGenesisStore';
import { motion, AnimatePresence } from "framer-motion";
import { Loader2, Sparkles, Wand2, ArrowRight } from "lucide-react";

export default function Wizard() {
    const {
        inspiration, setInspiration,
        generateProposals, proposals, isLoadingProposals,
        initializeProject, isInitializing, error
    } = useGenesisStore();

    const [step, setStep] = useState('input'); // input | proposals | init
    const [selectedIdx, setSelectedIdx] = useState(null);
    const [customName, setCustomName] = useState("");

    const handleGenerate = async () => {
        if (!inspiration.trim()) return;
        await generateProposals(inspiration);
        setStep('proposals');
    };

    const handleSelect = (idx) => {
        setSelectedIdx(idx);
        setCustomName(proposals[idx].title); // Default to proposal title
    };

    const handleInit = async () => {
        if (selectedIdx === null) return;
        const proposal = proposals[selectedIdx];
        // Sanitize project name for folder: pinyin or english is better but for now usage title
        // Actually backend expects a folder name. Let's ask user or auto-generate.
        // For simplicity, we use the title but user can edit. 
        // Ideally we convert title to safe filename.

        // Simple safe conversion for demo
        const safeName = customName.replace(/[^\w\u4e00-\u9fa5]/g, '_');

        const success = await initializeProject(safeName, proposal.config_yaml);
        if (success) {
            window.location.href = `/project/${safeName}`; // Redirect to legacy/new project view
        }
    };

    if (step === 'input' || (step === 'proposals' && isLoadingProposals)) {
        return (
            <div className="flex flex-col items-center justify-center min-h-screen p-4 bg-background">
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-lg">
                    <Card>
                        <CardHeader className="text-center">
                            <div className="mx-auto bg-primary/10 p-3 rounded-full w-fit mb-4">
                                <Sparkles className="w-8 h-8 text-primary" />
                            </div>
                            <CardTitle className="text-2xl">开启你的创作之旅</CardTitle>
                            <CardDescription>只需一个灵感，AI 为你生成三个完整的开局方案</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                <Input
                                    placeholder="例如：一个修仙者穿越到赛博朋克世界做黑客..."
                                    value={inspiration}
                                    onChange={(e) => setInspiration(e.target.value)}
                                    className="h-14 text-lg"
                                    disabled={isLoadingProposals}
                                />

                                {isLoadingProposals && (
                                    <div className="text-center text-sm text-muted-foreground animate-pulse flex items-center justify-center gap-2">
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                        正在构思方案方案 (需要 10-20 秒)...
                                    </div>
                                )}

                                {error && <div className="text-destructive text-sm text-center">{error}</div>}
                            </div>
                        </CardContent>
                        <CardFooter>
                            <Button
                                onClick={handleGenerate}
                                disabled={!inspiration.trim() || isLoadingProposals}
                                className="w-full h-12 text-lg gap-2"
                            >
                                {isLoadingProposals ? '头脑风暴中...' : (
                                    <>开始策划 <ArrowRight className="w-4 h-4" /></>
                                )}
                            </Button>
                        </CardFooter>
                    </Card>
                </motion.div>
            </div>
        );
    }

    if (step === 'proposals') {
        return (
            <div className="min-h-screen p-8 bg-background flex flex-col items-center justify-center">
                <div className="max-w-6xl w-full space-y-8">
                    <div className="text-center space-y-2">
                        <h2 className="text-3xl font-bold tracking-tight">选择你的故事走向</h2>
                        <p className="text-muted-foreground">AI 根据 "{inspiration}" 生成了以下方案</p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {proposals.map((proposal, idx) => (
                            <motion.div
                                key={idx}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: idx * 0.1 }}
                            >
                                <Card
                                    className={cn(
                                        "h-full cursor-pointer transition-all hover:border-primary",
                                        selectedIdx === idx ? "ring-2 ring-primary border-primary shadow-lg" : ""
                                    )}
                                    onClick={() => handleSelect(idx)}
                                >
                                    <CardHeader>
                                        <CardTitle className="text-xl">{proposal.title}</CardTitle>
                                        <CardDescription className="font-medium text-primary line-clamp-2">
                                            {proposal.core_positioning}
                                        </CardDescription>
                                    </CardHeader>
                                    <CardContent className="space-y-4">
                                        <div className="bg-muted/50 p-3 rounded-md text-sm">
                                            <span className="font-semibold block mb-1">核心卖点:</span>
                                            {proposal.highlights}
                                        </div>
                                        <p className="text-sm text-muted-foreground leading-relaxed">
                                            {proposal.introduction}
                                        </p>
                                    </CardContent>
                                    <CardFooter>
                                        {selectedIdx === idx && (
                                            <div className="w-full space-y-4 animate-in fade-in zoom-in duration-300">
                                                <Input
                                                    value={customName}
                                                    onChange={(e) => setCustomName(e.target.value)}
                                                    placeholder="确认书名/项目名"
                                                />
                                                <Button onClick={handleInit} disabled={isInitializing} className="w-full gap-2">
                                                    {isInitializing ? <Loader2 className="animate-spin" /> : <Wand2 className="w-4 h-4" />}
                                                    {isInitializing ? "正在构建世界..." : "使用此方案启动"}
                                                </Button>
                                            </div>
                                        )}
                                    </CardFooter>
                                </Card>
                            </motion.div>
                        ))}
                    </div>

                    {error && <div className="text-destructive text-center">{error}</div>}

                    <div className="text-center">
                        <Button variant="ghost" onClick={() => setStep('input')}>
                            返回重新输入
                        </Button>
                    </div>
                </div>
            </div>
        );
    }

    return null;
}

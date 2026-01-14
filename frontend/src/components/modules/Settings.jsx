import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import client from '@/api/client';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardHeader, CardTitle, CardContent, CardDescription, CardFooter } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import {
    Loader2, Save, Settings as SettingsIcon, Cpu, Sliders, FileText, Shield,
    CheckCircle2, XCircle, Key, Zap, Brain, Sparkles, RefreshCw, Eye, EyeOff
} from 'lucide-react';

export default function Settings() {
    const { projectId } = useParams();
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);

    // 全局设置
    const [globalSettings, setGlobalSettings] = useState(null);
    const [projectConfig, setProjectConfig] = useState(null);
    const [systemPrompt, setSystemPrompt] = useState('');

    // API Key 状态
    const [apiKey, setApiKey] = useState('');
    const [showApiKey, setShowApiKey] = useState(false);
    const [testingKey, setTestingKey] = useState(false);
    const [keyStatus, setKeyStatus] = useState(null); // null, 'valid', 'invalid'

    // 生成参数
    const [genConfig, setGenConfig] = useState({
        temperature: 0.7,
        top_p: 0.95,
        top_k: 40,
        max_tokens: 8192
    });

    // 安全设置
    const [safetySettings, setSafetySettings] = useState({
        harm_block_threshold: 'BLOCK_MEDIUM_AND_ABOVE',
        enable_content_filter: true
    });

    // 加载所有设置
    useEffect(() => {
        async function fetchAll() {
            try {
                setLoading(true);

                // 获取完整全局设置
                const { data: fullSettings } = await client.get('/api/settings/global/full');
                setGlobalSettings(fullSettings);
                setGenConfig(fullSettings.generation_config);
                setSafetySettings(fullSettings.safety_settings);

                // 获取项目配置
                if (projectId) {
                    const { data: project } = await client.get(`/api/projects/${projectId}`);
                    setProjectConfig(project.config);

                    // 获取系统 Prompt
                    const { data: promptData } = await client.get(`/api/settings/system-prompt/${projectId}`);
                    setSystemPrompt(promptData.content || '');
                }
            } catch (e) {
                console.error('Failed to load settings:', e);
            } finally {
                setLoading(false);
            }
        }
        fetchAll();
    }, [projectId]);

    // 测试 API Key
    const handleTestApiKey = async () => {
        if (!apiKey.trim()) return;
        setTestingKey(true);
        setKeyStatus(null);

        try {
            const { data } = await client.post('/api/settings/api-key/test', {
                api_key: apiKey,
                provider: 'gemini'
            });
            setKeyStatus(data.valid ? 'valid' : 'invalid');
        } catch (e) {
            setKeyStatus('invalid');
        } finally {
            setTestingKey(false);
        }
    };

    // 保存 API Key
    const handleSaveApiKey = async () => {
        if (!apiKey.trim() || keyStatus !== 'valid') return;

        try {
            await client.post('/api/settings/api-key/save', {
                api_key: apiKey,
                provider: 'gemini'
            });
            setGlobalSettings(prev => ({ ...prev, api_key_configured: true }));
        } catch (e) {
            alert('保存失败: ' + e.message);
        }
    };

    // 切换模型
    const handleModelChange = async (modelName) => {
        try {
            await client.post('/api/settings/global', { current_model: modelName });
            setGlobalSettings(prev => ({ ...prev, current_model: modelName }));
        } catch (e) {
            alert('切换模型失败');
        }
    };

    // 保存生成参数
    const handleSaveGenConfig = async () => {
        setSaving(true);
        try {
            await client.post('/api/settings/params', genConfig);
        } catch (e) {
            alert('保存失败');
        } finally {
            setSaving(false);
        }
    };

    // 应用预设
    const handleApplyPreset = async (presetName) => {
        try {
            const { data } = await client.post(`/api/settings/params/preset/${presetName}`);
            setGenConfig(data.config);
        } catch (e) {
            alert('应用预设失败');
        }
    };

    // 保存项目配置
    const handleSaveProject = async () => {
        setSaving(true);
        try {
            await client.post(`/api/project/${projectId}/config`, projectConfig);
        } catch (e) {
            alert('保存失败');
        } finally {
            setSaving(false);
        }
    };

    // 保存系统 Prompt
    const handleSaveSystemPrompt = async () => {
        setSaving(true);
        try {
            await client.post(`/api/settings/system-prompt/${projectId}`, {
                content: systemPrompt
            });
        } catch (e) {
            alert('保存失败');
        } finally {
            setSaving(false);
        }
    };

    // 保存安全设置
    const handleSaveSafety = async () => {
        try {
            await client.post('/api/settings/safety', safetySettings);
        } catch (e) {
            alert('保存失败');
        }
    };

    if (loading) {
        return (
            <div className="h-full flex items-center justify-center">
                <Loader2 className="animate-spin w-8 h-8 text-muted-foreground" />
            </div>
        );
    }

    return (
        <div className="h-full flex flex-col bg-background">
            {/* Header */}
            <div className="px-8 py-6 border-b flex items-center gap-3">
                <div className="p-2 bg-primary/10 rounded-lg text-primary">
                    <SettingsIcon className="w-6 h-6" />
                </div>
                <div>
                    <h1 className="text-2xl font-bold">设置 (Settings)</h1>
                    <p className="text-muted-foreground text-sm">配置 AI 模型、生成参数和项目属性</p>
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-8">
                <div className="max-w-4xl mx-auto">
                    <Tabs defaultValue="model" className="w-full">
                        <TabsList className="grid w-full grid-cols-5">
                            <TabsTrigger value="model" className="gap-2">
                                <Cpu className="w-4 h-4" /> AI 模型
                            </TabsTrigger>
                            <TabsTrigger value="params" className="gap-2">
                                <Sliders className="w-4 h-4" /> 生成参数
                            </TabsTrigger>
                            <TabsTrigger value="prompt" className="gap-2">
                                <FileText className="w-4 h-4" /> Prompt
                            </TabsTrigger>
                            <TabsTrigger value="project" className="gap-2">
                                <Sparkles className="w-4 h-4" /> 项目
                            </TabsTrigger>
                            <TabsTrigger value="advanced" className="gap-2">
                                <Shield className="w-4 h-4" /> 高级
                            </TabsTrigger>
                        </TabsList>

                        {/* Tab 1: AI 模型 */}
                        <TabsContent value="model" className="space-y-6 py-6">
                            {/* API Key */}
                            <Card>
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <Key className="w-5 h-5" />
                                        API Key 配置
                                    </CardTitle>
                                    <CardDescription>
                                        配置 Gemini API Key 以启用 AI 功能
                                    </CardDescription>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    <div className="flex items-center gap-2">
                                        <div className="relative flex-1">
                                            <Input
                                                type={showApiKey ? "text" : "password"}
                                                placeholder="输入 Gemini API Key..."
                                                value={apiKey}
                                                onChange={e => setApiKey(e.target.value)}
                                            />
                                            <button
                                                type="button"
                                                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                                                onClick={() => setShowApiKey(!showApiKey)}
                                            >
                                                {showApiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                            </button>
                                        </div>
                                        <Button
                                            variant="outline"
                                            onClick={handleTestApiKey}
                                            disabled={testingKey || !apiKey.trim()}
                                        >
                                            {testingKey ? <Loader2 className="w-4 h-4 animate-spin" /> : '测试'}
                                        </Button>
                                        <Button
                                            onClick={handleSaveApiKey}
                                            disabled={keyStatus !== 'valid'}
                                        >
                                            <Save className="w-4 h-4 mr-2" /> 保存
                                        </Button>
                                    </div>

                                    {/* 状态指示器 */}
                                    <div className="flex items-center gap-2">
                                        {globalSettings?.api_key_configured ? (
                                            <Badge variant="success" className="bg-green-500/10 text-green-500">
                                                <CheckCircle2 className="w-3 h-3 mr-1" /> 已配置
                                            </Badge>
                                        ) : (
                                            <Badge variant="destructive" className="bg-red-500/10 text-red-500">
                                                <XCircle className="w-3 h-3 mr-1" /> 未配置
                                            </Badge>
                                        )}
                                        {keyStatus === 'valid' && (
                                            <Badge className="bg-green-500/10 text-green-500">
                                                <CheckCircle2 className="w-3 h-3 mr-1" /> Key 有效
                                            </Badge>
                                        )}
                                        {keyStatus === 'invalid' && (
                                            <Badge className="bg-red-500/10 text-red-500">
                                                <XCircle className="w-3 h-3 mr-1" /> Key 无效
                                            </Badge>
                                        )}
                                    </div>
                                </CardContent>
                            </Card>

                            {/* 模型选择 */}
                            <Card>
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <Brain className="w-5 h-5" />
                                        选择模型
                                    </CardTitle>
                                    <CardDescription>
                                        当前: <span className="font-mono text-primary">{globalSettings?.current_model}</span>
                                    </CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <div className="space-y-6">
                                        {globalSettings?.available_models && Object.keys(globalSettings.available_models).length > 0 ? (
                                            Object.entries(globalSettings.available_models).map(([provider, models]) => (
                                                <div key={provider}>
                                                    <h3 className="text-sm font-medium text-muted-foreground mb-3 capitalize">{provider} Models</h3>
                                                    <div className="grid grid-cols-2 gap-3">
                                                        {models && models.map((model) => (
                                                            <div
                                                                key={model.name}
                                                                onClick={() => handleModelChange(model.name, provider)}
                                                                className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${globalSettings?.current_model === model.name
                                                                    ? 'border-primary bg-primary/5'
                                                                    : 'border-border hover:border-muted-foreground/50'
                                                                    }`}
                                                            >
                                                                <div className="flex items-center justify-between mb-2">
                                                                    <span className="font-mono text-sm font-medium">{model.name}</span>
                                                                    <Badge variant="outline" className="text-xs">
                                                                        {Math.round((model.context || 0) / 1000)}k
                                                                    </Badge>
                                                                </div>
                                                                <div className="flex items-center justify-between text-xs text-muted-foreground">
                                                                    <span>Context: {(model.context || 0).toLocaleString()}</span>
                                                                </div>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            ))
                                        ) : (
                                            <div className="text-center py-8 text-muted-foreground">
                                                暂无可用模型，请检查 API Key 配置
                                            </div>
                                        )}
                                    </div>
                                </CardContent>
                            </Card>
                        </TabsContent>

                        {/* Tab 2: 生成参数 */}
                        <TabsContent value="params" className="space-y-6 py-6">
                            {/* 预设 */}
                            <Card>
                                <CardHeader>
                                    <CardTitle>快速预设</CardTitle>
                                    <CardDescription>一键应用常用参数配置</CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <div className="flex gap-3">
                                        <Button
                                            variant="outline"
                                            onClick={() => handleApplyPreset('creative')}
                                            className="flex-1"
                                        >
                                            <Sparkles className="w-4 h-4 mr-2" /> 创意模式
                                        </Button>
                                        <Button
                                            variant="outline"
                                            onClick={() => handleApplyPreset('balanced')}
                                            className="flex-1"
                                        >
                                            <Zap className="w-4 h-4 mr-2" /> 平衡模式
                                        </Button>
                                        <Button
                                            variant="outline"
                                            onClick={() => handleApplyPreset('precise')}
                                            className="flex-1"
                                        >
                                            <Brain className="w-4 h-4 mr-2" /> 精确模式
                                        </Button>
                                    </div>
                                </CardContent>
                            </Card>

                            {/* 详细参数 */}
                            <Card>
                                <CardHeader>
                                    <CardTitle>详细参数</CardTitle>
                                    <CardDescription>微调 AI 生成行为</CardDescription>
                                </CardHeader>
                                <CardContent className="space-y-6">
                                    {/* Temperature */}
                                    <div className="space-y-3">
                                        <div className="flex items-center justify-between">
                                            <Label>Temperature (创造性)</Label>
                                            <span className="font-mono text-sm bg-muted px-2 py-1 rounded">
                                                {genConfig.temperature.toFixed(2)}
                                            </span>
                                        </div>
                                        <Slider
                                            value={[genConfig.temperature]}
                                            onValueChange={([v]) => setGenConfig(prev => ({ ...prev, temperature: v }))}
                                            min={0}
                                            max={2}
                                            step={0.1}
                                        />
                                        <p className="text-xs text-muted-foreground">
                                            低值 (0-0.5): 保守精确 | 中值 (0.5-1): 平衡 | 高值 (1-2): 创意发散
                                        </p>
                                    </div>

                                    {/* Top-P */}
                                    <div className="space-y-3">
                                        <div className="flex items-center justify-between">
                                            <Label>Top-P (核采样)</Label>
                                            <span className="font-mono text-sm bg-muted px-2 py-1 rounded">
                                                {genConfig.top_p.toFixed(2)}
                                            </span>
                                        </div>
                                        <Slider
                                            value={[genConfig.top_p]}
                                            onValueChange={([v]) => setGenConfig(prev => ({ ...prev, top_p: v }))}
                                            min={0}
                                            max={1}
                                            step={0.05}
                                        />
                                    </div>

                                    {/* Top-K */}
                                    <div className="space-y-3">
                                        <div className="flex items-center justify-between">
                                            <Label>Top-K</Label>
                                            <span className="font-mono text-sm bg-muted px-2 py-1 rounded">
                                                {genConfig.top_k}
                                            </span>
                                        </div>
                                        <Slider
                                            value={[genConfig.top_k]}
                                            onValueChange={([v]) => setGenConfig(prev => ({ ...prev, top_k: v }))}
                                            min={1}
                                            max={100}
                                            step={1}
                                        />
                                    </div>

                                    {/* Max Tokens */}
                                    <div className="grid grid-cols-4 items-center gap-4">
                                        <Label className="text-right">Max Tokens</Label>
                                        <Input
                                            type="number"
                                            value={genConfig.max_tokens}
                                            onChange={e => setGenConfig(prev => ({ ...prev, max_tokens: parseInt(e.target.value) || 4096 }))}
                                            className="col-span-3"
                                        />
                                    </div>
                                </CardContent>
                                <CardFooter className="flex justify-end">
                                    <Button onClick={handleSaveGenConfig} disabled={saving}>
                                        {saving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Save className="w-4 h-4 mr-2" />}
                                        保存参数
                                    </Button>
                                </CardFooter>
                            </Card>
                        </TabsContent>

                        {/* Tab 3: Prompt 编辑 */}
                        <TabsContent value="prompt" className="space-y-6 py-6">
                            <Card>
                                <CardHeader>
                                    <CardTitle>系统 Prompt</CardTitle>
                                    <CardDescription>
                                        定义 AI 的角色和写作风格，影响所有生成内容
                                    </CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <Textarea
                                        value={systemPrompt}
                                        onChange={e => setSystemPrompt(e.target.value)}
                                        placeholder="输入系统 Prompt...&#10;例如: 你是一位专业的网络小说作家，擅长写作玄幻、都市类型..."
                                        className="min-h-[300px] font-mono text-sm"
                                    />
                                </CardContent>
                                <CardFooter className="flex justify-between">
                                    <p className="text-sm text-muted-foreground">
                                        {systemPrompt.length} 字符
                                    </p>
                                    <Button onClick={handleSaveSystemPrompt} disabled={saving}>
                                        {saving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Save className="w-4 h-4 mr-2" />}
                                        保存 Prompt
                                    </Button>
                                </CardFooter>
                            </Card>
                        </TabsContent>

                        {/* Tab 4: 项目配置 */}
                        <TabsContent value="project" className="space-y-6 py-6">
                            <Card>
                                <CardHeader>
                                    <CardTitle>项目信息</CardTitle>
                                    <CardDescription>修改当前小说的基础元数据</CardDescription>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    <div className="grid grid-cols-4 items-center gap-4">
                                        <Label className="text-right">书名</Label>
                                        <Input
                                            value={projectConfig?.title || ''}
                                            onChange={e => setProjectConfig(prev => ({ ...prev, title: e.target.value }))}
                                            className="col-span-3"
                                        />
                                    </div>
                                    <div className="grid grid-cols-4 items-center gap-4">
                                        <Label className="text-right">类型/标签</Label>
                                        <Input
                                            value={projectConfig?.genre || ''}
                                            onChange={e => setProjectConfig(prev => ({ ...prev, genre: e.target.value }))}
                                            className="col-span-3"
                                        />
                                    </div>
                                    <div className="grid grid-cols-4 items-center gap-4">
                                        <Label className="text-right">目标字数</Label>
                                        <Input
                                            type="number"
                                            value={projectConfig?.target_words || 0}
                                            onChange={e => setProjectConfig(prev => ({ ...prev, target_words: parseInt(e.target.value) }))}
                                            className="col-span-3"
                                        />
                                    </div>
                                    <div className="grid grid-cols-4 items-center gap-4">
                                        <Label className="text-right">每章字数</Label>
                                        <Input
                                            type="number"
                                            value={projectConfig?.words_per_chapter || 3000}
                                            onChange={e => setProjectConfig(prev => ({ ...prev, words_per_chapter: parseInt(e.target.value) }))}
                                            className="col-span-3"
                                        />
                                    </div>
                                </CardContent>
                                <CardFooter className="flex justify-end">
                                    <Button onClick={handleSaveProject} disabled={saving}>
                                        {saving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Save className="w-4 h-4 mr-2" />}
                                        保存项目配置
                                    </Button>
                                </CardFooter>
                            </Card>
                        </TabsContent>

                        {/* Tab 5: 高级设置 */}
                        <TabsContent value="advanced" className="space-y-6 py-6">
                            <Card>
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <Shield className="w-5 h-5" />
                                        安全设置
                                    </CardTitle>
                                    <CardDescription>
                                        控制内容过滤级别
                                    </CardDescription>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <Label>启用内容过滤</Label>
                                            <p className="text-sm text-muted-foreground">
                                                过滤潜在有害或敏感内容
                                            </p>
                                        </div>
                                        <Switch
                                            checked={safetySettings.enable_content_filter}
                                            onCheckedChange={v => setSafetySettings(prev => ({ ...prev, enable_content_filter: v }))}
                                        />
                                    </div>

                                    <div className="grid grid-cols-4 items-center gap-4">
                                        <Label className="text-right">过滤级别</Label>
                                        <Select
                                            value={safetySettings.harm_block_threshold}
                                            onValueChange={v => setSafetySettings(prev => ({ ...prev, harm_block_threshold: v }))}
                                        >
                                            <SelectTrigger className="col-span-3">
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="BLOCK_NONE">无限制</SelectItem>
                                                <SelectItem value="BLOCK_LOW_AND_ABOVE">低</SelectItem>
                                                <SelectItem value="BLOCK_MEDIUM_AND_ABOVE">中 (推荐)</SelectItem>
                                                <SelectItem value="BLOCK_HIGH_AND_ABOVE">高</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>
                                </CardContent>
                                <CardFooter className="flex justify-end">
                                    <Button onClick={handleSaveSafety} variant="outline">
                                        <Save className="w-4 h-4 mr-2" /> 保存安全设置
                                    </Button>
                                </CardFooter>
                            </Card>

                            {/* Token 使用统计 */}
                            <Card>
                                <CardHeader>
                                    <CardTitle>使用统计</CardTitle>
                                    <CardDescription>本次会话的 Token 消耗</CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <div className="grid grid-cols-3 gap-4 text-center">
                                        <div className="p-4 bg-muted rounded-lg">
                                            <div className="text-2xl font-bold">
                                                {globalSettings?.usage_stats?.total_input_tokens?.toLocaleString() || 0}
                                            </div>
                                            <div className="text-sm text-muted-foreground">输入 Tokens</div>
                                        </div>
                                        <div className="p-4 bg-muted rounded-lg">
                                            <div className="text-2xl font-bold">
                                                {globalSettings?.usage_stats?.total_output_tokens?.toLocaleString() || 0}
                                            </div>
                                            <div className="text-sm text-muted-foreground">输出 Tokens</div>
                                        </div>
                                        <div className="p-4 bg-muted rounded-lg">
                                            <div className="text-2xl font-bold text-primary">
                                                ${globalSettings?.usage_stats?.total_cost_usd?.toFixed(4) || '0.00'}
                                            </div>
                                            <div className="text-sm text-muted-foreground">预估成本</div>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        </TabsContent>
                    </Tabs>
                </div>
            </div>
        </div>
    );
}

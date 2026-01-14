import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import client from '@/api/client';
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Download, FileText, FileType, BookOpen, Loader2, CheckCircle2 } from 'lucide-react';

export default function Export() {
    const { projectId } = useParams();
    const [format, setFormat] = useState('txt');
    const [isExporting, setIsExporting] = useState(false);
    const [exportResult, setExportResult] = useState(null);

    const formats = [
        { value: 'txt', label: 'TXT 纯文本', icon: FileText, desc: '简单文本格式，兼容性最佳' },
        { value: 'docx', label: 'DOCX Word文档', icon: FileType, desc: '带格式的Word文档' },
        { value: 'epub', label: 'EPUB 电子书', icon: BookOpen, desc: '适合电子阅读器' },
    ];

    const handleExport = async () => {
        setIsExporting(true);
        setExportResult(null);

        try {
            const response = await client.post(`/api/export/${format}`, {
                project: projectId
            });

            if (response.data.filename) {
                // 触发下载
                const downloadUrl = `/api/export/${projectId}/download/${response.data.filename}`;
                const link = document.createElement('a');
                link.href = downloadUrl;
                link.download = response.data.filename;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);

                setExportResult({
                    success: true,
                    message: `导出成功: ${response.data.filename}`,
                    filename: response.data.filename
                });
            }
        } catch (err) {
            setExportResult({
                success: false,
                message: `导出失败: ${err.response?.data?.error || err.message}`
            });
        } finally {
            setIsExporting(false);
        }
    };

    return (
        <div className="h-full flex flex-col bg-background">
            {/* Header */}
            <div className="px-8 py-6 border-b flex items-center gap-3">
                <div className="p-2 bg-primary/10 rounded-lg text-primary">
                    <Download className="w-6 h-6" />
                </div>
                <div>
                    <h1 className="text-2xl font-bold">导出 (Export)</h1>
                    <p className="text-muted-foreground text-sm">将小说导出为不同格式</p>
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-8">
                <div className="max-w-2xl mx-auto space-y-6">

                    {/* Format Selection */}
                    <Card>
                        <CardHeader>
                            <CardTitle>选择导出格式</CardTitle>
                            <CardDescription>根据你的需求选择合适的文件格式</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="grid gap-4">
                                {formats.map((fmt) => {
                                    const Icon = fmt.icon;
                                    return (
                                        <div
                                            key={fmt.value}
                                            onClick={() => setFormat(fmt.value)}
                                            className={`
                                                flex items-center gap-4 p-4 rounded-lg border-2 cursor-pointer transition-all
                                                ${format === fmt.value
                                                    ? 'border-primary bg-primary/5'
                                                    : 'border-border hover:border-muted-foreground/50'}
                                            `}
                                        >
                                            <div className={`p-2 rounded-md ${format === fmt.value ? 'bg-primary text-primary-foreground' : 'bg-muted'}`}>
                                                <Icon className="w-5 h-5" />
                                            </div>
                                            <div className="flex-1">
                                                <div className="font-medium">{fmt.label}</div>
                                                <div className="text-sm text-muted-foreground">{fmt.desc}</div>
                                            </div>
                                            {format === fmt.value && (
                                                <CheckCircle2 className="w-5 h-5 text-primary" />
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        </CardContent>
                    </Card>

                    {/* Export Button */}
                    <Card>
                        <CardContent className="pt-6">
                            <Button
                                onClick={handleExport}
                                disabled={isExporting}
                                size="lg"
                                className="w-full gap-2"
                            >
                                {isExporting ? (
                                    <>
                                        <Loader2 className="w-5 h-5 animate-spin" />
                                        正在导出...
                                    </>
                                ) : (
                                    <>
                                        <Download className="w-5 h-5" />
                                        导出为 {formats.find(f => f.value === format)?.label}
                                    </>
                                )}
                            </Button>

                            {/* Result */}
                            {exportResult && (
                                <div className={`mt-4 p-4 rounded-lg ${exportResult.success ? 'bg-green-500/10 text-green-500' : 'bg-destructive/10 text-destructive'}`}>
                                    {exportResult.message}
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}

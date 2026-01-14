import React from 'react';
import { Card, CardHeader, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Pencil, Trash2, User, MapPin, Box, Zap, FileText } from 'lucide-react';

const TYPE_ICONS = {
    character: User,
    location: MapPin,
    item: Box,
    concept: Zap,
    default: FileText
};

const TYPE_COLORS = {
    character: "bg-blue-500/10 text-blue-500 hover:bg-blue-500/20",
    location: "bg-green-500/10 text-green-500 hover:bg-green-500/20",
    item: "bg-amber-500/10 text-amber-500 hover:bg-amber-500/20",
    concept: "bg-purple-500/10 text-purple-500 hover:bg-purple-500/20",
    default: "bg-slate-500/10 text-slate-500"
};

export default function CardGrid({ cards, onEdit, onDelete }) {
    if (!cards || cards.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center p-12 text-muted-foreground border-2 border-dashed rounded-xl">
                <div className="mb-4 p-4 bg-muted rounded-full">
                    <Box className="w-8 h-8 opacity-50" />
                </div>
                <p>暂无设定，点击右上角新建卡片</p>
            </div>
        );
    }

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 p-6">
            {cards.map(card => {
                const type = (card.card_type || "default").toLowerCase();
                const Icon = TYPE_ICONS[type] || TYPE_ICONS.default;
                const colorClass = TYPE_COLORS[type] || TYPE_COLORS.default;

                return (
                    <Card key={card.id} className="group relative overflow-hidden transition-all hover:shadow-md hover:border-primary/50">
                        <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
                            <div className="flex items-center gap-3">
                                <div className={`p-2 rounded-md ${colorClass}`}>
                                    <Icon className="w-5 h-5" />
                                </div>
                                <div className="font-semibold truncate max-w-[120px]" title={card.name}>
                                    {card.name}
                                </div>
                            </div>
                            <Badge variant="outline" className="capitalize text-[10px] opacity-70">
                                {type}
                            </Badge>
                        </CardHeader>
                        <CardContent>
                            <p className="text-sm text-muted-foreground line-clamp-3 h-[60px]">
                                {card.description || "暂无描述..."}
                            </p>
                        </CardContent>
                        <CardFooter className="flex justify-end gap-2 pt-0 opacity-0 group-hover:opacity-100 transition-opacity">
                            <Button size="icon" variant="ghost" className="h-8 w-8" onClick={() => onEdit(card)}>
                                <Pencil className="w-4 h-4" />
                            </Button>
                            <Button size="icon" variant="ghost" className="h-8 w-8 text-destructive hover:text-destructive" onClick={() => onDelete(card.id)}>
                                <Trash2 className="w-4 h-4" />
                            </Button>
                        </CardFooter>
                    </Card>
                );
            })}
        </div>
    );
}

import { useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Info, X } from 'lucide-react';

export default function KnowledgeDetailModal({ detail, onClose }) {
    useEffect(() => {
        if (detail) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = 'unset';
        }
        return () => {
            document.body.style.overflow = 'unset';
        };
    }, [detail]);

    if (!detail) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
            <Card className="w-full max-w-2xl max-h-[90vh] overflow-hidden shadow-2xl flex flex-col animate-in zoom-in-95 duration-200">
                <CardHeader className="border-b bg-muted/30 pb-4">
                    <div className="flex justify-between items-center">
                        <div className="flex items-center gap-2">
                            <div className="p-2 bg-primary/10 rounded-lg text-primary">
                                <Info className="w-5 h-5" />
                            </div>
                            <CardTitle className="text-xl">{detail.point || detail.语法 || '考点详情'}</CardTitle>
                        </div>
                        <Button
                            variant="ghost"
                            size="icon"
                            className="rounded-full h-8 w-8"
                            onClick={onClose}
                        >
                            <X className="w-4 h-4" />
                        </Button>
                    </div>
                </CardHeader>
                <CardContent className="overflow-y-auto p-6 space-y-6">
                    {Object.entries(detail).map(([key, value]) => {
                        // Skip internal or display keys already shown
                        if (['point', 'source_file', 'description', '语法'].includes(key)) return null;
                        if (key.startsWith('col_')) return null;
                        if (!value) return null;

                        return (
                            <div key={key} className="space-y-1.5">
                                <h4 className="text-sm font-bold text-primary flex items-center gap-2">
                                    <span className="w-1.5 h-1.5 rounded-full bg-primary" />
                                    {key}
                                </h4>
                                <div className="text-sm leading-relaxed text-muted-foreground bg-muted/30 p-3 rounded-lg border border-muted whitespace-pre-wrap">
                                    {value}
                                </div>
                            </div>
                        );
                    })}

                    {detail.description && !Object.keys(detail).some(k => !['point', 'source_file', 'description', '语法'].includes(k) && !k.startsWith('col_')) && (
                        <div className="space-y-1.5">
                            <h4 className="text-sm font-bold text-primary flex items-center gap-2">
                                <span className="w-1.5 h-1.5 rounded-full bg-primary" />
                                考点说明
                            </h4>
                            <div className="text-sm leading-relaxed text-muted-foreground bg-muted/30 p-3 rounded-lg border border-muted whitespace-pre-wrap">
                                {detail.description}
                            </div>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}

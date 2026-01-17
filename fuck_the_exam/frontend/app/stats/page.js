'use client';

import { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/card';
import { BarChart, Bar, XAxis, YAxis, Tooltip as RechartsTooltip, ResponsiveContainer, LineChart, Line, CartesianGrid } from 'recharts';
import { Loader2 } from 'lucide-react';
import { getStats, getAnalysis } from '../../lib/api';
import Link from 'next/link';
import { Button } from '../../components/ui/button';
import TrainingSuggestions from '../../components/TrainingSuggestions';

export default function StatsPage() {
    const [stats, setStats] = useState(null);
    const [analysis, setAnalysis] = useState(null);
    const [suggestions, setSuggestions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [analyzing, setAnalyzing] = useState(false);

    useEffect(() => {
        async function fetchData() {
            try {
                // Fetch Stats
                const statsData = await getStats();
                setStats(statsData);

                const wrongPoints = statsData.top_wrong_points || [];
                const sugData = wrongPoints.map(wp => ({
                    point: wp.point,
                    description: `错题解析正在后台分析中... 已累积错误 ${wp.count} 次。`
                }));
                setSuggestions(sugData);

                // Start AI Analysis in background
                fetchAnalysis();

            } catch (e) {
                console.error("Failed to load stats", e);
            } finally {
                setLoading(false);
            }
        }
        fetchData();
    }, []);

    const fetchAnalysis = async () => {
        setAnalyzing(true);
        try {
            const data = await getAnalysis();
            setAnalysis(data);
        } catch (e) {
            console.error("AI Analysis failed:", e);
        } finally {
            setAnalyzing(false);
        }
    };

    if (loading) {
        return (
            <div className="flex h-screen items-center justify-center">
                <Loader2 className="animate-spin w-8 h-8 text-primary" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-background p-4 md:p-8">
            <div className="max-w-6xl mx-auto space-y-8">

                <header className="flex flex-col sm:flex-row justify-between sm:items-end border-b pb-6 gap-4">
                    <div>
                        <div className="flex items-center gap-2 mb-1">
                            <div className="px-2 py-0.5 bg-primary/10 text-primary text-[10px] sm:text-xs font-bold rounded-full uppercase tracking-wider">AI Diagnostic Center</div>
                            {analyzing && <span className="text-[10px] sm:text-xs text-muted-foreground animate-pulse">正在深度分析中...</span>}
                        </div>
                        <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight">日语 N1 诊断报告</h1>
                        <p className="text-sm text-muted-foreground mt-1">基于 AI 的全方位语言能力评估与预测中心。</p>
                    </div>
                    <Link href="/" className="sm:self-center flex-shrink-0">
                        <Button variant="outline" className="rounded-full whitespace-nowrap w-full sm:w-auto">返回仪表盘</Button>
                    </Link>
                </header>

                {/* AI Summary Highlight */}
                {analysis && (
                    <Card className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white border-none shadow-xl">
                        <CardContent className="p-8">
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-center">
                                <div className="md:col-span-2">
                                    <h2 className="text-2xl font-bold mb-3 flex items-center gap-2">
                                        ✨ AI 核心诊断
                                    </h2>
                                    <p className="text-blue-50 text-lg leading-relaxed mb-4">
                                        {analysis.summary}
                                    </p>
                                    <div className="flex gap-4">
                                        <div className="bg-white/10 px-4 py-2 rounded-lg">
                                            <div className="text-xs text-blue-200">备考状态预测</div>
                                            <div className="font-bold">{analysis.prediction}</div>
                                        </div>
                                    </div>
                                </div>
                                <div className="flex flex-col gap-3">
                                    <div className="text-sm font-medium opacity-80 uppercase tracking-widest">Mastery Overview</div>
                                    {Object.entries(analysis.mastery_scores || {}).map(([key, value]) => (
                                        <div key={key} className="space-y-1">
                                            <div className="flex justify-between text-xs font-bold">
                                                <span>{key === 'grammar' ? '语法' : key === 'vocab' ? '词汇' : '阅读'}</span>
                                                <span>{value}%</span>
                                            </div>
                                            <div className="h-1.5 bg-white/20 rounded-full overflow-hidden">
                                                <div className="h-full bg-white transition-all duration-1000" style={{ width: `${value}%` }}></div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                )}

                {/* Key Metrics Dashboard */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <Card className="bg-secondary/30 border-none">
                        <CardHeader className="pb-1">
                            <CardTitle className="text-xs font-bold text-muted-foreground uppercase">累计练习</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-black">{stats?.total_answered} <span className="text-xs font-normal">题</span></div>
                        </CardContent>
                    </Card>
                    <Card className="bg-secondary/30 border-none">
                        <CardHeader className="pb-1">
                            <CardTitle className="text-xs font-bold text-muted-foreground uppercase">综合正确率</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-black text-green-500">
                                {stats?.total_answered ? ((stats.correct_count / stats.total_answered) * 100).toFixed(1) : 0}%
                            </div>
                        </CardContent>
                    </Card>
                    <Card className="bg-secondary/30 border-none">
                        <CardHeader className="pb-1">
                            <CardTitle className="text-xs font-bold text-muted-foreground uppercase">薄弱考点数</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-black text-orange-500">{stats?.top_wrong_points?.length || 0}</div>
                        </CardContent>
                    </Card>
                    <Card className="bg-secondary/30 border-none">
                        <CardHeader className="pb-1">
                            <CardTitle className="text-xs font-bold text-muted-foreground uppercase">预测等级</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-black">N1 <span className="text-xs font-normal opacity-50">Level</span></div>
                        </CardContent>
                    </Card>
                </div>

                {/* Deep Analysis Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

                    {/* Mastery Charts */}
                    <div className="lg:col-span-2 space-y-8">
                        <Card>
                            <CardHeader className="flex flex-row items-center justify-between">
                                <CardTitle className="text-xl">能力演进趋势</CardTitle>
                                <span className="text-xs text-muted-foreground font-mono">Real-time performance trajectory</span>
                            </CardHeader>
                            <CardContent className="h-[350px]">
                                <ResponsiveContainer width="100%" height="100%">
                                    <LineChart data={stats?.daily_stats}>
                                        <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
                                        <XAxis dataKey="date" fontSize={10} tickLine={false} axisLine={false} />
                                        <YAxis fontSize={10} tickLine={false} axisLine={false} />
                                        <RechartsTooltip
                                            contentStyle={{ backgroundColor: 'hsl(var(--card))', borderRadius: '12px', border: '1px solid hsl(var(--border))', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }}
                                        />
                                        <Line type="stepAfter" dataKey="correct" stroke="hsl(var(--primary))" strokeWidth={4} dot={{ r: 4, fill: 'hsl(var(--primary))' }} activeDot={{ r: 6 }} name="正确回答" />
                                        <Line type="stepAfter" dataKey="wrong" stroke="#ef4444" strokeWidth={2} strokeDasharray="5 5" dot={{ r: 2 }} name="错误记录" />
                                    </LineChart>
                                </ResponsiveContainer>
                            </CardContent>
                        </Card>

                        {/* Weakness Breakdown */}
                        <Card>
                            <CardHeader>
                                <CardTitle className="text-xl">知识薄弱项分布</CardTitle>
                            </CardHeader>
                            <CardContent className="h-[300px]">
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart layout="vertical" data={stats?.top_wrong_points}>
                                        <XAxis type="number" hide />
                                        <YAxis dataKey="point" type="category" width={140} fontSize={11} tickLine={false} axisLine={false} />
                                        <RechartsTooltip cursor={{ fill: 'hsl(var(--secondary))', opacity: 0.5 }} />
                                        <Bar dataKey="count" fill="hsl(var(--primary))" radius={[0, 8, 8, 0]} barSize={24} name="错误频次" />
                                    </BarChart>
                                </ResponsiveContainer>
                            </CardContent>
                        </Card>
                    </div>

                    {/* AI Suggestions Column */}
                    <div className="space-y-8">
                        <Card className="h-full border-primary/20 bg-primary/5">
                            <CardHeader>
                                <CardTitle className="text-xl flex items-center gap-2">
                                    💡 改进建议
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-6">
                                    {analysis?.weakness_analysis?.map((w, i) => (
                                        <div key={i} className="bg-white/50 dark:bg-black/20 p-4 rounded-xl border border-primary/10 transition-all hover:shadow-md">
                                            <div className="font-bold text-primary mb-1 underline decoration-dotted">{w.point}</div>
                                            <div className="text-xs text-muted-foreground mb-2 italic">"{w.reason}"</div>
                                            <div className="text-sm border-l-2 border-primary/30 pl-3 py-1 bg-primary/5 rounded-r-md">
                                                {w.advice}
                                            </div>
                                        </div>
                                    ))}
                                    {(!analysis || !analysis.weakness_analysis) && (
                                        <div className="text-center py-12 text-muted-foreground italic">
                                            正在生成深度改进建议...
                                        </div>
                                    )}
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                </div>

                {/* Training Recommendations */}
                <Card className="border-t-4 border-t-indigo-500 overflow-hidden shadow-2xl">
                    <CardHeader className="bg-indigo-50/50 dark:bg-indigo-950/20">
                        <CardTitle className="text-xl">🎯 针对性强化方案</CardTitle>
                    </CardHeader>
                    <CardContent className="p-0">
                        <TrainingSuggestions suggestions={suggestions} />
                    </CardContent>
                </Card>

            </div>
        </div>
    );
}

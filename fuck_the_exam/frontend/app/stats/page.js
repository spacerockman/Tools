'use client';

import { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/card';
import { BarChart, Bar, XAxis, YAxis, Tooltip as RechartsTooltip, ResponsiveContainer, LineChart, Line, CartesianGrid } from 'recharts';
import { Loader2 } from 'lucide-react';
import TrainingSuggestions from '../../components/TrainingSuggestions';
import Link from 'next/link';
import { Button } from '../../components/ui/button';

export default function StatsPage() {
    const [stats, setStats] = useState(null);
    const [suggestions, setSuggestions] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchData() {
            try {
                // Fetch Stats
                const statsRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/stats`);
                const statsData = await statsRes.json();
                setStats(statsData);

                // Fetch Suggestions (Mock/Real)
                // Since we don't have a real filtering logic in KnowledgeService yet matching stats,
                // we'll fetch general suggestions. Ideally backend does this join.
                // Let's use the top wrong points from stats to filter knowledge points if possible,
                // or just rely on backend suggestions endpoint if it was smart. 
                // Our planned backend endpoint just returns all points.
                // Let's just map "Top Wrong" to suggestions for UI.

                const wrongPoints = statsData.top_wrong_points || [];
                // Convert to suggestion format
                const sugData = wrongPoints.map(wp => ({
                    point: wp.point,
                    description: `You missed this ${wp.count} times.`
                }));
                setSuggestions(sugData);

            } catch (e) {
                console.error("Failed to load stats", e);
            } finally {
                setLoading(false);
            }
        }
        fetchData();
    }, []);

    if (loading) {
        return (
            <div className="flex h-screen items-center justify-center">
                <Loader2 className="animate-spin w-8 h-8 text-primary" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-background p-8">
            <div className="max-w-6xl mx-auto space-y-8">

                <header className="flex justify-between items-center">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight">Your Progress</h1>
                        <p className="text-muted-foreground">Analyze your strengths and weaknesses.</p>
                    </div>
                    <Link href="/">
                        <Button variant="outline">Back to Dashboard</Button>
                    </Link>
                </header>

                {/* Key Metrics */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <Card>
                        <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-medium text-muted-foreground">Total Answered</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-3xl font-bold">{stats?.total_answered}</div>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-medium text-muted-foreground">Correct Rate</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-3xl font-bold text-green-600">
                                {stats?.total_answered ? ((stats.correct_count / stats.total_answered) * 100).toFixed(1) : 0}%
                            </div>
                            <p className="text-xs text-muted-foreground">{stats?.correct_count} Correct / {stats?.wrong_count} Wrong</p>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-medium text-muted-foreground">Current Streak</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-3xl font-bold">--</div>
                            <p className="text-xs text-muted-foreground">Keep it up!</p>
                        </CardContent>
                    </Card>
                </div>

                {/* Charts Row */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    {/* Daily Accuracy Trend */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="text-lg">Daily Accuracy Trend</CardTitle>
                        </CardHeader>
                        <CardContent className="h-[300px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={stats?.daily_stats}>
                                    <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                                    <XAxis dataKey="date" fontSize={12} tickLine={false} axisLine={false} />
                                    <YAxis fontSize={12} tickLine={false} axisLine={false} />
                                    <RechartsTooltip
                                        contentStyle={{ backgroundColor: 'var(--background)', borderRadius: '8px', border: '1px solid var(--border)' }}
                                    />
                                    <Line type="monotone" dataKey="correct" stroke="#16a34a" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} name="Correct" />
                                    <Line type="monotone" dataKey="wrong" stroke="#ef4444" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} name="Wrong" />
                                </LineChart>
                            </ResponsiveContainer>
                        </CardContent>
                    </Card>

                    {/* Weakest Points Bar Chart */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="text-lg">Top 5 Weak Points</CardTitle>
                        </CardHeader>
                        <CardContent className="h-[300px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart layout="vertical" data={stats?.top_wrong_points}>
                                    <CartesianGrid strokeDasharray="3 3" opacity={0.2} horizontal={true} vertical={false} />
                                    <XAxis type="number" hide />
                                    <YAxis dataKey="point" type="category" width={120} fontSize={11} tickLine={false} axisLine={false} />
                                    <RechartsTooltip cursor={{ fill: 'transparent' }} />
                                    <Bar dataKey="count" fill="#f59e0b" radius={[0, 4, 4, 0]} barSize={20} name="Mistakes" />
                                </BarChart>
                            </ResponsiveContainer>
                        </CardContent>
                    </Card>
                </div>

                {/* Suggestions & Wrong Questions Link */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    <div className="lg:col-span-2">
                        <Card>
                            <CardContent className="pt-6">
                                <TrainingSuggestions suggestions={suggestions} />
                            </CardContent>
                        </Card>
                    </div>
                    <div>
                        <Link href="/wrong-questions" className="block h-full">
                            <Card className="h-full bg-gradient-to-br from-indigo-500 to-purple-600 text-white hover:opacity-90 transition">
                                <CardContent className="flex flex-col items-center justify-center h-full p-8 text-center space-y-4">
                                    <h3 className="text-2xl font-bold">Review Black Book</h3>
                                    <p className="text-indigo-100">
                                        42 Questions pending review.
                                    </p>
                                    <Button variant="secondary" size="lg" className="w-full">
                                        Start Review
                                    </Button>
                                </CardContent>
                            </Card>
                        </Link>
                    </div>
                </div>

            </div>
        </div>
    );
}

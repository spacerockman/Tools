'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { generateQuiz, getStudySession } from '../lib/api';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';

export default function Dashboard() {
  const router = useRouter();
  const [topic, setTopic] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [feedback, setFeedback] = useState({ type: '', message: '' });

  const handleGenerate = async (e) => {
    e.preventDefault();
    if (!topic.trim()) {
      setFeedback({ type: 'error', message: '请输入一个 N1 考点！' });
      return;
    }

    setIsLoading(true);
    setFeedback({ type: '', message: '' });

    try {
      const response = await generateQuiz(topic, 5);
      localStorage.setItem('currentQuestions', JSON.stringify(response));
      localStorage.setItem('currentTopic', topic);
      router.push('/quiz/session');
    } catch (error) {
      console.error(error);
      const errorMessage = error.response?.data?.detail || '生成失败，请检查后端服务。';
      setFeedback({ type: 'error', message: errorMessage });
    } finally {
      setIsLoading(false);
    }
  };

  const handleStudy = async () => {
    setIsLoading(true);
    setFeedback({ type: '', message: '' });
    try {
      const response = await getStudySession();
      if (response.length === 0) {
        setFeedback({ type: 'info', message: '暂无待复习题目或新题，请先生成一些题目！' });
        return;
      }
      localStorage.setItem('currentQuestions', JSON.stringify(response));
      localStorage.setItem('currentTopic', 'Daily Study Session');
      router.push('/quiz/session');
    } catch (error) {
      console.error(error);
      setFeedback({ type: 'error', message: '获取复习计划失败。' });
    } finally {
      setIsLoading(false);
    }
  };

  const quickTopics = ["N1 Grammar: ～ざるを得ない", "N1 Reading: Philosophy", "N1 Vocabulary: Synonyms"];

  return (
    <div className="min-h-screen bg-background p-8">
      <header className="mb-12 flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold tracking-tight mb-2">My N1 Journey</h1>
          <p className="text-muted-foreground">Keep pushing. Consistency is key.</p>
        </div>
        <div className="flex gap-4">
          {/* Placeholder for user profile */}
          <div className="h-10 w-10 rounded-full bg-secondary"></div>
        </div>
      </header>

      <main className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-7xl mx-auto">

        {/* Left Column: Generator */}
        <div className="md:col-span-2 space-y-8">
          <Card>
            <CardHeader>
              <CardTitle>⚡️ Quick Start Quiz</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="mb-6 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-slate-900 dark:to-slate-800 p-6 rounded-lg border border-blue-100 dark:border-slate-700">
                <h3 className="font-bold text-lg mb-2">📅 Daily Study Session (SRS)</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Review due questions based on Ebbinghaus curve + Learn new items.
                </p>
                <Button onClick={handleStudy} className="w-full bg-indigo-600 hover:bg-indigo-700 text-white" disabled={isLoading}>
                  Start My Daily Review
                </Button>
              </div>

              <div className="relative mb-6">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-background px-2 text-muted-foreground">Or Generate New</span>
                </div>
              </div>

              <form onSubmit={handleGenerate} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Target Topic</label>
                  <input
                    type="text"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    placeholder="e.g. Grammar: ～なしに"
                    className="w-full flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    disabled={isLoading}
                  />
                </div>

                <div className="flex flex-wrap gap-2">
                  {quickTopics.map(t => (
                    <button
                      key={t}
                      type="button"
                      onClick={() => setTopic(t)}
                      className="text-xs bg-secondary text-secondary-foreground px-2 py-1 rounded hover:bg-secondary/80 transition"
                    >
                      {t}
                    </button>
                  ))}
                </div>

                <div className="pt-2">
                  <Button type="submit" className="w-full" disabled={isLoading}>
                    {isLoading ? (
                      <span className="flex items-center gap-2">
                        <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Generating N1 Context...
                      </span>
                    ) : 'Generate Quiz'}
                  </Button>
                </div>

                {feedback.message && (
                  <p className={`text-sm ${feedback.type === 'error' ? 'text-destructive' : 'text-green-600'}`}>
                    {feedback.message}
                  </p>
                )}
              </form>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Link href="/wrong-questions" className="block">
              <Card className="hover:bg-accent/50 transition cursor-pointer h-full">
                <CardHeader>
                  <CardTitle className="text-lg">📖 Review Mistakes</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground text-sm">Target your weak points. Repetition is the mother of learning.</p>
                </CardContent>
              </Card>
            </Link>
            {/* Future Feature */}
            <Card className="opacity-50 h-full">
              <CardHeader>
                <CardTitle className="text-lg">🗣️ Shadowing (Coming Soon)</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground text-sm">Practice pronunciation and intonation.</p>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Right Column: Stats & Logs */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Daily Progress</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold mb-1">80%</div>
              <p className="text-xs text-muted-foreground">Average accuracy today</p>
              <div className="mt-4 h-2 bg-secondary rounded-full overflow-hidden">
                <div className="h-full bg-primary w-[80%]"></div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Recent Logs</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-4">
                <li className="flex justify-between items-center text-sm">
                  <span className="truncate max-w-[150px]">Grammar: ～ざるを得ない</span>
                  <span className="text-muted-foreground">10m ago</span>
                </li>
                <li className="flex justify-between items-center text-sm">
                  <span className="truncate max-w-[150px]">Reading: Philosophy</span>
                  <span className="text-muted-foreground">2h ago</span>
                </li>
                <li className="flex justify-between items-center text-sm">
                  <span className="truncate max-w-[150px]">Vocab: Compound Verbs</span>
                  <span className="text-muted-foreground">Yesterday</span>
                </li>
              </ul>
            </CardContent>
          </Card>
        </div>

      </main>
    </div>
  );
}

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Question from '../../../components/Question';
import { Button } from '../../../components/ui/button';
import { Card, CardContent } from '../../../components/ui/card';
import { finishQuiz } from '../../../lib/api';

export default function QuizSession() {
    const router = useRouter();
    const [questions, setQuestions] = useState([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(true);
    const [topic, setTopic] = useState('');

    useEffect(() => {
        // Load questions from localStorage
        const savedQuestions = localStorage.getItem('currentQuestions');
        const savedTopic = localStorage.getItem('currentTopic') || 'General Practice';

        if (savedQuestions) {
            setQuestions(JSON.parse(savedQuestions));
            setTopic(savedTopic);
            setLoading(false);
        } else {
            // Redirect back if no questions
            router.push('/');
        }
    }, [router]);

    const handleNext = async (result) => {
        let currentResults = results;
        if (!result.deleted) {
            currentResults = [...results, result];
            setResults(currentResults);
        }

        if (currentIndex < questions.length - 1) {
            setCurrentIndex(currentIndex + 1);
        } else {
            // Quiz Finished
            if (currentResults.length > 0) {
                await handleFinish(currentResults);
            } else {
                router.push('/');
            }
        }
    };

    const handleFinish = async (finalResults) => {
        try {
            // Log session to backend
            await finishQuiz(topic, finalResults);
            // Clear storage
            localStorage.removeItem('currentQuestions');
            localStorage.removeItem('currentTopic');
            // Go to dashboard or results page (Dashboard for now)
            router.push('/');
        } catch (error) {
            console.error("Error logging session:", error);
            // Even if logging fails, go back
            router.push('/');
        }
    };

    const handleQuit = async () => {
        if (results.length > 0) {
            if (window.confirm(`已完成 ${results.length} 道题。是否保存进度并退出？`)) {
                await handleFinish(results);
            } else if (window.confirm('确定要直接退出吗？（本次练习进度将不会被记录）')) {
                localStorage.removeItem('currentQuestions');
                localStorage.removeItem('currentTopic');
                router.push('/');
            }
        } else {
            localStorage.removeItem('currentQuestions');
            localStorage.removeItem('currentTopic');
            router.push('/');
        }
    };

    if (loading) return <div className="flex h-screen items-center justify-center">正在加载...</div>;

    const progress = (currentIndex / questions.length) * 100;

    return (
        <div className="min-h-screen bg-background p-4 md:p-8">
            <div className="max-w-2xl mx-auto mb-8">
                <div className="flex justify-between items-end mb-2">
                    <h2 className="text-xl font-bold">{topic}</h2>
                    <span className="text-sm text-muted-foreground">{currentIndex + 1} / {questions.length}</span>
                </div>
                <div className="h-2 bg-secondary rounded-full overflow-hidden">
                    <div
                        className="h-full bg-primary transition-all duration-300"
                        style={{ width: `${progress}%` }}
                    ></div>
                </div>
            </div>

            <Question
                key={currentIndex} // Force re-render on new question
                question={questions[currentIndex]}
                onNext={handleNext}
            />

            <div className="mt-8 text-center">
                <Button variant="ghost" onClick={handleQuit} size="sm">
                    中途退出
                </Button>
            </div>
        </div>
    );
}

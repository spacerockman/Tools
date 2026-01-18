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
            const parsedQuestions = JSON.parse(savedQuestions);
            setQuestions(parsedQuestions);
            setTopic(savedTopic);
            setResults(new Array(parsedQuestions.length).fill(null));
            setLoading(false);
        } else {
            // Redirect back if no questions
            router.push('/');
        }
    }, [router]);

    const handleNext = async (result) => {
        const newResults = [...results];

        if (result.skipped) {
            // If deleted, we might need special handling, but for now just keep null
        } else {
            newResults[currentIndex] = result;
            setResults(newResults);
        }

        const shouldAdvance = result.autoAdvance !== false;

        if (shouldAdvance) {
            if (currentIndex < questions.length - 1) {
                setCurrentIndex(currentIndex + 1);
            } else {
                // Check if all questions are answered or if we should just finish
                const finishedResults = newResults.filter(r => r !== null && !r.skipped);
                if (finishedResults.length > 0) {
                    await handleFinish(finishedResults);
                } else {
                    router.push('/');
                }
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
        const activeResults = results.filter(r => r !== null);
        if (activeResults.length > 0) {
            if (window.confirm(`已完成 ${activeResults.length} 道题。是否保存进度并退出？`)) {
                await handleFinish(activeResults);
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

    if (questions.length === 0) {
        router.push('/');
        return null;
    }

    const progress = (currentIndex / questions.length) * 100;

    return (
        <div className="min-h-screen bg-background p-4 md:p-8">
            <div className="max-w-2xl mx-auto mb-8">
                <div className="flex justify-between items-center mb-4">
                    <h2 className="text-xl font-bold">{topic}</h2>
                    <span className="text-sm font-medium bg-muted px-3 py-1 rounded-full">
                        {currentIndex + 1} / {questions.length}
                    </span>
                </div>

                {/* Clickable Navigation Grid */}
                <div className="flex flex-wrap gap-2 mb-6">
                    {questions.map((_, index) => {
                        const isCurrent = index === currentIndex;
                        const isAnswered = results[index] !== null;
                        const isCorrect = results[index]?.is_correct;

                        let btnClass = "w-10 h-10 rounded-lg flex items-center justify-center text-sm font-bold transition-all border-2 ";

                        if (isCurrent) {
                            btnClass += "border-primary bg-primary/10 text-primary scale-110 z-10 shadow-md";
                        } else if (isAnswered) {
                            if (isCorrect) {
                                btnClass += "bg-green-100 border-green-500 text-green-700 dark:bg-green-900/30 dark:text-green-400";
                            } else {
                                btnClass += "bg-red-100 border-red-500 text-red-700 dark:bg-red-900/30 dark:text-red-400";
                            }
                        } else {
                            btnClass += "border-muted-foreground/20 bg-muted/50 text-muted-foreground hover:border-muted-foreground/40";
                        }

                        return (
                            <button
                                key={index}
                                onClick={() => setCurrentIndex(index)}
                                className={btnClass}
                            >
                                {index + 1}
                            </button>
                        );
                    })}
                </div>
            </div>

            <Question
                key={currentIndex}
                question={questions[currentIndex]}
                initialResult={results[currentIndex]}
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

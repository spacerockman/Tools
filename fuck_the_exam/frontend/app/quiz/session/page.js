'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Question from '../../../components/Question';
import { Button } from '../../../components/ui/button';
import { Card, CardContent } from '../../../components/ui/card';
import { finishQuiz } from '../../../lib/api';

const getApiBase = () => {
    if (typeof window === 'undefined') return '';
    const { protocol, hostname } = window.location;
    return `${protocol}//${hostname}:28888`;
};

const normalizeResults = (questionsList, storedResults) => {
    if (!Array.isArray(questionsList) || questionsList.length === 0) return [];
    const resultsArray = Array.isArray(storedResults) ? storedResults : [];
    return questionsList.map((question, index) => {
        const raw = resultsArray[index];
        if (!raw) return null;
        const correctAnswer = raw?.result_details?.correct_answer || question?.correct_answer;
        const isCorrect = typeof raw?.is_correct === 'boolean'
            ? raw.is_correct
            : typeof raw?.is_correct === 'number'
                ? raw.is_correct === 1
                : (raw?.selected_answer && correctAnswer ? raw.selected_answer === correctAnswer : raw?.result_details?.is_correct);

        const resultDetails = raw?.result_details || (correctAnswer ? {
            ...raw,
            correct_answer: correctAnswer,
            explanation: raw?.result_details?.explanation || question?.explanation,
            memorization_tip: raw?.result_details?.memorization_tip || question?.memorization_tip,
            is_correct: isCorrect
        } : null);

        return {
            ...raw,
            is_correct: isCorrect,
            result_details: resultDetails
        };
    });
};

export default function QuizSession() {
    const router = useRouter();
    const [questions, setQuestions] = useState([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(true);
    const [topic, setTopic] = useState('');

    const saveSession = async (payload) => {
        try {
            await fetch(`${getApiBase()}/api/quiz/session`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        } catch (error) {
            console.error('Failed to sync session:', error);
        }
    };

    const clearSession = async () => {
        try {
            await fetch(`${getApiBase()}/api/quiz/session?session_key=default`, {
                method: 'DELETE'
            });
        } catch (error) {
            console.error('Failed to clear session:', error);
        }
    };

    const persistIndex = (index) => {
        localStorage.setItem('currentIndex', String(index));
        setCurrentIndex(index);
    };

    const applySession = (session) => {
        const { questions: sessionQuestions, results: sessionResults, topic: sessionTopic, currentIndex: sessionIndex } = session;
        localStorage.setItem('currentQuestions', JSON.stringify(sessionQuestions || []));
        localStorage.setItem('currentTopic', sessionTopic || 'General Practice');
        localStorage.setItem('currentResults', JSON.stringify(sessionResults || []));
        localStorage.setItem('currentIndex', String(sessionIndex || 0));
        if (session.updatedAt) {
            localStorage.setItem('sessionUpdatedAt', session.updatedAt);
        }

        setQuestions(sessionQuestions || []);
        setTopic(sessionTopic || 'General Practice');
        const resultsData = normalizeResults(sessionQuestions || [], sessionResults || []);
        setResults(resultsData.length ? resultsData : new Array((sessionQuestions || []).length).fill(null));
        setCurrentIndex(Math.min(sessionIndex || 0, (sessionQuestions || []).length - 1));
        setLoading(false);
    };

    useEffect(() => {
        const loadSession = async () => {
            try {
                const response = await fetch(`${getApiBase()}/api/quiz/session?session_key=default`);
                const data = await response.json();
                const savedQuestions = localStorage.getItem('currentQuestions');
                const savedTopic = localStorage.getItem('currentTopic') || 'General Practice';
                const savedResults = localStorage.getItem('currentResults');
                const savedIndex = localStorage.getItem('currentIndex');
                const savedUpdatedAt = localStorage.getItem('sessionUpdatedAt');

                const localSession = savedQuestions ? {
                    questions: JSON.parse(savedQuestions),
                    topic: savedTopic,
                    results: savedResults ? JSON.parse(savedResults) : [],
                    currentIndex: parseInt(savedIndex, 10) || 0,
                    updatedAt: savedUpdatedAt
                } : null;

                const serverSession = data?.exists ? {
                    questions: data.questions || [],
                    topic: data.topic || 'General Practice',
                    results: data.results || [],
                    currentIndex: data.current_index || 0,
                    updatedAt: data.updated_at
                } : null;

                if (localSession && serverSession) {
                    const localTime = localSession.updatedAt ? Date.parse(localSession.updatedAt) : 0;
                    const serverTime = serverSession.updatedAt ? Date.parse(serverSession.updatedAt) : 0;
                    if (serverTime > localTime) {
                        applySession(serverSession);
                        return;
                    }

                    applySession(localSession);
                    await saveSession({
                        session_key: 'default',
                        topic: localSession.topic,
                        questions: localSession.questions,
                        results: localSession.results,
                        current_index: localSession.currentIndex
                    });
                    return;
                }

                if (serverSession) {
                    applySession(serverSession);
                    return;
                }

                if (localSession) {
                    applySession(localSession);
                    await saveSession({
                        session_key: 'default',
                        topic: localSession.topic,
                        questions: localSession.questions,
                        results: localSession.results,
                        current_index: localSession.currentIndex
                    });
                    return;
                }
            } catch (error) {
                console.error('Failed to load session:', error);
            }

            router.push('/');
        };

        loadSession();
    }, [router]);

    useEffect(() => {
        if (loading || questions.length === 0) return;
        const updatedAt = new Date().toISOString();
        localStorage.setItem('sessionUpdatedAt', updatedAt);
        const payload = {
            session_key: 'default',
            topic,
            questions,
            results,
            current_index: currentIndex
        };
        saveSession(payload);
    }, [loading, questions, results, currentIndex, topic]);

    const handleNext = async (result) => {
        const newResults = [...results];

        if (result.skipped) {
            // If deleted, we might need special handling, but for now just keep null
        } else {
            newResults[currentIndex] = result;
            setResults(newResults);
        }

        // Sync to localStorage for Resume feature
        // storage format: { questions: [], topic: "", results: [] } 
        // We already have 'currentQuestions' and 'currentTopic'. Let's add 'currentResults'.
        localStorage.setItem('currentResults', JSON.stringify(newResults));
        localStorage.setItem('currentIndex', String(currentIndex));

        const shouldAdvance = result.autoAdvance !== false;

        if (shouldAdvance) {
            if (currentIndex < questions.length - 1) {
                persistIndex(currentIndex + 1);
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
            localStorage.removeItem('currentResults');
            localStorage.removeItem('currentIndex');
            await clearSession();
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
        // Custom confirm dialog logic could be better, but using window.confirm for simplicity
        if (window.confirm('要暂停并退出吗？\n\n点击 [确定] 保存进度并退出（可以在首页恢复）。\n点击 [取消] 继续做题。')) {
            // Just redirect, storage is already there
            router.push('/');
        }
    };

    const handleQuestionUpdate = (index, changes) => {
        const newQuestions = [...questions];
        newQuestions[index] = { ...newQuestions[index], ...changes };
        setQuestions(newQuestions);
        localStorage.setItem('currentQuestions', JSON.stringify(newQuestions));
    };

    const handleQuestionDelete = (index) => {
        const newQuestions = questions.filter((_, i) => i !== index);
        const newResults = results.filter((_, i) => i !== index);

        setQuestions(newQuestions);
        setResults(newResults);

        localStorage.setItem('currentQuestions', JSON.stringify(newQuestions));
        localStorage.setItem('currentResults', JSON.stringify(newResults));

        // Adjust currentIndex if necessary
        if (index < currentIndex) {
            persistIndex(currentIndex - 1);
        } else if (index === currentIndex) {
            if (newQuestions.length === 0) {
                router.push('/');
            } else if (index >= newQuestions.length) {
                // Deleted the last item, move back one
                persistIndex(Math.max(0, currentIndex - 1));
            }
            // If deleted current and there are more after it, index stays same (effectively moves to next)
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
                                onClick={() => persistIndex(index)}
                                className={btnClass}
                            >
                                {index + 1}
                            </button>
                        );
                    })}
                </div>
            </div>

            <Question
                key={`${currentIndex}-${questions[currentIndex].id}`} // Ensure re-mount on index change or question change
                question={questions[currentIndex]}
                initialResult={results[currentIndex]}
                onNext={handleNext}
                onUpdate={(changes) => handleQuestionUpdate(currentIndex, changes)}
                onDelete={() => handleQuestionDelete(currentIndex)}
            />

            <div className="mt-8 text-center">
                <Button variant="ghost" onClick={handleQuit} size="sm">
                    中途退出
                </Button>
            </div>
        </div>
    );
}

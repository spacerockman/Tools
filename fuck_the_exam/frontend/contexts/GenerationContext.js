'use client';

import { createContext, useContext, useState, useCallback } from 'react';
import { generateQuiz } from '../lib/api';

const GenerationContext = createContext(null);

export function GenerationProvider({ children }) {
    const [isGenerating, setIsGenerating] = useState(false);
    const [generationStatus, setGenerationStatus] = useState('');
    const [generatedQuestions, setGeneratedQuestions] = useState(null);
    const [error, setError] = useState(null);

    const startGeneration = useCallback(async (topic, numQuestions) => {
        setIsGenerating(true);
        setError(null);
        setGenerationStatus('🔗 连接AI服务...');

        // Progress stages
        const stages = [
            { message: '🧠 AI正在分析知识点...', delay: 3000 },
            { message: '✍️ 生成题目中...', delay: 15000 },
            { message: '📝 整理题目格式...', delay: 30000 },
            { message: '⏳ 请稍等，AI正在努力工作...', delay: 60000 },
            { message: '🔄 仍在处理中，请耐心等待...', delay: 60000 },
            { message: '⌛ 快完成了，再等一下...', delay: 120000 },
        ];

        let stageIndex = 0;
        const stageTimer = setInterval(() => {
            if (stageIndex < stages.length) {
                setGenerationStatus(stages[stageIndex].message);
                stageIndex++;
            }
        }, stages[stageIndex]?.delay || 30000);

        try {
            const response = await generateQuiz(topic, numQuestions);
            setGeneratedQuestions(response);
            localStorage.setItem('currentQuestions', JSON.stringify(response));
            localStorage.setItem('currentTopic', topic);
            setGenerationStatus('✅ 生成完成！点击开始答题');

            // Auto-clear success after 10 seconds
            setTimeout(() => {
                if (generationStatus.includes('完成')) {
                    setGenerationStatus('');
                    setIsGenerating(false);
                }
            }, 10000);

        } catch (err) {
            console.error(err);
            setError(err.response?.data?.detail || '生成失败，AI服务可能繁忙，请稍后重试。');
            setGenerationStatus('');
        } finally {
            clearInterval(stageTimer);
            if (!generatedQuestions) {
                setIsGenerating(false);
            }
        }
    }, []);

    const clearGeneration = useCallback(() => {
        setIsGenerating(false);
        setGenerationStatus('');
        setGeneratedQuestions(null);
        setError(null);
    }, []);

    return (
        <GenerationContext.Provider value={{
            isGenerating,
            generationStatus,
            generatedQuestions,
            error,
            startGeneration,
            clearGeneration,
        }}>
            {children}
        </GenerationContext.Provider>
    );
}

export function useGeneration() {
    const context = useContext(GenerationContext);
    if (!context) {
        throw new Error('useGeneration must be used within GenerationProvider');
    }
    return context;
}

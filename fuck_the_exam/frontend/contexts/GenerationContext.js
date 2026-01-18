'use client';

import { createContext, useContext, useState, useCallback } from 'react';
import { generateQuiz } from '../lib/api';

const GenerationContext = createContext(null);

export function GenerationProvider({ children }) {
    const [isGenerating, setIsGenerating] = useState(false);
    const [generationStatus, setGenerationStatus] = useState('');
    const [generatedQuestions, setGeneratedQuestions] = useState(null);
    const [error, setError] = useState(null);

    const startGeneration = useCallback(async (topic, numQuestions, isBatch = false) => {
        setIsGenerating(true);
        setError(null);
        setGeneratedQuestions(null);

        const updateStatus = (msg) => {
            setGenerationStatus(isBatch ? `[批量处理] ${msg}` : msg);
        };

        updateStatus('🔗 连接AI服务...');

        // Progress stages
        const stages = [
            { message: '🧠 AI正在分析知识点...', delay: 3000 },
            { message: '✍️ 生成题目中...', delay: 15000 },
            { message: '📝 整理题目格式...', delay: 30000 },
            { message: '⌛ 深度优化解析中...', delay: 45000 },
        ];

        let stageIndex = 0;
        const stageTimer = setInterval(() => {
            if (stageIndex < stages.length) {
                updateStatus(stages[stageIndex].message);
                stageIndex++;
            }
        }, 15000); // Slower updates

        try {
            const response = await generateQuiz(topic, numQuestions);
            setGeneratedQuestions(response);
            localStorage.setItem('currentQuestions', JSON.stringify(response));
            localStorage.setItem('currentTopic', topic);

            if (!isBatch) {
                setGenerationStatus('✅ 生成完成！点击开始答题');
                setTimeout(() => {
                    setGenerationStatus((prev) => prev.includes('完成') ? '' : prev);
                    setIsGenerating(false);
                }, 5000);
            } else {
                updateStatus(`✅ ${topic} 生成成功`);
            }
            return response;
        } catch (err) {
            console.error(err);
            const msg = err.response?.data?.detail || '生成失败，AI服务可能繁忙，请稍后重试。';
            setError(msg);
            if (!isBatch) {
                setGenerationStatus('');
                setIsGenerating(false);
            }
            throw err; // Re-throw for batch handler
        } finally {
            clearInterval(stageTimer);
            if (!isBatch) {
                // For batch, the batch handler will set this to false at the end
                // But for single, if it failed, we must set it to false
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
            setIsGenerating,
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

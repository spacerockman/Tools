'use client';

import { useGeneration } from '../contexts/GenerationContext';
import { useRouter } from 'next/navigation';
import { X } from 'lucide-react';

export default function GenerationToast() {
    const { isGenerating, generationStatus, generatedQuestions, error, clearGeneration } = useGeneration();
    const router = useRouter();

    if (!isGenerating && !error && !generatedQuestions) return null;

    const handleGoToQuiz = () => {
        clearGeneration();
        router.push('/quiz/session');
    };

    return (
        <div className="fixed bottom-4 right-4 z-50 max-w-sm">
            {/* Error State */}
            {error && (
                <div className="bg-red-500 text-white p-4 rounded-lg shadow-xl animate-in slide-in-from-bottom-2">
                    <div className="flex justify-between items-start gap-2">
                        <div>
                            <p className="font-medium">生成失败</p>
                            <p className="text-sm text-red-100">{error}</p>
                        </div>
                        <button onClick={clearGeneration} className="text-white/70 hover:text-white">
                            <X className="w-4 h-4" />
                        </button>
                    </div>
                </div>
            )}

            {/* Generating State */}
            {isGenerating && !generatedQuestions && (
                <div className="bg-gradient-to-r from-indigo-500 to-purple-600 text-white p-4 rounded-lg shadow-xl">
                    <div className="flex items-center gap-3 mb-2">
                        <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        <span className="font-medium">{generationStatus}</span>
                    </div>
                    <p className="text-xs text-white/70">
                        后台生成中，你可以继续浏览其他页面
                    </p>
                </div>
            )}

            {/* Success State */}
            {generatedQuestions && (
                <div className="bg-green-500 text-white p-4 rounded-lg shadow-xl animate-in slide-in-from-bottom-2">
                    <div className="flex justify-between items-start gap-2 mb-3">
                        <div>
                            <p className="font-medium">✅ 生成完成！</p>
                            <p className="text-sm text-green-100">已生成 {generatedQuestions.length} 道题目</p>
                        </div>
                        <button onClick={clearGeneration} className="text-white/70 hover:text-white">
                            <X className="w-4 h-4" />
                        </button>
                    </div>
                    <button
                        onClick={handleGoToQuiz}
                        className="w-full bg-white text-green-600 font-medium py-2 rounded hover:bg-green-50 transition"
                    >
                        开始答题 →
                    </button>
                </div>
            )}
        </div>
    );
}

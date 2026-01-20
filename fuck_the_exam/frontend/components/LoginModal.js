'use client';

import React, { useState } from 'react';
import { useUser } from '../contexts/UserContext';
import { User, LogIn, Plus, BookOpen, Database, ShieldCheck } from 'lucide-react';

export default function LoginModal() {
    const {
        user,
        availableUsers,
        loading,
        showLoginModal,
        login,
        loginWithPassword,
        handleCreateUser,
        examType,
        switchMode
    } = useUser();

    const [newUsername, setNewUsername] = useState('');
    const [password, setPassword] = useState('');
    const [selectedUser, setSelectedUser] = useState(null);
    const [isCreating, setIsCreating] = useState(false);
    const [error, setError] = useState('');

    if (loading || !showLoginModal) return null;

    const handleNewUserSubmit = async (e) => {
        e.preventDefault();
        setError('');
        if (!newUsername.trim() || !password.trim()) {
            setError('Both name and password are required');
            return;
        }
        try {
            await handleCreateUser(newUsername.trim(), password.trim());
            setNewUsername('');
            setPassword('');
            setIsCreating(false);
        } catch (e) {
            setError(e.message);
        }
    };

    const handleLoginSubmit = async (e) => {
        e.preventDefault();
        setError('');
        try {
            await loginWithPassword(selectedUser.username, password);
            setPassword('');
            setSelectedUser(null);
        } catch (e) {
            setError(e.message);
        }
    };

    return (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/80 backdrop-blur-md p-4">
            <div className="w-full max-w-2xl bg-[#1e1e2d] border border-white/10 rounded-3xl overflow-hidden shadow-2xl flex flex-col md:flex-row">

                {/* Left: App Info */}
                <div className="md:w-5/12 p-8 bg-gradient-to-br from-indigo-600 to-purple-700 flex flex-col justify-center items-center text-center text-white">
                    <div className="w-20 h-20 bg-white/20 backdrop-blur-xl rounded-2xl flex items-center justify-center mb-6 shadow-xl">
                        <ShieldCheck size={48} className="text-white" />
                    </div>
                    <h1 className="text-3xl font-extrabold mb-2 tracking-tight">Antigravity</h1>
                    <p className="text-indigo-100/80 text-sm leading-relaxed max-w-[150px]">
                        Personalized Exam Mastery System
                    </p>
                </div>

                {/* Right: Forms */}
                <div className="md:w-7/12 p-8 bg-[#1e1e2d] flex flex-col">
                    <div className="mb-8">
                        <h2 className="text-2xl font-bold text-white mb-2">Access Portal</h2>
                        <p className="text-slate-400 text-sm">Please select your profile or register to continue.</p>
                    </div>

                    {/* User Selection */}
                    <div className="flex-1 overflow-y-auto max-h-[350px] pr-2 custom-scrollbar">
                        <label className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3 block">Existing Profiles</label>

                        {error && (
                            <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-xs font-medium flex items-center space-x-2">
                                <span>⚠️</span>
                                <span>{error}</span>
                            </div>
                        )}

                        <div className="space-y-2 mb-6">
                            {availableUsers.map(u => (
                                <div key={u.id} className="w-full">
                                    <button
                                        onClick={() => {
                                            setError('');
                                            setSelectedUser(selectedUser?.id === u.id ? null : u);
                                        }}
                                        className={`w-full flex items-center justify-between p-4 border rounded-2xl transition-all group ${selectedUser?.id === u.id
                                            ? 'bg-indigo-600/10 border-indigo-500'
                                            : 'bg-white/5 border-white/5 hover:bg-white/10'
                                            }`}
                                    >
                                        <div className="flex items-center space-x-3">
                                            <div className={`w-10 h-10 rounded-full flex items-center justify-center transition-colors ${selectedUser?.id === u.id ? 'bg-indigo-600 text-white' : 'bg-slate-700 text-slate-300'
                                                }`}>
                                                <User size={18} />
                                            </div>
                                            <span className="text-slate-200 font-medium">{u.username}</span>
                                        </div>
                                        <LogIn size={16} className={selectedUser?.id === u.id ? 'text-indigo-400' : 'text-slate-500'} />
                                    </button>

                                    {selectedUser?.id === u.id && (
                                        <form onSubmit={handleLoginSubmit} className="mt-2 p-3 bg-indigo-600/5 rounded-xl border border-indigo-500/20 flex space-x-2 animate-in fade-in slide-in-from-top-2 duration-300">
                                            <input
                                                autoFocus
                                                type="password"
                                                placeholder="Password"
                                                value={password}
                                                onChange={(e) => setPassword(e.target.value)}
                                                className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white placeholder:text-slate-600 focus:outline-none focus:border-indigo-500 transition-colors"
                                            />
                                            <button
                                                type="submit"
                                                className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-bold transition-colors"
                                            >
                                                Go
                                            </button>
                                        </form>
                                    )}
                                </div>
                            ))}
                        </div>

                        {isCreating ? (
                            <form onSubmit={handleNewUserSubmit} className="mt-4 p-4 border border-indigo-500/30 bg-indigo-500/5 rounded-2xl animate-in zoom-in-95 duration-300">
                                <label className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest mb-2 block">Quick Registration</label>
                                <div className="space-y-2">
                                    <input
                                        autoFocus
                                        type="text"
                                        placeholder="Username"
                                        value={newUsername}
                                        onChange={(e) => setNewUsername(e.target.value)}
                                        className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-white placeholder:text-slate-600 focus:outline-none focus:border-indigo-500 transition-colors"
                                    />
                                    <div className="flex space-x-2">
                                        <input
                                            type="password"
                                            placeholder="Set Password"
                                            value={password}
                                            onChange={(e) => setPassword(e.target.value)}
                                            className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-white placeholder:text-slate-600 focus:outline-none focus:border-indigo-500 transition-colors"
                                        />
                                        <button
                                            type="submit"
                                            className="px-6 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-bold transition-colors shadow-lg shadow-indigo-500/20"
                                        >
                                            Register
                                        </button>
                                    </div>
                                </div>
                                <button
                                    type="button"
                                    onClick={() => {
                                        setIsCreating(false);
                                        setError('');
                                    }}
                                    className="mt-3 text-xs text-slate-500 hover:text-slate-300 transition-colors"
                                >
                                    Back to selection
                                </button>
                            </form>
                        ) : (
                            <button
                                onClick={() => {
                                    setIsCreating(true);
                                    setError('');
                                }}
                                className="w-full flex items-center justify-center space-x-2 p-4 border-2 border-dashed border-white/10 rounded-2xl text-slate-500 hover:border-indigo-500/50 hover:text-indigo-400 transition-all group"
                            >
                                <Plus size={18} className="group-hover:rotate-90 transition-transform" />
                                <span className="font-bold">Register New Account</span>
                            </button>
                        )}
                    </div>
                </div>
            </div>

            <style jsx>{`
                .custom-scrollbar::-webkit-scrollbar {
                    width: 4px;
                }
                .custom-scrollbar::-webkit-scrollbar-track {
                    background: transparent;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb {
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 10px;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb:hover {
                    background: rgba(255, 255, 255, 0.2);
                }
            `}</style>
        </div>
    );
}

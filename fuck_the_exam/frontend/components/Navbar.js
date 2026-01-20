'use client';

import Link from 'next/link';
import { Button } from './ui/button';
import { useUser } from '../contexts/UserContext';
import { User, LogOut, RefreshCw, BookOpen, Database } from 'lucide-react';

const Navbar = () => {
  const { user, logout, examType, switchMode } = useUser();

  if (!user) return null;
  return (
    <nav className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 max-w-screen-2xl items-center justify-between">
        <div className="flex items-center gap-6">
          <Link href="/" className="mr-6 flex items-center space-x-2">
            <span className="font-bold inline-block text-indigo-400">
              {examType === 'Databricks' ? 'Databricks 認定' : 'N1 対策'}
            </span>
          </Link>
          <div className="flex gap-4">
            <Link href="/" className="text-sm font-medium transition-colors hover:text-indigo-400">
              首页
            </Link>
            <Link href="/knowledge" className="text-sm font-medium text-muted-foreground transition-colors hover:text-indigo-400">
              知识库
            </Link>
            <Link href="/wrong-questions" className="text-sm font-medium text-muted-foreground transition-colors hover:text-indigo-400 whitespace-nowrap">
              错题复习
            </Link>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Mode Toggle Switch */}
          <div className="flex items-center bg-white/5 border border-white/10 rounded-full p-1 shadow-inner group">
            <button
              onClick={() => switchMode('N1')}
              className={`flex items-center space-x-1.5 px-3 py-1 rounded-full text-[10px] font-bold transition-all duration-300 ${examType === 'N1'
                  ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/30'
                  : 'text-slate-500 hover:text-slate-300'
                }`}
            >
              <BookOpen size={12} strokeWidth={2.5} />
              <span>N1</span>
            </button>
            <button
              onClick={() => switchMode('Databricks')}
              className={`flex items-center space-x-1.5 px-3 py-1 rounded-full text-[10px] font-bold transition-all duration-300 ${examType === 'Databricks'
                  ? 'bg-purple-600 text-white shadow-lg shadow-purple-500/30'
                  : 'text-slate-500 hover:text-slate-300'
                }`}
            >
              <Database size={12} strokeWidth={2.5} />
              <span>DATABRICKS</span>
            </button>
          </div>

          <div className="h-4 w-[1px] bg-white/10 hidden sm:block"></div>

          {/* User Info */}
          <div className="flex items-center space-x-3">
            <div className="flex flex-col items-end hidden md:flex">
              <span className="text-xs font-bold text-slate-200">{user.username}</span>
              <button
                onClick={logout}
                className="text-[10px] text-slate-500 hover:text-indigo-400 flex items-center space-x-1"
              >
                <span>Switch User</span>
              </button>
            </div>
            <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-slate-300 border border-white/10">
              <User size={14} />
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;

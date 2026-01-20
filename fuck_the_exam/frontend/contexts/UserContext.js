'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { getUsers, createUser, loginUser } from '../lib/api';

const UserContext = createContext();

export const useUser = () => useContext(UserContext);

export const UserProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [examType, setExamType] = useState('N1');
    const [availableUsers, setAvailableUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showLoginModal, setShowLoginModal] = useState(false);

    useEffect(() => {
        const initUser = async () => {
            try {
                // 1. Load from localStorage
                const savedUserId = localStorage.getItem('userId');
                const savedUsername = localStorage.getItem('username');
                const savedExamType = localStorage.getItem('examType');

                if (savedExamType) setExamType(savedExamType);

                // 2. Fetch available users
                const users = await getUsers();
                setAvailableUsers(users);

                if (savedUserId && savedUsername) {
                    setUser({ id: parseInt(savedUserId), username: savedUsername });
                } else {
                    setShowLoginModal(true);
                }
            } catch (error) {
                console.error('Failed to initialize user session:', error);
            } finally {
                setLoading(false);
            }
        };

        initUser();
    }, []);

    const loginWithPassword = async (username, password) => {
        const u = await loginUser(username, password);
        setUser(u);
        localStorage.setItem('userId', u.id);
        localStorage.setItem('username', u.username);
        setShowLoginModal(false);
        return u;
    };

    const login = (u) => {
        // This is now used for session restoration or verified users
        setUser(u);
        localStorage.setItem('userId', u.id);
        localStorage.setItem('username', u.username);
        setShowLoginModal(false);
    };

    const logout = () => {
        setUser(null);
        localStorage.removeItem('userId');
        localStorage.removeItem('username');
        setShowLoginModal(true);
    };

    const handleCreateUser = async (username, password) => {
        const newUser = await createUser(username, password);
        // Refresh users list
        const updatedUsers = await getUsers();
        setAvailableUsers(updatedUsers);
        login(newUser);
        return newUser;
    };

    const switchMode = (mode) => {
        if (mode === examType) return;
        setExamType(mode);
        localStorage.setItem('examType', mode);
        window.location.reload();
    };

    return (
        <UserContext.Provider value={{
            user,
            examType,
            availableUsers,
            loading,
            showLoginModal,
            setShowLoginModal,
            login,
            loginWithPassword,
            logout,
            handleCreateUser,
            switchMode
        }}>
            {children}
        </UserContext.Provider>
    );
};

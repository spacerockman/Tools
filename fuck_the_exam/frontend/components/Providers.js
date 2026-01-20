'use client';

import { GenerationProvider } from '../contexts/GenerationContext';
import { UserProvider } from '../contexts/UserContext';
import GenerationToast from './GenerationToast';
import LoginModal from './LoginModal';

export default function Providers({ children }) {
    return (
        <UserProvider>
            <GenerationProvider>
                {children}
                <GenerationToast />
                <LoginModal />
            </GenerationProvider>
        </UserProvider>
    );
}

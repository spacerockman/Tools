'use client';

import { GenerationProvider } from '../contexts/GenerationContext';
import GenerationToast from './GenerationToast';

export default function Providers({ children }) {
    return (
        <GenerationProvider>
            {children}
            <GenerationToast />
        </GenerationProvider>
    );
}

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const useThemeStore = create(
    persist(
        (set) => ({
            theme: 'dark', // 'dark' | 'light' | 'system'

            setTheme: (theme) => {
                set({ theme });

                // 应用主题
                const root = document.documentElement;
                if (theme === 'system') {
                    const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                    root.classList.toggle('dark', systemDark);
                } else {
                    root.classList.toggle('dark', theme === 'dark');
                }
            },

            toggleTheme: () => {
                set((state) => {
                    const newTheme = state.theme === 'dark' ? 'light' : 'dark';
                    const root = document.documentElement;
                    root.classList.toggle('dark', newTheme === 'dark');
                    return { theme: newTheme };
                });
            },
        }),
        {
            name: 'novel-agent-theme',
            onRehydrateStorage: () => (state) => {
                // 初始化时应用保存的主题
                if (state) {
                    const root = document.documentElement;
                    if (state.theme === 'system') {
                        const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                        root.classList.toggle('dark', systemDark);
                    } else {
                        root.classList.toggle('dark', state.theme === 'dark');
                    }
                }
            }
        }
    )
);

export default useThemeStore;

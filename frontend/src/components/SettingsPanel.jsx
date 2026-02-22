import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export default function SettingsPanel() {
    const [isOpen, setIsOpen] = useState(false);

    return (
        <>
            {/* Modern Settings Button */}
            <motion.button
                onClick={() => setIsOpen(true)}
                className={`fixed bottom-6 left-6 z-40 w-12 h-12 rounded-full flex items-center justify-center shadow-md transition-all hover:scale-105 active:scale-95 border
                ${isOpen ? 'bg-slate-100 text-slate-700 border-slate-300 shadow-inner' : 'bg-white text-slate-600 border-slate-200 hover:text-primary hover:border-primary/30'}`}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                title="Settings"
            >
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
            </motion.button>

            {/* Modern Settings Window (Centered Modal) */}
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 z-[100] bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4"
                        onClick={() => setIsOpen(false)}
                    >
                        <motion.div
                            initial={{ scale: 0.95, y: 20 }}
                            animate={{ scale: 1, y: 0 }}
                            exit={{ scale: 0.95, y: 20 }}
                            onClick={(e) => e.stopPropagation()}
                            className="w-full max-w-md bg-white rounded-2xl flex flex-col shadow-2xl overflow-hidden border border-slate-200"
                        >
                            {/* Settings Header */}
                            <div className="bg-slate-50 border-b border-slate-200 p-5 flex justify-between items-center">
                                <h3 className="text-xl font-bold text-slate-900 tracking-tight">System Settings</h3>
                                <button
                                    onClick={() => setIsOpen(false)}
                                    className="w-8 h-8 rounded-full flex items-center justify-center text-slate-400 hover:text-slate-900 hover:bg-slate-200 transition-colors"
                                >
                                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                    </svg>
                                </button>
                            </div>

                            {/* Content Area */}
                            <div className="p-6 flex flex-col gap-6">

                                {/* AI Status Module (Always On) */}
                                <div className="p-5 rounded-xl border border-primary shadow-sm shadow-primary/10 relative bg-white">
                                    <div className="flex justify-between items-center mb-4">
                                        <div className="flex flex-col">
                                            <span className="text-base font-bold text-primary">
                                                NVIDIA AI Routing
                                            </span>
                                            <span className="text-xs font-medium text-slate-500 mt-0.5">
                                                Kimi-K2 Neural Net Model
                                            </span>
                                        </div>

                                        <div className="flex items-center gap-2 text-primary font-bold text-xs bg-primary/5 px-3 py-1.5 rounded-full border border-primary/10">
                                            <div className="w-2 h-2 rounded-full bg-primary animate-pulse"></div>
                                            ACTIVE
                                        </div>
                                    </div>

                                    {/* Status Dashboard */}
                                    <div className="p-3 rounded-lg flex items-start gap-3 bg-blue-50 border border-blue-100 transition-colors">
                                        <div className="mt-0.5 w-4 h-4 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                                            <div className="w-2 h-2 rounded-full bg-primary"></div>
                                        </div>
                                        <div>
                                            <p className="text-sm text-blue-900 leading-snug">
                                                <strong className="block mb-1 text-primary">Connected to Cloud AI</strong>
                                                All matching requests are automatically routed through advanced infrastructure for maximum accuracy.
                                            </p>
                                        </div>
                                    </div>
                                </div>

                                <p className="text-xs text-slate-400 text-center pt-2">
                                    Advanced AI is permanently enabled for all users.
                                </p>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </>
    );
}

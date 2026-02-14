import { useState } from 'react';

/**
 * SettingsPanel Component
 * A floating settings gear button above the chatbot (bottom-right)
 * Contains toggle for NVIDIA AI product matching
 */
export default function SettingsPanel({ useNvidia, setUseNvidia }) {
    const [isOpen, setIsOpen] = useState(false);

    return (
        <>
            {/* Settings Gear Button */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="settings-toggle"
                title="Settings"
            >
                <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
            </button>

            {/* Settings Panel */}
            <div className={`settings-panel ${isOpen ? 'settings-panel-open' : 'settings-panel-closed'}`}>
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-bold text-gray-800">⚙️ Settings</h3>
                    <button
                        onClick={() => setIsOpen(false)}
                        className="text-gray-400 hover:text-gray-600 transition-colors"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                {/* NVIDIA AI Toggle */}
                <div className="border border-gray-200 rounded-lg p-3">
                    <div className="flex items-center justify-between">
                        <div className="flex-1 mr-3">
                            <div className="flex items-center gap-2">
                                <span className="text-sm font-semibold text-gray-800">NVIDIA AI Matching</span>
                                <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${useNvidia ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                                    {useNvidia ? 'ON' : 'OFF'}
                                </span>
                            </div>
                            <p className="text-xs text-gray-500 mt-1">
                                Use NVIDIA Kimi-K2 cloud AI for product matching instead of local model
                            </p>
                        </div>
                        <label className="toggle-switch">
                            <input
                                type="checkbox"
                                checked={useNvidia}
                                onChange={(e) => setUseNvidia(e.target.checked)}
                            />
                            <span className="toggle-slider"></span>
                        </label>
                    </div>

                    {/* Status info */}
                    <div className={`mt-3 text-xs rounded-md p-2 ${useNvidia ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-gray-50 text-gray-500 border border-gray-200'}`}>
                        {useNvidia ? (
                            <div className="flex items-center gap-1.5">
                                <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 text-green-500 flex-shrink-0" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M24 12c0-1.29-.21-2.53-.59-3.69l-1.5.82c.25.91.38 1.87.38 2.87 0 5.68-4.48 10.32-10.1 10.57V20.5l-3.16 2.25L12.19 25v-2.14C18.67 22.61 24 17.85 24 12z"/>
                                    <path d="M12 4.71V2.14C5.33 2.39 0 7.15 0 13c0 1.29.21 2.53.59 3.69l1.5-.82A9.858 9.858 0 011.71 13c0-5.68 4.48-10.32 10.1-10.57V4.5l3.16-2.25L11.81 0v2.14z"/>
                                </svg>
                                <span><strong>NVIDIA Cloud AI</strong> active — product matching uses Kimi-K2 model via API</span>
                            </div>
                        ) : (
                            <div className="flex items-center gap-1.5">
                                <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                                </svg>
                                <span><strong>Local Model</strong> active — using sentence-transformers for matching</span>
                            </div>
                        )}
                    </div>
                </div>

                <p className="text-[10px] text-gray-400 mt-3 text-center">
                    Changes apply to the next search
                </p>
            </div>
        </>
    );
}

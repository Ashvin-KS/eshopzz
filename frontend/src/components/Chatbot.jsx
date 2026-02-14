import { useState, useRef, useEffect } from 'react';

const API_BASE_URL = 'http://localhost:5002';

/**
 * Chatbot Component
 * A floating chatbot in the bottom-left corner that helps users:
 * 1. Find the best product from current search results
 * 2. Describe a product they don't know the name of and search for it
 */
export default function Chatbot({ onSearch, products }) {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState([
        {
            role: 'bot',
            text: "👋 Hi! I'm ShopSync Assistant. I can help you:\n\n• **Find the best deal** from your search results\n• **Describe a product** you're looking for and I'll search for it\n\nTry saying things like:\n- \"What's the best product?\"\n- \"I need something to listen to music wirelessly\"\n- \"Find me a budget laptop under 30000\"",
            products: null
        }
    ]);
    const [input, setInput] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);

    // Auto-scroll to bottom when new messages arrive
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    // Focus input when chat opens
    useEffect(() => {
        if (isOpen) {
            setTimeout(() => inputRef.current?.focus(), 300);
        }
    }, [isOpen]);

    const addBotMessage = (text, chatProducts = null) => {
        setMessages(prev => [...prev, { role: 'bot', text, products: chatProducts }]);
    };

    const handleSend = async () => {
        const userMsg = input.trim();
        if (!userMsg || isTyping) return;

        // Add user message
        setMessages(prev => [...prev, { role: 'user', text: userMsg, products: null }]);
        setInput('');
        setIsTyping(true);

        try {
            const response = await fetch(`${API_BASE_URL}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: userMsg,
                    current_products: products.slice(0, 20) // Send top 20 products for context
                })
            });

            const data = await response.json();

            if (data.success) {
                // If the bot wants to trigger a search
                if (data.action === 'search' && data.search_query) {
                    addBotMessage(data.reply);
                    // Trigger search in the main app
                    onSearch(data.search_query);
                } else if (data.action === 'recommend' && data.recommended_products) {
                    addBotMessage(data.reply, data.recommended_products);
                } else {
                    addBotMessage(data.reply);
                }
            } else {
                addBotMessage("Sorry, I couldn't process that. Try again!");
            }
        } catch (err) {
            console.error('Chat error:', err);
            addBotMessage("⚠️ Couldn't connect to the server. Make sure the backend is running.");
        } finally {
            setIsTyping(false);
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const formatPrice = (price) => {
        if (!price) return '—';
        return '₹' + price.toLocaleString('en-IN');
    };

    return (
        <>
            {/* Chat Toggle Button */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="chatbot-toggle"
                title="Chat with ShopSync Assistant"
            >
                {isOpen ? (
                    <svg xmlns="http://www.w3.org/2000/svg" className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                ) : (
                    <svg xmlns="http://www.w3.org/2000/svg" className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                )}
            </button>

            {/* Chat Window */}
            <div className={`chatbot-window ${isOpen ? 'chatbot-open' : 'chatbot-closed'}`}>
                {/* Header */}
                <div className="chatbot-header">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-full bg-amazon-gold flex items-center justify-center">
                            <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5 text-amazon-dark" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
                            </svg>
                        </div>
                        <div>
                            <h3 className="text-white font-semibold text-sm">ShopSync Assistant</h3>
                            <span className="text-green-300 text-xs">● Online</span>
                        </div>
                    </div>
                    <button
                        onClick={() => setIsOpen(false)}
                        className="text-gray-300 hover:text-white transition-colors"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                        </svg>
                    </button>
                </div>

                {/* Messages Area */}
                <div className="chatbot-messages">
                    {messages.map((msg, idx) => (
                        <div key={idx} className={`chatbot-msg ${msg.role === 'user' ? 'chatbot-msg-user' : 'chatbot-msg-bot'}`}>
                            {msg.role === 'bot' && (
                                <div className="chatbot-avatar">
                                    <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 text-amazon-dark" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
                                    </svg>
                                </div>
                            )}
                            <div className={`chatbot-bubble ${msg.role === 'user' ? 'chatbot-bubble-user' : 'chatbot-bubble-bot'}`}>
                                <p className="text-sm whitespace-pre-line">{msg.text}</p>

                                {/* Product Cards inside chat */}
                                {msg.products && msg.products.length > 0 && (
                                    <div className="mt-3 space-y-2">
                                        {msg.products.map((p, pidx) => (
                                            <div key={pidx} className="chatbot-product-card">
                                                <div className="flex gap-2">
                                                    <img
                                                        src={p.image || 'https://via.placeholder.com/60x60?text=No+Image'}
                                                        alt={p.title}
                                                        className="w-14 h-14 object-contain rounded flex-shrink-0"
                                                        onError={(e) => { e.target.src = 'https://via.placeholder.com/60x60?text=No+Image'; }}
                                                    />
                                                    <div className="flex-1 min-w-0">
                                                        <p className="text-xs font-medium line-clamp-2 text-gray-800">{p.title}</p>
                                                        <div className="flex items-center gap-1 mt-1">
                                                            {p.rating && (
                                                                <span className="text-xs text-amazon-star">★ {p.rating}</span>
                                                            )}
                                                        </div>
                                                        <div className="flex gap-2 mt-1 text-xs">
                                                            {p.amazon_price && (
                                                                <span className={`font-semibold ${p.amazon_price <= (p.flipkart_price || Infinity) ? 'text-green-600' : 'text-gray-600'}`}>
                                                                    Amazon: {formatPrice(p.amazon_price)}
                                                                </span>
                                                            )}
                                                            {p.flipkart_price && (
                                                                <span className={`font-semibold ${p.flipkart_price < (p.amazon_price || Infinity) ? 'text-green-600' : 'text-gray-600'}`}>
                                                                    Flipkart: {formatPrice(p.flipkart_price)}
                                                                </span>
                                                            )}
                                                        </div>
                                                    </div>
                                                </div>
                                                <div className="flex gap-1 mt-2">
                                                    {p.amazon_link && (
                                                        <a href={p.amazon_link} target="_blank" rel="noopener noreferrer"
                                                            className="text-[10px] px-2 py-1 bg-amazon-orange text-white rounded hover:bg-orange-500 transition-colors">
                                                            Amazon →
                                                        </a>
                                                    )}
                                                    {p.flipkart_link && (
                                                        <a href={p.flipkart_link} target="_blank" rel="noopener noreferrer"
                                                            className="text-[10px] px-2 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors">
                                                            Flipkart →
                                                        </a>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}

                    {/* Typing indicator */}
                    {isTyping && (
                        <div className="chatbot-msg chatbot-msg-bot">
                            <div className="chatbot-avatar">
                                <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 text-amazon-dark" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
                                </svg>
                            </div>
                            <div className="chatbot-bubble chatbot-bubble-bot">
                                <div className="chatbot-typing">
                                    <span></span><span></span><span></span>
                                </div>
                            </div>
                        </div>
                    )}

                    <div ref={messagesEndRef} />
                </div>

                {/* Quick Actions */}
                {products.length > 0 && messages.length <= 2 && (
                    <div className="chatbot-quick-actions">
                        <button onClick={() => { setInput("What's the best deal?"); setTimeout(handleSend, 100); }}
                            className="chatbot-quick-btn">🏆 Best Deal</button>
                        <button onClick={() => { setInput("What's the cheapest option?"); setTimeout(handleSend, 100); }}
                            className="chatbot-quick-btn">💰 Cheapest</button>
                        <button onClick={() => { setInput("What's the highest rated?"); setTimeout(handleSend, 100); }}
                            className="chatbot-quick-btn">⭐ Top Rated</button>
                    </div>
                )}

                {/* Input Area */}
                <div className="chatbot-input-area">
                    <input
                        ref={inputRef}
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Describe what you're looking for..."
                        className="chatbot-input"
                        disabled={isTyping}
                    />
                    <button
                        onClick={handleSend}
                        disabled={isTyping || !input.trim()}
                        className="chatbot-send-btn"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
                        </svg>
                    </button>
                </div>
            </div>
        </>
    );
}

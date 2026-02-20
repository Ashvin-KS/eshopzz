import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export default function Navbar({ onSearch, isLoading }) {
    const [searchQuery, setSearchQuery] = useState('');
    const [scrolled, setScrolled] = useState(false);

    useEffect(() => {
        const handleScroll = () => {
            setScrolled(window.scrollY > 20);
        };
        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    const handleSubmit = (e) => {
        e.preventDefault();
        onSearch(searchQuery);
    };

    return (
        <nav className={`sticky top-0 z-50 transition-all duration-300 ${scrolled ? 'bg-white shadow-md' : 'bg-surface border-b border-light'}`}>


            {/* Main Navbar */}
            <div className="flex items-center justify-between px-6 py-4 gap-8 max-w-screen-2xl mx-auto">

                {/* Logo Section */}
                <div className="flex-shrink-0 cursor-pointer flex items-center gap-2">
                    <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center text-white font-bold text-xl shadow-sm">
                        S
                    </div>
                    <div className="flex flex-col">
                        <span className="text-xl font-bold tracking-tight text-slate-900 leading-tight">ShopSync</span>
                        <span className="text-[10px] uppercase font-semibold text-primary tracking-wider leading-none">Smart Aggregator</span>
                    </div>
                </div>

                {/* Search Bar - Modern Rounded Pill */}
                <form
                    onSubmit={handleSubmit}
                    className="flex-1 max-w-3xl relative group"
                >
                    <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                        <svg className="w-5 h-5 text-slate-400 group-focus-within:text-primary transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                    </div>

                    <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Search for laptops, phones, electronics..."
                        className="w-full pl-12 pr-32 py-3 bg-slate-100 border border-transparent focus:bg-white focus:border-primary/30 focus:shadow-[0_0_0_4px_rgba(59,130,246,0.1)] rounded-full outline-none text-slate-900 transition-all text-sm sm:text-base placeholder-slate-400"
                        disabled={isLoading}
                    />

                    <div className="absolute inset-y-0 right-1.5 flex items-center">
                        <button
                            type="submit"
                            disabled={isLoading}
                            className={`px-6 py-2 rounded-full font-medium text-sm transition-all
                            ${isLoading
                                    ? 'bg-slate-200 text-slate-500 cursor-not-allowed'
                                    : 'bg-primary text-white hover:bg-primary-hover shadow-sm hover:shadow active:scale-95'}`}
                        >
                            {isLoading ? (
                                <div className="flex items-center gap-2">
                                    <svg className="animate-spin h-4 w-4 text-slate-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                    <span>Searching</span>
                                </div>
                            ) : 'Search'}
                        </button>
                    </div>
                </form>

                {/* Right Section - Account & Cart */}
                <div className="flex items-center gap-6">

                    {/* User Profile */}
                    <div className="hidden lg:flex items-center gap-3 cursor-pointer group p-2 hover:bg-slate-50 rounded-lg transition-colors border border-transparent hover:border-slate-200">
                        <div className="w-9 h-9 bg-slate-100 rounded-full flex items-center justify-center text-slate-600 group-hover:bg-primary/10 group-hover:text-primary transition-colors">
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>
                        </div>
                        <div className="flex flex-col">
                            <span className="text-xs text-slate-500">Welcome,</span>
                            <span className="text-sm font-semibold text-slate-900">Sign In</span>
                        </div>
                    </div>

                    {/* Cart Tool */}
                    <div className="relative cursor-pointer group flex items-center p-2">
                        <div className="relative">
                            <svg className="w-6 h-6 text-slate-700 group-hover:text-primary transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" /></svg>
                            <span className="absolute -top-2 -right-2 bg-primary text-white text-[10px] font-bold w-5 h-5 rounded-full flex items-center justify-center border-2 border-white shadow-sm">
                                0
                            </span>
                        </div>
                        <span className="ml-3 hidden sm:block text-sm font-medium text-slate-700 group-hover:text-primary transition-colors">Cart</span>
                    </div>
                </div>
            </div>

            {/* Main Categories Navigation */}
            <div className="border-t border-slate-200 bg-white">
                <div className="max-w-screen-2xl mx-auto px-6 py-2.5 flex items-center gap-8 overflow-x-auto no-scrollbar">
                    <button className="flex items-center gap-2 text-slate-700 hover:text-primary font-medium text-sm flex-shrink-0 transition-colors">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" /></svg>
                        All Categories
                    </button>
                    <nav className="flex items-center gap-6 flex-1 min-w-max">
                        {['Today\'s Deals', 'Customer Service', 'Registry', 'Gift Cards', 'Sell', 'Electronics', 'Fashion'].map((item) => (
                            <a href="#" key={item} className="text-sm text-slate-600 hover:text-primary transition-colors">{item}</a>
                        ))}
                    </nav>
                </div>
            </div>
        </nav>
    );
}

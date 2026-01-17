import { useState } from 'react';

/**
 * Amazon-style Navbar Component
 * Replicates the dark blue header with logo, search bar, and account section
 */
export default function Navbar({ onSearch, isLoading }) {
    const [searchQuery, setSearchQuery] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        if (searchQuery.trim()) {
            onSearch(searchQuery.trim());
        }
    };

    return (
        <nav className="bg-amazon-dark sticky top-0 z-50">
            {/* Main Navbar */}
            <div className="flex items-center px-4 py-2 gap-4">
                {/* Logo */}
                <div className="flex items-center flex-shrink-0 cursor-pointer hover:outline hover:outline-1 hover:outline-white p-1 rounded">
                    <span className="text-white text-2xl font-bold tracking-tight">
                        Shop<span className="text-amazon-gold">Sync</span>
                    </span>
                </div>

                {/* Deliver to Location */}
                <div className="hidden md:flex items-center text-white cursor-pointer hover:outline hover:outline-1 hover:outline-white p-1 rounded">
                    <svg className="w-5 h-5 text-white mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    <div className="flex flex-col text-xs">
                        <span className="text-gray-300">Deliver to</span>
                        <span className="font-bold">India</span>
                    </div>
                </div>

                {/* Search Bar */}
                <form onSubmit={handleSubmit} className="flex-1 flex max-w-3xl">
                    <div className="flex w-full rounded-md overflow-hidden focus-within:ring-2 focus-within:ring-[#FEBD69] focus-within:ring-offset-0">
                        {/* Category Dropdown */}
                        <div className="relative flex-shrink-0 bg-gray-100 border-r border-[#cdcdcd] hover:bg-[#d4d4d4] cursor-pointer">
                            <select className="appearance-none bg-transparent h-full text-[#0F1111] text-xs px-3 pr-6 outline-none cursor-pointer">
                                <option>All</option>
                                <option>Electronics</option>
                                <option>Computers</option>
                                <option>Fashion</option>
                                <option>Home</option>
                                <option>Books</option>
                            </select>
                            <svg className="w-2 h-2 absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none fill-[#555]" viewBox="0 0 24 24">
                                <path d="M7 10l5 5 5-5z" />
                            </svg>
                        </div>

                        {/* Search Input */}
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Search ShopSync"
                            className="flex-1 px-3 py-2 bg-white text-[#0F1111] outline-none text-[15px] font-normal placeholder-gray-500"
                            disabled={isLoading}
                        />

                        {/* Search Button */}
                        <button
                            type="submit"
                            className="bg-[#FEBD69] hover:bg-[#F3A847] px-4 transition-colors duration-200 flex items-center justify-center"
                            disabled={isLoading}
                        >
                            {isLoading ? (
                                <svg className="w-6 h-6 text-[#0F1111] animate-spin" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                            ) : (
                                <svg className="w-6 h-6 text-[#0F1111]" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2.5">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                </svg>
                            )}
                        </button>
                    </div>
                </form>

                {/* Right Section - Account & Cart */}
                <div className="flex items-center gap-4">
                    {/* Language */}
                    <div className="hidden lg:flex items-center text-white cursor-pointer hover:outline hover:outline-1 hover:outline-white p-1 rounded">
                        <span className="text-sm font-bold">EN</span>
                        <svg className="w-3 h-3 ml-1" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                        </svg>
                    </div>

                    {/* Hello, Sign in */}
                    <div className="hidden md:flex flex-col text-white cursor-pointer hover:outline hover:outline-1 hover:outline-white p-1 rounded">
                        <span className="text-xs text-gray-300">Hello, Sign in</span>
                        <div className="flex items-center">
                            <span className="text-sm font-bold">Account & Lists</span>
                            <svg className="w-3 h-3 ml-1" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                            </svg>
                        </div>
                    </div>

                    {/* Returns & Orders */}
                    <div className="hidden md:flex flex-col text-white cursor-pointer hover:outline hover:outline-1 hover:outline-white p-1 rounded">
                        <span className="text-xs text-gray-300">Returns</span>
                        <span className="text-sm font-bold">& Orders</span>
                    </div>

                    {/* Cart */}
                    <div className="flex items-center text-white cursor-pointer hover:outline hover:outline-1 hover:outline-white p-1 rounded">
                        <div className="relative">
                            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
                            </svg>
                            <span className="absolute -top-1 right-0 bg-amazon-orange text-amazon-dark text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
                                0
                            </span>
                        </div>
                        <span className="font-bold text-sm ml-1">Cart</span>
                    </div>
                </div>
            </div>

            {/* Secondary Navbar */}
            <div className="bg-amazon-light text-white text-sm px-4 py-2 flex items-center gap-4 overflow-x-auto">
                <div className="flex items-center cursor-pointer hover:outline hover:outline-1 hover:outline-white p-1 rounded whitespace-nowrap">
                    <svg className="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                    </svg>
                    <span className="font-bold">All</span>
                </div>
                <span className="cursor-pointer hover:underline whitespace-nowrap">Today's Deals</span>
                <span className="cursor-pointer hover:underline whitespace-nowrap">Customer Service</span>
                <span className="cursor-pointer hover:underline whitespace-nowrap">Best Sellers</span>
                <span className="cursor-pointer hover:underline whitespace-nowrap">Prime</span>
                <span className="cursor-pointer hover:underline whitespace-nowrap">New Releases</span>
                <span className="cursor-pointer hover:underline whitespace-nowrap">Fashion</span>
                <span className="cursor-pointer hover:underline whitespace-nowrap">Electronics</span>
                <span className="cursor-pointer hover:underline whitespace-nowrap">Mobiles</span>
            </div>
        </nav>
    );
}

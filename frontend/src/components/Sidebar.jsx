import { useState } from 'react';

/**
 * Sidebar Filter Component
 * Amazon-style filter panel with categories, price range, and ratings
 */
export default function Sidebar({ filters, onFilterChange }) {
    const [expandedSections, setExpandedSections] = useState({
        categories: true,
        price: true,
        rating: true,
        prime: true
    });

    const categories = [
        'All Categories',
        'Electronics',
        'Computers & Accessories',
        'Mobile Phones',
        'Headphones',
        'Shoes & Footwear',
        'Fashion',
        'Home & Kitchen',
        'Books',
        'Sports & Outdoors'
    ];

    const priceRanges = [
        { label: 'Under ₹1,000', min: 0, max: 1000 },
        { label: '₹1,000 - ₹5,000', min: 1000, max: 5000 },
        { label: '₹5,000 - ₹10,000', min: 5000, max: 10000 },
        { label: '₹10,000 - ₹25,000', min: 10000, max: 25000 },
        { label: '₹25,000 - ₹50,000', min: 25000, max: 50000 },
        { label: 'Over ₹50,000', min: 50000, max: Infinity }
    ];

    const toggleSection = (section) => {
        setExpandedSections(prev => ({
            ...prev,
            [section]: !prev[section]
        }));
    };

    const handleCategoryChange = (category) => {
        onFilterChange({ ...filters, category });
    };

    const handlePriceChange = (priceRange) => {
        onFilterChange({ ...filters, priceRange });
    };

    const handleRatingChange = (minRating) => {
        onFilterChange({ ...filters, minRating });
    };

    const handlePrimeChange = (primeOnly) => {
        onFilterChange({ ...filters, primeOnly });
    };

    const renderStars = (count) => {
        return (
            <div className="flex items-center">
                {[1, 2, 3, 4, 5].map(i => (
                    <svg
                        key={i}
                        className={`w-4 h-4 ${i <= count ? 'text-amazon-star' : 'text-gray-300'}`}
                        fill="currentColor"
                        viewBox="0 0 20 20"
                    >
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                ))}
                <span className="text-amazon-link text-sm ml-1">& Up</span>
            </div>
        );
    };

    return (
        <aside className="w-64 flex-shrink-0 bg-white p-4">
            {/* Categories */}
            <div className="mb-2">
                <h3 className="font-bold text-sm text-[#0F1111] mb-2">Department</h3>
                <ul className="space-y-1">
                    {categories.map(cat => (
                        <li
                            key={cat}
                            onClick={() => handleCategoryChange(cat)}
                            className={`text-sm cursor-pointer hover:text-[#C7511F] transition-colors pl-2 py-0.5
                            ${filters.category === cat ? 'font-bold text-[#0F1111]' : 'text-[#0F1111]'}`}
                        >
                            {cat}
                        </li>
                    ))}
                </ul>
            </div>

            <div className="my-4 border-b border-gray-200"></div>

            {/* Customer Reviews */}
            <div className="mb-4">
                <h3 className="font-bold text-sm text-[#0F1111] mb-2">Customer Reviews</h3>
                <div className="space-y-1">
                    {[4, 3, 2, 1].map(rating => (
                        <div
                            key={rating}
                            onClick={() => handleRatingChange(rating)}
                            className={`cursor-pointer flex items-center hover:opacity-80 group`}
                        >
                            <div className="flex text-[#FFA41C]">
                                {[1, 2, 3, 4, 5].map(i => (
                                    <svg
                                        key={i}
                                        className={`w-5 h-5 ${i <= rating ? 'fill-current' : 'text-white stroke-[#FFA41C] border-2'}`}
                                        xmlns="http://www.w3.org/2000/svg"
                                        viewBox="0 0 24 24"
                                    >
                                        <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z" />
                                    </svg>
                                ))}
                            </div>
                            <span className="text-sm ml-2 group-hover:text-[#C7511F] group-hover:underline text-[#0F1111]">& Up</span>
                        </div>
                    ))}
                </div>
            </div>

            <div className="my-4 border-b border-gray-200"></div>

            {/* Price Range */}
            <div className="mb-4">
                <h3 className="font-bold text-sm text-[#0F1111] mb-2">Price</h3>
                <ul className="space-y-1">
                    {priceRanges.map((range, idx) => (
                        <li
                            key={idx}
                            onClick={() => handlePriceChange(range)}
                            className={`text-sm cursor-pointer hover:text-[#C7511F] hover:underline transition-colors
                            ${filters.priceRange?.label === range.label ? 'font-bold text-[#0F1111]' : 'text-[#0F1111]'}`}
                        >
                            {range.label}
                        </li>
                    ))}
                </ul>
            </div>

            <div className="my-4 border-b border-gray-200"></div>

            {/* Prime */}
            <div className="mb-4">
                <h3 className="font-bold text-sm text-[#0F1111] mb-2">Pay On Delivery</h3>
                <label className="flex items-start cursor-pointer group">
                    <div className="relative flex items-center">
                        <input
                            type="checkbox"
                            checked={filters.primeOnly || false}
                            onChange={(e) => handlePrimeChange(e.target.checked)}
                            className="peer h-4 w-4 cursor-pointer appearance-none rounded border border-gray-400 checked:bg-[#007185] checked:border-[#007185] transition-all hover:border-[#C7511F]"
                        />
                        <svg
                            className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-3 h-3 pointer-events-none hidden peer-checked:block text-white"
                            xmlns="http://www.w3.org/2000/svg"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="4"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                        >
                            <polyline points="20 6 9 17 4 12"></polyline>
                        </svg>
                    </div>

                    <div className="ml-2">
                        <span className="text-sm text-[#0F1111] group-hover:text-[#C7511F]">Eligible for Pay On Delivery</span>
                        <div className="flex items-center mt-1">
                            <input type="checkbox" checked={true} readOnly className="h-4 w-4 appearance-none" /> {/* Spacer */}
                        </div>
                    </div>
                </label>
            </div>

            {/* Clear Filters */}
            <button
                onClick={() => onFilterChange({ category: 'All Categories', priceRange: null, minRating: null, primeOnly: false })}
                className="w-full mt-4 text-[#007185] text-xs hover:text-[#C7511F] hover:underline text-left pl-1"
            >
                Clear all filters
            </button>
        </aside>
    );
}

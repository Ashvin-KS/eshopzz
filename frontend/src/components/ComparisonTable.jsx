import { useState } from 'react';

/**
 * ComparisonTable Component
 * Full-page comparison overlay showing detailed specs side-by-side
 */
export default function ComparisonTable({ data, isLoading, onClose }) {
    const [highlightDiffs, setHighlightDiffs] = useState(true);

    if (!data && !isLoading) return null;

    // Get all unique spec keys across all products, preserving order
    const allKeys = [];
    const seenKeys = new Set();
    if (data) {
        // Priority keys first
        const priorityKeys = ['Brand', 'Model', 'Model Name', 'Model Number', 'Colour', 'Color',
            'RAM', 'Storage', 'ROM', 'Display', 'Screen Size', 'Battery', 'Battery Capacity',
            'Processor', 'Operating System', 'OS', 'Camera', 'Weight', 'Warranty',
            'Key Features', 'Highlights', 'Description'];

        for (const key of priorityKeys) {
            for (const p of data) {
                if (p.specs[key] && !seenKeys.has(key)) {
                    allKeys.push(key);
                    seenKeys.add(key);
                }
            }
        }

        // Then remaining keys
        for (const p of data) {
            for (const key of Object.keys(p.specs)) {
                if (!seenKeys.has(key)) {
                    allKeys.push(key);
                    seenKeys.add(key);
                }
            }
        }
    }

    const formatPrice = (price) => {
        if (!price) return '—';
        return '₹' + price.toLocaleString('en-IN');
    };

    const getMinPrice = (p) => {
        const prices = [p.amazon_price, p.flipkart_price].filter(v => v != null);
        return prices.length > 0 ? Math.min(...prices) : null;
    };

    // Check if values differ across products for a given key
    const valuesDiffer = (key) => {
        if (!data || data.length < 2) return false;
        const vals = data.map(p => (p.specs[key] || '').toLowerCase().trim()).filter(v => v && v !== '—');
        if (vals.length < 2) return false;
        return !vals.every(v => v === vals[0]);
    };

    return (
        <div className="compare-overlay">
            <div className="compare-container">
                {/* Header */}
                <div className="compare-header">
                    <div className="flex items-center gap-3">
                        <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6 text-amazon-gold" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2" />
                        </svg>
                        <div>
                            <h2 className="text-xl font-bold text-white">Product Comparison</h2>
                            <p className="text-xs text-gray-400">
                                {isLoading ? 'Fetching detailed specifications...' : `Comparing ${data?.length || 0} products`}
                            </p>
                        </div>
                    </div>
                    <div className="flex items-center gap-4">
                        {!isLoading && data && (
                            <label className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={highlightDiffs}
                                    onChange={(e) => setHighlightDiffs(e.target.checked)}
                                    className="rounded"
                                />
                                Highlight differences
                            </label>
                        )}
                        <button onClick={onClose} className="compare-close-btn">
                            <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>
                </div>

                {/* Loading State */}
                {isLoading && (
                    <div className="compare-loading">
                        <div className="compare-spinner"></div>
                        <p className="text-lg font-medium text-gray-700 mt-4">Scraping product details...</p>
                        <p className="text-sm text-gray-500 mt-1">Visiting each product page to extract specifications</p>
                        <p className="text-xs text-gray-400 mt-2">This may take 15-30 seconds</p>
                    </div>
                )}

                {/* Comparison Table */}
                {!isLoading && data && data.length > 0 && (
                    <div className="compare-table-wrapper">
                        <table className="compare-table">
                            <thead>
                                <tr>
                                    <th className="compare-th-label">Feature</th>
                                    {data.map((p, i) => (
                                        <th key={i} className="compare-th-product">
                                            <div className="compare-product-header">
                                                <img
                                                    src={p.image || 'https://via.placeholder.com/80x80?text=N/A'}
                                                    alt={p.title}
                                                    className="w-20 h-20 object-contain mx-auto mb-2"
                                                    onError={(e) => { e.target.src = 'https://via.placeholder.com/80x80?text=N/A'; }}
                                                />
                                                <p className="text-xs font-medium line-clamp-2 text-gray-800">{p.title}</p>
                                            </div>
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {/* Price Row */}
                                <tr className="compare-row-price">
                                    <td className="compare-td-label">
                                        <span className="font-semibold">💰 Best Price</span>
                                    </td>
                                    {data.map((p, i) => {
                                        const minP = getMinPrice(p);
                                        const allMins = data.map(getMinPrice).filter(v => v != null);
                                        const isLowest = minP != null && minP === Math.min(...allMins) && allMins.length > 1;
                                        return (
                                            <td key={i} className={`compare-td-value ${isLowest ? 'compare-best-value' : ''}`}>
                                                <span className={`text-lg font-bold ${isLowest ? 'text-green-600' : 'text-gray-800'}`}>
                                                    {formatPrice(minP)}
                                                </span>
                                                {isLowest && <span className="compare-best-badge">Best Price</span>}
                                            </td>
                                        );
                                    })}
                                </tr>

                                {/* Amazon Price Row */}
                                <tr>
                                    <td className="compare-td-label">Amazon Price</td>
                                    {data.map((p, i) => (
                                        <td key={i} className="compare-td-value">
                                            <div className="flex items-center gap-2 justify-center">
                                                <span>{formatPrice(p.amazon_price)}</span>
                                                {p.amazon_link && (
                                                    <a href={p.amazon_link} target="_blank" rel="noopener noreferrer"
                                                        className="text-[10px] bg-[#FEBD69] text-[#0F1111] px-2 py-0.5 rounded hover:bg-[#F3A847]">
                                                        View →
                                                    </a>
                                                )}
                                            </div>
                                        </td>
                                    ))}
                                </tr>

                                {/* Flipkart Price Row */}
                                <tr>
                                    <td className="compare-td-label">Flipkart Price</td>
                                    {data.map((p, i) => (
                                        <td key={i} className="compare-td-value">
                                            <div className="flex items-center gap-2 justify-center">
                                                <span>{formatPrice(p.flipkart_price)}</span>
                                                {p.flipkart_link && (
                                                    <a href={p.flipkart_link} target="_blank" rel="noopener noreferrer"
                                                        className="text-[10px] bg-[#2874F0] text-white px-2 py-0.5 rounded hover:bg-[#1e65d8]">
                                                        View →
                                                    </a>
                                                )}
                                            </div>
                                        </td>
                                    ))}
                                </tr>

                                {/* Rating Row */}
                                <tr>
                                    <td className="compare-td-label">⭐ Rating</td>
                                    {data.map((p, i) => {
                                        const allRatings = data.map(d => d.rating).filter(v => v != null);
                                        const isBest = p.rating != null && p.rating === Math.max(...allRatings) && allRatings.length > 1;
                                        return (
                                            <td key={i} className={`compare-td-value ${isBest ? 'compare-best-value' : ''}`}>
                                                <div className="flex items-center gap-1 justify-center">
                                                    <div className="flex text-[#FFA41C]">
                                                        {[1, 2, 3, 4, 5].map(s => (
                                                            <svg key={s} className={`w-4 h-4 ${s <= Math.round(p.rating || 0) ? 'fill-current' : 'text-gray-200'}`}
                                                                xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                                                                <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z" />
                                                            </svg>
                                                        ))}
                                                    </div>
                                                    <span className="text-sm font-medium">{p.rating || 'N/A'}</span>
                                                    {isBest && <span className="compare-best-badge">Top</span>}
                                                </div>
                                            </td>
                                        );
                                    })}
                                </tr>

                                {/* Spec Rows */}
                                {allKeys.map((key) => {
                                    const differs = highlightDiffs && valuesDiffer(key);
                                    return (
                                        <tr key={key} className={differs ? 'compare-row-diff' : ''}>
                                            <td className="compare-td-label">{key}</td>
                                            {data.map((p, i) => {
                                                const val = p.specs[key] || '—';
                                                const isLong = val.length > 120;
                                                return (
                                                    <td key={i} className="compare-td-value">
                                                        <span className={`${isLong ? 'text-xs' : 'text-sm'} ${val === '—' ? 'text-gray-300' : ''}`}>
                                                            {isLong ? val.slice(0, 150) + '...' : val}
                                                        </span>
                                                    </td>
                                                );
                                            })}
                                        </tr>
                                    );
                                })}

                                {/* Empty specs warning */}
                                {allKeys.length === 0 && (
                                    <tr>
                                        <td colSpan={data.length + 1} className="text-center py-8 text-gray-500">
                                            <p className="text-lg">No detailed specifications found</p>
                                            <p className="text-sm mt-1">The product pages may have blocked scraping or use a different layout</p>
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
}

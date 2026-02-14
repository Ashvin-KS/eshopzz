import { useState, useEffect, useCallback } from 'react';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import ProductGrid from './components/ProductGrid';
import Chatbot from './components/Chatbot';
import SettingsPanel from './components/SettingsPanel';
import ComparisonTable from './components/ComparisonTable';
import './App.css';

// API Configuration
const API_BASE_URL = 'http://localhost:5002';

/**
 * ShopSync - E-Commerce Price Aggregator
 * Main application component that replicates Amazon UI
 * while showing price comparisons from Amazon and Flipkart
 */
function App() {
    const [products, setProducts] = useState([]);
    const [filteredProducts, setFilteredProducts] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [isFallback, setIsFallback] = useState(false);
    const [sortBy, setSortBy] = useState('relevance');
    const [useNvidia, setUseNvidia] = useState(false);
    const [compareList, setCompareList] = useState([]);
    const [comparisonData, setComparisonData] = useState(null);
    const [isComparing, setIsComparing] = useState(false);
    const [showComparison, setShowComparison] = useState(false);
    const [filters, setFilters] = useState({
        category: 'All Categories',
        priceRange: null,
        minRating: null,
        primeOnly: false
    });

    // Apply filters to products
    const applyFilters = useCallback((productList, currentFilters) => {
        let result = [...productList];

        // Price range filter
        if (currentFilters.priceRange) {
            result = result.filter(p => {
                const price = p.amazon_price || p.flipkart_price;
                return price >= currentFilters.priceRange.min && price <= currentFilters.priceRange.max;
            });
        }

        // Rating filter
        if (currentFilters.minRating) {
            result = result.filter(p => p.rating >= currentFilters.minRating);
        }

        // Prime filter
        if (currentFilters.primeOnly) {
            result = result.filter(p => p.is_prime);
        }

        return result;
    }, []);

    // Update filtered products when filters or products change
    useEffect(() => {
        let result = applyFilters(products, filters);

        // Apply Sorting
        const getMinPrice = (p) => {
            const prices = [p.amazon_price, p.flipkart_price].filter(p => p !== null);
            return prices.length > 0 ? Math.min(...prices) : Infinity;
        };

        result.sort((a, b) => {
            // Primary Sort: Prioritize products with comparisons (matches)
            const aHasMatch = a.amazon_price && a.flipkart_price;
            const bHasMatch = b.amazon_price && b.flipkart_price;

            if (aHasMatch && !bHasMatch) return -1;
            if (!aHasMatch && bHasMatch) return 1;

            // Secondary Sort: Based on selected criteria
            if (sortBy === 'price_asc') {
                return getMinPrice(a) - getMinPrice(b);
            } else if (sortBy === 'price_desc') {
                return getMinPrice(b) - getMinPrice(a);
            } else if (sortBy === 'rating') {
                return (b.rating || 0) - (a.rating || 0);
            } else {
                // Default Relevance: use original ID as tie-breaker
                return a.id - b.id;
            }
        });

        setFilteredProducts(result);
    }, [products, filters, applyFilters, sortBy]);

    // Search products from API
    const handleSearch = async (query) => {
        setSearchQuery(query);
        setIsLoading(true);
        setError(null);

        try {
            // Try live scraping first (may take 15-30 seconds)
            const response = await fetch(`${API_BASE_URL}/search?q=${encodeURIComponent(query)}&nvidia=${useNvidia}`);

            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                setProducts(data.products || []);
                setIsFallback(data.is_fallback || false);
            } else {
                throw new Error(data.error || 'Search failed');
            }
        } catch (err) {
            console.error('Live scraping failed, trying fallback:', err);

            // Fallback to mock data
            try {
                const fallbackResponse = await fetch(`${API_BASE_URL}/search?q=${encodeURIComponent(query)}&mock=true`);
                const fallbackData = await fallbackResponse.json();

                if (fallbackData.success) {
                    setProducts(fallbackData.products || []);
                    setIsFallback(true);
                    setError(null); // Clear error since fallback worked
                } else {
                    throw new Error('Fallback also failed');
                }
            } catch (fallbackErr) {
                console.error('Fallback failed:', fallbackErr);
                setError('Could not fetch products. Please try again.');
                setProducts([]);
            }
        } finally {
            setIsLoading(false);
        }
    };

    // Handle filter changes
    const handleFilterChange = (newFilters) => {
        setFilters(newFilters);
    };

    // Toggle a product in compare list
    const handleToggleCompare = (product) => {
        setCompareList(prev => {
            const key = product.id || product.title;
            const exists = prev.some(p => (p.id || p.title) === key);
            if (exists) {
                return prev.filter(p => (p.id || p.title) !== key);
            }
            if (prev.length >= 4) return prev;
            return [...prev, product];
        });
    };

    // Start comparison — calls backend
    const startComparison = async () => {
        if (compareList.length < 2) return;
        setIsComparing(true);
        setShowComparison(true);
        setComparisonData(null);

        try {
            const response = await fetch(`${API_BASE_URL}/compare-details`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ products: compareList })
            });
            const data = await response.json();
            if (data.success) {
                setComparisonData(data.comparison);
            } else {
                console.error('Comparison failed:', data.error);
            }
        } catch (err) {
            console.error('Comparison error:', err);
        } finally {
            setIsComparing(false);
        }
    };

    // Close comparison overlay
    const closeComparison = () => {
        setShowComparison(false);
        setComparisonData(null);
    };

    // Clear compare list
    const clearCompareList = () => {
        setCompareList([]);
    };

    return (
        <div className="min-h-screen bg-amazon-bg">
            {/* Navbar */}
            <Navbar onSearch={handleSearch} isLoading={isLoading} />

            {/* Banner for fallback data */}
            {isFallback && products.length > 0 && (
                <div className="bg-amber-100 border-b border-amber-300 px-4 py-2 text-center">
                    <span className="text-amber-800 text-sm">
                        ⚠️ Showing demo data. Live scraping may be blocked or timed out.
                    </span>
                </div>
            )}

            {/* Error Banner */}
            {error && (
                <div className="bg-red-100 border-b border-red-300 px-4 py-2 text-center">
                    <span className="text-red-800 text-sm">
                        ❌ {error}
                    </span>
                </div>
            )}

            {/* Main Content */}
            <div className="flex">
                {/* Sidebar */}
                <Sidebar filters={filters} onFilterChange={handleFilterChange} />

                {/* Product Grid */}
                <ProductGrid
                    products={filteredProducts}
                    isLoading={isLoading}
                    query={searchQuery}
                    sortBy={sortBy}
                    onSortChange={setSortBy}
                    compareList={compareList}
                    onToggleCompare={handleToggleCompare}
                />
            </div>

            {/* Chatbot */}
            <Chatbot onSearch={handleSearch} products={filteredProducts} />

            {/* Settings Panel */}
            <SettingsPanel useNvidia={useNvidia} setUseNvidia={setUseNvidia} />

            {/* Floating Compare Bar */}
            {compareList.length > 0 && !showComparison && (
                <div className="compare-bar">
                    <div className="compare-bar-inner">
                        <div className="compare-bar-info">
                            <span className="compare-bar-count">{compareList.length}</span>
                            <span className="compare-bar-text">
                                {compareList.length === 1 ? 'product selected' : 'products selected'}
                            </span>
                            <div className="compare-bar-thumbs">
                                {compareList.map((p, i) => (
                                    <img
                                        key={i}
                                        src={p.image || 'https://via.placeholder.com/32'}
                                        alt=""
                                        className="compare-bar-thumb"
                                        onClick={() => handleToggleCompare(p)}
                                        title={`Remove ${p.title}`}
                                    />
                                ))}
                            </div>
                        </div>
                        <div className="compare-bar-actions">
                            <button className="compare-bar-clear" onClick={clearCompareList}>
                                Clear
                            </button>
                            <button
                                className="compare-bar-btn"
                                onClick={startComparison}
                                disabled={compareList.length < 2}
                            >
                                Compare ({compareList.length})
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Comparison Overlay */}
            {showComparison && (
                <ComparisonTable
                    data={comparisonData}
                    isLoading={isComparing}
                    onClose={closeComparison}
                />
            )}

            {/* Footer */}
            <footer className="bg-amazon-light text-white text-center py-8 mt-8">
                <div className="text-sm text-gray-300">
                    <p className="mb-2">
                        <span className="font-bold text-white">ShopSync</span> - Price Comparison Made Easy
                    </p>
                    <p className="text-xs text-gray-400">
                        Aggregating prices from Amazon and Flipkart to help you find the best deals.
                    </p>
                    <p className="text-xs text-gray-500 mt-4">
                        © 2026 ShopSync. This is a demo project. Not affiliated with Amazon or Flipkart.
                    </p>
                </div>
            </footer>
        </div>
    );
}

export default App;

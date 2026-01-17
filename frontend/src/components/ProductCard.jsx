/**
 * ProductCard Component
 * Amazon-style product card with Price Comparison Box
 * Shows Amazon and Flipkart prices side-by-side with the lower price highlighted
 */
export default function ProductCard({ product }) {
    const {
        id,
        title,
        image,
        rating,
        is_prime,
        amazon_price,
        amazon_link,
        flipkart_price,
        flipkart_link
    } = product;

    // Determine which price is lower
    const amazonIsLower = amazon_price && flipkart_price && amazon_price < flipkart_price;
    const flipkartIsLower = amazon_price && flipkart_price && flipkart_price < amazon_price;
    const samePrice = amazon_price && flipkart_price && amazon_price === flipkart_price;

    // Format price with Indian currency format
    const formatPrice = (price) => {
        if (!price) return '—';
        return '₹' + price.toLocaleString('en-IN');
    };

    // Calculate savings
    const getSavings = () => {
        if (!amazon_price || !flipkart_price) return null;
        const diff = Math.abs(amazon_price - flipkart_price);
        if (diff === 0) return null;
        return formatPrice(diff);
    };

    return (
        <div className="product-card bg-white rounded-sm border border-gray-200 flex flex-col hover:shadow-amazon-hover transition-all duration-200">
            {/* Image Container - Fixed height */}
            <div className="relative p-2 bg-white flex justify-center items-center h-52">
                <a href={amazon_link || flipkart_link || '#'} target="_blank" rel="noopener noreferrer" className="block w-full h-full">
                    <img
                        src={image || '/placeholder.jpg'}
                        alt={title}
                        className="w-full h-full object-contain mix-blend-multiply"
                        onError={(e) => {
                            e.target.src = 'https://via.placeholder.com/200x200?text=No+Image';
                        }}
                    />
                </a>

                {/* Prime Badge */}
                {is_prime && (
                    <div className="absolute top-2 left-2">
                        <img
                            src="https://m.media-amazon.com/images/G/31/marketing/prime/Prime_icon_blue._CB485947477_.png"
                            alt="Prime"
                            className="h-5"
                        />
                    </div>
                )}
            </div>

            <div className="p-4 flex flex-col flex-grow">
                {/* Product Title */}
                <h3 className="text-sm font-medium leading-tight mb-1 line-clamp-3 min-h-[3.5rem]">
                    <a
                        href={amazon_link || flipkart_link || '#'}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[#0F1111] hover:text-[#C7511F] hover:underline"
                    >
                        {title === "Unknown Product" ? "Product Title Unavailable" : title}
                    </a>
                </h3>

                {/* Star Rating */}
                {rating && (
                    <div className="flex items-center mb-2">
                        <div className="flex text-[#FFA41C]">
                            {[1, 2, 3, 4, 5].map(i => (
                                <svg
                                    key={i}
                                    className={`w-4 h-4 ${i <= Math.round(rating) ? 'fill-current' : 'text-gray-200 stroke-current'}`}
                                    xmlns="http://www.w3.org/2000/svg"
                                    viewBox="0 0 24 24"
                                >
                                    <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z" />
                                </svg>
                            ))}
                        </div>
                        <span className="text-[#007185] text-xs ml-1 hover:text-[#C7511F] hover:underline cursor-pointer">
                            {Math.floor(Math.random() * 5000) + 100}
                        </span>
                    </div>
                )}

                {/* Price Comparison Block */}
                <div className="mt-auto border-t border-gray-100 pt-2 space-y-2">
                    {/* Amazon Price Row */}
                    <div className={`flex justify-between items-center ${amazonIsLower ? 'bg-green-50 -mx-2 px-2 py-1 rounded' : ''}`}>
                        <div className="flex items-center gap-2">
                            <span className="text-xs text-gray-500 w-16">Amazon</span>
                            <span className={`text-lg ${amazonIsLower ? 'font-bold text-[#B12704]' : 'text-[#0F1111]'}`}>
                                {amazon_price ? (
                                    <>
                                        <span className="text-xs align-top relative top-0.5">₹</span>
                                        {amazon_price.toLocaleString('en-IN')}
                                    </>
                                ) : '—'}
                            </span>
                        </div>
                        {amazon_link && (
                            <a
                                href={amazon_link}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-[10px] bg-[#FEBD69] hover:bg-[#F3A847] text-[#0F1111] px-2 py-1 rounded border border-[#FCD200] cursor-pointer no-underline"
                            >
                                View
                            </a>
                        )}
                    </div>

                    {/* Flipkart Price Row */}
                    <div className={`flex justify-between items-center ${flipkartIsLower ? 'bg-green-50 -mx-2 px-2 py-1 rounded' : ''}`}>
                        <div className="flex items-center gap-2">
                            <span className="text-xs text-gray-500 w-16">Flipkart</span>
                            <span className={`text-lg ${flipkartIsLower ? 'font-bold text-[#B12704]' : 'text-[#565959]'}`}>
                                {flipkart_price ? (
                                    <>
                                        <span className="text-xs align-top relative top-0.5">₹</span>
                                        {flipkart_price.toLocaleString('en-IN')}
                                    </>
                                ) : '—'}
                            </span>
                        </div>
                        {flipkart_link && (
                            <a
                                href={flipkart_link}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-[10px] bg-[#2874F0] hover:bg-[#1e65d8] text-white px-2 py-1 rounded border border-[#2874F0] cursor-pointer no-underline"
                            >
                                View
                            </a>
                        )}
                    </div>
                </div>

                {/* Savings Message */}
                {getSavings() && !samePrice && (
                    <div className="mt-2 text-xs text-[#B12704] font-medium">
                        Save {getSavings()} on {amazonIsLower ? 'Amazon' : 'Flipkart'}
                    </div>
                )}
            </div>
        </div>
    );
}

import { motion, AnimatePresence } from 'framer-motion';

export default function CartDrawer({ isOpen, onClose, cart, onUpdateQuantity, onRemoveItem }) {
    const calculateTotal = () => {
        return cart.reduce((total, item) => {
            const price = item.store === 'amazon' ? item.product.amazon_price : item.product.flipkart_price;
            return total + (price || 0) * item.quantity;
        }, 0);
    };

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-[60]"
                    />

                    {/* Drawer */}
                    <motion.div
                        initial={{ x: '100%' }}
                        animate={{ x: 0 }}
                        exit={{ x: '100%' }}
                        transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                        className="fixed top-0 right-0 h-full w-full max-w-md bg-white shadow-2xl z-[70] flex flex-col"
                    >
                        {/* Header */}
                        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
                            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                                <svg className="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" /></svg>
                                Your Cart
                            </h2>
                            <button onClick={onClose} className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-200 rounded-full transition-colors">
                                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>

                        {/* Cart Items */}
                        <div className="flex-1 overflow-y-auto p-6 space-y-6">
                            {cart.length === 0 ? (
                                <div className="h-full flex flex-col items-center justify-center text-slate-500 space-y-4">
                                    <div className="w-20 h-20 bg-slate-100 rounded-full flex items-center justify-center mb-2">
                                        <svg className="w-10 h-10 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
                                        </svg>
                                    </div>
                                    <p className="text-lg font-medium text-slate-700">Your cart is empty</p>
                                    <p className="text-sm text-slate-400 text-center max-w-[250px]">Looks like you haven't added any products to your cart yet.</p>
                                    <button onClick={onClose} className="mt-4 px-6 py-2.5 bg-primary text-white rounded-lg font-medium hover:bg-primary-hover transition-colors shadow-sm">
                                        Continue Shopping
                                    </button>
                                </div>
                            ) : (
                                cart.map((item, idx) => {
                                    const price = item.store === 'amazon' ? item.product.amazon_price : item.product.flipkart_price;
                                    return (
                                        <div key={`${item.product.id}-${item.store}-${idx}`} className="flex gap-4 border-b border-slate-100 pb-6 last:border-0">
                                            <div className="w-20 h-20 flex-shrink-0 bg-white border border-slate-200 rounded-lg p-2">
                                                <img src={item.product.image} alt={item.product.title} className="w-full h-full object-contain" />
                                            </div>
                                            <div className="flex-1 flex flex-col">
                                                <h3 className="text-sm font-medium text-slate-900 line-clamp-2 mb-1">{item.product.title}</h3>
                                                <div className="flex items-center gap-2 mb-2">
                                                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider ${item.store === 'amazon' ? 'bg-sky-100 text-sky-800' : 'bg-yellow-100 text-yellow-800'}`}>
                                                        {item.store}
                                                    </span>
                                                    <span className="text-sm font-bold text-slate-900">₹{price?.toLocaleString('en-IN')}</span>
                                                </div>
                                                <div className="flex items-center justify-between mt-auto">
                                                    <div className="flex items-center border border-slate-200 rounded-lg">
                                                        <button onClick={() => onUpdateQuantity(item.product.id, item.store, -1)} className="px-2.5 py-1 text-slate-500 hover:bg-slate-100 hover:text-slate-700 transition-colors rounded-l-lg">-</button>
                                                        <span className="px-3 py-1 text-sm font-medium text-slate-700 border-x border-slate-200 min-w-[2.5rem] text-center">{item.quantity}</span>
                                                        <button onClick={() => onUpdateQuantity(item.product.id, item.store, 1)} className="px-2.5 py-1 text-slate-500 hover:bg-slate-100 hover:text-slate-700 transition-colors rounded-r-lg">+</button>
                                                    </div>
                                                    <button onClick={() => onRemoveItem(item.product.id, item.store)} className="text-xs font-medium text-red-500 hover:text-red-600 transition-colors">
                                                        Remove
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })
                            )}
                        </div>

                        {/* Footer */}
                        {cart.length > 0 && (
                            <div className="border-t border-slate-200 p-6 bg-slate-50">
                                <div className="flex items-center justify-between mb-4">
                                    <span className="text-slate-600 font-medium">Subtotal</span>
                                    <span className="text-xl font-bold text-slate-900">₹{calculateTotal().toLocaleString('en-IN')}</span>
                                </div>
                                <button className="w-full py-3 bg-primary text-white rounded-xl font-bold shadow-sm hover:bg-primary-hover hover:shadow transition-all active:scale-[0.98]">
                                    Proceed to Checkout
                                </button>
                            </div>
                        )}
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
}

"""
ShopSync Flask API
==================
Backend API for the ShopSync e-commerce aggregator.
Provides /search endpoint that scrapes Amazon and Flipkart.
Uses NVIDIA AI (Kimi-K2) for intelligent chatbot responses.
"""

import os
import json
import re
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from openai import OpenAI

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:5176", "http://localhost:5177", "http://localhost:5178"], supports_credentials=True)

# Load fallback data
FALLBACK_DATA_PATH = os.path.join(os.path.dirname(__file__), 'fallback_data.json')

def load_fallback_data():
    """Load fallback data from JSON file."""
    try:
        with open(FALLBACK_DATA_PATH, 'r') as f:
            data = json.load(f)
            return data.get('products', [])
    except Exception as e:
        print(f"Error loading fallback data: {e}")
        return []


def search_with_timeout(query, timeout=15, use_nvidia=False):
    """
    Execute scraper with timeout.
    Falls back to mock data if scraping fails or takes too long.
    """
    from scraper import search_products
    
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(search_products, query, timeout, use_nvidia)
        
        try:
            results = future.result(timeout=timeout)
            if results and len(results) > 0:
                return results, False  # Results, is_fallback
        except FuturesTimeoutError:
            print(f"[API] Scraping timed out after {timeout}s")
        except Exception as e:
            print(f"[API] Scraping error: {e}")
    
    # Return fallback data
    return load_fallback_data(), True


@app.route('/search', methods=['GET'])
def search():
    """
    Search endpoint for product aggregation.
    
    Query Parameters:
        q (str): Search query string
        sort (str): Sort option (relevance, price_asc, price_desc, rating)
        
    Returns:
        JSON response with products array
    """
    query = request.args.get('q', '').strip()
    use_mock = request.args.get('mock', 'false').lower() == 'true'
    sort_by = request.args.get('sort', 'relevance').lower()
    use_nvidia = request.args.get('nvidia', 'false').lower() == 'true'
    
    if not query:
        return jsonify({
            'success': False,
            'error': 'Query parameter "q" is required',
            'products': []
        }), 400
    
    print(f"[API] Searching for: {query} (Sort: {sort_by}, NVIDIA: {use_nvidia})")
    start_time = time.time()
    
    if use_mock:
        # Force use of fallback data (for demo/testing)
        products = load_fallback_data()
        is_fallback = True
    else:
        # Increase timeout for live scraping
        products, is_fallback = search_with_timeout(query, timeout=45, use_nvidia=use_nvidia)
    
    # Implement Sorting
    if products and not is_fallback:
        def get_min_price(p):
            prices = [p.get('amazon_price'), p.get('flipkart_price')]
            valid_prices = [pr for pr in prices if pr is not None]
            return min(valid_prices) if valid_prices else float('inf')

        if sort_by == 'price_asc':
            products.sort(key=get_min_price)
        elif sort_by == 'price_desc':
            products.sort(key=get_min_price, reverse=True)
        elif sort_by == 'rating':
            products.sort(key=lambda p: p.get('rating') or 0, reverse=True)
        # default is relevance (matched first), which scraper.py already handles
    
    elapsed = time.time() - start_time
    print(f"[API] Returning {len(products)} products in {elapsed:.2f}s (fallback={is_fallback})")
    
    return jsonify({
        'success': True,
        'query': query,
        'count': len(products),
        'is_fallback': is_fallback,
        'products': products,
        'elapsed_time': round(elapsed, 2)
    })


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'ShopSync API'
    })


@app.route('/chat', methods=['POST'])
def chat():
    """
    AI-powered chatbot endpoint using NVIDIA Kimi-K2 model.
    
    Handles:
    1. Recommending best products from current search results
    2. Understanding product descriptions and triggering searches
    3. General shopping assistance via AI
    """
    data = request.get_json()
    message = (data.get('message', '') or '').strip()
    current_products = data.get('current_products', [])
    
    if not message:
        return jsonify({'success': False, 'error': 'Message is required'}), 400
    
    print(f"[CHAT] User: {message}")
    
    try:
        response = process_chat_with_ai(message, current_products)
        print(f"[CHAT] Action: {response.get('action', 'reply')}")
        return jsonify({'success': True, **response})
    except Exception as e:
        print(f"[CHAT] AI Error: {e}")
        # Fallback to keyword-based processing if AI fails
        try:
            response = process_chat_fallback(message, current_products)
            return jsonify({'success': True, **response})
        except Exception as e2:
            print(f"[CHAT] Fallback Error: {e2}")
            return jsonify({
                'success': True,
                'action': 'reply',
                'reply': "I'm having trouble processing that. Could you rephrase your question?"
            })


# ═══════════════════════════════════════════════════════════
# NVIDIA AI Integration
# ═══════════════════════════════════════════════════════════

NVIDIA_CLIENT = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key="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"
)

SYSTEM_PROMPT = """You are ShopSync Assistant — an intelligent shopping helper for an e-commerce price comparison platform that aggregates products from Amazon and Flipkart.

Your capabilities:
1. **Recommend products** from currently loaded search results
2. **Understand vague product descriptions** and convert them into search queries
3. **Answer shopping questions** naturally

RESPONSE FORMAT — You MUST respond with valid JSON only (no markdown, no code fences):
{
  "action": "reply" | "search" | "recommend",
  "reply": "Your message to the user (use markdown bold ** for emphasis, use emojis)",
  "search_query": "product search term (only when action=search)",
  "criteria": "best" | "cheapest" | "rating" | "compare" (only when action=recommend),
  "budget": null or number (optional budget constraint)
}

RULES:
- When user describes something they need (e.g., "I need something to listen to music"), set action="search" and search_query to the best product search term (e.g., "wireless headphones"). Be smart in translating descriptions to real product names.
- When user asks about current results (e.g., "what's the best deal?", "cheapest one?"), set action="recommend" with appropriate criteria.
- When user asks to compare, set action="recommend" with criteria="compare".
- For greetings, help questions, thanks, or general chat, set action="reply".
- Keep replies concise, friendly, and helpful. Use emojis sparingly.
- If the user mentions a budget like "under 5000", include it in the budget field as a number.
- For search queries, extract the core product name — do not include "under X" in the search_query, put the budget in the budget field instead.
- ALWAYS respond with valid JSON. No extra text outside the JSON object."""


def process_chat_with_ai(message, current_products):
    """
    Process chat message using NVIDIA Kimi-K2 AI model.
    The AI decides the action (search/recommend/reply) and generates the response.
    """
    # Build context about current products
    product_context = ""
    if current_products:
        product_summary = []
        for i, p in enumerate(current_products[:15], 1):
            prices = []
            if p.get('amazon_price'):
                prices.append(f"Amazon: ₹{p['amazon_price']:,.0f}")
            if p.get('flipkart_price'):
                prices.append(f"Flipkart: ₹{p['flipkart_price']:,.0f}")
            price_str = " | ".join(prices) if prices else "Price N/A"
            rating_str = f"★{p.get('rating', 'N/A')}" if p.get('rating') else ""
            product_summary.append(f"{i}. {p.get('title', 'Unknown')[:80]} — {price_str} {rating_str}")
        
        product_context = f"\n\nCURRENT SEARCH RESULTS ({len(current_products)} products loaded):\n" + "\n".join(product_summary)
    else:
        product_context = "\n\nNo products are currently loaded. If the user asks about results, tell them to search first."

    user_message = f"User message: {message}{product_context}"
    
    # Call NVIDIA API
    completion = NVIDIA_CLIENT.chat.completions.create(
        model="moonshotai/kimi-k2-instruct-0905",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        temperature=0.6,
        top_p=0.9,
        max_tokens=1024,
        stream=False
    )
    
    ai_response = completion.choices[0].message.content.strip()
    print(f"[CHAT AI] Raw response: {ai_response[:200]}")
    
    # Parse JSON response from AI
    # Clean up potential markdown code fences
    ai_response = re.sub(r'^```(?:json)?\s*', '', ai_response)
    ai_response = re.sub(r'\s*```$', '', ai_response)
    ai_response = ai_response.strip()
    
    parsed = json.loads(ai_response)
    
    action = parsed.get('action', 'reply')
    reply = parsed.get('reply', '')
    
    # Handle search action
    if action == 'search' and parsed.get('search_query'):
        search_query = parsed['search_query']
        budget = parsed.get('budget')
        if budget:
            reply += f"\n\n💰 Budget noted: under ₹{int(budget):,}"
        return {
            'action': 'search',
            'search_query': search_query,
            'reply': reply or f"🔍 Searching for **\"{search_query}\"**... Results will appear in the main area!"
        }
    
    # Handle recommend action — use our product data functions
    if action == 'recommend' and current_products:
        criteria = parsed.get('criteria', 'best')
        budget = parsed.get('budget')
        
        if criteria == 'compare':
            result = compare_products(current_products)
        else:
            result = recommend_best(current_products, criteria, budget=int(budget) if budget else None)
        
        # Use AI's reply text but our product data
        if reply:
            result['reply'] = reply + "\n\n" + result.get('reply', '')
        return result
    
    # Default reply
    return {
        'action': 'reply',
        'reply': reply or "I'm not sure what you mean. Try describing a product or asking about current results!"
    }


def process_chat_fallback(message, current_products):
    """
    Fallback keyword-based processing when AI is unavailable.
    """
    msg = message.lower().strip()
    
    # Best deal
    if any(kw in msg for kw in ['best', 'recommend', 'top', 'suggest', 'deal']) and current_products:
        return recommend_best(current_products, 'best')
    
    # Cheapest
    if any(kw in msg for kw in ['cheap', 'lowest', 'budget', 'affordable']) and current_products:
        budget_match = re.search(r'under\s*₹?\s*(\d[\d,]*)', msg)
        budget = int(budget_match.group(1).replace(',', '')) if budget_match else None
        return recommend_best(current_products, 'cheapest', budget=budget)
    
    # Rating
    if any(kw in msg for kw in ['rated', 'rating', 'stars', 'popular']) and current_products:
        return recommend_best(current_products, 'rating')
    
    # Compare
    if any(kw in msg for kw in ['compare', 'vs', 'versus']) and current_products:
        return compare_products(current_products)
    
    # Treat as search
    if len(msg.split()) >= 2:
        return {
            'action': 'search',
            'search_query': msg,
            'reply': f"🔍 Searching for **\"{msg}\"**..."
        }
    
    return {
        'action': 'reply',
        'reply': "Tell me what you're looking for, or ask about the current search results!"
    }


# ═══════════════════════════════════════════════════════════
# Product Helper Functions
# ═══════════════════════════════════════════════════════════

def recommend_best(products, criteria='best', budget=None):
    """Recommend the best product(s) from current results based on criteria."""
    if not products:
        return {
            'action': 'reply',
            'reply': "There are no products loaded yet. Search for something first, then ask me for recommendations!"
        }
    
    def get_min_price(p):
        prices = [p.get('amazon_price'), p.get('flipkart_price')]
        valid = [pr for pr in prices if pr is not None]
        return min(valid) if valid else float('inf')
    
    def get_savings(p):
        a = p.get('amazon_price')
        f = p.get('flipkart_price')
        if a and f:
            return abs(a - f)
        return 0
    
    filtered = products
    if budget:
        filtered = [p for p in products if get_min_price(p) <= budget]
        if not filtered:
            return {
                'action': 'reply',
                'reply': f"No products found under ₹{budget:,}. The cheapest option is ₹{get_min_price(min(products, key=get_min_price)):,.0f}. Try a higher budget?"
            }
    
    if criteria == 'cheapest':
        sorted_prods = sorted(filtered, key=get_min_price)
        top = sorted_prods[:3]
        label = "💰 **Cheapest Options**"
        if budget:
            label = f"💰 **Best Options Under ₹{budget:,}**"
        
    elif criteria == 'rating':
        sorted_prods = sorted(filtered, key=lambda p: p.get('rating') or 0, reverse=True)
        top = sorted_prods[:3]
        label = "⭐ **Highest Rated Products**"
        
    else:  # 'best' — balance of price, rating, and savings
        def score(p):
            price = get_min_price(p)
            rating = p.get('rating') or 0
            savings = get_savings(p)
            has_both = 1 if (p.get('amazon_price') and p.get('flipkart_price')) else 0
            price_score = max(0, 100 - (price / 1000)) if price < float('inf') else 0
            return (rating * 20) + price_score + (savings / 100) + (has_both * 10)
        
        sorted_prods = sorted(filtered, key=score, reverse=True)
        top = sorted_prods[:3]
        label = "🏆 **Best Deals — Top Picks**"
    
    reply_lines = [f"{label}\n"]
    for i, p in enumerate(top, 1):
        price = get_min_price(p)
        price_str = f"₹{price:,.0f}" if price < float('inf') else "Price N/A"
        rating_str = f" | ★ {p.get('rating', 'N/A')}" if p.get('rating') else ""
        savings = get_savings(p)
        savings_str = f" | Save ₹{savings:,.0f}" if savings > 0 else ""
        title = p.get('title', 'Unknown')[:60]
        reply_lines.append(f"{i}. **{title}**\n   {price_str}{rating_str}{savings_str}")
    
    reply_lines.append("\n👆 Here are the product details with links:")
    
    return {
        'action': 'recommend',
        'reply': '\n'.join(reply_lines),
        'recommended_products': top
    }


def compare_products(products):
    """Compare top products side by side."""
    if len(products) < 2:
        return {
            'action': 'reply',
            'reply': "Need at least 2 products to compare. Search for more items first!"
        }
    
    def get_min_price(p):
        prices = [p.get('amazon_price'), p.get('flipkart_price')]
        valid = [pr for pr in prices if pr is not None]
        return min(valid) if valid else float('inf')
    
    cheapest = min(products[:10], key=get_min_price)
    highest_rated = max(products[:10], key=lambda p: p.get('rating') or 0)
    
    top = []
    seen_titles = set()
    for p in [cheapest, highest_rated]:
        t = p.get('title', '')[:40]
        if t not in seen_titles:
            top.append(p)
            seen_titles.add(t)
    
    reply = "📊 **Quick Comparison**\n\n"
    cheapest_price = get_min_price(cheapest)
    reply += f"💰 **Cheapest**: {cheapest.get('title', '')[:50]}\n   → ₹{cheapest_price:,.0f}\n\n"
    reply += f"⭐ **Top Rated**: {highest_rated.get('title', '')[:50]}\n   → ★ {highest_rated.get('rating', 'N/A')}\n"
    
    return {
        'action': 'recommend',
        'reply': reply,
        'recommended_products': top
    }


@app.route('/compare-details', methods=['POST'])
def compare_details():
    """
    Deep-scrape product pages to get technical specifications for comparison.
    
    Request Body:
        products: Array of {title, amazon_link, flipkart_link, amazon_price, flipkart_price, image, rating}
    
    Returns:
        JSON with detailed specs for each product
    """
    data = request.get_json()
    products_to_compare = data.get('products', [])
    
    if not products_to_compare or len(products_to_compare) < 2:
        return jsonify({
            'success': False,
            'error': 'At least 2 products are required for comparison'
        }), 400
    
    if len(products_to_compare) > 4:
        return jsonify({
            'success': False,
            'error': 'Maximum 4 products can be compared at once'
        }), 400
    
    print(f"[COMPARE] Comparing {len(products_to_compare)} products...")
    start_time = time.time()
    
    from scraper import scrape_product_details
    
    results = []
    for p in products_to_compare:
        title = p.get('title', 'Unknown')
        print(f"[COMPARE] Scraping details for: {title[:50]}...")
        
        # Scrape specs from both links if available
        amazon_specs = {}
        flipkart_specs = {}
        
        if p.get('amazon_link'):
            amazon_specs = scrape_product_details(p['amazon_link'])
        
        if p.get('flipkart_link'):
            flipkart_specs = scrape_product_details(p['flipkart_link'])
        
        # Merge specs (Amazon primary, Flipkart fills gaps)
        merged_specs = {**flipkart_specs, **amazon_specs}
        
        results.append({
            'title': title,
            'image': p.get('image', ''),
            'rating': p.get('rating'),
            'amazon_price': p.get('amazon_price'),
            'flipkart_price': p.get('flipkart_price'),
            'amazon_link': p.get('amazon_link'),
            'flipkart_link': p.get('flipkart_link'),
            'specs': merged_specs
        })
    
    elapsed = time.time() - start_time
    print(f"[COMPARE] Done in {elapsed:.1f}s — returned {len(results)} products")
    
    return jsonify({
        'success': True,
        'comparison': results,
        'elapsed_time': round(elapsed, 2)
    })


@app.route('/', methods=['GET'])
def index():
    """Root endpoint with API info."""
    return jsonify({
        'name': 'ShopSync API',
        'version': '1.0.0',
        'endpoints': {
            '/search': 'GET - Search products (params: q, sort, mock, nvidia)',
            '/chat': 'POST - Chatbot endpoint (body: message, current_products)',
            '/compare-details': 'POST - Deep compare products (body: products[])',
            '/health': 'GET - Health check'
        },
        'sort_options': ['relevance', 'price_asc', 'price_desc', 'rating']
    })


if __name__ == '__main__':
    print("=" * 50)
    print("ShopSync API Server")
    print("=" * 50)
    
    # Preload AI model at startup (not lazy)
    print("[STARTUP] Preloading AI model...")
    from scraper import preload_model
    preload_model()
    
    print("Endpoints:")
    print("  GET  /search?q=<query>  - Search products")
    print("  POST /chat              - Chatbot")
    print("  GET  /health            - Health check")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5002, debug=True)

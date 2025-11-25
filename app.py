import streamlit as st
from googleapiclient.discovery import build

# -------------------------------------------------------------------------
# 1. SETUP YOUR KEYS (Keep these consistent from your last fix)
# -------------------------------------------------------------------------
GOOGLE_API_KEY = "AIzaSyBhjRBhEsXoBlEsMJaV5u7EJomG65djWnI"  # Replace with your AIza... key
SEARCH_ENGINE_ID = "80a7463cfec4a4134"    # Replace with your cx=... ID

# -------------------------------------------------------------------------
# 2. THE EXPANDED LEGITIMATE SOURCE LIST
# -------------------------------------------------------------------------
# We categorize them to help you understand the source.

AUTHORIZED_RETAILERS = [
    "sephora.com", "ulta.com", "macys.com", "nordstrom.com", 
    "bloomingdales.com", "saksfifthavenue.com", "neimanmarcus.com", 
    "dillards.com", "harrods.com", "selfridges.com", "johnlewis.com",
    "boots.com", "myworld.com"
]

# Legit Discounters (Grey Market - Safe, better prices)
DISCOUNTERS = [
    "fragrancenet.com", "fragrancex.com", "perfume.com", "perfumania.com", 
    "jomashop.com", "maxaroma.com", "aurafragrance.com", "venbafragrance.com",
    "olfactoryfactoryllc.com", "foreverlux.com", "costco.com", "samsclub.com",
    "notino.co.uk", "notino.com", "makeupstore.com"
]

# Niche & Luxury Boutiques (Hard to find, high-end stuff)
NICHE_BOUTIQUES = [
    "luckyscent.com", "twistedlily.com", "ministryofscent.com", 
    "scentsplit.com", "noseparis.com", "essenza-nobile.de", 
    "aedes.com", "beautyhabit.com", "smallflower.com"
]

# Official Brands (Always safe, usually full price)
OFFICIAL_BRANDS = [
    "dior.com", "chanel.com", "gucci.com", "yslbeautyus.com", 
    "tomford.com", "creedboutique.com", "parfumsdemarly.com",
    "franciskurkdjian.com", "byredo.com", "lelabofragrances.com",
    "jomalone.com", "guerlain.com", "hermes.com"
]

# Combine all lists for the search filter
ALL_TRUSTED_SITES = AUTHORIZED_RETAILERS + DISCOUNTERS + NICHE_BOUTIQUES + OFFICIAL_BRANDS

# -------------------------------------------------------------------------
# FUNCTIONS
# -------------------------------------------------------------------------

def get_store_category(link):
    """Identifies which category a store belongs to for the UI."""
    for site in DISCOUNTERS:
        if site in link: return "✅ Verified Discounter (Best Price?)"
    for site in AUTHORIZED_RETAILERS:
        if site in link: return "🏬 Department Store"
    for site in NICHE_BOUTIQUES:
        if site in link: return "💎 Niche Boutique"
    for site in OFFICIAL_BRANDS:
        if site in link: return "🎖️ Official Brand Site"
    return "✅ Verified Retailer"

def extract_price(item):
    """
    Tries to find a price inside Google's rich snippet data.
    """
    try:
        pagemap = item.get('pagemap', {})
        
        # 1. Try 'offer' schema
        offer = pagemap.get('offer', [])
        if offer and isinstance(offer, list):
            price = offer[0].get('price')
            currency = offer[0].get('pricecurrency', '$')
            if price:
                return f"{price} {currency}", float(price)
        
        # 2. Try 'product' schema
        product = pagemap.get('product', [])
        if product and isinstance(product, list):
            price = product[0].get('price')
            if price:
                return f"${price}", float(price)

        # 3. Try metatags
        metatags = pagemap.get('metatags', [])
        if metatags:
            for tag in metatags:
                if 'og:price:amount' in tag:
                    return f"${tag['og:price:amount']}", float(tag['og:price:amount'])
                if 'product:price:amount' in tag:
                    return f"${tag['product:price:amount']}", float(tag['product:price:amount'])
                
    except Exception:
        pass
    
    return "Check Website", float('inf')

def search_google_custom(query):
    service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
    
    # We construct a massive OR query. 
    # Note: Google has a limit on query length, so we prioritize the most likely hits if the list is too long.
    # For now, we will strictly filter the RESULTS, rather than the QUERY, to avoid the limit.
    
    try:
        # Search the web generally for the product name
        res = service.cse().list(
            q=query,
            cx=SEARCH_ENGINE_ID,
            num=10
        ).execute()
        
        items = res.get('items', [])
        clean_results = []

        for item in items:
            link = item.get('link', '').lower()
            
            # THE FILTER: Only accept if the link is in our massive trusted list
            is_trusted = False
            for trusted_site in ALL_TRUSTED_SITES:
                if trusted_site in link:
                    is_trusted = True
                    break
            
            if is_trusted:
                price_str, price_val = extract_price(item)
                
                # Clean up title
                title = item.get('title')
                
                # Get Image
                pagemap = item.get('pagemap', {})
                cse_image = pagemap.get('cse_image', [])
                image_url = cse_image[0]['src'] if cse_image else None

                clean_results.append({
                    "title": title,
                    "price_str": price_str,
                    "price_val": price_val,
                    "store_cat": get_store_category(link),
                    "link": link,
                    "image": image_url
                })
            
        # Sort by price (Low to High), putting "Check Website" at the bottom
        clean_results.sort(key=lambda x: x['price_val'])
        
        return clean_results

    except Exception as e:
        st.error(f"Error: {e}")
        return []

# -------------------------------------------------------------------------
# UI
# -------------------------------------------------------------------------
st.set_page_config(page_title="LegitScents Expanded", page_icon="💎")

st.title("💎 LegitScents: Expanded Verified Search")
st.markdown("""
Searching over **40+ Verified Sources** including Authorized Retailers, Grey Market Discounters, and Niche Boutiques.
""")

query = st.text_input("Enter fragrance name:", placeholder="e.g. Creed Aventus")

if st.button("Search Trusted Sources"):
    if not query:
        st.warning("Please enter a name.")
    else:
        with st.spinner("Scanning legitimate retailers..."):
            # We add "perfume" to the query to help Google find product pages
            results = search_google_custom(query + " perfume buy")
            
            if not results:
                st.warning("No trusted results found on the first page. Try being more specific (e.g. 'Bleu de Chanel EDT').")
            else:
                st.success(f"Found {len(results)} trusted options!")
                
                for item in results:
                    with st.container():
                        col1, col2 = st.columns([1, 3])
                        
                        with col1:
                            if item['image']:
                                st.image(item['image'], width=100)
                            else:
                                st.write("🧴")
                        
                        with col2:
                            st.subheader(item['title'])
                            st.caption(item['store_cat'])
                            
                            if item['price_val'] != float('inf'):
                                st.markdown(f"### {item['price_str']}")
                            else:
                                st.markdown("**Price not detected** (Click to check)")
                                
                            st.markdown(f"[Go to Store ↗]({item['link']})")
                        
                        st.divider()

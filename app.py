import streamlit as st
from googleapiclient.discovery import build
import re

# -------------------------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------------------------

# 1. Your Google Cloud API Key
GOOGLE_API_KEY = "AIzaSyBhjRBhEsXoBlEsMJaV5u7EJomG65djWnI"

# 2. Your Search Engine ID (from programmablesearchengine.google.com)
SEARCH_ENGINE_ID = "80a7463cfec4a4134"

# Trusted Retailers
TRUSTED_RETAILERS = [
    "sephora.com", "ulta.com", "macys.com", "nordstrom.com", 
    "bloomingdales.com", "fragrancenet.com", "notino.com", 
    "dior.com", "chanel.com", "creedboutique.com"
]

# -------------------------------------------------------------------------
# FUNCTIONS
# -------------------------------------------------------------------------

def extract_price(item):
    """
    Tries to find a price inside Google's rich snippet data (PageMap).
    This is harder than SerpApi because the data is not always clean.
    """
    try:
        # Check for 'offer' data in the pagemap (Schema.org)
        pagemap = item.get('pagemap', {})
        offer = pagemap.get('offer', [])
        
        if offer and isinstance(offer, list):
            price = offer[0].get('price')
            currency = offer[0].get('pricecurrency', '$')
            if price:
                return f"{price} {currency}", float(price)
        
        # Fallback: Check metatags
        metatags = pagemap.get('metatags', [])
        if metatags:
            for tag in metatags:
                if 'og:price:amount' in tag:
                    return f"${tag['og:price:amount']}", float(tag['og:price:amount'])
                
    except Exception:
        pass
    
    return "Check Website", float('inf')

def search_google_custom(query):
    if GOOGLE_API_KEY == "AIzaSyCjOHiNdwWmHdoNrLGXU6rYFWs0Tt6EKBE":
        st.error("Please insert your valid Google Cloud API Key.")
        return []

    service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
    
    # We restrict the search to our trusted sites using the 'site:' operator
    # Creating a massive OR query: "Dior Sauvage (site:sephora.com OR site:ulta.com ...)"
    sites_query = " OR ".join([f"site:{site}" for site in TRUSTED_RETAILERS])
    full_query = f"{query} ({sites_query})"
    
    try:
        # Execute search
        res = service.cse().list(
            q=full_query,
            cx=SEARCH_ENGINE_ID,
            num=10
        ).execute()
        
        items = res.get('items', [])
        clean_results = []

        for item in items:
            title = item.get('title')
            link = item.get('link')
            snippet = item.get('snippet')
            
            # Get Image
            pagemap = item.get('pagemap', {})
            cse_image = pagemap.get('cse_image', [])
            image_url = cse_image[0]['src'] if cse_image else None
            
            # Extract Price
            price_str, price_val = extract_price(item)

            # Determine Store Name from Link
            store_name = "Unknown"
            for retailer in TRUSTED_RETAILERS:
                if retailer in link:
                    store_name = retailer.replace(".com", "").capitalize()
                    break

            clean_results.append({
                "title": title,
                "price_str": price_str,
                "price_val": price_val,
                "store": store_name,
                "link": link,
                "image": image_url
            })
            
        # Sort by price (Low to High)
        clean_results.sort(key=lambda x: x['price_val'])
        
        return clean_results

    except Exception as e:
        st.error(f"Error: {e}")
        return []

# -------------------------------------------------------------------------
# UI
# -------------------------------------------------------------------------
st.set_page_config(page_title="LegitScents (Official API)", page_icon="🕵️")
st.title("🕵️ LegitScents: Official Google API Version")

query = st.text_input("Enter fragrance name:", placeholder="e.g. Bleu de Chanel")

if st.button("Search"):
    if not query:
        st.warning("Please enter a name.")
    else:
        with st.spinner("Searching trusted retailers..."):
            results = search_google_custom(query)
            
            if not results:
                st.warning("No results found. Try a different spelling.")
            
            for item in results:
                with st.container():
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        if item['image']:
                            st.image(item['image'], width=100)
                    with col2:
                        st.subheader(item['title'])
                        st.caption(f"Store: **{item['store']}**")
                        
                        # Highlight price
                        if item['price_val'] != float('inf'):
                            st.metric("Estimated Price", item['price_str'])
                        else:
                            st.info("Price not listed in search snippet")
                            
                        st.markdown(f"[Visit Website]({item['link']})")
                    st.divider()

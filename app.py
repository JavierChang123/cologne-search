import streamlit as st
from serpapi import GoogleSearch
import pandas as pd

# -------------------------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------------------------

# Replace this with your actual API key from https://serpapi.com/
# For testing without a key, you can leave it blank, but it won't fetch real data.
API_KEY = "YOUR_SERPAPI_KEY_HERE"

# THE WHITELIST: Only results from these specific merchants will be shown.
# This ensures users only buy from verified/legitimate sources.
TRUSTED_RETAILERS = [
    "sephora",
    "ulta",
    "macy's",
    "nordstrom",
    "bloomingdale's",
    "saks fifth avenue",
    "fragrancenet",
    "notino",
    "dior",
    "chanel",
    "creed boutique",
    "neiman marcus"
]

# -------------------------------------------------------------------------
# FUNCTIONS
# -------------------------------------------------------------------------

def is_trusted_source(merchant_name):
    """Checks if the merchant is in our trusted list."""
    if not merchant_name:
        return False
    
    merchant_lower = merchant_name.lower()
    for trusted in TRUSTED_RETAILERS:
        if trusted in merchant_lower:
            return True
    return False

def search_fragrance(query):
    """
    Searches Google Shopping for the fragrance and filters for trusted stores.
    """
    if API_KEY == "YOUR_SERPAPI_KEY_HERE":
        st.error("Please insert a valid SerpApi Key in the code to fetch real data.")
        return []

    params = {
        "engine": "google_shopping",
        "q": query,
        "api_key": API_KEY,
        "google_domain": "google.com",
        "gl": "us", # Location: US
        "hl": "en"  # Language: English
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        
        shopping_results = results.get("shopping_results", [])
        
        # Filter and clean data
        verified_options = []
        
        for item in shopping_results:
            merchant = item.get("source") # The store name
            
            # THE CORE SECURITY LOGIC:
            if is_trusted_source(merchant):
                verified_options.append({
                    "title": item.get("title"),
                    "price_str": item.get("price"),
                    "price_val": item.get("extracted_price"),
                    "store": merchant,
                    "link": item.get("link"),
                    "image": item.get("thumbnail"),
                    "rating": item.get("rating", "N/A"),
                    "reviews": item.get("reviews", 0)
                })
        
        # Sort by price (Low to High)
        verified_options.sort(key=lambda x: x['price_val'] if x['price_val'] else float('inf'))
        
        return verified_options

    except Exception as e:
        st.error(f"An error occurred: {e}")
        return []

# -------------------------------------------------------------------------
# STREAMLIT UI
# -------------------------------------------------------------------------

st.set_page_config(page_title="LegitScents", page_icon="🧴")

st.title("🧴 LegitScents: Price Comparator")
st.markdown("""
Find the best prices for perfumes and colognes from **verified, legitimate retailers only**. 
We filter out unauthorized sellers to ensure authenticity.
""")

# Input
query = st.text_input("Enter the name of a cologne or perfume:", placeholder="e.g. Dior Sauvage Elixir")

if st.button("Find Best Price"):
    if not query:
        st.warning("Please enter a fragrance name.")
    else:
        with st.spinner(f"Searching verified retailers for '{query}'..."):
            results = search_fragrance(query)
            
            if not results:
                st.warning("No results found from trusted retailers. It might be out of stock or sold by unauthorized sellers.")
            else:
                st.success(f"Found {len(results)} verified options!")
                
                # Display results
                for item in results:
                    with st.container():
                        col1, col2, col3 = st.columns([1, 2, 1])
                        
                        with col1:
                            if item['image']:
                                st.image(item['image'], width=100)
                        
                        with col2:
                            st.subheader(item['title'])
                            st.caption(f"Sold by: **{item['store']}**")
                            if item['rating'] != "N/A":
                                st.write(f"⭐ {item['rating']} ({item['reviews']} reviews)")
                        
                        with col3:
                            st.metric(label="Price", value=item['price_str'])
                            st.link_button("Buy Now", item['link'])
                        
                        st.divider()

# Sidebar Info
st.sidebar.header("Trusted Sources")
st.sidebar.write("We currently check the following retailers:")
st.sidebar.write(", ".join([t.title() for t in TRUSTED_RETAILERS]))

# src/scraper.py
import os
from homeharvest import scrape_property
from datetime import datetime
import pandas as pd

def scrape_properties(zip_code, max_price):
    """
    Scrape properties from HomeHarvest based on zip code and max price.
    
    Args:
        zip_code (str): The zip code to search in
        max_price (int): Maximum price to filter properties
        
    Returns:
        list: List of property dictionaries
    """
    # Ensure the 'data' directory exists
    if not os.path.exists('data'):
        os.makedirs('data')

    # Generate filename based on current timestamp
    current_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"data/HomeHarvest_{current_timestamp}.csv"

    # Fetch properties with the provided parameters
    properties = scrape_property(
        location=f"{zip_code}",
        listing_type="for_sale",
        past_days=30
    )

    # Convert max_price to integer
    max_price = int(max_price)

    # Filter the results after fetching
    if max_price:
        # Convert list_price to numeric, coercing errors to NaN
        properties['list_price'] = pd.to_numeric(properties['list_price'], errors='coerce')
        # Drop rows where list_price is NaN
        properties = properties.dropna(subset=['list_price'])
        # Filter by max_price
        properties = properties[properties['list_price'] <= max_price]

    # Save to CSV
    properties.to_csv(filename, index=False)
    print(f"Number of properties: {len(properties)}")
    print(properties.head())

    # Convert DataFrame to list of dictionaries
    properties_list = properties.to_dict('records')

    return properties_list

if __name__ == "__main__":
    # Default values for command line usage
    scrape_properties("92101", 1000000)
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
    print(f"\nStarting property search for zip code {zip_code} with max price ${max_price}")
    
    try:
        # Ensure the 'data' directory exists
        if not os.path.exists('data'):
            os.makedirs('data')
            print("Created data directory")

        # Generate filename based on current timestamp
        current_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/HomeHarvest_{current_timestamp}.csv"
        print(f"Will save results to: {filename}")

        print("\nCalling HomeHarvester API...")
        # Fetch properties with the provided parameters
        properties = scrape_property(
            location=f"{zip_code}",
            listing_type="for_sale",
            past_days=30
        )
        print(f"Initial API response type: {type(properties)}")
        if isinstance(properties, pd.DataFrame):
            print(f"Initial property count: {len(properties)}")

        # Convert max_price to integer
        max_price = int(max_price)
        print(f"\nFiltering for properties under ${max_price}")

        # Filter the results after fetching
        if max_price and isinstance(properties, pd.DataFrame) and not properties.empty:
            # Convert list_price to numeric, coercing errors to NaN
            properties['list_price'] = pd.to_numeric(properties['list_price'], errors='coerce')
            print(f"Properties with valid prices: {len(properties.dropna(subset=['list_price']))}")
            
            # Drop rows where list_price is NaN
            properties = properties.dropna(subset=['list_price'])
            # Filter by max_price
            properties = properties[properties['list_price'] <= max_price]
            print(f"Properties under max price: {len(properties)}")

        if isinstance(properties, pd.DataFrame) and not properties.empty:
            # Save to CSV
            properties.to_csv(filename, index=False)
            print(f"\nSaved {len(properties)} properties to {filename}")
            print("\nSample of properties found:")
            print(properties.head())

            # Convert DataFrame to list of dictionaries
            properties_list = properties.to_dict('records')
            return properties_list
        else:
            print("\nNo properties found or invalid response from HomeHarvester")
            return []

    except Exception as e:
        print(f"\nError in scrape_properties: {str(e)}")
        raise

if __name__ == "__main__":
    # Test with provided parameters
    results = scrape_properties("32835", 1000000)
    print(f"\nReturned {len(results)} properties")
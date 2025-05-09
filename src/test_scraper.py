from scraper import scrape_properties
import pandas as pd
pd.set_option('display.max_columns', None)

print("Testing HomeHarvester scraper...")
properties = scrape_properties("32835", 1000000)
print(f"\nFound {len(properties)} properties")
if properties:
    print("\nFirst property details:")
    print(pd.DataFrame(properties).head(1).to_string()) 
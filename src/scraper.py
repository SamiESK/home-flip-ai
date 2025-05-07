import os
from homeharvest import scrape_property
from datetime import datetime
from tqdm import tqdm  # Import tqdm for the progress bar

# Ensure the 'data' directory exists
if not os.path.exists('data'):
    os.makedirs('data')

# Generate filename based on current timestamp
current_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"data/HomeHarvest_{current_timestamp}.csv"  # Save inside 'data' folder

# Fetch properties
properties = scrape_property(
    location="San Diego, CA",
    listing_type="for_sale",  # or 'for_sale', 'for_rent', 'pending'
    past_days=30,  # Last 30 days
)

# Set up a tqdm progress bar with a description and custom styling
with tqdm(total=len(properties), desc="Scraping properties", ncols=100, bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed} < {remaining}, {rate_fmt}]") as pbar:
    for index, property in properties.iterrows():
        # Process each property (or add your custom logic here)
        # For example: (You can replace this with your actual property processing code)
        # property['processed'] = some_processing_function(property)

        # Update the progress bar
        pbar.update(1)

# Save to CSV
properties.to_csv(filename, index=False)
print(f"Number of properties: {len(properties)}")
print(properties.head())

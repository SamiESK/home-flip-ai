import subprocess
import os
from time import sleep

def run_scraper():
    """Run the scraper to gather new property data"""
    print("Running scraper.py...")
    try:
        subprocess.run(["python", "scraper.py"], check=True)
        print("Scraper completed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running scraper.py: {e}")

def run_predictor():
    """Run the predictor to make predictions on the scraped data"""
    print("Running predictor.py...")
    try:
        subprocess.run(["python", "predictor.py"], check=True)
        print("Predictions completed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running predictor.py: {e}")

def main():
    """Main function to run the entire process"""
    # Ensure all steps run sequentially and successfully
    run_scraper()
    sleep(2)  # Optional: sleep to allow any processes to finalize before running the next step
    run_predictor()

if __name__ == "__main__":
    main()

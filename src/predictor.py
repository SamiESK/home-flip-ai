import pandas as pd
import pickle
import os

# Load the trained model
with open('model.p', 'rb') as f:
    model = pickle.load(f)

# Dynamically get the latest file name from the 'data' folder
# Find the latest file based on timestamp in the filename
data_folder = 'data'
latest_file = max([os.path.join(data_folder, f) for f in os.listdir(data_folder) if f.startswith('HomeHarvest')], key=os.path.getctime)

# Load the new data
df_new = pd.read_csv(latest_file)  # Use the dynamically fetched file

# Prepare the data (make sure to select the same features used for training)
X_new = df_new[['list_price', 'sqft', 'beds', 'full_baths', 'days_on_mls']]  # Adjust columns as necessary

# Make predictions using the trained model
predictions = model.predict(X_new)

# Add predictions to the DataFrame (optional)
df_new['is_good_flip'] = predictions

# Print or save the predictions
print(df_new[['property_id', 'is_good_flip']])  # Display the results
df_new.to_csv('predictions.csv', index=False)  # Optionally save predictions to a new CSV file

print("Predictions complete and saved to 'predictions.csv'")

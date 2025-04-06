from src.predictor import predict

new_property = {
    'price': 250000,
    'sqft': 1800,
    'beds': 3,
    'baths': 2,
    'days_on_market': 15
}


flip_class, flip_score = predict(new_property)
print(f"Prediction: {'Good Flip ✅' if flip_class else 'Bad Flip ❌'}")
print(f"Confidence Score: {flip_score}%")

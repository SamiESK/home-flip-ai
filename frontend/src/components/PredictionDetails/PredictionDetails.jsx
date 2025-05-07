import React from 'react';
import './PredictionDetails.css';

const PredictionDetails = ({ prediction }) => {
  return (
    <div className="prediction-details">
      <h2>AI Prediction Analysis</h2>
      <div className="prediction-score">
        <h3>Flip Score</h3>
        <div className="score-indicator">
          {prediction.is_good_flip ? 'Recommended' : 'Not Recommended'}
        </div>
      </div>
      <div className="prediction-factors">
        <h3>Key Factors</h3>
        <ul>
          <li>Price per Sqft: ${(prediction.list_price / prediction.sqft).toFixed(2)}</li>
          <li>Days on Market: {prediction.days_on_mls}</li>
          <li>Property Size: {prediction.sqft} sqft</li>
        </ul>
      </div>
    </div>
  );
};

export default PredictionDetails;
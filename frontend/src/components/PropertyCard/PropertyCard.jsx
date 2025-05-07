import React from 'react';
import './PropertyCard.css';

const PropertyCard = ({ property, onClick, isSelected }) => {
  const { 
    list_price, 
    sqft, 
    beds, 
    full_baths, 
    days_on_mls,
    is_good_flip,
    confidence_score,
    url
  } = property;

  const formatNumber = (num) => {
    return num?.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  };

  return (
    <div 
      className={`property-card ${is_good_flip ? 'good-flip' : ''} ${isSelected ? 'selected' : ''}`}
      onClick={onClick}
    >
      <div className="property-card__header">
        <h3>${formatNumber(list_price)}</h3>
        {is_good_flip && (
          <span className="good-flip-badge">
            Good Flip ({confidence_score}% confidence)
          </span>
        )}
      </div>
      <div className="property-card__details">
        <p>{beds} beds • {full_baths} baths • {formatNumber(sqft)} sqft</p>
        <p>Days on Market: {days_on_mls}</p>
        {url && (
          <a 
            href={url} 
            target="_blank" 
            rel="noopener noreferrer"
            className="property-link"
            onClick={(e) => e.stopPropagation()}
          >
            View Listing
          </a>
        )}
      </div>
    </div>
  );
};

export default PropertyCard;
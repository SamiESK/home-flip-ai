// frontend/src/components/PropertyCard/PropertyCard.jsx
import React from 'react';
import './PropertyCard.css';

const PropertyCard = ({ property, onClick, isSelected }) => {
  const { 
    list_price,
    sqft,
    beds,
    full_baths,
    days_on_mls,
    property_url, // This is the image URL
    street,
    city,
    state,
    zip_code,
    primary_photo, // This is another possible image URL
    realtor_url, // This is the listing URL
    property_id
  } = property;

  const formatNumber = (num) => {
    return num?.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  };

  // Use primary_photo if available, fallback to property_url
  const imageUrl = primary_photo || property_url;

  return (
    <div 
      className={`property-card ${isSelected ? 'selected' : ''}`}
      onClick={onClick}
    >
      <div className="property-card__image-container">
        {imageUrl ? (
          <img 
            src={imageUrl} 
            alt={`Property ${property_id}`}
            className="property-card__image"
            onError={(e) => {
              e.target.src = 'https://via.placeholder.com/300x200?text=No+Image';
            }}
          />
        ) : (
          <div className="property-card__image-placeholder">
            No Image Available
          </div>
        )}
      </div>
      
      <div className="property-card__content">
        <div className="property-card__header">
          <h3>${formatNumber(list_price)}</h3>
        </div>
        
        <div className="property-card__details">
          <p className="property-address">
            {street && `${street}, ${city}, ${state} ${zip_code}`}
          </p>
          <p>{beds} beds • {full_baths} baths • {formatNumber(sqft)} sqft</p>
          <p>Days on Market: {days_on_mls}</p>
          {property_url && (
            <a 
              href={property_url}
              target="_blank"
              rel="noopener noreferrer"
              className="property-link"
              onClick={(e) => e.stopPropagation()}
            >
              View Property
            </a>
          )}
          {realtor_url && (
            <a 
              href={realtor_url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="property-link"
              onClick={(e) => e.stopPropagation()}
            >
              View on Realtor.com
            </a>
          )}
        </div>
      </div>
    </div>
  );
};

export default PropertyCard;
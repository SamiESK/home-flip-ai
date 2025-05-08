// frontend/src/components/PropertyCard/PropertyCard.jsx
import React from 'react';
import './PropertyCard.css';

const PropertyCard = ({ property, onClick, isSelected }) => {
  if (!property) return null;

  const { 
    list_price = 0,
    sqft = 0,
    beds = 0,
    full_baths = 0,
    days_on_mls = 0,
    photos = [],
    street = '',
    city = '',
    state = '',
    zip_code = '',
    agent_name = '',
    agent_phones = [],
    property_id = '',
    property_url = ''
  } = property;

  // Debug log to check photo data
  console.log('Property photos:', {
    propertyId: property_id,
    photos: photos,
    firstPhoto: photos?.[0],
    photoType: typeof photos
  });

  // Get the first valid photo URL or use placeholder
  const getPhotoUrl = () => {
    if (Array.isArray(photos) && photos.length > 0) {
      return photos[0];
    }
    if (typeof photos === 'string' && photos.length > 0) {
      return photos;
    }
    return 'https://placehold.co/600x400/e0e0e0/999999?text=No+Image';
  };

  return (
    <div 
      className={`property-card ${isSelected ? 'selected' : ''}`}
      onClick={onClick}
    >
      <div className="property-card__image-container">
        <img 
          src={getPhotoUrl()}
          alt={`Property at ${street}`}
          className="property-card__image"
          onError={(e) => {
            console.log('Image load error:', e.target.src);
            e.target.src = 'https://placehold.co/600x400/e0e0e0/999999?text=No+Image';
          }}
        />
      </div>
      
      <div className="property-card__content">
        <div className="property-card__header">
          <h3>${list_price.toLocaleString()}</h3>
        </div>
        
        <div className="property-card__details">
          <p className="property-address">
            {street}, {city}, {state} {zip_code}
          </p>
          <p>{beds} beds • {full_baths} baths • {sqft.toLocaleString()} sqft</p>
          {days_on_mls > 0 && <p>Days on Market: {days_on_mls}</p>}
          {agent_name && (
            <p className="property-agent">
              Agent: {agent_name}
              {agent_phones?.[0]?.number && <span> • {agent_phones[0].number}</span>}
            </p>
          )}
          {property_url && (
            <a 
              href={property_url}
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
    </div>
  );
};

export default PropertyCard;
// frontend/src/components/PropertyCard/PropertyCard.jsx
import React, { useState, useEffect } from 'react';
import './PropertyCard.css';

const PropertyCard = ({ property, onClick, isSelected }) => {
  const [imageError, setImageError] = useState(false);
  const [photoUrl, setPhotoUrl] = useState(null);
  
  useEffect(() => {
    // Debug logging
    console.log('Property data in PropertyCard:', property);
    console.log('Property photos:', property?.photos);
    
    // Get the first valid photo URL
    const getPhotoUrl = () => {
      if (imageError) {
        console.log('Image error occurred, no photo will be shown');
        return null;
      }
      
      const photos = property?.photos || [];
      console.log('Processing photos:', photos);
      
      // Handle array of photos
      if (Array.isArray(photos) && photos.length > 0) {
        const url = photos[0];
        if (url && typeof url === 'string' && url.trim() !== '') {
          console.log('Using first photo URL from array:', url);
          return url;
        }
      }
      
      // Handle single photo string
      if (typeof photos === 'string' && photos.trim() !== '') {
        console.log('Using single photo URL:', photos);
        return photos;
      }
      
      console.log('No valid photos found');
      return null;
    };

    const url = getPhotoUrl();
    console.log('Final photo URL:', url);
    setPhotoUrl(url);
  }, [property?.photos, imageError]);
  
  if (!property) {
    console.log('No property data provided');
    return null;
  }

  const { 
    list_price = 0,
    sale_price,
    original_list_price,
    sqft = 0,
    beds = 0,
    baths = 0,
    days_on_market = 0,
    street = '',
    city = '',
    state = '',
    zip_code = '',
    status = '',
    sale_date = '',
    year_built,
    lot_size,
    price_per_sqft,
    property_url = '',
    similarity_score
  } = property;

  const handleImageError = () => {
    console.log('Image failed to load:', photoUrl);
    setImageError(true);
  };

  const formatAddress = () => {
    const parts = [street, city, state, zip_code];
    return parts.filter(part => part).join(', ');
  };

  const formatPrice = (value) => {
    if (!value || isNaN(value)) return 'N/A';
    return `$${value.toLocaleString()}`;
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString();
  };

  const handleLinkClick = (e) => {
    e.stopPropagation();
  };

  const getStatusClass = (status) => {
    if (!status) return '';
    switch (status.toLowerCase()) {
      case 'sold': return 'status-sold';
      case 'pending': return 'status-pending';
      default: return '';
    }
  };

  return (
    <div 
      className={`property-card ${isSelected ? 'selected' : ''}`}
      onClick={onClick}
    >
      <div className="property-card__image-container">
        {photoUrl ? (
        <img 
            src={photoUrl}
            alt={`Property at ${formatAddress()}`}
          className="property-card__image"
            onError={handleImageError}
            crossOrigin="anonymous"
          />
        ) : (
          <div className="property-card__no-image">
            No Image Available
          </div>
        )}
        {similarity_score !== undefined && (
          <div className="similarity-score">
            {Math.round(similarity_score * 100)}% Match
          </div>
        )}
        {status && (
          <div className={`property-status ${getStatusClass(status)}`}>
            {status}
          </div>
        )}
      </div>
      
      <div className="property-card__content">
        <div className="property-card__header">
          <h3>{formatPrice(list_price)}</h3>
          {sale_price && (
            <div className="sale-price">
              Sold: {formatPrice(sale_price)}
              {sale_date && <span className="sale-date">on {formatDate(sale_date)}</span>}
            </div>
          )}
          {price_per_sqft && (
            <div className="price-per-sqft">
              ${Math.round(price_per_sqft)}/sqft
            </div>
          )}
        </div>
        
        <div className="property-card__details">
          <p className="property-address">{formatAddress()}</p>
          <p>{beds} beds • {baths} baths • {sqft.toLocaleString()} sqft</p>
          {days_on_market > 0 && <p>Days on Market: {days_on_market}</p>}
          {year_built && <p>Built in {year_built}</p>}
          {lot_size && <p>Lot Size: {lot_size.toLocaleString()} sqft</p>}
          {property_url && (
            <a 
              href={property_url}
              target="_blank"
              rel="noopener noreferrer"
              className="property-link"
              onClick={handleLinkClick}
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
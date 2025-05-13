import React from 'react';
import PropertyCard from '../PropertyCard/PropertyCard';
import './PropertyList.css';

const PropertyList = ({ properties, onPropertySelect, selectedProperty }) => {
  // Sort properties by price in descending order
  const sortedProperties = [...properties].sort((a, b) => b.list_price - a.list_price);

  const handlePropertyClick = (property) => {
    console.log('Property clicked in PropertyList:', property);
    if (!property || !property.property_id) {
      console.error('Invalid property clicked:', property);
      return;
    }
    onPropertySelect(property);
  };

  if (!Array.isArray(properties) || properties.length === 0) {
    return (
      <div className="no-properties">
        No properties found
      </div>
    );
  }

  return (
    <div className="property-list">
      <div className="properties-header">
        Found {sortedProperties.length} properties
      </div>
      <div className="properties-grid">
        {sortedProperties.map((property, index) => (
          <div key={`${property.property_id}-${index}`} className="property-wrapper">
            <PropertyCard 
              property={property}
              onClick={() => handlePropertyClick(property)}
              isSelected={selectedProperty?.property_id === property.property_id}
            />
          </div>
        ))}
      </div>
    </div>
  );
};

export default PropertyList;
import React from 'react';
import PropertyCard from '../PropertyCard/PropertyCard';
import './PropertyList.css';

const PropertyList = ({ properties, onPropertySelect, selectedProperty }) => {
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
        Found {properties.length} properties
      </div>
      <div className="properties-grid">
        {properties.map((property, index) => (
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
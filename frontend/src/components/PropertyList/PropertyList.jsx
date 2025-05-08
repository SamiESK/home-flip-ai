import React from 'react';
import PropertyCard from '../PropertyCard/PropertyCard';
import './PropertyList.css';

const PropertyList = ({ properties, onPropertySelect, selectedProperty }) => {
  console.log('PropertyList rendering with:', {
    propertyCount: properties?.length,
    firstProperty: properties?.[0]
  });

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
        {properties.map((property, index) => {
          // Add debug rendering
          console.log(`Rendering property ${index}:`, property);
          
          return (
            <div key={`${property.property_id}-${index}`} className="property-wrapper">
              <PropertyCard 
                property={property}
                onClick={() => onPropertySelect(property)}
                isSelected={selectedProperty?.property_id === property.property_id}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default PropertyList;
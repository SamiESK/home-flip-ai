import React from 'react';
import PropertyCard from '../PropertyCard/PropertyCard';
import './PropertyList.css';

const PropertyList = ({ properties, onPropertySelect, selectedProperty }) => {
  if (!properties?.length) {
    return <div className="no-properties">No properties found</div>;
  }

  return (
    <div className="property-list">
      {properties.map((property) => (
        <PropertyCard 
          key={property.property_id} 
          property={property}
          onClick={() => onPropertySelect(property)}
          isSelected={selectedProperty?.property_id === property.property_id}
        />
      ))}
    </div>
  );
};

export default PropertyList;
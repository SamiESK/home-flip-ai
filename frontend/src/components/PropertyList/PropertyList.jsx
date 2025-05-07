import React from 'react';
import PropertyCard from '../PropertyCard/PropertyCard';
import './PropertyList.css';

const PropertyList = ({ properties, onPropertySelect, selectedProperty }) => {
  console.log('PropertyList render', {
    propertiesLength: properties?.length,
    properties: properties,
    selectedProperty: selectedProperty
  });

  if (!properties?.length) {
    return (
      <div className="no-properties" style={{ border: '3px solid green' }}>
        No properties found (Length: {properties?.length})
      </div>
    );
  }

  return (
    <div className="property-list" style={{ border: '3px solid purple' }}>
      <div style={{ padding: '10px', background: '#f0f0f0' }}>
        Found {properties.length} properties
      </div>
      {properties.map((property) => {
        console.log('Mapping property:', property);
        return (
          <PropertyCard 
            key={property.property_id} 
            property={property}
            onClick={() => onPropertySelect(property)}
            isSelected={selectedProperty?.property_id === property.property_id}
          />
        );
      })}
    </div>
  );
};

export default PropertyList;
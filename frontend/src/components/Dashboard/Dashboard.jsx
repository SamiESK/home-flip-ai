import React from 'react';
import PropertyList from '../PropertyList/PropertyList';
import PropertyFilter from '../PropertyFilter/PropertyFilter';
import { sampleProperties } from '../../data/sampleProperties';
import './Dashboard.css';

const Dashboard = () => {
  const [properties] = React.useState(sampleProperties);
  const [filters, setFilters] = React.useState({});
  const [selectedProperty, setSelectedProperty] = React.useState(null);

  const handleFilterChange = (filterName, value) => {
    setFilters(prev => ({
      ...prev,
      [filterName]: value
    }));
  };

  const handlePropertySelect = (property) => {
    setSelectedProperty(property);
  };

  // Filter properties based on current filters
  const filteredProperties = React.useMemo(() => {
    return properties.filter(property => {
      // Price range filter
      if (filters.minPrice && property.list_price < Number(filters.minPrice.replace(/,/g, ''))) {
        return false;
      }
      if (filters.maxPrice && property.list_price > Number(filters.maxPrice.replace(/,/g, ''))) {
        return false;
      }

      // Square footage filter
      if (filters.minSqft && property.sqft < Number(filters.minSqft.replace(/,/g, ''))) {
        return false;
      }
      if (filters.maxSqft && property.sqft > Number(filters.maxSqft.replace(/,/g, ''))) {
        return false;
      }

      // Good flips filter
      if (filters.onlyGoodFlips && !property.is_good_flip) {
        return false;
      }

      return true;
    });
  }, [properties, filters]);

  return (
    <div className="dashboard">
      <h1>Home Flipper AI Dashboard</h1>
      <div className="dashboard-content">
        <div className="property-list-container">
          <PropertyList 
            properties={filteredProperties} 
            onPropertySelect={handlePropertySelect}
            selectedProperty={selectedProperty}
          />
        </div>
        <div className="details-container">
          <PropertyFilter onFilterChange={handleFilterChange} />
          {selectedProperty && (
            <div className="property-details">
              {/* Property details component will go here */}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
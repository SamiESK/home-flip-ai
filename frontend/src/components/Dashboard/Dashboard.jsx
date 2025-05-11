// frontend/src/components/Dashboard/Dashboard.jsx
import React, { useCallback, useEffect } from 'react';
import PropertyList from '../PropertyList/PropertyList';
import PropertyFilter from '../PropertyFilter/PropertyFilter';
import MapView from '../MapView/MapView';
import MarketAnalysis from '../MarketAnalysis/MarketAnalysis';
import GoogleMapsLoader from '../GoogleMapsLoader/GoogleMapsLoader';
import './Dashboard.css';

const Dashboard = () => {
  const [properties, setProperties] = React.useState([]);
  const [filters, setFilters] = React.useState({});
  const [selectedProperty, setSelectedProperty] = React.useState(null);
  const [isGoogleMapsLoaded, setIsGoogleMapsLoaded] = React.useState(false);
  const [mapLoadAttempts, setMapLoadAttempts] = React.useState(0);

  const handleFilterChange = (filterName, value) => {
    setFilters(prev => ({
      ...prev,
      [filterName]: value
    }));
  };

  const handlePropertiesLoaded = useCallback((newProperties) => {
    console.log('Properties loaded in Dashboard:', newProperties);
    if (Array.isArray(newProperties) && newProperties.length > 0) {
      console.log('Setting properties:', newProperties);
      // When new properties are loaded, update the filters to match the search criteria
      const firstProperty = newProperties[0];
      setFilters({
        zipCode: firstProperty.zip_code,
        maxPrice: firstProperty.list_price
      });
      setProperties(newProperties);
    } else {
      console.log('No valid properties received');
      setProperties([]);
    }
  }, []);

  const handlePropertySelect = useCallback((property) => {
    console.log('Property selected in Dashboard:', property);
    if (!property || !property.property_id) {
      console.error('Invalid property selected:', property);
      return;
    }
    setSelectedProperty(property);
  }, []);

  const handleGoogleMapsLoad = useCallback(() => {
    setIsGoogleMapsLoaded(true);
  }, []);

  // Add this effect to handle map loading retries
  useEffect(() => {
    if (!isGoogleMapsLoaded && mapLoadAttempts < 3) {
      const timer = setTimeout(() => {
        setMapLoadAttempts(prev => prev + 1);
      }, 2000);

      return () => clearTimeout(timer);
    }
  }, [isGoogleMapsLoaded, mapLoadAttempts]);

  // Filter properties based on current filters
  const filteredProperties = React.useMemo(() => {
    if (!Array.isArray(properties)) {
      console.log('Properties is not an array:', properties);
      return [];
    }
    
    console.log('Filtering properties with filters:', filters);
    const filtered = properties.filter(property => {
      // Filter out non-active properties
      const status = (property.status || '').toUpperCase();
      if (status === 'PENDING' || status === 'SOLD' || status === 'CLOSED') {
        console.log('Property filtered out by status:', {
          property: property.street,
          status: status
        });
        return false;
      }

      // Convert both to strings for comparison
      const propertyZip = String(property.zip_code || '');
      const filterZip = String(filters.zipCode || '');
      
      // Only apply zip code filter if it exists and doesn't match
      if (filters.zipCode && propertyZip !== filterZip) {
        console.log('Property filtered out by zip code:', {
          property: propertyZip,
          filter: filterZip
        });
        return false;
      }

      // Only apply price filter if it exists
      if (filters.maxPrice) {
        const maxPrice = Number(String(filters.maxPrice).replace(/[^0-9.-]+/g, ''));
        const propertyPrice = Number(property.list_price);
        if (!isNaN(maxPrice) && !isNaN(propertyPrice) && propertyPrice > maxPrice) {
          console.log('Property filtered out by price:', {
            property: propertyPrice,
            max: maxPrice
          });
          return false;
        }
      }

      return true;
    });
    
    console.log('Filtered properties:', filtered);
    return filtered;
  }, [properties, filters]);

  return (
    <div className="dashboard">
      <GoogleMapsLoader onLoad={handleGoogleMapsLoad} />
      <h1>🍉</h1>
      <div className="dashboard-content">
        <div className="left-panel">
          <PropertyFilter 
            onFilterChange={handleFilterChange}
            onPropertiesLoaded={handlePropertiesLoaded}
          />
          <div className="property-list-container">
            {filteredProperties.length > 0 ? (
              <PropertyList 
                properties={filteredProperties}
                onPropertySelect={handlePropertySelect}
                selectedProperty={selectedProperty}
              />
            ) : (
              <div className="no-properties">
                {properties.length > 0 ? 'No properties match the current filters' : 'Enter a zip code and price to search for properties'}
              </div>
            )}
          </div>
        </div>
        <div className="right-panel">
          {isGoogleMapsLoaded ? (
            <>
              <MapView 
                properties={filteredProperties}
                selectedProperty={selectedProperty}
                onPropertySelect={handlePropertySelect}
              />
              {selectedProperty && selectedProperty.property_id && (
                <div className="market-analysis-container">
                  <MarketAnalysis property={selectedProperty} />
                </div>
              )}
            </>
          ) : (
            <div className="map-loading">
              <div className="loading-spinner"></div>
              <p>Loading map... {mapLoadAttempts > 0 ? `(Attempt ${mapLoadAttempts})` : ''}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

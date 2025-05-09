import React, { useEffect, useRef, useState } from 'react';
import './MapView.css';

const MapView = ({ properties, selectedProperty, onPropertySelect }) => {
  const mapRef = useRef(null);
  const googleMapRef = useRef(null);
  const markersRef = useRef({});
  const selectedInfoWindowRef = useRef(null);
  const hoveredInfoWindowRef = useRef(null);
  const [mapError, setMapError] = useState(null);
  const propertiesRef = useRef(new Set());

  // Create info window content
  const createInfoWindowContent = (property) => {
    const photoUrl = property.photos?.[0];
    const hasValidPhoto = photoUrl && typeof photoUrl === 'string' && photoUrl.startsWith('http');
    
    return `
      <div style="padding: 8px; max-width: 300px;">
        <div style="margin-bottom: 8px;">
          ${hasValidPhoto ? `
            <img 
              src="${photoUrl}" 
              alt="${property.street}"
              style="width: 100%; height: 150px; object-fit: cover; border-radius: 4px;"
              onerror="this.parentElement.innerHTML = '<div style=\'width: 100%; height: 150px; display: flex; align-items: center; justify-content: center; background: #f5f5f5; color: #666; border-radius: 4px;\'>No Image Available</div>'"
            />
          ` : `
            <div style="width: 100%; height: 150px; display: flex; align-items: center; justify-content: center; background: #f5f5f5; color: #666; border-radius: 4px;">
              No Image Available
            </div>
          `}
        </div>
        <h3 style="margin: 0 0 8px 0; font-size: 16px;">$${property.list_price.toLocaleString()}</h3>
        <p style="margin: 0 0 4px 0; font-size: 14px;">${property.street}</p>
        <p style="margin: 0 0 8px 0; font-size: 14px;">${property.beds} beds • ${property.baths} baths • ${property.sqft.toLocaleString()} sqft</p>
        ${property.property_url ? `
          <a 
            href="${property.property_url}" 
            target="_blank" 
            rel="noopener noreferrer"
            style="
              display: inline-block;
              padding: 6px 12px;
              background-color: #007bff;
              color: white;
              text-decoration: none;
              border-radius: 4px;
              font-size: 14px;
              margin-top: 8px;
            "
          >
            View Listing
          </a>
        ` : ''}
      </div>
    `;
  };

  useEffect(() => {
    if (!window.google || !window.google.maps || !mapRef.current) {
      console.log('MapView: Missing dependencies', {
        google: !!window.google,
        maps: !!window.google?.maps,
        mapRef: !!mapRef.current,
        properties: properties?.length
      });
      setMapError('Map is still initializing...');
      return;
    }

    // Store current ref values for cleanup
    const currentMarkers = markersRef.current;
    const currentProperties = propertiesRef.current;

    try {
      console.log('MapView: Initializing with properties:', {
        count: properties?.length,
        first: properties?.[0],
        hasGoogleMaps: !!window.google?.maps
      });

      // Only initialize the map if it hasn't been initialized yet
      if (!googleMapRef.current) {
        console.log('MapView: Creating new map instance');
        googleMapRef.current = new window.google.maps.Map(mapRef.current, {
          center: { lat: 28.5383, lng: -81.3792 }, // Orlando
          zoom: 10,
          mapTypeControl: true,
          streetViewControl: true,
          fullscreenControl: true,
        });
      }

      // Create bounds object to fit all markers
      const bounds = new window.google.maps.LatLngBounds();
      let hasValidMarkers = false;

      // Log the properties we're about to process
      console.log('MapView: Properties to process:', properties?.map(p => ({
        id: p.property_id,
        street: p.street,
        lat: p.latitude,
        lng: p.longitude
      })));

      // Add new markers only for properties that don't have markers yet
      properties.forEach(property => {
        console.log('MapView: Processing property:', {
          id: property.property_id,
          street: property.street,
          lat: property.latitude,
          lng: property.longitude,
          hasMarker: currentProperties.has(property.property_id)
        });

        if (property.latitude && property.longitude && !currentProperties.has(property.property_id)) {
          const position = { 
            lat: parseFloat(property.latitude), 
            lng: parseFloat(property.longitude) 
          };

          console.log('MapView: Creating marker at position:', position);

          const marker = new window.google.maps.Marker({
            position: position,
            map: googleMapRef.current,
            title: property.address
          });

          // Extend bounds to include this marker
          bounds.extend(position);
          hasValidMarkers = true;

          // Create info window
          const infoWindow = new window.google.maps.InfoWindow({
            content: createInfoWindowContent(property),
            maxWidth: 300,
            pixelOffset: new window.google.maps.Size(0, -10)
          });

          // Add click listener to marker
          const clickListener = marker.addListener('click', () => {
            // Close any existing info windows
            if (selectedInfoWindowRef.current) {
              selectedInfoWindowRef.current.close();
            }
            if (hoveredInfoWindowRef.current) {
              hoveredInfoWindowRef.current.close();
              hoveredInfoWindowRef.current = null;
            }

            // Select the property and open its info window
            onPropertySelect(property);
            infoWindow.open(googleMapRef.current, marker);
            selectedInfoWindowRef.current = infoWindow;
          });

          // Add hover listeners
          const mouseoverListener = marker.addListener('mouseover', () => {
            // Only show hover info window if this marker isn't already selected
            if (!selectedProperty || selectedProperty.property_id !== property.property_id) {
              if (hoveredInfoWindowRef.current) {
                hoveredInfoWindowRef.current.close();
              }
              infoWindow.open(googleMapRef.current, marker);
              hoveredInfoWindowRef.current = infoWindow;
            }
          });

          const mouseoutListener = marker.addListener('mouseout', () => {
            // Only close the info window if it's the hovered one
            if (hoveredInfoWindowRef.current === infoWindow) {
              infoWindow.close();
              hoveredInfoWindowRef.current = null;
            }
          });

          // Store marker, info window, and listeners
          currentMarkers[property.property_id] = { 
            marker, 
            infoWindow,
            listeners: [clickListener, mouseoverListener, mouseoutListener]
          };
          currentProperties.add(property.property_id);
        }
      });

      // Fit map to show all markers if we have any
      if (hasValidMarkers) {
        googleMapRef.current.fitBounds(bounds);
        
        // Add padding to the bounds
        const listener = window.google.maps.event.addListener(googleMapRef.current, 'idle', () => {
          if (googleMapRef.current.getZoom() > 15) {
            googleMapRef.current.setZoom(15);
          }
          window.google.maps.event.removeListener(listener);
        });
      }

    } catch (error) {
      setMapError(error.message);
    }

    // Cleanup function
    return () => {
      // Remove all markers and their listeners
      Object.values(currentMarkers).forEach(({ marker, listeners }) => {
        listeners.forEach(listener => window.google.maps.event.removeListener(listener));
        marker.setMap(null);
      });
      // Clear the refs
      markersRef.current = {};
      propertiesRef.current.clear();
    };
  }, [properties, onPropertySelect, selectedProperty]);

  // Handle selected property changes
  useEffect(() => {
    if (!googleMapRef.current || !selectedProperty || !markersRef.current[selectedProperty.property_id]) return;

    const { marker, infoWindow } = markersRef.current[selectedProperty.property_id];
    
    // Close any existing info windows
    if (selectedInfoWindowRef.current && selectedInfoWindowRef.current !== infoWindow) {
      selectedInfoWindowRef.current.close();
    }
    if (hoveredInfoWindowRef.current) {
      hoveredInfoWindowRef.current.close();
      hoveredInfoWindowRef.current = null;
    }
    
    // Open and select this info window
    infoWindow.open(googleMapRef.current, marker);
    selectedInfoWindowRef.current = infoWindow;

    // Center the map on the selected marker
    googleMapRef.current.panTo(marker.getPosition());
  }, [selectedProperty]);

  return (
    <div className="map-container">
      {mapError && (
        <div className="map-error">
          {mapError}
        </div>
      )}
      <div 
        ref={mapRef} 
        className="map-view"
        style={{ 
          height: '100%', 
          width: '100%',
          borderRadius: '8px',
          overflow: 'hidden',
          backgroundColor: '#f0f0f0'
        }}
      />
    </div>
  );
};

export default MapView;

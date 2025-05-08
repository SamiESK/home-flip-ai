import React, { useEffect, useRef, useState } from 'react';
import './MapView.css';

const MapView = ({ properties, selectedProperty, onPropertySelect }) => {
  const mapRef = useRef(null);
  const googleMapRef = useRef(null);
  const markersRef = useRef({});
  const selectedInfoWindowRef = useRef(null);
  const [mapError, setMapError] = useState(null);
  const [isMapInitialized, setIsMapInitialized] = useState(false);

  // Initialize map only once
  useEffect(() => {
    if (!window.google || googleMapRef.current) return;

    try {
      googleMapRef.current = new window.google.maps.Map(mapRef.current, {
        center: { lat: 28.5383, lng: -81.3792 }, // Orlando coordinates
        zoom: 10,
        mapTypeId: 'roadmap',
        mapTypeControl: true,
        mapTypeControlOptions: {
          style: window.google.maps.MapTypeControlStyle.DROPDOWN_MENU,
          mapTypeIds: ['roadmap', 'satellite']
        },
        zoomControl: true,
        streetViewControl: true,
        fullscreenControl: false
      });

      // Add a listener for when the map is ready
      window.google.maps.event.addListenerOnce(googleMapRef.current, 'idle', () => {
        setIsMapInitialized(true);
      });
    } catch (error) {
      console.error('Error initializing map:', error);
      setMapError('Error loading map');
    }
  }, []);

  // Handle markers creation/update
  useEffect(() => {
    if (!isMapInitialized || !googleMapRef.current || !properties.length) return;

    // Clear existing markers
    Object.values(markersRef.current).forEach(({ marker }) => marker.setMap(null));
    markersRef.current = {};

    const bounds = new window.google.maps.LatLngBounds();

    properties.forEach(property => {
      if (!property.latitude || !property.longitude) return;

      const position = {
        lat: parseFloat(property.latitude),
        lng: parseFloat(property.longitude)
      };

      bounds.extend(position);

      const marker = new window.google.maps.Marker({
        position,
        map: googleMapRef.current,
        title: `$${property.list_price.toLocaleString()}`,
      });

      const infoWindow = new window.google.maps.InfoWindow({
        content: `
          <div style="padding: 10px; max-width: 300px;">
            <div style="margin-bottom: 10px;">
              <img 
                src="${property.photos?.[0] || 'https://placehold.co/300x200/e0e0e0/999999?text=No+Image'}" 
                alt="Property" 
                style="width: 100%; height: 200px; object-fit: cover; border-radius: 4px;"
              />
            </div>
            <h3 style="margin: 0 0 10px 0; color: #333;">$${property.list_price.toLocaleString()}</h3>
            <p style="margin: 0 0 5px 0; color: #666;">${property.beds} beds • ${property.full_baths} baths</p>
            <p style="margin: 0; color: #666;">${property.street}</p>
            ${property.sqft ? `<p style="margin: 5px 0; color: #666;">${property.sqft.toLocaleString()} sqft</p>` : ''}
            ${property.property_url ? `
              <a 
                href="${property.property_url}" 
                target="_blank" 
                rel="noopener noreferrer" 
                style="
                  display: inline-block;
                  margin-top: 10px;
                  padding: 8px 16px;
                  background-color: #007bff;
                  color: white;
                  text-decoration: none;
                  border-radius: 4px;
                  font-weight: 500;
                "
              >
                View Listing
              </a>
            ` : ''}
          </div>
        `
      });

      // Add hover listeners
      marker.addListener('mouseover', () => {
        // Only show on hover if this isn't the selected marker
        if (selectedInfoWindowRef.current !== infoWindow) {
          infoWindow.open(googleMapRef.current, marker);
        }
      });

      marker.addListener('mouseout', () => {
        // Only close on mouseout if this isn't the selected marker
        if (selectedInfoWindowRef.current !== infoWindow) {
          infoWindow.close();
        }
      });

      // Click handler for selection
      marker.addListener('click', () => {
        // If there's a different info window selected, close it
        if (selectedInfoWindowRef.current && selectedInfoWindowRef.current !== infoWindow) {
          selectedInfoWindowRef.current.close();
        }
        
        // Open and select this info window
        infoWindow.open(googleMapRef.current, marker);
        selectedInfoWindowRef.current = infoWindow;
        onPropertySelect(property);
      });

      // Add close button listener
      window.google.maps.event.addListener(infoWindow, 'closeclick', () => {
        selectedInfoWindowRef.current = null;
        onPropertySelect(null);
      });

      markersRef.current[property.property_id] = { marker, infoWindow };
    });

    // Only fit bounds if we have valid positions
    if (bounds.getNorthEast().equals(bounds.getSouthWest())) {
      // If all markers are at the same position, zoom out
      googleMapRef.current.setZoom(10);
    } else {
      googleMapRef.current.fitBounds(bounds);
    }

    return () => {
      Object.values(markersRef.current).forEach(({ marker }) => marker.setMap(null));
      markersRef.current = {};
      selectedInfoWindowRef.current = null;
    };
  }, [properties, onPropertySelect, isMapInitialized]);

  // Handle selected property changes
  useEffect(() => {
    if (!isMapInitialized || !selectedProperty || !markersRef.current[selectedProperty.property_id]) return;

    const { marker, infoWindow } = markersRef.current[selectedProperty.property_id];
    
    // Close any previously selected info window
    if (selectedInfoWindowRef.current && selectedInfoWindowRef.current !== infoWindow) {
      selectedInfoWindowRef.current.close();
    }
    
    // Open and select this info window
    infoWindow.open(googleMapRef.current, marker);
    selectedInfoWindowRef.current = infoWindow;
  }, [selectedProperty, isMapInitialized]);

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
          overflow: 'hidden'
        }}
      />
    </div>
  );
};

export default MapView;

import { useEffect } from 'react';

const GoogleMapsLoader = ({ onLoad }) => {
  useEffect(() => {
    // Check if Google Maps is already loaded
    if (window.google && window.google.maps) {
      onLoad();
      return;
    }

    const apiKey = process.env.REACT_APP_GOOGLE_MAPS_API_KEY;
    console.log('API Key available:', !!apiKey); // This will log true/false without exposing the key

    if (!apiKey) {
      console.error('Google Maps API key is not defined. Please check your .env file in the root directory.');
      return;
    }

    // Create script element
    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=places`;
    script.async = true;
    script.defer = true;

    // Add event listeners
    script.addEventListener('load', () => {
      console.log('Google Maps script loaded successfully');
      onLoad();
    });

    script.addEventListener('error', (error) => {
      console.error('Error loading Google Maps:', error);
    });

    // Append script to document
    document.head.appendChild(script);

    // Cleanup
    return () => {
      if (script.parentNode) {
        script.parentNode.removeChild(script);
      }
    };
  }, [onLoad]);

  return null;
};

export default GoogleMapsLoader;
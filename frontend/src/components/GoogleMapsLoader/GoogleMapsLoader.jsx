import { useEffect, useState, useCallback } from 'react';

const GOOGLE_MAPS_STATUS = {
  NOT_LOADED: 'NOT_LOADED',
  LOADING: 'LOADING',
  LOADED: 'LOADED',
  ERROR: 'ERROR'
};

// Global promise for script loading
let loadPromise = null;

const loadGoogleMapsScript = (apiKey) => {
  if (loadPromise) {
    return loadPromise;
  }

  loadPromise = new Promise((resolve, reject) => {
    // If Google Maps is already loaded, resolve immediately
    if (window.google && window.google.maps) {
      resolve();
      return;
    }

    // Remove any existing scripts and initMap function
    const existingScripts = document.querySelectorAll('script[src*="maps.googleapis.com"]');
    existingScripts.forEach(script => script.remove());
    delete window.initMap;

    // Create new initMap function
    window.initMap = () => {
      console.log('Google Maps initialized via callback');
      resolve();
    };

    // Create and append script
    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=places&callback=initMap`;
    script.async = true;
    script.defer = true;

    script.addEventListener('error', (error) => {
      console.error('Error loading Google Maps:', error);
      loadPromise = null;
      reject(error);
    });

    document.head.appendChild(script);
  });

  return loadPromise;
};

const GoogleMapsLoader = ({ onLoad }) => {
  const [status, setStatus] = useState(GOOGLE_MAPS_STATUS.NOT_LOADED);

  const cleanup = useCallback(() => {
    if (status === GOOGLE_MAPS_STATUS.LOADING) {
      const script = document.querySelector('script[src*="maps.googleapis.com"]');
      if (script && script.parentNode) {
        script.parentNode.removeChild(script);
      }
      delete window.initMap;
      loadPromise = null;
    }
  }, [status]);

  useEffect(() => {
    const apiKey = process.env.REACT_APP_GOOGLE_MAPS_API_KEY;
    
    if (!apiKey) {
      console.error('Google Maps API key is missing in .env file');
      setStatus(GOOGLE_MAPS_STATUS.ERROR);
      return;
    }

    setStatus(GOOGLE_MAPS_STATUS.LOADING);

    loadGoogleMapsScript(apiKey)
      .then(() => {
        setStatus(GOOGLE_MAPS_STATUS.LOADED);
        onLoad();
      })
      .catch((error) => {
        console.error('Failed to load Google Maps:', error);
        setStatus(GOOGLE_MAPS_STATUS.ERROR);
      });

    return cleanup;
  }, [onLoad, cleanup]);

  return null;
};

export default GoogleMapsLoader;
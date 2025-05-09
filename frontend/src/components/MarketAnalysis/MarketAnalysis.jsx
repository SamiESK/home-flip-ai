import React, { useEffect, useState, useRef } from 'react';
import axios from 'axios';
import './MarketAnalysis.css';

const API_BASE_URL = 'http://localhost:8000';

const ANALYSIS_ICONS = {
  price: '💰',
  size: '📏',
  market_timing: '⏰',
  location: '📍',
  historical: '📈',
  overall: '🎯'
};

const CONFIDENCE_COLORS = {
  high: '#2ecc71',
  medium: '#f1c40f',
  low: '#e74c3c'
};

const DEFAULT_METRICS = {
  avg_price: 0,
  avg_price_per_sqft: 0,
  avg_days_on_market: 0
};

const formatNumber = (value) => {
  if (value === null || value === undefined || isNaN(value)) {
    return 'N/A';
  }
  return value.toLocaleString();
};

const formatPrice = (value) => {
  if (value === null || value === undefined || isNaN(value)) {
    return 'N/A';
  }
  return `$${value.toLocaleString()}`;
};

const MarketAnalysis = ({ property }) => {
  const [analysisData, setAnalysisData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const containerRef = useRef(null);
  const [isResizing, setIsResizing] = useState(false);
  const [startHeight, setStartHeight] = useState(0);
  const [startY, setStartY] = useState(0);

  // Resize functionality
  useEffect(() => {
    const handleMouseDown = (e) => {
      const handle = e.target.closest('.resize-handle');
      if (handle) {
        e.preventDefault();
        e.stopPropagation();
        document.body.style.cursor = 'ns-resize';
        setIsResizing(true);
        setStartHeight(containerRef.current.offsetHeight);
        setStartY(e.clientY);
        containerRef.current.classList.add('resizing');
      }
    };

    const handleMouseMove = (e) => {
      if (!isResizing) return;
      
      e.preventDefault();
      const deltaY = startY - e.clientY;
      const newHeight = Math.max(200, startHeight + (deltaY * -1));
      
      if (containerRef.current) {
        requestAnimationFrame(() => {
          containerRef.current.style.height = `${newHeight}px`;
        });
      }
    };

    const handleMouseUp = () => {
      if (isResizing) {
        document.body.style.cursor = '';
        setIsResizing(false);
        containerRef.current?.classList.remove('resizing');
      }
    };

    window.addEventListener('mousedown', handleMouseDown);
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    window.addEventListener('mouseleave', handleMouseUp);

    return () => {
      window.removeEventListener('mousedown', handleMouseDown);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
      window.removeEventListener('mouseleave', handleMouseUp);
      document.body.style.cursor = '';
    };
  }, [isResizing, startHeight, startY]);

  useEffect(() => {
    const fetchAnalysis = async () => {
      if (!property?.property_url) {
        setLoading(false);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        // Use the numeric property ID directly
        const propertyId = property.property_id;
        const response = await axios.get(`${API_BASE_URL}/api/market-analysis/${propertyId}`);
        
        // Log the response data for debugging
        console.log('Market analysis response:', response.data);
        
        setAnalysisData(response.data);
      } catch (err) {
        console.error('Error fetching market analysis:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalysis();
  }, [property]);

  const renderAnalysisCard = (analysis) => {
    if (!analysis) return null;
    
    return (
      <div key={analysis.type} className={`analysis-card ${analysis.confidence}`}>
        <div className="analysis-header">
          <span className="analysis-icon">{ANALYSIS_ICONS[analysis.type] || '📌'}</span>
          <h3 className="analysis-title">
            {analysis.type.split('_').map(word => 
              word.charAt(0).toUpperCase() + word.slice(1)
            ).join(' ')}
          </h3>
          <span 
            className={`confidence-badge ${analysis.confidence}`}
            style={{ backgroundColor: CONFIDENCE_COLORS[analysis.confidence] }}
          >
            {analysis.confidence}
          </span>
        </div>
        <p className="analysis-message">{analysis.message}</p>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="market-analysis" ref={containerRef}>
        <div className="loading">
          <div className="loading-spinner"></div>
          <p>Loading market analysis...</p>
        </div>
        <div className="resize-handle" title="Drag to resize" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="market-analysis" ref={containerRef}>
        <div className="error">
          <p>{error}</p>
        </div>
        <div className="resize-handle" title="Drag to resize" />
      </div>
    );
  }

  if (!analysisData) {
    return (
      <div className="market-analysis" ref={containerRef}>
        <div className="error">
          <p>No market data available</p>
        </div>
        <div className="resize-handle" title="Drag to resize" />
      </div>
    );
  }

  const { market_metrics = DEFAULT_METRICS, comparable_properties = [], analysis = [] } = analysisData;

  // Calculate ROI potential
  const calculateROIPotential = () => {
    if (!comparable_properties?.length) return null;

    // Get average sold price of comparable properties
    const soldProperties = comparable_properties.filter(p => p.status?.toLowerCase() === 'sold');
    if (!soldProperties.length) return null;

    // Calculate metrics
    const avgSoldPrice = soldProperties.reduce((sum, p) => sum + (p.sale_price || 0), 0) / soldProperties.length;
    const priceDiff = property.list_price ? ((avgSoldPrice - property.list_price) / property.list_price) * 100 : 0;
    const avgDOM = soldProperties.reduce((sum, p) => sum + (p.days_on_market || 0), 0) / soldProperties.length;
    const avgPricePerSqft = soldProperties.reduce((sum, p) => {
      if (p.sale_price && p.sqft) return sum + (p.sale_price / p.sqft);
      return sum;
    }, 0) / soldProperties.length;
    
    return {
      potentialARV: avgSoldPrice,
      priceDifference: priceDiff,
      averageDaysOnMarket: avgDOM,
      pricePerSqft: avgPricePerSqft,
      soldCount: soldProperties.length
    };
  };

  const roi = calculateROIPotential();

  return (
    <div className="market-analysis" ref={containerRef}>
      <div className="resize-handle" title="Drag to resize" />
      
      <h2>Property Analysis</h2>
      
      <div className="metrics-grid">
        <div className="metric-card">
          <h3>Market Average Price</h3>
          <div className="metric-value">{formatPrice(market_metrics.avg_price)}</div>
        </div>
        <div className="metric-card">
          <h3>Market Average Price/Sqft</h3>
          <div className="metric-value">{formatPrice(market_metrics.avg_price_per_sqft)}/sqft</div>
        </div>
        <div className="metric-card">
          <h3>Market Average DOM</h3>
          <div className="metric-value">{formatNumber(market_metrics.avg_days_on_market)} days</div>
        </div>
      </div>

      <div className="property-metrics">
        <h3>Selected Property</h3>
        <div className="metrics-grid">
          <div className="metric-card">
            <h3>List Price</h3>
            <div className="metric-value">{formatPrice(property.list_price)}</div>
          </div>
          <div className="metric-card">
            <h3>Price/Sqft</h3>
            <div className="metric-value">{formatPrice(property.list_price / property.sqft)}/sqft</div>
          </div>
          <div className="metric-card">
            <h3>Days on Market</h3>
            <div className="metric-value">{formatNumber(property.days_on_market)} days</div>
          </div>
        </div>
      </div>

      {roi && (
        <div className="roi-analysis">
          <h3>Investment Potential</h3>
          <div className="roi-metrics">
            <div className="roi-metric">
              <label>Potential ARV</label>
              <value>{formatPrice(roi.potentialARV)}</value>
              <trend className={roi.priceDifference > 0 ? 'positive' : 'negative'}>
                {roi.priceDifference > 0 ? '↑' : '↓'} {Math.abs(roi.priceDifference).toFixed(1)}%
              </trend>
            </div>
            <div className="roi-metric">
              <label>Market Average DOM</label>
              <value>{formatNumber(roi.averageDaysOnMarket)} days</value>
            </div>
            <div className="roi-metric">
              <label>Market Price/Sqft</label>
              <value>{formatPrice(roi.pricePerSqft)}/sqft</value>
            </div>
          </div>
        </div>
      )}

      <div className="key-insights">
        <h3>Key Insights</h3>
        {roi && (
          <ul className="insights-list">
            {roi.priceDifference > 10 && (
              <li className="insight positive">
                <span className="icon">💰</span>
                <span className="text">Property is priced {Math.abs(roi.priceDifference).toFixed(1)}% below market value, indicating strong profit potential</span>
              </li>
            )}
            {roi.priceDifference < -10 && (
              <li className="insight negative">
                <span className="icon">⚠️</span>
                <span className="text">Property is priced {Math.abs(roi.priceDifference).toFixed(1)}% above market value - consider negotiating</span>
              </li>
            )}
            {roi.averageDaysOnMarket > 60 && (
              <li className="insight neutral">
                <span className="icon">⏰</span>
                <span className="text">Average time to sell is {formatNumber(roi.averageDaysOnMarket)} days - consider this in your holding costs</span>
              </li>
            )}
            {property.list_price / property.sqft < roi.pricePerSqft && (
              <li className="insight positive">
                <span className="icon">📊</span>
                <span className="text">Price per sqft is below market average, suggesting room for value appreciation</span>
              </li>
            )}
          </ul>
        )}
      </div>

      {analysis.length > 0 && (
        <div className="analysis-section">
          <h3>Market Analysis</h3>
          <div className="analysis-grid">
            {analysis.map(renderAnalysisCard)}
          </div>
        </div>
      )}

      {comparable_properties?.length > 0 && (
        <div className="comparable-properties">
          <h3>Comparable Properties ({comparable_properties.length})</h3>
          <div className="comps-grid">
            {comparable_properties.map((comp, index) => {
              console.log('Processing property:', comp.property_id);
              console.log('Raw photos data:', comp.photos);
              
              // Get the first valid photo URL
              let photoUrl = null;
              
              if (Array.isArray(comp.photos) && comp.photos.length > 0) {
                const url = comp.photos[0];
                if (typeof url === 'string' && url.trim() && url.startsWith('http')) {
                  photoUrl = url.trim();
                  console.log('Using actual property photo:', photoUrl);
                } else {
                  console.log('Invalid photo URL:', url);
                }
              } else {
                console.log('No photos array found for property:', comp.property_id);
              }

              const handleCompClick = () => {
                if (comp.property_url) {
                  window.open(comp.property_url, '_blank', 'noopener,noreferrer');
                }
              };

              return (
                <div 
                  key={index} 
                  className="comp-card"
                  onClick={handleCompClick}
                  style={{ cursor: comp.property_url ? 'pointer' : 'default' }}
                >
                  <div className="comp-image">
                    {photoUrl ? (
                      <img 
                        src={photoUrl}
                        alt={`${comp.street}`}
                        onError={(e) => {
                          console.log('Image load error:', e.target.src);
                          e.target.parentElement.innerHTML = '<div class="no-image">Image Not Available</div>';
                        }}
                      />
                    ) : (
                      <div className="placeholder-image">No photo available</div>
                    )}
                    <div className={`status-badge ${comp.status?.toLowerCase()}`}>
                      {comp.status || 'Active'}
                    </div>
                  </div>
                  <div className="comp-details">
                    <h4>{comp.street}</h4>
                    <div className="comp-stats">
                      <div className="stat">
                        <span className="label">Price:</span>
                        <span className="value">{formatPrice(comp.list_price)}</span>
                      </div>
                      <div className="stat">
                        <span className="label">Sqft:</span>
                        <span className="value">{formatNumber(comp.sqft)}</span>
                      </div>
                      <div className="stat">
                        <span className="label">$/sqft:</span>
                        <span className="value">{formatPrice(comp.list_price / comp.sqft)}/sqft</span>
                      </div>
                      <div className="stat">
                        <span className="label">DOM:</span>
                        <span className="value">{comp.days_on_market} days</span>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default MarketAnalysis;
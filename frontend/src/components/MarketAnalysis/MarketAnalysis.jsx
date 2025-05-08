import React, { useEffect, useState } from 'react';
import { Line } from 'react-chartjs-2';
import './MarketAnalysis.css';

const MarketAnalysis = ({ property }) => {
  const [marketData, setMarketData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Log when component mounts and when property changes
  useEffect(() => {
    console.log('MarketAnalysis mounted/updated with property:', {
      propertyId: property?.property_id,
      address: property?.street,
      price: property?.list_price
    });
  }, [property]);

  useEffect(() => {
    const fetchMarketData = async () => {
      console.log('Starting market data fetch for property:', property?.property_id);
      setLoading(true);
      setError(null);

      try {
        console.log('Making API request to /api/market-analysis/');
        const response = await fetch(`/api/market-analysis/${property.property_id}`);
        const data = await response.json();
        
        console.log('Received market data:', {
          recentSalesCount: data.recent_sales?.length,
          marketTrends: data.market_trends,
          comparablePropertiesCount: data.comparable_properties?.length
        });

        // Log detailed market trends
        console.log('Market Trends Details:', {
          avgPricePerSqFt: data.market_trends?.avg_price_per_sqft,
          avgDaysOnMarket: data.market_trends?.avg_days_on_market,
          priceTrend: data.market_trends?.price_trend,
          seasonalFactor: data.market_trends?.seasonal_factor
        });

        // Log sample of comparable properties
        if (data.comparable_properties?.length > 0) {
          console.log('Sample Comparable Property:', {
            address: data.comparable_properties[0].street,
            price: data.comparable_properties[0].list_price,
            beds: data.comparable_properties[0].beds,
            baths: data.comparable_properties[0].full_baths,
            sqft: data.comparable_properties[0].sqft
          });
        }

        setMarketData(data);
      } catch (err) {
        console.error('Error fetching market data:', {
          error: err.message,
          propertyId: property?.property_id
        });
        setError('Failed to load market analysis');
      } finally {
        setLoading(false);
        console.log('Market data fetch completed');
      }
    };

    if (property) {
      fetchMarketData();
    } else {
      console.log('No property selected, skipping market data fetch');
    }
  }, [property]);

  // Log render state
  console.log('MarketAnalysis render state:', {
    loading,
    hasError: !!error,
    hasMarketData: !!marketData
  });

  if (loading) {
    console.log('Rendering loading state');
    return <div>Loading market analysis...</div>;
  }
  
  if (error) {
    console.log('Rendering error state:', error);
    return <div className="error">{error}</div>;
  }
  
  if (!marketData) {
    console.log('Rendering null state - no market data available');
    return null;
  }

  return (
    <div className="market-analysis">
      <h2>Local Market Analysis</h2>
      
      <div className="market-stats">
        <div className="stat-card">
          <h3>Price per Sq Ft</h3>
          <p>${marketData.market_trends.avg_price_per_sqft.toFixed(2)}</p>
        </div>
        
        <div className="stat-card">
          <h3>Days on Market</h3>
          <p>{marketData.market_trends.avg_days_on_market.toFixed(0)} days</p>
        </div>
        
        <div className="stat-card">
          <h3>Price Trend</h3>
          <p>{marketData.market_trends.price_trend > 0 ? '↑' : '↓'} 
             {Math.abs(marketData.market_trends.price_trend * 100).toFixed(1)}%</p>
        </div>
      </div>

      <div className="comparable-properties">
        <h3>Comparable Properties</h3>
        <div className="comps-list">
          {marketData.comparable_properties.map(comp => {
            console.log('Rendering comparable property:', {
              id: comp.property_id,
              address: comp.street,
              price: comp.list_price
            });
            
            return (
              <div key={comp.property_id} className="comp-card">
                <img 
                  src={comp.photos[0]} 
                  alt={comp.street}
                  onError={(e) => {
                    console.error('Error loading image for property:', {
                      propertyId: comp.property_id,
                      imageUrl: comp.photos[0]
                    });
                    e.target.src = 'https://placehold.co/300x200/e0e0e0/999999?text=No+Image';
                  }}
                />
                <div className="comp-details">
                  <h4>${comp.list_price.toLocaleString()}</h4>
                  <p>{comp.beds} beds • {comp.full_baths} baths</p>
                  <p>{comp.sqft.toLocaleString()} sqft</p>
                  <p>{comp.street}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default MarketAnalysis;
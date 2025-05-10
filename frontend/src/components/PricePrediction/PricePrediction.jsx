import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Grid,
  CircularProgress,
  Box,
  Divider,
  List,
  ListItem,
  ListItemText,
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { formatCurrency } from '../../utils/formatters';

const PricePrediction = ({ propertyId }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [predictionData, setPredictionData] = useState(null);
  const [marketTrends, setMarketTrends] = useState(null);

  useEffect(() => {
    const fetchPredictionData = async () => {
      try {
        setLoading(true);
        const response = await fetch(`http://localhost:8000/api/price-prediction/${propertyId}`);
        if (!response.ok) {
          throw new Error('Failed to fetch prediction data');
        }
        const data = await response.json();
        setPredictionData(data.prediction);
        setMarketTrends(data.market_trends);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (propertyId) {
      fetchPredictionData();
    }
  }, [propertyId]);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent>
          <Typography color="error">Error: {error}</Typography>
        </CardContent>
      </Card>
    );
  }

  if (!predictionData || !marketTrends) {
    return null;
  }

  // Prepare chart data
  const chartData = marketTrends.monthly_trends.map(trend => ({
    date: new Date(trend.date).toLocaleDateString(),
    price: trend.mean,
    count: trend.count
  }));

  return (
    <Grid container spacing={3}>
      {/* Price Prediction Card */}
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Price Prediction
            </Typography>
            <Typography variant="h4" color="primary" gutterBottom>
              {formatCurrency(predictionData.predicted_price)}
            </Typography>
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle1" gutterBottom>
              Feature Importance
            </Typography>
            <List dense>
              {Object.entries(predictionData.feature_importance)
                .sort(([, a], [, b]) => b - a)
                .map(([feature, importance]) => (
                  <ListItem key={feature}>
                    <ListItemText
                      primary={feature.replace(/_/g, ' ').toUpperCase()}
                      secondary={`${(importance * 100).toFixed(1)}%`}
                    />
                  </ListItem>
                ))}
            </List>
          </CardContent>
        </Card>
      </Grid>

      {/* Market Trends Card */}
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Market Trends
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Typography variant="subtitle2" color="textSecondary">
                  3 Month Change
                </Typography>
                <Typography
                  variant="h6"
                  color={(marketTrends?.price_change_3m ?? 0) >= 0 ? 'success.main' : 'error.main'}
                >
                  {(marketTrends?.price_change_3m ?? 0).toFixed(1)}%
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="subtitle2" color="textSecondary">
                  6 Month Change
                </Typography>
                <Typography
                  variant="h6"
                  color={(marketTrends?.price_change_6m ?? 0) >= 0 ? 'success.main' : 'error.main'}
                >
                  {(marketTrends?.price_change_6m ?? 0).toFixed(1)}%
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="subtitle2" color="textSecondary">
                  12 Month Change
                </Typography>
                <Typography
                  variant="h6"
                  color={(marketTrends?.price_change_12m ?? 0) >= 0 ? 'success.main' : 'error.main'}
                >
                  {(marketTrends?.price_change_12m ?? 0).toFixed(1)}%
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="subtitle2" color="textSecondary">
                  Avg Days on Market
                </Typography>
                <Typography variant="h6">
                  {Math.round(marketTrends?.avg_days_on_market ?? 0)} days
                </Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Grid>

      {/* Price Trend Chart */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Price Trend
            </Typography>
            <Box height={300}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis
                    tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                  />
                  <Tooltip
                    formatter={(value) => formatCurrency(value)}
                    labelFormatter={(label) => `Date: ${label}`}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="price"
                    stroke="#8884d8"
                    name="Average Price"
                  />
                </LineChart>
              </ResponsiveContainer>
            </Box>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};

export default PricePrediction; 
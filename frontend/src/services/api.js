import axios from 'axios';

const API_URL = 'http://localhost:5000/api';

export const fetchProperties = async () => {
  try {
    console.log('Fetching properties from:', `${API_URL}/properties`);
    const response = await axios.get(`${API_URL}/properties`);
    console.log('Raw API response:', response);
    return response.data;
  } catch (error) {
    console.error('Error fetching properties:', error);
    return { properties: [] };
  }
};

export const scrapeProperties = async (zipCode, maxPrice) => {
  try {
    console.log('Scraping properties with:', { zipCode, maxPrice });
    const response = await axios.post(`${API_URL}/scrape`, {
      zipCode,
      maxPrice
    });
    console.log('Scraper response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Scraper error:', error);
    throw error;
  }
};

export const predictProperty = async (propertyData) => {
  try {
    console.log('Sending prediction request with data:', propertyData);
    const response = await axios.post(`${API_URL}/predict`, propertyData);
    console.log('Prediction response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Prediction error details:', {
      status: error.response?.status,
      data: error.response?.data,
      message: error.message
    });
    throw error;
  }
};
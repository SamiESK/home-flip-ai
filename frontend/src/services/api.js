import axios from 'axios';

const API_URL = 'http://localhost:5000/api';

export const fetchProperties = async () => {
  try {
    console.log('Fetching properties...');
    const response = await axios.get(`${API_URL}/properties`);
    console.log('Properties fetched:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error fetching properties:', error.response?.data || error.message);
    return [];
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
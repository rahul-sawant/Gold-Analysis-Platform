import axios from 'axios';

// Create axios instance
const api = axios.create({
  // The baseURL should be empty or '/' since our endpoints already include '/api/v1'
  baseURL: '',
  headers: {
    'Content-Type': 'application/json',
  },
});

// API endpoints
const endpoints = {
  // Data endpoints
  getPriceData: (timeframe = '1h', limit = 100) => 
    api.get(`/api/v1/data/price?timeframe=${timeframe}&limit=${limit}`),
  getIndicators: (timeframe = '1h', limit = 100) => 
    api.get(`/api/v1/data/indicators?timeframe=${timeframe}&limit=${limit}`),
  updateData: () => 
    api.post('/api/v1/data/update'),
  
  // Prediction endpoints
  getPredictions: (timeframe = '1h') => 
    api.get(`/api/v1/predict/${timeframe}`),
  
  // Signal endpoints
  getSignal: (timeframe = '1h') => 
    api.get(`/api/v1/signals/${timeframe}`),
  getAllSignals: () => 
    api.get('/api/v1/signals'),
  
  // Zerodha endpoints
  getZerodhaLoginUrl: () => 
    api.get('/api/v1/auth/zerodha/login'),
  zerodhaCallback: (requestToken) => 
    api.get(`/api/v1/auth/zerodha/callback?request_token=${requestToken}`),
  getZerodhaProfile: () => 
    api.get('/api/v1/zerodha/profile'),
  getZerodhaMargins: () => 
    api.get('/api/v1/zerodha/margins'),
  getZerodhaHoldings: () => 
    api.get('/api/v1/zerodha/holdings'),
  getZerodhaPositions: () => 
    api.get('/api/v1/zerodha/positions'),
  getZerodhaOrders: () => 
    api.get('/api/v1/zerodha/orders'),
  getZerodhaOrder: (orderId) => 
    api.get(`/api/v1/zerodha/order/${orderId}`),
  placeZerodhaOrder: (orderData) => 
    api.post('/api/v1/zerodha/order', orderData),
  cancelZerodhaOrder: (orderId) => 
    api.delete(`/api/v1/zerodha/order/${orderId}`),
  placeTradeFromSignal: (tradeData) => 
    api.post('/api/v1/zerodha/trade/signal', tradeData),
};

export default endpoints;
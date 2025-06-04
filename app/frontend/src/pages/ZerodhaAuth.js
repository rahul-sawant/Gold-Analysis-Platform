import React, { useEffect, useState } from 'react';
import { Container, Alert, Spinner } from 'react-bootstrap';
import { useNavigate, useLocation } from 'react-router-dom';
import api from '../services/api';

const ZerodhaAuth = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const handleAuth = async () => {
      try {
        // Get the request token from URL
        const params = new URLSearchParams(location.search);
        const requestToken = params.get('request_token');
        
        if (!requestToken) {
          setError('No request token found in the URL. Authentication failed.');
          setLoading(false);
          return;
        }
        
        // Send the request token to the backend
        await api.zerodhaCallback(requestToken);
        
        setSuccess(true);
        setLoading(false);
        
        // Redirect to trading page after a short delay
        setTimeout(() => {
          navigate('/trading');
        }, 3000);
      } catch (err) {
        console.error('Zerodha authentication error:', err);
        setError('Failed to authenticate with Zerodha. Please try again later.');
        setLoading(false);
      }
    };

    handleAuth();
  }, [location, navigate]);

  return (
    <Container className="text-center mt-5">
      <h1 className="page-title">Zerodha Authentication</h1>
      
      {loading && (
        <div className="my-5">
          <Spinner animation="border" variant="warning" />
          <p className="mt-3">Processing authentication with Zerodha...</p>
        </div>
      )}
      
      {error && (
        <Alert variant="danger" className="my-4">
          <Alert.Heading>Authentication Error</Alert.Heading>
          <p>{error}</p>
          <hr />
          <div className="d-flex justify-content-end">
            <button 
              onClick={() => navigate('/trading')} 
              className="btn btn-outline-danger"
            >
              Return to Trading
            </button>
          </div>
        </Alert>
      )}
      
      {success && (
        <Alert variant="success" className="my-4">
          <Alert.Heading>Authentication Successful!</Alert.Heading>
          <p>You have successfully authenticated with Zerodha.</p>
          <p>You will be redirected to the trading dashboard in a few seconds...</p>
        </Alert>
      )}
    </Container>
  );
};

export default ZerodhaAuth; 
import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Button, ButtonGroup, Alert } from 'react-bootstrap';
import PriceChart from '../components/PriceChart';
import SignalDisplay from '../components/SignalDisplay';
import LoadingSpinner from '../components/LoadingSpinner';
import api from '../services/api';

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [priceData, setPriceData] = useState([]);
  const [predictions, setPredictions] = useState([]);
  const [signals, setSignals] = useState({});
  const [selectedTimeframe, setSelectedTimeframe] = useState('1h');
  const [lastUpdate, setLastUpdate] = useState(null);
  const [showPredictions, setShowPredictions] = useState(true);

  // Fetch dashboard data
  const fetchDashboardData = async (timeframe) => {
    setLoading(true);
    setError(null);
    
    try {
      // Fetch price data
      const priceResponse = await api.getPriceData(timeframe, 100);
      
      // Check if response has the expected structure
      if (priceResponse && priceResponse.data && 
          (priceResponse.data.status === 'success' || priceResponse.data.data)) {
        // Set data based on response structure
        if (Array.isArray(priceResponse.data.data)) {
          setPriceData(priceResponse.data.data);
        } else if (Array.isArray(priceResponse.data)) {
          setPriceData(priceResponse.data);
        } else {
          console.warn('Price data is not in the expected format:', priceResponse.data);
          setPriceData([]);
        }
      } else {
        console.warn('Invalid price data response:', priceResponse);
        setPriceData([]);
      }
      
      // Fetch predictions
      const predictionsResponse = await api.getPredictions(timeframe);
      
      // Check if response has the expected structure
      if (predictionsResponse && predictionsResponse.data &&
          (predictionsResponse.data.status === 'success' || predictionsResponse.data.data)) {
        // Set data based on response structure
        if (Array.isArray(predictionsResponse.data.data)) {
          setPredictions(predictionsResponse.data.data);
        } else if (Array.isArray(predictionsResponse.data)) {
          setPredictions(predictionsResponse.data);
        } else {
          console.warn('Prediction data is not in the expected format:', predictionsResponse.data);
          setPredictions([]);
        }
      } else {
        console.warn('Invalid prediction data response:', predictionsResponse);
        setPredictions([]);
      }
      
      // Fetch signal
      const signalResponse = await api.getSignal(timeframe);
      
      // Check if response has the expected structure
      if (signalResponse && signalResponse.data) {
        if (signalResponse.data.status === 'success' && signalResponse.data.data) {
          setSignals(signalResponse.data.data);
        } else if (typeof signalResponse.data === 'object' && !signalResponse.data.error) {
          setSignals(signalResponse.data);
        } else {
          console.warn('Signal data is not in the expected format:', signalResponse.data);
          setSignals({});
        }
      } else {
        console.warn('Invalid signal data response:', signalResponse);
        setSignals({});
      }
      
      setLastUpdate(new Date());
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setError('Failed to load dashboard data. Please try again later.');
      setPriceData([]);
      setPredictions([]);
      setSignals({});
    } finally {
      setLoading(false);
    }
  };

  // Refresh data
  const handleRefresh = () => {
    fetchDashboardData(selectedTimeframe);
  };

  // Update data from source
  const handleUpdateData = async () => {
    try {
      setLoading(true);
      const response = await api.updateData();
      
      if (response && response.data && response.data.status === 'success') {
        console.log('Data update successful:', response.data.message);
      } else {
        console.warn('Data update response not as expected:', response);
      }
      
      handleRefresh();
    } catch (err) {
      console.error('Error updating data:', err);
      setError('Failed to update data. Please try again later.');
      setLoading(false);
    }
  };

  // Change timeframe
  const handleTimeframeChange = (timeframe) => {
    setSelectedTimeframe(timeframe);
    fetchDashboardData(timeframe);
  };

  // Initial data load
  useEffect(() => {
    fetchDashboardData(selectedTimeframe);
  }, [selectedTimeframe]);

  if (loading && !priceData.length) {
    return <LoadingSpinner text="Loading dashboard data..." />;
  }

  return (
    <Container fluid className="dashboard-container">
      <h1 className="page-title">Gold Analysis Dashboard</h1>
      
      {error && <Alert variant="danger">{error}</Alert>}
      
      <div className="d-flex justify-content-between align-items-center mb-4">
        <ButtonGroup className="timeframe-selector">
          <Button 
            variant={selectedTimeframe === '1h' ? 'warning' : 'outline-warning'}
            onClick={() => handleTimeframeChange('1h')}
          >
            1 Hour
          </Button>
          <Button 
            variant={selectedTimeframe === '4h' ? 'warning' : 'outline-warning'}
            onClick={() => handleTimeframeChange('4h')}
          >
            4 Hours
          </Button>
          <Button 
            variant={selectedTimeframe === '1d' ? 'warning' : 'outline-warning'}
            onClick={() => handleTimeframeChange('1d')}
          >
            Daily
          </Button>
          <Button 
            variant={selectedTimeframe === '1w' ? 'warning' : 'outline-warning'}
            onClick={() => handleTimeframeChange('1w')}
          >
            Weekly
          </Button>
        </ButtonGroup>
        
        <div>
          <Button variant="outline-primary" onClick={handleRefresh} className="me-2">
            Refresh
          </Button>
          <Button variant="outline-success" onClick={handleUpdateData}>
            Update Data
          </Button>
          {lastUpdate && (
            <small className="text-muted ms-2">
              Last updated: {lastUpdate.toLocaleTimeString()}
            </small>
          )}
        </div>
      </div>
      
      <Row>
        <Col>
          <Card className="mb-4">
            <Card.Header className="d-flex justify-content-between align-items-center">
              <h5 className="mb-0">Gold Price Chart</h5>
              <div>
                <Button
                  size="sm"
                  variant={showPredictions ? 'info' : 'outline-info'}
                  onClick={() => setShowPredictions(!showPredictions)}
                >
                  {showPredictions ? 'Hide Predictions' : 'Show Predictions'}
                </Button>
              </div>
            </Card.Header>
            <Card.Body>
              {loading && priceData.length > 0 ? (
                <LoadingSpinner text="Updating chart..." />
              ) : (
                <PriceChart 
                  priceData={priceData} 
                  showPrediction={showPredictions}
                  predictionData={predictions}
                  title={`Gold Price - ${selectedTimeframe.toUpperCase()} Timeframe`}
                />
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>
      
      <Row>
        <Col>
          <SignalDisplay signal={signals} />
        </Col>
      </Row>
    </Container>
  );
};

export default Dashboard; 
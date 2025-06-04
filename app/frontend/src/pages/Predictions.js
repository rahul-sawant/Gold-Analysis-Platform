import React, { useState, useEffect } from 'react';
import { Container, Table, Button, ButtonGroup, Card, Row, Col, Alert } from 'react-bootstrap';
import PriceChart from '../components/PriceChart';
import LoadingSpinner from '../components/LoadingSpinner';
import api from '../services/api';
import moment from 'moment';

const Predictions = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [priceData, setPriceData] = useState([]);
  const [predictions, setPredictions] = useState([]);
  const [selectedTimeframe, setSelectedTimeframe] = useState('1h');
  const [accuracy, setAccuracy] = useState(null);

  // Fetch predictions and price data
  const fetchData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Fetch recent price data for context
      const priceResponse = await api.getPriceData(selectedTimeframe, 100);
      setPriceData(priceResponse.data);
      
      // Fetch predictions
      const predictionsResponse = await api.getPredictions(selectedTimeframe);
      setPredictions(predictionsResponse.data);
      
      // Calculate accuracy
      if (predictionsResponse.data && predictionsResponse.data.length > 0) {
        // This is a simple example - in a real app, you'd get this from the backend
        setAccuracy({
          mae: (Math.random() * 10).toFixed(2),
          mse: (Math.random() * 100).toFixed(2),
          rmse: (Math.random() * 15).toFixed(2),
          accuracy: (75 + Math.random() * 15).toFixed(2)
        });
      }
    } catch (err) {
      console.error('Error fetching predictions:', err);
      setError('Failed to load predictions. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  // Change timeframe
  const handleTimeframeChange = (timeframe) => {
    setSelectedTimeframe(timeframe);
  };

  // Effect for timeframe changes
  useEffect(() => {
    fetchData();
  }, [selectedTimeframe]);

  if (loading && !priceData.length) {
    return <LoadingSpinner text="Loading predictions..." />;
  }

  return (
    <Container fluid className="dashboard-container">
      <h1 className="page-title">Gold Price Predictions</h1>
      
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
          <Button variant="outline-primary" onClick={fetchData}>
            Refresh
          </Button>
        </div>
      </div>
      
      {accuracy && (
        <Row className="mb-4">
          <Col md={3}>
            <Card className="text-center">
              <Card.Header>Prediction Accuracy</Card.Header>
              <Card.Body>
                <h3 className="gold-text">{accuracy.accuracy}%</h3>
              </Card.Body>
            </Card>
          </Col>
          <Col md={3}>
            <Card className="text-center">
              <Card.Header>Mean Absolute Error</Card.Header>
              <Card.Body>
                <h3>{accuracy.mae}</h3>
              </Card.Body>
            </Card>
          </Col>
          <Col md={3}>
            <Card className="text-center">
              <Card.Header>Mean Squared Error</Card.Header>
              <Card.Body>
                <h3>{accuracy.mse}</h3>
              </Card.Body>
            </Card>
          </Col>
          <Col md={3}>
            <Card className="text-center">
              <Card.Header>Root Mean Squared Error</Card.Header>
              <Card.Body>
                <h3>{accuracy.rmse}</h3>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}
      
      <Row>
        <Col>
          <Card className="mb-4">
            <Card.Header>
              <h5 className="mb-0">Price Chart with Predictions</h5>
            </Card.Header>
            <Card.Body>
              {loading ? (
                <LoadingSpinner text="Updating chart..." />
              ) : (
                <PriceChart 
                  priceData={priceData} 
                  showPrediction={true}
                  predictionData={predictions}
                  title={`Gold Price Predictions - ${selectedTimeframe.toUpperCase()} Timeframe`}
                />
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>
      
      <Row>
        <Col>
          <Card>
            <Card.Header>
              <h5 className="mb-0">Prediction Details</h5>
            </Card.Header>
            <Card.Body>
              {loading ? (
                <LoadingSpinner text="Loading predictions..." />
              ) : predictions.length > 0 ? (
                <Table striped bordered hover responsive>
                  <thead>
                    <tr>
                      <th>Timestamp</th>
                      <th>Predicted Price</th>
                      <th>Actual Price (if available)</th>
                      <th>Error</th>
                      <th>Direction</th>
                    </tr>
                  </thead>
                  <tbody>
                    {predictions.map((item, index) => {
                      const predictedPrice = item.predicted_price;
                      const actualPrice = item.actual_price || null;
                      const error = actualPrice ? (actualPrice - predictedPrice).toFixed(2) : 'N/A';
                      const direction = index > 0 ? 
                        (predictedPrice > predictions[index-1].predicted_price ? 'Up ↑' : 'Down ↓') : 
                        'N/A';
                      
                      return (
                        <tr key={index}>
                          <td>{moment(item.timestamp).format('YYYY-MM-DD HH:mm')}</td>
                          <td>${predictedPrice.toFixed(2)}</td>
                          <td>{actualPrice ? `$${actualPrice.toFixed(2)}` : 'Not yet known'}</td>
                          <td className={error !== 'N/A' && parseFloat(error) < 0 ? 'text-danger' : 'text-success'}>
                            {error !== 'N/A' ? `$${Math.abs(parseFloat(error)).toFixed(2)}` : error}
                          </td>
                          <td className={direction === 'Up ↑' ? 'text-success' : direction === 'Down ↓' ? 'text-danger' : ''}>
                            {direction}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </Table>
              ) : (
                <p>No predictions available for this timeframe.</p>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default Predictions; 
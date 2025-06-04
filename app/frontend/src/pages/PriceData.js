import React, { useState, useEffect } from 'react';
import { Container, Table, Button, ButtonGroup, Card, Row, Col, Alert } from 'react-bootstrap';
import PriceChart from '../components/PriceChart';
import LoadingSpinner from '../components/LoadingSpinner';
import api from '../services/api';
import moment from 'moment';

const PriceData = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [priceData, setPriceData] = useState([]);
  const [selectedTimeframe, setSelectedTimeframe] = useState('1h');
  const [limit, setLimit] = useState(100);

  // Fetch price data
  const fetchPriceData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.getPriceData(selectedTimeframe, limit);
      setPriceData(response.data);
    } catch (err) {
      console.error('Error fetching price data:', err);
      setError('Failed to load price data. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  // Change timeframe
  const handleTimeframeChange = (timeframe) => {
    setSelectedTimeframe(timeframe);
  };

  // Change limit
  const handleLimitChange = (newLimit) => {
    setLimit(newLimit);
  };

  // Update data from source
  const handleUpdateData = async () => {
    try {
      setLoading(true);
      await api.updateData();
      fetchPriceData();
    } catch (err) {
      console.error('Error updating data:', err);
      setError('Failed to update data. Please try again later.');
      setLoading(false);
    }
  };

  // Effect for timeframe or limit changes
  useEffect(() => {
    fetchPriceData();
  }, [selectedTimeframe, limit]);

  if (loading && !priceData.length) {
    return <LoadingSpinner text="Loading price data..." />;
  }

  return (
    <Container fluid className="dashboard-container">
      <h1 className="page-title">Gold Price Data</h1>
      
      {error && <Alert variant="danger">{error}</Alert>}
      
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h5 className="mb-2">Timeframe:</h5>
          <ButtonGroup className="timeframe-selector me-3">
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

          <h5 className="mb-2 mt-3">Limit:</h5>
          <ButtonGroup className="timeframe-selector">
            <Button 
              variant={limit === 50 ? 'secondary' : 'outline-secondary'}
              onClick={() => handleLimitChange(50)}
            >
              50
            </Button>
            <Button 
              variant={limit === 100 ? 'secondary' : 'outline-secondary'}
              onClick={() => handleLimitChange(100)}
            >
              100
            </Button>
            <Button 
              variant={limit === 200 ? 'secondary' : 'outline-secondary'}
              onClick={() => handleLimitChange(200)}
            >
              200
            </Button>
            <Button 
              variant={limit === 500 ? 'secondary' : 'outline-secondary'}
              onClick={() => handleLimitChange(500)}
            >
              500
            </Button>
          </ButtonGroup>
        </div>
        
        <div>
          <Button variant="outline-success" onClick={handleUpdateData}>
            Update Data
          </Button>
        </div>
      </div>
      
      <Row>
        <Col>
          <Card className="mb-4">
            <Card.Header>
              <h5 className="mb-0">Gold Price Chart - {selectedTimeframe.toUpperCase()}</h5>
            </Card.Header>
            <Card.Body>
              {loading ? (
                <LoadingSpinner text="Updating chart..." />
              ) : (
                <PriceChart 
                  priceData={priceData} 
                  title={`Gold Price - ${selectedTimeframe.toUpperCase()} Timeframe`}
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
              <h5 className="mb-0">Price History</h5>
            </Card.Header>
            <Card.Body>
              {loading ? (
                <LoadingSpinner text="Loading data..." />
              ) : (
                <Table striped bordered hover responsive>
                  <thead>
                    <tr>
                      <th>Timestamp</th>
                      <th>Open</th>
                      <th>High</th>
                      <th>Low</th>
                      <th>Close</th>
                      <th>Volume</th>
                    </tr>
                  </thead>
                  <tbody>
                    {priceData.map((item, index) => (
                      <tr key={index}>
                        <td>{moment(item.timestamp).format('YYYY-MM-DD HH:mm')}</td>
                        <td>{item.open.toFixed(2)}</td>
                        <td>{item.high.toFixed(2)}</td>
                        <td>{item.low.toFixed(2)}</td>
                        <td>{item.close.toFixed(2)}</td>
                        <td>{item.volume.toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default PriceData; 
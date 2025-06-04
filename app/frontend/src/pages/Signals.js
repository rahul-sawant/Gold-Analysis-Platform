import React, { useState, useEffect } from 'react';
import { Container, Button, ButtonGroup, Alert, Row, Col, Tab, Nav } from 'react-bootstrap';
import SignalDisplay from '../components/SignalDisplay';
import LoadingSpinner from '../components/LoadingSpinner';
import api from '../services/api';

const Signals = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [signals, setSignals] = useState({});
  const [selectedTimeframe, setSelectedTimeframe] = useState('1h');
  const [lastUpdate, setLastUpdate] = useState(null);

  const timeframes = ['1h', '4h', '1d', '1w'];

  // Fetch signals
  const fetchSignals = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Option 1: Fetch all signals at once
      const response = await api.getAllSignals();
      setSignals(response.data);
      
      // Option 2: Fetch only the selected timeframe
      // const response = await api.getSignal(selectedTimeframe);
      // setSignals(prev => ({
      //   ...prev,
      //   [selectedTimeframe]: response.data
      // }));
      
      setLastUpdate(new Date());
    } catch (err) {
      console.error('Error fetching signals:', err);
      setError('Failed to load signals. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  // Change timeframe
  const handleTimeframeChange = (timeframe) => {
    setSelectedTimeframe(timeframe);
  };
  
  // Refresh data
  const handleRefresh = () => {
    fetchSignals();
  };

  // Update data from source
  const handleUpdateData = async () => {
    try {
      setLoading(true);
      await api.updateData();
      fetchSignals();
    } catch (err) {
      console.error('Error updating data:', err);
      setError('Failed to update data. Please try again later.');
      setLoading(false);
    }
  };

  // Initial data load
  useEffect(() => {
    fetchSignals();
  }, []);

  if (loading && Object.keys(signals).length === 0) {
    return <LoadingSpinner text="Loading signals..." />;
  }

  return (
    <Container fluid className="dashboard-container">
      <h1 className="page-title">Trading Signals</h1>
      
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

      {/* Display signal for selected timeframe */}
      <Row className="mb-4">
        <Col>
          <SignalDisplay signal={signals[selectedTimeframe]} />
        </Col>
      </Row>
      
      {/* Tabs for all timeframes */}
      <h2 className="mb-3">All Timeframes</h2>
      <Tab.Container id="signals-tabs" defaultActiveKey="1h">
        <Row>
          <Col sm={12}>
            <Nav variant="tabs" className="mb-3">
              {timeframes.map(tf => (
                <Nav.Item key={tf}>
                  <Nav.Link eventKey={tf}>
                    {tf === '1h' ? '1 Hour' : 
                     tf === '4h' ? '4 Hours' : 
                     tf === '1d' ? 'Daily' : 'Weekly'}
                  </Nav.Link>
                </Nav.Item>
              ))}
            </Nav>
          </Col>
          <Col sm={12}>
            <Tab.Content>
              {timeframes.map(tf => (
                <Tab.Pane key={tf} eventKey={tf}>
                  <SignalDisplay signal={signals[tf]} />
                </Tab.Pane>
              ))}
            </Tab.Content>
          </Col>
        </Row>
      </Tab.Container>
    </Container>
  );
};

export default Signals; 
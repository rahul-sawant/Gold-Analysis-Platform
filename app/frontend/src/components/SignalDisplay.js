import React from 'react';
import { Card, Badge, Row, Col, ListGroup } from 'react-bootstrap';
import moment from 'moment';

const SignalDisplay = ({ signal }) => {
  // Improved error handling
  const hasValidData = signal && 
                        typeof signal === 'object' && 
                        !signal.error && 
                        Object.keys(signal).length > 0;
  
  if (!hasValidData) {
    return (
      <Card>
        <Card.Header>Trading Signal</Card.Header>
        <Card.Body>
          <p className="text-muted">No signal data available</p>
        </Card.Body>
      </Card>
    );
  }

  // Check if timeframe exists
  const timeframe = signal.timeframe || 'Unknown';

  // Safely format timestamp if it exists
  const formattedTimestamp = signal.timestamp 
    ? moment(signal.timestamp).format('MM/DD/YYYY HH:mm:ss')
    : 'No timestamp available';

  // Determine signal class for styling
  const getSignalClass = (action) => {
    if (!action) return 'hold-signal';
    if (action === 'BUY') return 'buy-signal';
    if (action === 'SELL') return 'sell-signal';
    return 'hold-signal';
  };

  // Determine signal strength class
  const getStrengthClass = (strength) => {
    return strength === 'STRONG' ? 'strong-signal' : '';
  };

  // Get signal indicator color
  const getSignalIndicator = (action) => {
    if (!action) return 'hold';
    if (action === 'BUY') return 'buy';
    if (action === 'SELL') return 'sell';
    return 'hold';
  };

  return (
    <Card>
      <Card.Header>
        <Row>
          <Col>
            <h5>
              Trading Signal - {timeframe.toUpperCase()}
              <span className="ms-2 text-muted small">
                {formattedTimestamp}
              </span>
            </h5>
          </Col>
          <Col xs="auto">
            <h5>
              <span className={`signal-indicator ${getSignalIndicator(signal.action)}`}></span>
              <span className={`${getSignalClass(signal.action)} ${getStrengthClass(signal.signal_strength)}`}>
                {signal.action || 'HOLD'} {signal.signal_strength ? `- ${signal.signal_strength}` : ''}
              </span>
            </h5>
          </Col>
        </Row>
      </Card.Header>
      <Card.Body>
        <Row>
          <Col md={4}>
            <Card>
              <Card.Header>Current Price</Card.Header>
              <Card.Body className="text-center">
                <h3>{signal.current_price?.toFixed(2) || 'N/A'}</h3>
              </Card.Body>
            </Card>
          </Col>
          <Col md={4}>
            <Card>
              <Card.Header>Stop Loss</Card.Header>
              <Card.Body className="text-center">
                <h3 className="text-danger">{signal.stop_loss?.toFixed(2) || 'N/A'}</h3>
              </Card.Body>
            </Card>
          </Col>
          <Col md={4}>
            <Card>
              <Card.Header>Take Profit</Card.Header>
              <Card.Body className="text-center">
                <h3 className="text-success">{signal.take_profit?.toFixed(2) || 'N/A'}</h3>
              </Card.Body>
            </Card>
          </Col>
        </Row>

        <Row className="mt-4">
          <Col md={6}>
            <Card>
              <Card.Header>Signal Breakdown</Card.Header>
              <ListGroup variant="flush">
                {signal.signals && typeof signal.signals === 'object' && Object.entries(signal.signals).map(([key, value]) => (
                  <ListGroup.Item key={key}>
                    <Row>
                      <Col>{key.charAt(0).toUpperCase() + key.slice(1)}</Col>
                      <Col xs="auto">
                        <Badge 
                          bg={
                            value && value.includes && value.includes('BUY') ? 'success' : 
                            value && value.includes && value.includes('SELL') ? 'danger' : 'secondary'
                          }
                        >
                          {value || 'NEUTRAL'}
                        </Badge>
                      </Col>
                    </Row>
                  </ListGroup.Item>
                ))}
                {(!signal.signals || typeof signal.signals !== 'object' || Object.keys(signal.signals).length === 0) && (
                  <ListGroup.Item>No signal breakdown available</ListGroup.Item>
                )}
              </ListGroup>
            </Card>
          </Col>
          <Col md={6}>
            <Card>
              <Card.Header>Key Indicators</Card.Header>
              <ListGroup variant="flush">
                {signal.indicators && typeof signal.indicators === 'object' ? (
                  <>
                    <ListGroup.Item>
                      <Row>
                        <Col>RSI (14)</Col>
                        <Col xs="auto">{signal.indicators.rsi_14?.toFixed(2) || 'N/A'}</Col>
                      </Row>
                    </ListGroup.Item>
                    <ListGroup.Item>
                      <Row>
                        <Col>MACD</Col>
                        <Col xs="auto">{signal.indicators.macd?.toFixed(4) || 'N/A'}</Col>
                      </Row>
                    </ListGroup.Item>
                    <ListGroup.Item>
                      <Row>
                        <Col>MACD Signal</Col>
                        <Col xs="auto">{signal.indicators.macd_signal?.toFixed(4) || 'N/A'}</Col>
                      </Row>
                    </ListGroup.Item>
                    <ListGroup.Item>
                      <Row>
                        <Col>MACD Histogram</Col>
                        <Col xs="auto">{signal.indicators.macd_histogram?.toFixed(4) || 'N/A'}</Col>
                      </Row>
                    </ListGroup.Item>
                  </>
                ) : (
                  <ListGroup.Item>No indicator data available</ListGroup.Item>
                )}
              </ListGroup>
            </Card>
          </Col>
        </Row>
      </Card.Body>
    </Card>
  );
};

export default SignalDisplay; 
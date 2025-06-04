import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Form, Button, Alert, Table, Badge, Tabs, Tab } from 'react-bootstrap';
import LoadingSpinner from '../components/LoadingSpinner';
import SignalDisplay from '../components/SignalDisplay';
import api from '../services/api';
import moment from 'moment';

const Trading = () => {
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [signal, setSignal] = useState({});
  const [zerodhaStatus, setZerodhaStatus] = useState({
    isLoggedIn: false,
    profile: null,
    margins: null
  });
  const [orders, setOrders] = useState([]);
  const [positions, setPositions] = useState([]);
  const [tradeForm, setTradeForm] = useState({
    timeframe: '1h',
    quantity: 1,
    orderType: 'MARKET',
    stopLoss: null,
    takeProfit: null,
    useSignalLevels: true
  });

  // Fetch initial data
  const fetchData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Check Zerodha login status
      try {
        const profileResponse = await api.getZerodhaProfile();
        setZerodhaStatus({
          isLoggedIn: true,
          profile: profileResponse.data
        });
        
        // If logged in, fetch margins
        const marginsResponse = await api.getZerodhaMargins();
        setZerodhaStatus(prev => ({
          ...prev,
          margins: marginsResponse.data
        }));
        
        // Fetch orders and positions
        const [ordersResponse, positionsResponse] = await Promise.all([
          api.getZerodhaOrders(),
          api.getZerodhaPositions()
        ]);
        
        setOrders(ordersResponse.data);
        setPositions(positionsResponse.data);
      } catch (err) {
        console.log('Not logged in to Zerodha');
        setZerodhaStatus({
          isLoggedIn: false,
          profile: null,
          margins: null
        });
      }
      
      // Fetch current signal
      const signalResponse = await api.getSignal(tradeForm.timeframe);
      setSignal(signalResponse.data);
      
      // Set stop loss and take profit from signal if available
      if (signalResponse.data && signalResponse.data.stop_loss && signalResponse.data.take_profit) {
        setTradeForm(prev => ({
          ...prev,
          stopLoss: signalResponse.data.stop_loss,
          takeProfit: signalResponse.data.take_profit
        }));
      }
    } catch (err) {
      console.error('Error loading trading data:', err);
      setError('Failed to load trading data. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  // Handle Zerodha login
  const handleZerodhaLogin = async () => {
    try {
      const response = await api.getZerodhaLoginUrl();
      window.location.href = response.data.login_url;
    } catch (err) {
      console.error('Error getting Zerodha login URL:', err);
      setError('Failed to initiate Zerodha login. Please try again later.');
    }
  };

  // Handle form changes
  const handleFormChange = (e) => {
    const { name, value, type, checked } = e.target;
    setTradeForm(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  // Handle timeframe change
  const handleTimeframeChange = async (timeframe) => {
    setTradeForm(prev => ({ ...prev, timeframe }));
    
    try {
      setLoading(true);
      const signalResponse = await api.getSignal(timeframe);
      setSignal(signalResponse.data);
      
      // Update stop loss and take profit if useSignalLevels is true
      if (tradeForm.useSignalLevels && signalResponse.data) {
        setTradeForm(prev => ({
          ...prev,
          stopLoss: signalResponse.data.stop_loss,
          takeProfit: signalResponse.data.take_profit
        }));
      }
    } catch (err) {
      console.error('Error fetching signal for timeframe:', err);
    } finally {
      setLoading(false);
    }
  };

  // Handle trade execution
  const handleExecuteTrade = async (action) => {
    setSubmitting(true);
    setError(null);
    setSuccess(null);
    
    try {
      if (!zerodhaStatus.isLoggedIn) {
        setError('You must log in to Zerodha to execute trades.');
        setSubmitting(false);
        return;
      }
      
      const tradeData = {
        action: action, // 'BUY' or 'SELL'
        timeframe: tradeForm.timeframe,
        quantity: parseInt(tradeForm.quantity),
        order_type: tradeForm.orderType,
        stop_loss: tradeForm.useSignalLevels && signal.stop_loss ? signal.stop_loss : tradeForm.stopLoss,
        take_profit: tradeForm.useSignalLevels && signal.take_profit ? signal.take_profit : tradeForm.takeProfit
      };
      
      const response = await api.placeTradeFromSignal(tradeData);
      setSuccess(`Trade executed successfully! Order ID: ${response.data.order_id}`);
      
      // Refresh orders
      const ordersResponse = await api.getZerodhaOrders();
      setOrders(ordersResponse.data);
    } catch (err) {
      console.error('Error executing trade:', err);
      setError('Failed to execute trade. Please check your inputs and try again.');
    } finally {
      setSubmitting(false);
    }
  };

  // Load data on component mount
  useEffect(() => {
    fetchData();
  }, []);

  // Order status badge
  const getOrderStatusBadge = (status) => {
    switch (status) {
      case 'COMPLETE':
        return <Badge bg="success">Complete</Badge>;
      case 'REJECTED':
        return <Badge bg="danger">Rejected</Badge>;
      case 'CANCELLED':
        return <Badge bg="warning">Cancelled</Badge>;
      case 'PENDING':
        return <Badge bg="info">Pending</Badge>;
      default:
        return <Badge bg="secondary">{status}</Badge>;
    }
  };

  if (loading && !zerodhaStatus.isLoggedIn && !signal) {
    return <LoadingSpinner text="Loading trading data..." />;
  }

  return (
    <Container fluid className="dashboard-container">
      <h1 className="page-title">Trading Dashboard</h1>
      
      {error && <Alert variant="danger">{error}</Alert>}
      {success && <Alert variant="success">{success}</Alert>}
      
      <Row>
        <Col md={4}>
          <Card className="mb-4">
            <Card.Header>
              <h5 className="mb-0">Zerodha Account</h5>
            </Card.Header>
            <Card.Body>
              {zerodhaStatus.isLoggedIn ? (
                <>
                  <div className="mb-3">
                    <h6>Account Status</h6>
                    <p className="text-success">
                      <strong>Connected</strong> - {zerodhaStatus.profile?.user_name || 'User'}
                    </p>
                  </div>
                  
                  {zerodhaStatus.margins && (
                    <div>
                      <h6>Account Margins</h6>
                      <table className="table table-sm">
                        <tbody>
                          <tr>
                            <td>Available Margin</td>
                            <td className="text-end">
                              ₹{zerodhaStatus.margins.available?.toLocaleString() || 0}
                            </td>
                          </tr>
                          <tr>
                            <td>Used Margin</td>
                            <td className="text-end">
                              ₹{zerodhaStatus.margins.used?.toLocaleString() || 0}
                            </td>
                          </tr>
                          <tr>
                            <td><strong>Total Margin</strong></td>
                            <td className="text-end">
                              <strong>₹{zerodhaStatus.margins.total?.toLocaleString() || 0}</strong>
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  )}
                  
                  <Button 
                    variant="outline-primary" 
                    className="mt-3" 
                    onClick={fetchData}
                  >
                    Refresh Account Data
                  </Button>
                </>
              ) : (
                <div className="text-center">
                  <p className="text-danger mb-3">Not connected to Zerodha</p>
                  <Button variant="warning" onClick={handleZerodhaLogin}>
                    Login to Zerodha
                  </Button>
                </div>
              )}
            </Card.Body>
          </Card>
          
          <Card>
            <Card.Header>
              <h5 className="mb-0">Execute Trade</h5>
            </Card.Header>
            <Card.Body>
              {!zerodhaStatus.isLoggedIn ? (
                <Alert variant="warning">
                  Please log in to Zerodha to execute trades.
                </Alert>
              ) : (
                <Form className="trade-form">
                  <Form.Group className="mb-3">
                    <Form.Label>Signal Timeframe</Form.Label>
                    <Form.Select 
                      name="timeframe"
                      value={tradeForm.timeframe}
                      onChange={(e) => handleTimeframeChange(e.target.value)}
                    >
                      <option value="1h">1 Hour</option>
                      <option value="4h">4 Hours</option>
                      <option value="1d">Daily</option>
                      <option value="1w">Weekly</option>
                    </Form.Select>
                  </Form.Group>
                  
                  <Form.Group className="mb-3">
                    <Form.Label>Quantity</Form.Label>
                    <Form.Control 
                      type="number" 
                      name="quantity"
                      min="1"
                      value={tradeForm.quantity}
                      onChange={handleFormChange}
                    />
                  </Form.Group>
                  
                  <Form.Group className="mb-3">
                    <Form.Label>Order Type</Form.Label>
                    <Form.Select 
                      name="orderType"
                      value={tradeForm.orderType}
                      onChange={handleFormChange}
                    >
                      <option value="MARKET">Market</option>
                      <option value="LIMIT">Limit</option>
                      <option value="SL">Stop Loss</option>
                      <option value="SL-M">Stop Loss Market</option>
                    </Form.Select>
                  </Form.Group>
                  
                  <Form.Group className="mb-3">
                    <Form.Check 
                      type="checkbox"
                      id="useSignalLevels"
                      name="useSignalLevels"
                      label="Use signal stop loss and take profit levels"
                      checked={tradeForm.useSignalLevels}
                      onChange={handleFormChange}
                    />
                  </Form.Group>
                  
                  {!tradeForm.useSignalLevels && (
                    <>
                      <Form.Group className="mb-3">
                        <Form.Label>Stop Loss</Form.Label>
                        <Form.Control 
                          type="number" 
                          name="stopLoss"
                          value={tradeForm.stopLoss || ''}
                          onChange={handleFormChange}
                          step="0.01"
                        />
                      </Form.Group>
                      
                      <Form.Group className="mb-3">
                        <Form.Label>Take Profit</Form.Label>
                        <Form.Control 
                          type="number" 
                          name="takeProfit"
                          value={tradeForm.takeProfit || ''}
                          onChange={handleFormChange}
                          step="0.01"
                        />
                      </Form.Group>
                    </>
                  )}
                  
                  <div className="d-flex justify-content-between mt-4">
                    <Button 
                      variant="success" 
                      onClick={() => handleExecuteTrade('BUY')}
                      disabled={submitting}
                      className="w-100 me-2"
                    >
                      {submitting ? 'Processing...' : 'BUY'}
                    </Button>
                    <Button 
                      variant="danger" 
                      onClick={() => handleExecuteTrade('SELL')}
                      disabled={submitting}
                      className="w-100 ms-2"
                    >
                      {submitting ? 'Processing...' : 'SELL'}
                    </Button>
                  </div>
                </Form>
              )}
            </Card.Body>
          </Card>
        </Col>
        
        <Col md={8}>
          <Card className="mb-4">
            <Card.Header>
              <h5 className="mb-0">Current Signal</h5>
            </Card.Header>
            <Card.Body>
              <SignalDisplay signal={signal} />
            </Card.Body>
          </Card>
          
          <Tabs defaultActiveKey="orders" className="mb-3">
            <Tab eventKey="orders" title="Recent Orders">
              <Card>
                <Card.Body>
                  {orders.length > 0 ? (
                    <Table responsive striped bordered hover>
                      <thead>
                        <tr>
                          <th>Order ID</th>
                          <th>Timestamp</th>
                          <th>Symbol</th>
                          <th>Type</th>
                          <th>Quantity</th>
                          <th>Price</th>
                          <th>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {orders.map((order, index) => (
                          <tr key={index}>
                            <td>{order.order_id}</td>
                            <td>{moment(order.order_timestamp).format('MM/DD/YYYY HH:mm')}</td>
                            <td>{order.tradingsymbol}</td>
                            <td className={order.transaction_type === 'BUY' ? 'text-success' : 'text-danger'}>
                              {order.transaction_type}
                            </td>
                            <td>{order.quantity}</td>
                            <td>{order.price || 'Market'}</td>
                            <td>{getOrderStatusBadge(order.status)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </Table>
                  ) : (
                    <p className="text-muted">No recent orders</p>
                  )}
                </Card.Body>
              </Card>
            </Tab>
            <Tab eventKey="positions" title="Current Positions">
              <Card>
                <Card.Body>
                  {positions.length > 0 ? (
                    <Table responsive striped bordered hover>
                      <thead>
                        <tr>
                          <th>Symbol</th>
                          <th>Quantity</th>
                          <th>Average Price</th>
                          <th>Current Price</th>
                          <th>P&L</th>
                          <th>% Change</th>
                        </tr>
                      </thead>
                      <tbody>
                        {positions.map((position, index) => {
                          const pnl = position.pnl || 0;
                          const pnlPercent = ((pnl / (position.average_price * position.quantity)) * 100) || 0;
                          
                          return (
                            <tr key={index}>
                              <td>{position.tradingsymbol}</td>
                              <td className={position.quantity > 0 ? 'text-success' : 'text-danger'}>
                                {position.quantity}
                              </td>
                              <td>{position.average_price?.toFixed(2)}</td>
                              <td>{position.last_price?.toFixed(2)}</td>
                              <td className={pnl >= 0 ? 'text-success' : 'text-danger'}>
                                {pnl >= 0 ? '+' : ''}{pnl.toFixed(2)}
                              </td>
                              <td className={pnlPercent >= 0 ? 'text-success' : 'text-danger'}>
                                {pnlPercent >= 0 ? '+' : ''}{pnlPercent.toFixed(2)}%
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </Table>
                  ) : (
                    <p className="text-muted">No open positions</p>
                  )}
                </Card.Body>
              </Card>
            </Tab>
          </Tabs>
        </Col>
      </Row>
    </Container>
  );
};

export default Trading; 
import React, { useState } from 'react';
import { Container, Row, Col, Card, Form, Button, Alert, Tab, Nav } from 'react-bootstrap';

const Settings = () => {
  const [zerodhaSettings, setZerodhaSettings] = useState({
    apiKey: '',
    apiSecret: '',
    redirectUrl: window.location.origin + '/zerodha-auth'
  });
  
  const [dataSettings, setDataSettings] = useState({
    dataSource: 'yahoo',
    updateFrequency: '1h',
    storeHistoricalData: true,
    maxHistoricalPeriod: '5y'
  });
  
  const [modelSettings, setModelSettings] = useState({
    predictionModel: 'lstm',
    trainingFrequency: '1d',
    trainingDataPeriod: '1y',
    autoTrain: true
  });
  
  const [success, setSuccess] = useState(null);
  const [error, setError] = useState(null);

  // Handle Zerodha form changes
  const handleZerodhaChange = (e) => {
    const { name, value } = e.target;
    setZerodhaSettings(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // Handle data settings changes
  const handleDataSettingsChange = (e) => {
    const { name, value, type, checked } = e.target;
    setDataSettings(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  // Handle model settings changes
  const handleModelSettingsChange = (e) => {
    const { name, value, type, checked } = e.target;
    setModelSettings(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  // Save settings
  const handleSaveSettings = (settingsType) => {
    setSuccess(`${settingsType} settings saved successfully!`);
    setError(null);
    
    // In a real application, you would make API calls to save the settings
    setTimeout(() => {
      setSuccess(null);
    }, 3000);
  };

  return (
    <Container fluid className="dashboard-container">
      <h1 className="page-title">Settings</h1>
      
      {success && <Alert variant="success">{success}</Alert>}
      {error && <Alert variant="danger">{error}</Alert>}
      
      <Tab.Container id="settings-tabs" defaultActiveKey="zerodha">
        <Row>
          <Col sm={3}>
            <Nav variant="pills" className="flex-column">
              <Nav.Item>
                <Nav.Link eventKey="zerodha">Zerodha API</Nav.Link>
              </Nav.Item>
              <Nav.Item>
                <Nav.Link eventKey="data">Data Settings</Nav.Link>
              </Nav.Item>
              <Nav.Item>
                <Nav.Link eventKey="model">Model Settings</Nav.Link>
              </Nav.Item>
              <Nav.Item>
                <Nav.Link eventKey="notifications">Notifications</Nav.Link>
              </Nav.Item>
              <Nav.Item>
                <Nav.Link eventKey="system">System</Nav.Link>
              </Nav.Item>
            </Nav>
          </Col>
          <Col sm={9}>
            <Tab.Content>
              {/* Zerodha Settings */}
              <Tab.Pane eventKey="zerodha">
                <Card>
                  <Card.Header>
                    <h5 className="mb-0">Zerodha API Configuration</h5>
                  </Card.Header>
                  <Card.Body>
                    <Form>
                      <Form.Group className="mb-3">
                        <Form.Label>API Key</Form.Label>
                        <Form.Control 
                          type="text" 
                          name="apiKey"
                          value={zerodhaSettings.apiKey}
                          onChange={handleZerodhaChange}
                          placeholder="Enter your Zerodha API key"
                        />
                        <Form.Text className="text-muted">
                          You can find your API key in the Zerodha developer dashboard.
                        </Form.Text>
                      </Form.Group>
                      
                      <Form.Group className="mb-3">
                        <Form.Label>API Secret</Form.Label>
                        <Form.Control 
                          type="password" 
                          name="apiSecret"
                          value={zerodhaSettings.apiSecret}
                          onChange={handleZerodhaChange}
                          placeholder="Enter your Zerodha API secret"
                        />
                      </Form.Group>
                      
                      <Form.Group className="mb-3">
                        <Form.Label>Redirect URL</Form.Label>
                        <Form.Control 
                          type="text" 
                          name="redirectUrl"
                          value={zerodhaSettings.redirectUrl}
                          onChange={handleZerodhaChange}
                          placeholder="Redirect URL after authentication"
                        />
                        <Form.Text className="text-muted">
                          This should match the redirect URL registered in your Zerodha app.
                        </Form.Text>
                      </Form.Group>
                      
                      <Button 
                        variant="primary" 
                        onClick={() => handleSaveSettings('Zerodha API')}
                      >
                        Save Zerodha Settings
                      </Button>
                    </Form>
                  </Card.Body>
                </Card>
              </Tab.Pane>
              
              {/* Data Settings */}
              <Tab.Pane eventKey="data">
                <Card>
                  <Card.Header>
                    <h5 className="mb-0">Data Settings</h5>
                  </Card.Header>
                  <Card.Body>
                    <Form>
                      <Form.Group className="mb-3">
                        <Form.Label>Data Source</Form.Label>
                        <Form.Select 
                          name="dataSource"
                          value={dataSettings.dataSource}
                          onChange={handleDataSettingsChange}
                        >
                          <option value="yahoo">Yahoo Finance</option>
                          <option value="zerodha">Zerodha (Requires Login)</option>
                          <option value="alphavantage">Alpha Vantage</option>
                        </Form.Select>
                      </Form.Group>
                      
                      <Form.Group className="mb-3">
                        <Form.Label>Update Frequency</Form.Label>
                        <Form.Select 
                          name="updateFrequency"
                          value={dataSettings.updateFrequency}
                          onChange={handleDataSettingsChange}
                        >
                          <option value="5m">Every 5 minutes</option>
                          <option value="15m">Every 15 minutes</option>
                          <option value="30m">Every 30 minutes</option>
                          <option value="1h">Every hour</option>
                          <option value="manual">Manual only</option>
                        </Form.Select>
                      </Form.Group>
                      
                      <Form.Group className="mb-3">
                        <Form.Check 
                          type="checkbox"
                          id="storeHistoricalData"
                          name="storeHistoricalData"
                          label="Store historical data"
                          checked={dataSettings.storeHistoricalData}
                          onChange={handleDataSettingsChange}
                        />
                      </Form.Group>
                      
                      <Form.Group className="mb-3">
                        <Form.Label>Maximum Historical Period</Form.Label>
                        <Form.Select 
                          name="maxHistoricalPeriod"
                          value={dataSettings.maxHistoricalPeriod}
                          onChange={handleDataSettingsChange}
                          disabled={!dataSettings.storeHistoricalData}
                        >
                          <option value="1m">1 month</option>
                          <option value="3m">3 months</option>
                          <option value="6m">6 months</option>
                          <option value="1y">1 year</option>
                          <option value="2y">2 years</option>
                          <option value="5y">5 years</option>
                          <option value="max">Maximum available</option>
                        </Form.Select>
                      </Form.Group>
                      
                      <Button 
                        variant="primary" 
                        onClick={() => handleSaveSettings('Data')}
                      >
                        Save Data Settings
                      </Button>
                    </Form>
                  </Card.Body>
                </Card>
              </Tab.Pane>
              
              {/* Model Settings */}
              <Tab.Pane eventKey="model">
                <Card>
                  <Card.Header>
                    <h5 className="mb-0">Model Settings</h5>
                  </Card.Header>
                  <Card.Body>
                    <Form>
                      <Form.Group className="mb-3">
                        <Form.Label>Prediction Model</Form.Label>
                        <Form.Select 
                          name="predictionModel"
                          value={modelSettings.predictionModel}
                          onChange={handleModelSettingsChange}
                        >
                          <option value="lstm">LSTM (Deep Learning)</option>
                          <option value="prophet">Prophet</option>
                          <option value="arima">ARIMA</option>
                          <option value="ensemble">Ensemble (Multiple Models)</option>
                        </Form.Select>
                      </Form.Group>
                      
                      <Form.Group className="mb-3">
                        <Form.Check 
                          type="checkbox"
                          id="autoTrain"
                          name="autoTrain"
                          label="Auto-train model"
                          checked={modelSettings.autoTrain}
                          onChange={handleModelSettingsChange}
                        />
                        <Form.Text className="text-muted">
                          Automatically retrain the model with new data.
                        </Form.Text>
                      </Form.Group>
                      
                      <Form.Group className="mb-3">
                        <Form.Label>Training Frequency</Form.Label>
                        <Form.Select 
                          name="trainingFrequency"
                          value={modelSettings.trainingFrequency}
                          onChange={handleModelSettingsChange}
                          disabled={!modelSettings.autoTrain}
                        >
                          <option value="1h">Every hour</option>
                          <option value="4h">Every 4 hours</option>
                          <option value="12h">Every 12 hours</option>
                          <option value="1d">Daily</option>
                          <option value="1w">Weekly</option>
                        </Form.Select>
                      </Form.Group>
                      
                      <Form.Group className="mb-3">
                        <Form.Label>Training Data Period</Form.Label>
                        <Form.Select 
                          name="trainingDataPeriod"
                          value={modelSettings.trainingDataPeriod}
                          onChange={handleModelSettingsChange}
                        >
                          <option value="1m">1 month</option>
                          <option value="3m">3 months</option>
                          <option value="6m">6 months</option>
                          <option value="1y">1 year</option>
                          <option value="2y">2 years</option>
                          <option value="max">All available data</option>
                        </Form.Select>
                      </Form.Group>
                      
                      <Button 
                        variant="primary" 
                        onClick={() => handleSaveSettings('Model')}
                        className="me-2"
                      >
                        Save Model Settings
                      </Button>
                      
                      <Button 
                        variant="warning"
                      >
                        Train Model Now
                      </Button>
                    </Form>
                  </Card.Body>
                </Card>
              </Tab.Pane>
              
              {/* Notifications */}
              <Tab.Pane eventKey="notifications">
                <Card>
                  <Card.Header>
                    <h5 className="mb-0">Notifications</h5>
                  </Card.Header>
                  <Card.Body>
                    <Form>
                      <Form.Group className="mb-3">
                        <Form.Check 
                          type="checkbox"
                          id="enableNotifications"
                          label="Enable notifications"
                        />
                      </Form.Group>
                      
                      <Form.Group className="mb-3">
                        <Form.Label>Email Address</Form.Label>
                        <Form.Control 
                          type="email" 
                          placeholder="Enter your email"
                        />
                      </Form.Group>
                      
                      <Form.Group className="mb-3">
                        <Form.Label>Notification Types</Form.Label>
                        <div>
                          <Form.Check 
                            type="checkbox"
                            id="notifySignals"
                            label="New trading signals"
                            className="mb-2"
                          />
                          <Form.Check 
                            type="checkbox"
                            id="notifyTrades"
                            label="Trade executions"
                            className="mb-2"
                          />
                          <Form.Check 
                            type="checkbox"
                            id="notifyPriceAlerts"
                            label="Price alerts"
                            className="mb-2"
                          />
                          <Form.Check 
                            type="checkbox"
                            id="notifySystemAlerts"
                            label="System alerts"
                          />
                        </div>
                      </Form.Group>
                      
                      <Button 
                        variant="primary" 
                        onClick={() => handleSaveSettings('Notifications')}
                      >
                        Save Notification Settings
                      </Button>
                    </Form>
                  </Card.Body>
                </Card>
              </Tab.Pane>
              
              {/* System Settings */}
              <Tab.Pane eventKey="system">
                <Card>
                  <Card.Header>
                    <h5 className="mb-0">System Settings</h5>
                  </Card.Header>
                  <Card.Body>
                    <Form>
                      <Form.Group className="mb-3">
                        <Form.Label>Database Path</Form.Label>
                        <Form.Control 
                          type="text" 
                          placeholder="Database file path"
                          defaultValue="gold_trading.db"
                          disabled
                        />
                      </Form.Group>
                      
                      <Form.Group className="mb-3">
                        <Form.Label>Log Level</Form.Label>
                        <Form.Select>
                          <option value="debug">Debug</option>
                          <option value="info">Info</option>
                          <option value="warning">Warning</option>
                          <option value="error">Error</option>
                        </Form.Select>
                      </Form.Group>
                      
                      <Form.Group className="mb-3">
                        <Form.Check 
                          type="checkbox"
                          id="enableDebug"
                          label="Enable debug mode"
                        />
                      </Form.Group>
                      
                      <div className="d-flex">
                        <Button 
                          variant="primary" 
                          onClick={() => handleSaveSettings('System')}
                          className="me-2"
                        >
                          Save System Settings
                        </Button>
                        
                        <Button 
                          variant="danger"
                        >
                          Clear Database
                        </Button>
                      </div>
                    </Form>
                  </Card.Body>
                </Card>
              </Tab.Pane>
            </Tab.Content>
          </Col>
        </Row>
      </Tab.Container>
    </Container>
  );
};

export default Settings; 
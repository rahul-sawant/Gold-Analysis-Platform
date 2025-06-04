import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Container } from 'react-bootstrap';
import Navigation from './components/Navigation';
import Dashboard from './pages/Dashboard';
import PriceData from './pages/PriceData';
import Predictions from './pages/Predictions';
import Signals from './pages/Signals';
import Trading from './pages/Trading';
import Settings from './pages/Settings';
import ZerodhaAuth from './pages/ZerodhaAuth';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Navigation />
        <Container fluid className="mt-4">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/price-data" element={<PriceData />} />
            <Route path="/predictions" element={<Predictions />} />
            <Route path="/signals" element={<Signals />} />
            <Route path="/trading" element={<Trading />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/zerodha-auth" element={<ZerodhaAuth />} />
          </Routes>
        </Container>
      </div>
    </Router>
  );
}

export default App; 
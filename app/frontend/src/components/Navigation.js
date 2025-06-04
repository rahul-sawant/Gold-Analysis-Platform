import React from 'react';
import { Navbar, Nav, Container } from 'react-bootstrap';
import { Link, useLocation } from 'react-router-dom';

const Navigation = () => {
  const location = useLocation();

  return (
    <Navbar expand="lg" className="navbar-gold" variant="dark">
      <Container>
        <Navbar.Brand as={Link} to="/">
          <span className="me-2">💰</span>
          Gold Analysis Platform
        </Navbar.Brand>
        <Navbar.Toggle aria-controls="basic-navbar-nav" />
        <Navbar.Collapse id="basic-navbar-nav">
          <Nav className="me-auto">
            <Nav.Link 
              as={Link} 
              to="/" 
              active={location.pathname === '/'}
            >
              Dashboard
            </Nav.Link>
            <Nav.Link 
              as={Link} 
              to="/price-data" 
              active={location.pathname === '/price-data'}
            >
              Price Data
            </Nav.Link>
            <Nav.Link 
              as={Link} 
              to="/predictions" 
              active={location.pathname === '/predictions'}
            >
              Predictions
            </Nav.Link>
            <Nav.Link 
              as={Link} 
              to="/signals" 
              active={location.pathname === '/signals'}
            >
              Trading Signals
            </Nav.Link>
            <Nav.Link 
              as={Link} 
              to="/trading" 
              active={location.pathname === '/trading'}
            >
              Trading
            </Nav.Link>
          </Nav>
          <Nav>
            <Nav.Link 
              as={Link} 
              to="/settings" 
              active={location.pathname === '/settings'}
            >
              Settings
            </Nav.Link>
          </Nav>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
};

export default Navigation; 
import React from 'react';
import { Spinner } from 'react-bootstrap';

const LoadingSpinner = ({ text = 'Loading...' }) => {
  return (
    <div className="loading-spinner">
      <Spinner animation="border" role="status" variant="warning">
        <span className="visually-hidden">{text}</span>
      </Spinner>
      <span className="ms-2">{text}</span>
    </div>
  );
};

export default LoadingSpinner; 
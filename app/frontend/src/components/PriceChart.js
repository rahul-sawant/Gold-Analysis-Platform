import React from 'react';
import { Line } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js';
import moment from 'moment';

// Register ChartJS components
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

const PriceChart = ({ priceData, title = 'Gold Price Chart', showPrediction = false, predictionData = [] }) => {
  // Error handling for priceData
  if (!priceData || !Array.isArray(priceData)) {
    console.error('Invalid price data format:', priceData);
    return <div>No valid price data available</div>;
  }

  // Handle empty data
  if (priceData.length === 0) {
    return <div>No price data available</div>;
  }

  // Process price data for chart
  const timestamps = priceData.map(item => 
    item && item.timestamp ? moment(item.timestamp).format('MM/DD/YYYY HH:mm') : ''
  ).filter(item => item !== '');
  
  const closePrices = priceData.map(item => 
    item && typeof item.close !== 'undefined' ? item.close : null
  ).filter(item => item !== null);
  
  // If we don't have valid data after filtering, return error message
  if (timestamps.length === 0 || closePrices.length === 0) {
    return <div>Invalid data format</div>;
  }
  
  // Prepare prediction data if available
  let predictionTimestamps = [];
  let predictedPrices = [];
  
  if (showPrediction && predictionData) {
    // Ensure predictionData is an array
    const predArray = Array.isArray(predictionData) ? predictionData : [];
    
    if (predArray.length > 0) {
      predictionTimestamps = predArray
        .map(item => item && item.timestamp ? moment(item.timestamp).format('MM/DD/YYYY HH:mm') : '')
        .filter(item => item !== '');
        
      predictedPrices = predArray
        .map(item => item && typeof item.predicted_price !== 'undefined' ? item.predicted_price : null)
        .filter(item => item !== null);
    }
  }
  
  // Combine real data with predictions for continuous line
  const allTimestamps = [...timestamps];
  const allClosePrices = [...closePrices];
  
  if (showPrediction && predictionTimestamps.length > 0 && predictedPrices.length > 0) {
    // Add the prediction data
    allTimestamps.push(...predictionTimestamps);
    
    // Create a null-filled array matching the size of the real data
    const nullArray = Array(closePrices.length).fill(null);
    
    // Create prediction line with nulls for historical data points
    const predictionLine = [...nullArray, ...predictedPrices];
    
    // Ensure both arrays have the same length
    if (allTimestamps.length > predictionLine.length) {
      const diff = allTimestamps.length - predictionLine.length;
      for (let i = 0; i < diff; i++) {
        predictionLine.push(null);
      }
    }
    
    // Chart data
    const chartData = {
      labels: allTimestamps,
      datasets: [
        {
          label: 'Actual Price',
          data: allClosePrices,
          borderColor: '#d4af37',
          backgroundColor: 'rgba(212, 175, 55, 0.1)',
          fill: true,
          tension: 0.1
        },
        {
          label: 'Predicted Price',
          data: predictionLine,
          borderColor: '#3399ff',
          backgroundColor: 'rgba(51, 153, 255, 0.1)',
          borderDash: [5, 5],
          fill: true,
          tension: 0.1
        }
      ]
    };
    
    const options = {
      responsive: true,
      plugins: {
        legend: {
          position: 'top',
        },
        title: {
          display: true,
          text: title
        },
        tooltip: {
          mode: 'index',
          intersect: false
        }
      },
      hover: {
        mode: 'nearest',
        intersect: true
      },
      scales: {
        x: {
          display: true,
          title: {
            display: true,
            text: 'Time'
          }
        },
        y: {
          display: true,
          title: {
            display: true,
            text: 'Price'
          }
        }
      }
    };
    
    return <Line data={chartData} options={options} height={80} />;
  } else {
    // Simple chart without predictions
    const chartData = {
      labels: timestamps,
      datasets: [
        {
          label: 'Gold Price',
          data: closePrices,
          borderColor: '#d4af37',
          backgroundColor: 'rgba(212, 175, 55, 0.1)',
          fill: true,
          tension: 0.1
        }
      ]
    };
    
    const options = {
      responsive: true,
      plugins: {
        legend: {
          position: 'top',
        },
        title: {
          display: true,
          text: title
        }
      },
      scales: {
        x: {
          display: true,
          title: {
            display: true,
            text: 'Time'
          }
        },
        y: {
          display: true,
          title: {
            display: true,
            text: 'Price'
          }
        }
      }
    };
    
    return <Line data={chartData} options={options} height={80} />;
  }
};

export default PriceChart; 
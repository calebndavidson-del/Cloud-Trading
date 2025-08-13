/**
 * Dashboard Component
 * 
 * Main dashboard component that wraps the entire trading interface.
 * This component serves as an alias to the main App component for
 * compatibility with different import patterns.
 */

import React from 'react';
import App from '../App';

const Dashboard = (props) => {
  return <App {...props} />;
};

export default Dashboard;
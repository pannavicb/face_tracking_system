import React from 'react';
import { Bar } from 'react-chartjs-2';

const Dashboard = () => {
  const data = {
    labels: ['9AM', '10AM', '11AM'],
    datasets: [{
      label: 'People Entered',
      data: [5, 10, 7],
      backgroundColor: 'rgba(75,192,192,0.6)'
    }]
  };

  return (
    <div>
      <h2>Entry Statistics</h2>
      <Bar data={data} />
    </div>
  );
};

export default Dashboard;
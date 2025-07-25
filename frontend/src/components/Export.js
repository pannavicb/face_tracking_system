import React from 'react';

const Export = () => {
  const handleExportCSV = () => {
    alert('Export CSV Clicked');
  };

  const handleExportPDF = () => {
    alert('Export PDF Clicked');
  };

  return (
    <div>
      <button onClick={handleExportCSV}>Export CSV</button>
      <button onClick={handleExportPDF}>Export PDF</button>
    </div>
  );
};

export default Export;
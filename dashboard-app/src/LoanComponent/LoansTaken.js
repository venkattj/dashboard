// LoanComponent/LoansTaken.js
import React from 'react';
import { Link } from 'react-router-dom';
import { Paper, Typography } from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';

function LoansTaken() {
  return (
    <div>
      <Link to="/loans">
        <ArrowBackIcon style={{ fontSize: '2rem', marginBottom: '20px' }} />
      </Link>
      <Paper style={{ padding: '20px' }}>
        <Typography variant="h4">Loans Taken</Typography>
        <Typography variant="body1">List of loans you have taken.</Typography>
      </Paper>
    </div>
  );
}

export default LoansTaken;

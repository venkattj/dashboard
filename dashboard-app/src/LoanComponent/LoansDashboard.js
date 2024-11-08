// LoansDashboard.js

import React from 'react';
import { Grid, Paper, Tooltip } from '@mui/material';
import { Link } from 'react-router-dom';
import styled from 'styled-components';
import LocalAtmIcon from '@mui/icons-material/LocalAtm';
import PaidIcon from '@mui/icons-material/Paid';

const DashboardContainer = styled.div`
  min-height: 100vh;
  background: linear-gradient(45deg, #4a90e2, #50a7c2);
  padding: 20px;
  color: white;
`;

const Widget = styled(Paper)`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 30px 20px;
  text-align: center;
  background-color: rgba(255, 255, 255, 0.1) !important;
  color: white !important;
  cursor: pointer;
  text-decoration: none;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  height: 180px;

  &:hover {
    transform: scale(1.05);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  }

  h2 {
    margin: 10px 0 5px;
    font-size: 1.5rem;
  }

  p {
    font-size: 0.9rem;
  }
`;

const Header = styled.h1`
  text-align: center;
  margin-bottom: 40px;
  font-size: 3rem;
  font-weight: bold;
  color: #fff;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.6);
`;

const BackButton = styled(Link)`
  text-decoration: none;
  color: white;
  padding: 10px 20px;
  background-color: #1976d2;
  border-radius: 5px;
  margin-bottom: 20px;
  display: inline-block;
  font-weight: bold;

  &:hover {
    background-color: #1565c0;
  }
`;

function LoansDashboard() {
  return (
    <DashboardContainer>
      <BackButton to="/">Back to Main Dashboard</BackButton>
      <Header>Loans Dashboard</Header>
      <Grid container spacing={3} justifyContent="center">
        <Grid item xs={12} sm={6} md={4}>
          <Tooltip title="Details of loans you have given out" arrow>
            <Widget component={Link} to="/loans/given" elevation={3}>
              <LocalAtmIcon style={{ fontSize: '3rem', color: '#fff' }} />
              <h2>Loans Given</h2>
              <p>View details of loans given to others.</p>
            </Widget>
          </Tooltip>
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <Tooltip title="Details of loans you have taken" arrow>
            <Widget component={Link} to="/loans/taken" elevation={3}>
              <PaidIcon style={{ fontSize: '3rem', color: '#fff' }} />
              <h2>Loans Taken</h2>
              <p>View details of loans taken from others.</p>
            </Widget>
          </Tooltip>
        </Grid>
      </Grid>
    </DashboardContainer>
  );
}

export default LoansDashboard;

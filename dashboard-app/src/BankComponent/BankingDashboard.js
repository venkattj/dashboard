import React from 'react';
import { Grid, Paper, Link as MuiLink } from '@mui/material';
import { Link } from 'react-router-dom';
import styled from 'styled-components';

const DashboardContainer = styled.div`
  min-height: 100vh;
  background: linear-gradient(45deg, #4a90e2, #50a7c2);
  padding: 20px;
  color: white;
`;

const Widget = styled(Paper)`
  padding: 20px;
  text-align: center;
  background-color: rgba(255, 255, 255, 0.1) !important;
  color: white !important;
`;

const Header = styled.h1`
  text-align: center;
  margin-bottom: 40px;
  font-size: 2.5rem;
`;

const BackButton = styled(Link)`
  text-decoration: none;
  color: white;
  padding: 10px;
  background-color: #1976d2;
  border-radius: 5px;
  margin-bottom: 20px;
  display: inline-block;
`;

function BankingDashboard() {
  return (
    <DashboardContainer>
      <BackButton to="/">Back to Main Dashboard</BackButton>
      <Header>Banking Dashboard</Header>
      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} md={4}>
          <Widget elevation={3}>
            {/* Link to savings account */}
            <MuiLink component={Link} to="/banking/savings-accounts" style={{ color: 'white', textDecoration: 'none' }}>
              <h2>Savings Account</h2>
              <p>View your savings account balance and transactions.</p>
            </MuiLink>
          </Widget>
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <Widget elevation={3}>
            <MuiLink component={Link} to="/banking/fixed-deposits" style={{ color: 'white', textDecoration: 'none' }}>
            <h2>Fixed Deposit</h2>
            <p>Details of your fixed deposit accounts and maturity.</p>
            </MuiLink>
          </Widget>
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <Widget elevation={3}>
            <h2>Summary</h2>
            <p>A summary of all your banking transactions and accounts.</p>
          </Widget>
        </Grid>
      </Grid>
    </DashboardContainer>
  );
}

export default BankingDashboard;

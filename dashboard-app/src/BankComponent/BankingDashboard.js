import React from 'react';
import { Grid, Paper, Tooltip } from '@mui/material';
import { Link } from 'react-router-dom';
import styled from 'styled-components';
import SavingsIcon from '@mui/icons-material/Savings';
import AccountBalanceIcon from '@mui/icons-material/AccountBalance';
import SummaryIcon from '@mui/icons-material/Summarize';

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

function BankingDashboard() {
  return (
    <DashboardContainer>
      <BackButton to="/">Back to Main Dashboard</BackButton>
      <Header>Banking Dashboard</Header>
      <Grid container spacing={3} justifyContent="center">
        <Grid item xs={12} sm={6} md={4}>
          <Tooltip title="View your savings account balance and transactions" arrow>
            <Widget component={Link} to="/banking/savings-accounts" elevation={3}>
              <SavingsIcon style={{ fontSize: '3rem', color: '#fff' }} />
              <h2>Savings Account</h2>
              <p>View your savings account balance and transactions.</p>
            </Widget>
          </Tooltip>
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <Tooltip title="Details of your fixed deposit accounts and maturity" arrow>
            <Widget component={Link} to="/banking/fixed-deposits" elevation={3}>
              <AccountBalanceIcon style={{ fontSize: '3rem', color: '#fff' }} />
              <h2>Fixed Deposit</h2>
              <p>Details of your fixed deposit accounts and maturity.</p>
            </Widget>
          </Tooltip>
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <Tooltip title="A summary of all your banking transactions and accounts" arrow>
            <Widget component={Link} to="/banking/summary" elevation={3}>
              <SummaryIcon style={{ fontSize: '3rem', color: '#fff' }} />
              <h2>Summary</h2>
              <p>A summary of all your banking transactions and accounts.</p>
            </Widget>
          </Tooltip>
        </Grid>
      </Grid>
    </DashboardContainer>
  );
}

export default BankingDashboard;

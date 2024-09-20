import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Grid, Paper } from '@mui/material';
import styled from 'styled-components';
import BankingDashboard from './BankComponent/BankingDashboard'; // Import the BankingDashboard component
import SavingsAccounts from './BankComponent/SavingsAccounts'; // Import the SavingsAccounts component
import FixedDeposits from './BankComponent/FixedDeposits'; // Import the FixedDeposits component

const DashboardContainer = styled.div`
  min-height: 100vh;
  background: linear-gradient(45deg, #6b6b83, #7f53ac);
  padding: 20px;
  color: white;
`;

const Widget = styled(Paper)`
  padding: 20px;
  text-align: center;
  background-color: rgba(255, 255, 255, 0.1) !important;
  color: white !important;
  cursor: pointer; /* Makes the widget appear clickable */
  text-decoration: none; /* Removes underline from Link */
`;

const Header = styled.h1`
  text-align: center;
  margin-bottom: 40px;
  font-size: 2.5rem;
`;

function App() {
  return (
    <Router>
      <Routes>
        {/* Main dashboard route */}
        <Route path="/" element={
          <DashboardContainer>
            <Header>My Finance Dashboard</Header>
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6} md={4}>
                {/* Make the entire widget clickable by wrapping with Link */}
                <Widget component={Link} to="/banking" elevation={3}>
                  <h2>Banking</h2>
                  <p>Details about your bank accounts and transactions.</p>
                </Widget>
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <Widget elevation={3}>
                  <h2>Mutual Funds</h2>
                  <p>Overview of your mutual fund investments.</p>
                </Widget>
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <Widget elevation={3}>
                  <h2>Stocks</h2>
                  <p>Track the performance of your stock portfolio.</p>
                </Widget>
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <Widget elevation={3}>
                  <h2>Chits</h2>
                  <p>Monitor your chit fund contributions and returns.</p>
                </Widget>
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <Widget elevation={3}>
                  <h2>Summary</h2>
                  <p>Get a consolidated view of your financial assets.</p>
                </Widget>
              </Grid>
            </Grid>
          </DashboardContainer>
        } />

        {/* Banking dashboard route */}
        <Route path="/banking" element={<BankingDashboard />} />

        {/* Savings Accounts route */}
        <Route path="/banking/savings-accounts" element={<SavingsAccounts />} />
        <Route path="/banking/fixed-deposits" element={<FixedDeposits />} />

      </Routes>
    </Router>
  );
}

export default App;

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Grid, Paper } from '@mui/material';
import styled from 'styled-components';
import BankingDashboard from './BankComponent/BankingDashboard';
import SavingsAccounts from './BankComponent/SavingsAccounts';
import FixedDeposits from './BankComponent/FixedDeposits';
import SummaryPage from './BankComponent/SummaryPage';
import ChitsPage from './ChitComponent/ChitsPage';
import StandardChits from './ChitComponent/StandardChits';
import VariableChits from './ChitComponent/VariableChits';
import ChitSummary from './ChitComponent/ChitSummary';
import HomeLoan from './LoanComponent/HomeLoan';
import MoneyInvested from './Investments/MoneyInvested'; // Import the MoneyInvested component

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
  cursor: pointer;
  text-decoration: none;
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
        <Route path="/" element={
          <DashboardContainer>
            <Header>My Finance Dashboard</Header>
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6} md={4}>
                <Widget component={Link} to="/banking" elevation={3}>
                  <h2>Banking</h2>
                  <p>Details about your bank accounts and transactions.</p>
                </Widget>
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <Widget component={Link} to="/home-loan" elevation={3}>
                  <h2>Home Loan</h2>
                  <p>Details about your home loan status and repayments.</p>
                </Widget>
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <Widget component={Link} to="/money-invested" elevation={3}>
                  <h2>Money Invested</h2>
                  <p>Overview of all the money you've invested across different assets.</p>
                </Widget>
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <Widget component={Link} to="/chits" elevation={3}>
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

        <Route path="/banking" element={<BankingDashboard />} />
        <Route path="/banking/savings-accounts" element={<SavingsAccounts />} />
        <Route path="/banking/fixed-deposits" element={<FixedDeposits />} />
        <Route path="/banking/summary" element={<SummaryPage />} />
        <Route path="/chits" element={<ChitsPage />} />
        <Route path="/chits/standard" element={<StandardChits />} />
        <Route path="/chits/variable" element={<VariableChits />} />
        <Route path="/chits/summary" element={<ChitSummary />} />
        <Route path="/home-loan" element={<HomeLoan />} />
        <Route path="/money-invested" element={<MoneyInvested />} /> {/* New route for MoneyInvested */}

      </Routes>
    </Router>
  );
}

export default App;

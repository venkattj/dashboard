import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Grid, Paper, Tooltip, Button, Snackbar, Alert } from '@mui/material';
import styled from 'styled-components';
import BankingDashboard from './BankComponent/BankingDashboard';
import SavingsAccounts from './BankComponent/SavingsAccounts';
import FixedDeposits from './BankComponent/FixedDeposits';
import BankSummary from './BankComponent/SummaryPage';
import ChitsPage from './ChitComponent/ChitsPage';
import StandardChits from './ChitComponent/StandardChits';
import VariableChits from './ChitComponent/VariableChits';
import ChitSummary from './ChitComponent/ChitSummary';
import HomeLoan from './LoanComponent/HomeLoan';
import MoneyInvested from './Investments/MoneyInvested';
import AccountBalanceIcon from '@mui/icons-material/AccountBalance';
import HomeIcon from '@mui/icons-material/Home';
import SavingsIcon from '@mui/icons-material/Savings';
import LocalAtmIcon from '@mui/icons-material/LocalAtm';
import SummaryIcon from '@mui/icons-material/Summarize';
import LoansDashboard from './LoanComponent/LoansDashboard';
import LoansGiven from './LoanComponent/LoansGiven';
import LoansTaken from './LoanComponent/LoansTaken';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';
import MoneyOffIcon from '@mui/icons-material/MoneyOff';
import EarningsPage from './EarningComponent/EarningsPage';
import SpendingPage from './SpendingComponent/SpendingPage';
import SummaryPage from './SummaryPage';
import api from './api';

const DashboardContainer = styled.div`
  min-height: 100vh;
  background: linear-gradient(45deg, #6b6b83, #7f53ac);
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

const ButtonContainer = styled.div`
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-bottom: 20px;
`;

function App() {
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'success' });

  const handleMySQLStart = async () => {
    try {
      await api.get('/mysql/start');
      setNotification({ open: true, message: 'MySQL started successfully!', severity: 'success' });
    } catch (error) {
      setNotification({ open: true, message: 'Failed to start MySQL.', severity: 'error' });
    }
  };

  const handleMySQLStop = async () => {
    try {
      await api.get('/mysql/stop');
      setNotification({ open: true, message: 'MySQL stopped successfully!', severity: 'success' });
    } catch (error) {
      setNotification({ open: true, message: 'Failed to stop MySQL.', severity: 'error' });
    }
  };

  const handleCloseNotification = () => {
    setNotification({ ...notification, open: false });
  };

  return (
    <Router>
      <Routes>
        <Route path="/" element={
          <DashboardContainer>
            <Header>My Finance Dashboard</Header>
            <ButtonContainer>
                <Button variant="contained" color="primary" onClick={handleMySQLStart}>Start MySQL</Button>
                <Button variant="contained" color="secondary" onClick={handleMySQLStop}>Stop MySQL</Button>
            </ButtonContainer>
              <Snackbar open={notification.open} autoHideDuration={3000} onClose={handleCloseNotification}>
                <Alert onClose={handleCloseNotification} severity={notification.severity} sx={{ width: '100%' }}>
                  {notification.message}
                </Alert>
              </Snackbar>
            <Grid container spacing={3} justifyContent="center">
              <Grid item xs={12} sm={6} md={4} lg={3}>
                <Tooltip title="Details about your bank accounts and transactions" arrow>
                  <Widget component={Link} to="/banking" elevation={3} aria-label="Banking Section">
                    <AccountBalanceIcon style={{ fontSize: '3rem', color: '#fff' }} />
                    <h2>Banking</h2>
                    <p>Manage your bank accounts and transactions.</p>
                  </Widget>
                </Tooltip>
              </Grid>
              <Grid item xs={12} sm={6} md={4} lg={3}>
                <Tooltip title="Monitor your chit fund contributions and returns" arrow>
                  <Widget component={Link} to="/chits" elevation={3} aria-label="Chits Section">
                    <LocalAtmIcon style={{ fontSize: '3rem', color: '#fff' }} />
                    <h2>Chits</h2>
                    <p>Check chit fund contributions and returns.</p>
                  </Widget>
                </Tooltip>
              </Grid>
              <Grid item xs={12} sm={6} md={4} lg={3}>
                  <Tooltip title="Overview of all the money you've invested across different assets" arrow>
                    <Widget component={Link} to="/money-invested" elevation={3} aria-label="Money Invested Section">
                      <SavingsIcon style={{ fontSize: '3rem', color: '#fff' }} />
                      <h2>Money Invested</h2>
                      <p>Track your investments and assets.</p>
                    </Widget>
                  </Tooltip>
              </Grid>
              <Grid item xs={12} sm={6} md={4} lg={3}>
                <Tooltip title="Track your earnings" arrow>
                  <Widget component={Link} to="/earnings" elevation={3} aria-label="Earnings Section">
                    <AttachMoneyIcon style={{ fontSize: '3rem', color: '#fff' }} />
                    <h2>Earnings</h2>
                    <p>Track your earnings and income sources.</p>
                  </Widget>
                </Tooltip>
              </Grid>
              <Grid item xs={12} sm={6} md={4} lg={3}>
                <Tooltip title="Monitor your spending habits" arrow>
                  <Widget component={Link} to="/spending" elevation={3} aria-label="Spending Section">
                    <MoneyOffIcon style={{ fontSize: '3rem', color: '#fff' }} />
                    <h2>Spending</h2>
                    <p>Monitor your spending habits and expenses.</p>
                  </Widget>
                </Tooltip>
              </Grid>
              <Grid item xs={12} sm={6} md={4} lg={3}>
                  <Tooltip title="Details about your home loan status and repayments" arrow>
                    <Widget component={Link} to="/loans" elevation={3} aria-label="Home Loan Section">
                      <HomeIcon style={{ fontSize: '3rem', color: '#fff' }} />
                      <h2>Loans</h2>
                      <p>View loan status and repayments.</p>
                    </Widget>
                  </Tooltip>
              </Grid>
              <Grid item xs={12} sm={6} md={4} lg={3}>
                 <Tooltip title="Get a consolidated view of your financial assets" arrow>
                   <Widget component={Link} to="/summary" elevation={3} aria-label="Summary Section">
                     <SummaryIcon style={{ fontSize: '3rem', color: '#fff' }} />
                     <h2>Summary</h2>
                     <p>Consolidated view of financial assets.</p>
                   </Widget>
                 </Tooltip>
              </Grid>
            </Grid>
          </DashboardContainer>
        } />
        <Route path="/banking" element={<BankingDashboard />} />
        <Route path="/banking/savings-accounts" element={<SavingsAccounts />} />
        <Route path="/banking/fixed-deposits" element={<FixedDeposits />} />
        <Route path="/banking/summary" element={<BankSummary />} />
        <Route path="/chits" element={<ChitsPage />} />
        <Route path="/chits/standard" element={<StandardChits />} />
        <Route path="/chits/variable" element={<VariableChits />} />
        <Route path="/chits/summary" element={<ChitSummary />} />
        <Route path="/loans" element={<LoansDashboard />} />
        <Route path="/loans/given" element={<LoansGiven />} />
        <Route path="/loans/taken" element={<LoansTaken />} />
        <Route path="/money-invested" element={<MoneyInvested />} />
        <Route path="/earnings" element={<EarningsPage />} />
        <Route path="/spending" element={<SpendingPage />} />
        <Route path="/summary" element={<SummaryPage />} />
      </Routes>
    </Router>
  );
}

export default App;

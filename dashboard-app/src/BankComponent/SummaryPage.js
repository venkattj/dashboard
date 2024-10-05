import React, { useEffect, useState } from 'react';
import { Grid, Paper, Divider } from '@mui/material';
import { Link } from 'react-router-dom';
import styled from 'styled-components';
import dayjs from 'dayjs';
import api from '../api'; // Ensure this is your API module
import AccountBalanceIcon from '@mui/icons-material/AccountBalance';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';

const SummaryContainer = styled.div`
  min-height: 100vh;
  background: linear-gradient(45deg, #4a90e2, #50a7c2);
  padding: 40px;
  color: white;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
`;

const DashboardContainer = styled.div`
  min-height: 100vh;
  background: linear-gradient(135deg, #6b6b83, #7f53ac);
  padding: 40px;
  color: #fff;
`;

const BackButton = styled(Link)`
  text-decoration: none;
  color: white;
  padding: 10px 20px;
  background-color: #1976d2;
  border-radius: 5px;
  margin-bottom: 30px; /* Increased margin for spacing */
  display: inline-block;
  transition: background-color 0.3s;

  &:hover {
    background-color: #0d47a1;
  }
`;

const Widget = styled(Paper)`
  padding: 30px; /* Increased padding */
  text-align: center;
  background-color: rgba(255, 255, 255, 0.1) !important;
  color: white !important;
  margin: 20px 0; /* Uniform vertical margin */
  border-radius: 10px;
  transition: transform 0.3s, box-shadow 0.3s;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  height: 150px; /* Fixed height for uniformity */

  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5);
  }
`;

const Header = styled.h1`
  text-align: center;
  margin-bottom: 40px; /* Increased margin for spacing */
  font-size: 2.5rem;
  font-weight: bold;
`;

const TotalValue = styled.h2`
  color: #ffd700; /* Gold color */
  margin: 10px 0;
  font-size: 1.8rem;
  text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.5);
`;

const IconContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
`;

const SummaryPage = () => {
  const [totalSavings, setTotalSavings] = useState(0);
  const [totalFixedDeposits, setTotalFixedDeposits] = useState(0);

  const calculateCurrentValue = (deposit) => {
    const createdDate = dayjs(deposit.created_date, 'DD-MM-YYYY');
    const today = dayjs();
    const daysDifference = today.diff(createdDate, 'day');
    return (daysDifference * parseFloat(deposit.interest) * parseFloat(deposit.invested) / 36500) + parseFloat(deposit.invested);
  };

  useEffect(() => {
    const fetchTotals = async () => {
      try {
        const savingsResponse = await api.get('/api/savings'); // Adjust endpoint as necessary
        const fixedDepositsResponse = await api.get('/api/fixed-deposits'); // Adjust endpoint as necessary

        const savingsTotal = savingsResponse.data.reduce((total, account) => total + parseFloat(account.savings_account), 0);
        const fixedDepositsTotal = fixedDepositsResponse.data.reduce((total, deposit) => total + calculateCurrentValue(deposit), 0);

        setTotalSavings(savingsTotal);
        setTotalFixedDeposits(fixedDepositsTotal);
      } catch (error) {
        console.error('Error fetching totals:', error);
      }
    };

    fetchTotals();
  }, []);

  return (
    <DashboardContainer>
      <BackButton to="/banking">Back to Banking Dashboard</BackButton>

      <SummaryContainer>
        <Header>Banking Summary</Header>
        <Grid container spacing={3} justifyContent="center">
          <Grid item xs={12} sm={6} md={4}>
            <Widget elevation={3}>
              <IconContainer>
                <AccountBalanceIcon style={{ fontSize: '2rem', marginRight: '10px', color: '#ffd700' }} />
                <TotalValue>Total Savings: ₹{totalSavings.toFixed(2)}</TotalValue>
              </IconContainer>
            </Widget>
            <Divider style={{ backgroundColor: 'white', margin: '10px 0' }} />
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <Widget elevation={3}>
              <IconContainer>
                <AccountCircleIcon style={{ fontSize: '2rem', marginRight: '10px', color: '#ffd700' }} />
                <TotalValue>Total Fixed Deposits: ₹{totalFixedDeposits.toFixed(2)}</TotalValue>
              </IconContainer>
            </Widget>
            <Divider style={{ backgroundColor: 'white', margin: '10px 0' }} />
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <Widget elevation={3}>
              <TotalValue>Total: ₹{(totalFixedDeposits + totalSavings).toFixed(2)}</TotalValue>
            </Widget>
          </Grid>
        </Grid>
      </SummaryContainer>
    </DashboardContainer>
  );
};

export default SummaryPage;

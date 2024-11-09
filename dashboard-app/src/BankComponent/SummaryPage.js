import React, { useEffect, useState } from 'react';
import { Grid, Divider } from '@mui/material';
import { Link } from 'react-router-dom';
import styled from 'styled-components';
import dayjs from 'dayjs';
import api from '../api'; // Ensure this is your API module
import AccountBalanceIcon from '@mui/icons-material/AccountBalance';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';

const SummaryContainer = styled.div`
  min-height: 100vh;
  background: linear-gradient(135deg, #4a90e2, #50a7c2);
  padding: 40px;
  color: white;
  display: flex;
  flex-direction: column;
  align-items: center;
`;

const DashboardContainer = styled.div`
  padding: 40px;
  color: #fff;
`;

const BackButton = styled(Link)`
  text-decoration: none;
  color: white;
  padding: 10px 20px;
  background-color: #1976d2;
  border-radius: 5px;
  margin-bottom: 30px;
  display: inline-block;
  transition: background-color 0.3s;

  &:hover {
    background-color: #0d47a1;
  }
`;

const Header = styled.h1`
  text-align: center;
  margin-bottom: 40px;
  font-size: 2.5rem;
  font-weight: bold;
  color: #ffd700;
`;

const SummaryItem = styled.div`
  display: flex;
  align-items: center;
  font-size: 1.5rem;
  font-weight: 500;
  color: #fff;
  margin-bottom: 20px;
`;

const IconContainer = styled.div`
  margin-right: 10px;
  color: #ffd700;
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
        const savingsResponse = await api.get('/api/savings');
        const fixedDepositsResponse = await api.get('/api/fixed-deposits');

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
        <SummaryItem>
          <IconContainer>
            <AccountBalanceIcon style={{ fontSize: '2rem' }} />
          </IconContainer>
          Total Savings In Bank Accounts: ₹{totalSavings.toFixed(2)}
        </SummaryItem>
        <Divider style={{ backgroundColor: 'white', margin: '10px 0', width: '100%' }} />
        <SummaryItem>
          <IconContainer>
            <AccountCircleIcon style={{ fontSize: '2rem' }} />
          </IconContainer>
          Fixed Deposits In banks : ₹{totalFixedDeposits.toFixed(2)}
        </SummaryItem>
        <Divider style={{ backgroundColor: 'white', margin: '10px 0', width: '100%' }} />
        <SummaryItem>
          Total Combined: ₹{(totalFixedDeposits + totalSavings).toFixed(2)}
        </SummaryItem>
      </SummaryContainer>
    </DashboardContainer>
  );
};

export default SummaryPage;

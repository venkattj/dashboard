import React, { useEffect, useState } from 'react';
import { Typography, Divider } from '@mui/material';
import styled from 'styled-components';
import { useNavigate, Link } from 'react-router-dom';
import api from '../api'; // Ensure this points to your API module
import moment from 'moment';

const SummaryContainer = styled.div`
  min-height: 100vh;
  background: linear-gradient(45deg, #4a90e2, #50a7c2);
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
  font-size: 1.5rem;
  font-weight: 500;
  color: #fff;
  margin: 20px 0;
  text-align: center;
`;

const ChitSummary = () => {
  const navigate = useNavigate();
  const [totalVariableChitAmount, setTotalVariableChitAmount] = useState(0);
  const [totalStandardChitAmount, setTotalStandardChitAmount] = useState(0);

  useEffect(() => {
    const fetchChitTotals = async () => {
      try {
        const calculateCurrentValue = (chit) => {
          const value = chit.value ?? 0;
          const duration = chit.duration ?? 1;
          const emisPaid = chit.emis ? chit.emis.length : 0;
          return (emisPaid / duration) * value;
        };

        const calculateStandardCurrentValue = (chit) => {
          const currentDate = moment();
          const startedDate = moment(chit.started);
          const durationMonths = parseInt(chit.duration, 10);
          const monthsDiff = currentDate.diff(startedDate, 'months');
          const emIsPaid = Math.min(monthsDiff, durationMonths) + 1;
          return (chit.value * emIsPaid) / chit.duration;
        };

        const variableChitsResponse = await api.get('/api/variable_chits');
        const standardChitsResponse = await api.get('/api/chits');

        const totalVariable = variableChitsResponse.data.reduce((total, chit) => total + calculateCurrentValue(chit), 0);
        const totalStandard = standardChitsResponse.data.reduce((total, chit) => total + calculateStandardCurrentValue(chit), 0);

        setTotalVariableChitAmount(totalVariable);
        setTotalStandardChitAmount(totalStandard);
      } catch (error) {
        console.error('Error fetching chit totals:', error);
      }
    };

    fetchChitTotals();
  }, []);

  const totalValue = totalVariableChitAmount + totalStandardChitAmount;

  return (
    <DashboardContainer>
        <BackButton to="/chits">Back to Chits Dashboard</BackButton>
        <SummaryContainer>
          <Header>Chits Summary</Header>
          <SummaryItem>
            <Typography variant="h5">Total Variable Chit Amount: ₹{totalVariableChitAmount.toLocaleString()}</Typography>
          </SummaryItem>
          <Divider style={{ backgroundColor: 'white', margin: '10px 0', width: '80%' }} />
          <SummaryItem>
            <Typography variant="h5">Total Standard Chit Amount: ₹{totalStandardChitAmount.toLocaleString()}</Typography>
          </SummaryItem>
          <Divider style={{ backgroundColor: 'white', margin: '10px 0', width: '80%' }} />
          <SummaryItem>
            <Typography variant="h5">Total Value: ₹{totalValue.toLocaleString()}</Typography>
          </SummaryItem>
        </SummaryContainer>
    </DashboardContainer>
  );
};

export default ChitSummary;

// src/ChitComponent/ChitSummary.js

import React, { useEffect, useState } from 'react';
import { Paper, Typography, Button } from '@mui/material';
import styled from 'styled-components';
import { useNavigate } from 'react-router-dom';
import api from '../api'; // Ensure this points to your API module

const SummaryContainer = styled.div`
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
  margin: 20px 0;
`;

const Header = styled.h1`
  text-align: center;
  margin-bottom: 40px;
  font-size: 2.5rem;
`;

const ChitSummary = () => {
  const navigate = useNavigate();
  const [totalVariableChitAmount, setTotalVariableChitAmount] = useState(0);
  const [totalStandardChitAmount, setTotalStandardChitAmount] = useState(0);

  useEffect(() => {
    const fetchChitTotals = async () => {
      try {
        const variableChitsResponse = await api.get('/api/variable_chits');
        const standardChitsResponse = await api.get('/api/standard_chits');

        const totalVariable = variableChitsResponse.data.reduce((total, chit) => total + Number(chit.value ?? 0), 0);
        const totalStandard = standardChitsResponse.data.reduce((total, chit) => total + Number(chit.value ?? 0), 0);

        setTotalVariableChitAmount(totalVariable);
        setTotalStandardChitAmount(totalStandard);
      } catch (error) {
        console.error('Error fetching chit totals:', error);
      }
    };

    fetchChitTotals();
  }, []);

  const totalValue = totalVariableChitAmount + totalStandardChitAmount;

  const handleBack = () => {
    navigate(-1);
  };

  return (
    <SummaryContainer>
      <Header>Chits Summary</Header>
      <Button variant="outlined" color="secondary" onClick={handleBack} style={{ marginBottom: '20px' }}>
        Back to Chits Dashboard
      </Button>
      <Widget elevation={3}>
        <Typography variant="h5">Total Variable Chit Amount:</Typography>
        <Typography variant="h6">₹{totalVariableChitAmount.toLocaleString()}</Typography>
      </Widget>
      <Widget elevation={3}>
        <Typography variant="h5">Total Standard Chit Amount:</Typography>
        <Typography variant="h6">₹{totalStandardChitAmount.toLocaleString()}</Typography>
      </Widget>
      <Widget elevation={3}>
        <Typography variant="h5">Total Value:</Typography>
        <Typography variant="h6">₹{totalValue.toLocaleString()}</Typography>
      </Widget>
    </SummaryContainer>
  );
};

export default ChitSummary;

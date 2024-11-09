import React, { useEffect, useState } from 'react';
import { Grid, Paper, Divider } from '@mui/material';
import { Link } from 'react-router-dom';
import styled from 'styled-components';
import dayjs from 'dayjs';
import api from './api';
import ChitSummary from './ChitComponent/ChitSummary';
import BankSummary from './BankComponent/SummaryPage';

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

const Header = styled.h1`
  margin-bottom: 20px;
`;

const SummaryPage = () => {
  return (
    <DashboardContainer>
      <BackButton to="/">Back to Finance Dashboard</BackButton>

      <SummaryContainer>
        <BankSummary />
      </SummaryContainer>
      <SummaryContainer>
         <ChitSummary />
       </SummaryContainer>
    </DashboardContainer>
  );
};

export default SummaryPage;

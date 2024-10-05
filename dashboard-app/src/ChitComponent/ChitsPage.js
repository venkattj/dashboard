import React from 'react';
import { Grid, Paper } from '@mui/material';
import styled from 'styled-components';
import { Link } from 'react-router-dom';

const ChitsContainer = styled.div`
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
  cursor: pointer;
  transition: transform 0.3s;

  &:hover {
    transform: scale(1.05);
  }
`;

const Header = styled.h1`
  text-align: center;
  margin-bottom: 40px;
  font-size: 2.5rem;
`;

const ChitsPage = () => {
  return (
    <ChitsContainer>
      <Header>Chits Dashboard</Header>
      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} md={4}>
          <Widget elevation={3}>
            <Link to="/chits/variable" style={{ color: 'white', textDecoration: 'none' }}>
              <h2>Variable Chits</h2>
              <p>View details of variable chit funds.</p>
            </Link>
          </Widget>
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <Widget elevation={3}>
            <Link to="/chits/standard" style={{ color: 'white', textDecoration: 'none' }}>
              <h2>Standard Chits</h2>
              <p>Explore standard chit fund options.</p>
            </Link>
          </Widget>
        </Grid>
        <Grid item xs={12} sm={12} md={4}>
          <Widget elevation={3}>
            <Link to="/chits/summary" style={{ color: 'white', textDecoration: 'none' }}>
              <h2>Summary</h2>
              <p>Get a summary of all your chit contributions.</p>
            </Link>
          </Widget>
        </Grid>
      </Grid>
    </ChitsContainer>
  );
};

export default ChitsPage;

// src/App.js
import React from 'react';
import { Grid, Paper, Box } from '@mui/material';
import styled from 'styled-components';

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
`;

const Header = styled.h1`
  text-align: center;
  margin-bottom: 40px;
  font-size: 2.5rem;
`;

function App() {
  return (
    <DashboardContainer>
      <Header>My Dashboard</Header>
      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} md={4}>
          <Widget elevation={3}>
            <h2>Widget 1</h2>
            <p>Content for Widget 1</p>
          </Widget>
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <Widget elevation={3}>
            <h2>Widget 2</h2>
            <p>Content for Widget 2</p>
          </Widget>
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <Widget elevation={3}>
            <h2>Widget 3</h2>
            <p>Content for Widget 3</p>
          </Widget>
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <Widget elevation={3}>
            <h2>Widget 4</h2>
            <p>Content for Widget 4</p>
          </Widget>
        </Grid>
        {/* Add more widgets as necessary */}
      </Grid>
    </DashboardContainer>
  );
}

export default App;

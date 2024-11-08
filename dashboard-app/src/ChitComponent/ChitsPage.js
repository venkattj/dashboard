import React from 'react';
import { Grid, Paper, Button, Tooltip } from '@mui/material';
import styled from 'styled-components';
import { Link, useNavigate } from 'react-router-dom';
import VariableChitIcon from '@mui/icons-material/TrendingUp';
import StandardChitIcon from '@mui/icons-material/AttachMoney';
import SummaryIcon from '@mui/icons-material/Summarize';

const ChitsContainer = styled.div`
  min-height: 100vh;
  background: linear-gradient(45deg, #4a90e2, #50a7c2);
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
  transition: transform 0.3s, box-shadow 0.3s;
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

const ChitsPage = () => {
  const navigate = useNavigate();

  const handleBack = () => {
    navigate(-1);
  };

  return (
    <ChitsContainer>
      <Header>Chits Dashboard</Header>
      <Button
        variant="contained"
        color="secondary"
        onClick={handleBack}
        style={{ marginBottom: '20px', color: 'white', fontWeight: 'bold' }}
      >
        Back to Main Dashboard
      </Button>
      <Grid container spacing={3} justifyContent="center">
        <Grid item xs={12} sm={6} md={4}>
          <Tooltip title="View details of variable chit funds" arrow>
            <Widget component={Link} to="/chits/variable" elevation={3}>
              <VariableChitIcon style={{ fontSize: '3rem', color: '#fff' }} />
              <h2>Variable Chits</h2>
              <p>View details of variable chit funds.</p>
            </Widget>
          </Tooltip>
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <Tooltip title="Explore standard chit fund options" arrow>
            <Widget component={Link} to="/chits/standard" elevation={3}>
              <StandardChitIcon style={{ fontSize: '3rem', color: '#fff' }} />
              <h2>Standard Chits</h2>
              <p>Explore standard chit fund options.</p>
            </Widget>
          </Tooltip>
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <Tooltip title="Get a summary of all your chit contributions" arrow>
            <Widget component={Link} to="/chits/summary" elevation={3}>
              <SummaryIcon style={{ fontSize: '3rem', color: '#fff' }} />
              <h2>Summary</h2>
              <p>Get a summary of all your chit contributions.</p>
            </Widget>
          </Tooltip>
        </Grid>
      </Grid>
    </ChitsContainer>
  );
};

export default ChitsPage;

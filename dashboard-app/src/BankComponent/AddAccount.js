// AddAccount.js
import React, { useState } from 'react';
import { TextField, Button, Paper } from '@mui/material';
import styled from 'styled-components';
import { useHistory } from 'react-router-dom';

const AddAccountContainer = styled.div`
  max-width: 600px;
  margin: 40px auto;
  padding: 20px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
`;

const Header = styled.h2`
  text-align: center;
  color: #1976d2;
`;

const AddAccount = ({ addAccount }) => {
  const [newRow, setNewRow] = useState({ sno: '', accountHolder: '', bankName: '', savingsAccount: '', usedFor: '' });
  const history = useHistory();

  const handleInputChange = (e) => {
    setNewRow({ ...newRow, [e.target.name]: e.target.value });
  };

  const handleAddAccount = () => {
    if (newRow.sno && newRow.accountHolder && newRow.bankName && newRow.savingsAccount && newRow.usedFor) {
      addAccount({ ...newRow, savingsAccount: parseFloat(newRow.savingsAccount) });
      history.push('/savings'); // Redirect to Savings Accounts page
    }
  };

  return (
    <AddAccountContainer>
      <Header>Add New Savings Account</Header>
      <TextField label="S.No" variant="outlined" size="small" name="sno" value={newRow.sno} onChange={handleInputChange} fullWidth margin="normal" />
      <TextField label="Account Holder" variant="outlined" size="small" name="accountHolder" value={newRow.accountHolder} onChange={handleInputChange} fullWidth margin="normal" />
      <TextField label="Bank Name" variant="outlined" size="small" name="bankName" value={newRow.bankName} onChange={handleInputChange} fullWidth margin="normal" />
      <TextField label="Savings Account" variant="outlined" size="small" name="savingsAccount" value={newRow.savingsAccount} onChange={handleInputChange} fullWidth margin="normal" />
      <TextField label="Used For" variant="outlined" size="small" name="usedFor" value={newRow.usedFor} onChange={handleInputChange} fullWidth margin="normal" />
      <Button variant="contained" color="primary" onClick={handleAddAccount} fullWidth>
        Add Account
      </Button>
    </AddAccountContainer>
  );
};

export default AddAccount;

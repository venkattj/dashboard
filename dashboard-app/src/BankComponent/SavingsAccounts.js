import React, { useState, useEffect } from 'react';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Button, TextField, IconButton } from '@mui/material';
import { Link } from 'react-router-dom';
import { Delete as DeleteIcon, Edit as EditIcon, Save as SaveIcon } from '@mui/icons-material';
import styled from 'styled-components';
import api from '../api';

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
  margin-bottom: 20px;
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
`;

const TotalAmount = styled.h2`
  text-align: center;
  margin: 20px 0;
  font-size: 1.8rem;
  color: #ffd700;  /* Gold color */
`;

const AddForm = styled.div`
  margin-bottom: 20px;
  display: flex;
  gap: 10px;
  justify-content: center;
`;

const StyledTextField = styled(TextField)`
  background-color: #ffffff;
  border-radius: 4px;

  & .MuiOutlinedInput-root {
    & fieldset {
      border-color: #1976d2;
    }
    &:hover fieldset {
      border-color: #115293;
    }
    &.Mui-focused fieldset {
      border-color: #1976d2;
    }
  }
`;

const SavingsAccounts = () => {
  const [rows, setRows] = useState([]);
  const [newRow, setNewRow] = useState({ sno: '', accountHolder: '', bankName: '', savingsAccount: '', usedFor: '' });
  const [editRowIndex, setEditRowIndex] = useState(null);
  const [editRowData, setEditRowData] = useState(null);

  useEffect(() => {
    const fetchAccounts = async () => {
      try {
        const response = await api.get('/api/savings');
        console.log('API Response:', response.data);

        // Convert snake_case to camelCase and parse numeric values
        const accounts = response.data.map(account => ({
          id: account.id,
          sno: account.id, // Assuming `id` is used as `sno` here; adjust if needed
          accountHolder: account.account_holder,
          bankName: account.bank_name,
          savingsAccount: parseFloat(account.savings_account) || 0,
          usedFor: account.used_for
        }));

        setRows(accounts);
      } catch (error) {
        console.error('Error fetching accounts:', error);
      }
    };

    fetchAccounts();
  }, []);

  const totalAmount = rows.reduce((acc, row) => acc + row.savingsAccount, 0);

  const handleAddAccount = async () => {
    try {
      const response = await api.post('/api/savings', {
        account_holder: newRow.accountHolder,
        bank_name: newRow.bankName,
        savings_account: parseFloat(newRow.savingsAccount),
        used_for: newRow.usedFor
      });
      setRows([...rows, { ...newRow, id: response.data.id, savingsAccount: parseFloat(newRow.savingsAccount) }]);
      setNewRow({ sno: '', accountHolder: '', bankName: '', savingsAccount: '', usedFor: '' });
    } catch (error) {
      console.error('Error adding account:', error);
    }
  };

  const handleDelete = async (id) => {
    try {
      await api.delete(`/api/savings/${id}`);
      setRows(rows.filter((row) => row.id !== id));
    } catch (error) {
      console.error('Error deleting account:', error);
    }
  };

  const handleEdit = (index) => {
    setEditRowIndex(index);
    setEditRowData({ ...rows[index] });
  };

  const handleSaveEdit = async () => {
    try {
      await api.put(`/api/savings/${editRowData.id}`, {
        account_holder: editRowData.accountHolder,
        bank_name: editRowData.bankName,
        savings_account: parseFloat(editRowData.savingsAccount),
        used_for: editRowData.usedFor
      });
      const updatedRows = [...rows];
      updatedRows[editRowIndex] = { ...editRowData, savingsAccount: parseFloat(editRowData.savingsAccount) };
      setRows(updatedRows);
      setEditRowIndex(null);
      setEditRowData(null);
    } catch (error) {
      console.error('Error saving edit:', error);
    }
  };

  const handleInputChange = (e, setData, data) => {
    setData({ ...data, [e.target.name]: e.target.value });
  };

  return (
    <DashboardContainer>
      <BackButton to="/banking">Back to Banking Dashboard</BackButton>
      <Header>Savings Accounts</Header>

      <TotalAmount>Total Amount: ₹{totalAmount.toFixed(2)}</TotalAmount>

      <AddForm>
        <StyledTextField label="S.No" variant="outlined" size="small" name="sno" value={newRow.sno} onChange={(e) => handleInputChange(e, setNewRow, newRow)} />
        <StyledTextField label="Account Holder" variant="outlined" size="small" name="accountHolder" value={newRow.accountHolder} onChange={(e) => handleInputChange(e, setNewRow, newRow)} />
        <StyledTextField label="Bank Name" variant="outlined" size="small" name="bankName" value={newRow.bankName} onChange={(e) => handleInputChange(e, setNewRow, newRow)} />
        <StyledTextField label="Savings Account" variant="outlined" size="small" name="savingsAccount" value={newRow.savingsAccount} onChange={(e) => handleInputChange(e, setNewRow, newRow)} />
        <StyledTextField label="Used For" variant="outlined" size="small" name="usedFor" value={newRow.usedFor} onChange={(e) => handleInputChange(e, setNewRow, newRow)} />
        <Button variant="contained" color="primary" onClick={handleAddAccount}>Add Account</Button>
      </AddForm>

      <TableContainer component={Paper} style={{ borderRadius: '10px', overflow: 'hidden' }}>
        <Table>
          <TableHead>
            <TableRow style={{ backgroundColor: '#1976d2' }}>
              <TableCell style={{ color: '#fff' }}>S.No</TableCell>
              <TableCell style={{ color: '#fff' }}>Account Holder</TableCell>
              <TableCell style={{ color: '#fff' }}>Bank Name</TableCell>
              <TableCell style={{ color: '#fff' }}>Savings Account Balance</TableCell>
              <TableCell style={{ color: '#fff' }}>Used For</TableCell>
              <TableCell style={{ color: '#fff' }}>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map((row, index) => (
              <TableRow key={row.id}>
                {editRowIndex === index ? (
                  <>
                    <TableCell><StyledTextField size="small" value={editRowData.sno} name="sno" onChange={(e) => handleInputChange(e, setEditRowData, editRowData)} /></TableCell>
                    <TableCell><StyledTextField size="small" value={editRowData.accountHolder} name="accountHolder" onChange={(e) => handleInputChange(e, setEditRowData, editRowData)} /></TableCell>
                    <TableCell><StyledTextField size="small" value={editRowData.bankName} name="bankName" onChange={(e) => handleInputChange(e, setEditRowData, editRowData)} /></TableCell>
                    <TableCell><StyledTextField size="small" value={editRowData.savingsAccount} name="savingsAccount" onChange={(e) => handleInputChange(e, setEditRowData, editRowData)} /></TableCell>
                    <TableCell><StyledTextField size="small" value={editRowData.usedFor} name="usedFor" onChange={(e) => handleInputChange(e, setEditRowData, editRowData)} /></TableCell>
                    <TableCell>
                      <IconButton onClick={handleSaveEdit}><SaveIcon /></IconButton>
                    </TableCell>
                  </>
                ) : (
                  <>
                    <TableCell>{row.sno}</TableCell>
                    <TableCell>{row.accountHolder}</TableCell>
                    <TableCell>{row.bankName}</TableCell>
                    <TableCell>{row.savingsAccount.toFixed(2)}</TableCell>
                    <TableCell>{row.usedFor}</TableCell>
                    <TableCell>
                      <IconButton onClick={() => handleEdit(index)}><EditIcon /></IconButton>
                      <IconButton onClick={() => handleDelete(row.id)}><DeleteIcon /></IconButton>
                    </TableCell>
                  </>
                )}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </DashboardContainer>
  );
};

export default SavingsAccounts;

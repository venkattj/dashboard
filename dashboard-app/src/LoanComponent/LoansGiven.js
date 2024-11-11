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
  &:hover {
    background-color: #0d47a1;
  }
`;

const Header = styled.h1`
  text-align: center;
  margin-bottom: 20px;
  font-size: 2.5rem;
`;

const LoansGiven = () => {
  const [loans, setLoans] = useState([]);
  const [newLoan, setNewLoan] = useState({ receiver: '', amount: '', interest_rate: '', source: '' });
  const [editIndex, setEditIndex] = useState(null);
  const [editLoan, setEditLoan] = useState(null);

  // Calculate the total amount
  const totalAmount = loans.reduce((acc, loan) => acc + parseFloat(loan.amount || 0), 0);

  useEffect(() => {
    const fetchLoans = async () => {
      try {
        const response = await api.get('/api/loans_given');
        setLoans(response.data);
      } catch (error) {
        console.error('Error fetching loans:', error);
      }
    };
    fetchLoans();
  }, []);

  const handleAddLoan = async () => {
    try {
      const response = await api.post('/api/loans_given', {
        receiver: newLoan.receiver,
        amount: parseFloat(newLoan.amount),
        interest_rate: parseFloat(newLoan.interest_rate),
        source: newLoan.source,
      });
      setLoans([...loans, { ...newLoan, id: response.data.id }]);
      setNewLoan({ receiver: '', amount: '', interest_rate: '', source: '' });
    } catch (error) {
      console.error('Error adding loan:', error);
    }
  };

  const handleDeleteLoan = async (id) => {
    try {
      await api.delete(`/api/loans_given/${id}`);
      setLoans(loans.filter((loan) => loan.id !== id));
    } catch (error) {
      console.error('Error deleting loan:', error);
    }
  };

  const handleEditLoan = (index) => {
    setEditIndex(index);
    setEditLoan({ ...loans[index] });
  };

  const handleSaveEdit = async () => {
    try {
      await api.put(`/api/loans_given/${editLoan.id}`, {
        receiver: editLoan.receiver,
        amount: parseFloat(editLoan.amount),
        interest_rate: parseFloat(editLoan.interest_rate),
        source: editLoan.source,
      });
      const updatedLoans = [...loans];
      updatedLoans[editIndex] = editLoan;
      setLoans(updatedLoans);
      setEditIndex(null);
      setEditLoan(null);
    } catch (error) {
      console.error('Error saving loan edit:', error);
    }
  };

  const handleChange = (e, setLoanData, loanData) => {
    setLoanData({ ...loanData, [e.target.name]: e.target.value });
  };

  return (
    <DashboardContainer>
      <BackButton to="/loans">Back to Loans Dashboard</BackButton>
      <Header>Loans Given</Header>

      {/* Display the Total Amount */}
      <div style={{ textAlign: 'center', marginBottom: '20px', fontSize: '1.5rem' }}>
        Total Amount: ${totalAmount.toFixed(2)}
      </div>

      <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', marginBottom: '20px' }}>
        <TextField label="Receiver" name="receiver" value={newLoan.receiver} onChange={(e) => handleChange(e, setNewLoan, newLoan)} />
        <TextField label="Amount" name="amount" value={newLoan.amount} onChange={(e) => handleChange(e, setNewLoan, newLoan)} />
        <TextField label="Interest Rate" name="interest_rate" value={newLoan.interest_rate} onChange={(e) => handleChange(e, setNewLoan, newLoan)} />
        <TextField label="Source" name="source" value={newLoan.source} onChange={(e) => handleChange(e, setNewLoan, newLoan)} />
        <Button variant="contained" color="primary" onClick={handleAddLoan}>Add Loan</Button>
      </div>

      <TableContainer component={Paper} style={{ borderRadius: '10px', overflow: 'hidden' }}>
        <Table>
          <TableHead>
            <TableRow style={{ backgroundColor: '#1976d2' }}>
              <TableCell style={{ color: '#fff' }}>S.No</TableCell>
              <TableCell style={{ color: '#fff' }}>Receiver</TableCell>
              <TableCell style={{ color: '#fff' }}>Amount</TableCell>
              <TableCell style={{ color: '#fff' }}>Interest Rate</TableCell>
              <TableCell style={{ color: '#fff' }}>Source</TableCell>
              <TableCell style={{ color: '#fff' }}>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loans.map((loan, index) => (
              <TableRow key={loan.id}>
                <TableCell>{index + 1}</TableCell>
                {editIndex === index ? (
                  <>
                    <TableCell><TextField size="small" value={editLoan.receiver} name="receiver" onChange={(e) => handleChange(e, setEditLoan, editLoan)} /></TableCell>
                    <TableCell><TextField size="small" value={editLoan.amount} name="amount" onChange={(e) => handleChange(e, setEditLoan, editLoan)} /></TableCell>
                    <TableCell><TextField size="small" value={editLoan.interest_rate} name="interest_rate" onChange={(e) => handleChange(e, setEditLoan, editLoan)} /></TableCell>
                    <TableCell><TextField size="small" value={editLoan.source} name="source" onChange={(e) => handleChange(e, setEditLoan, editLoan)} /></TableCell>
                    <TableCell>
                      <IconButton onClick={handleSaveEdit}><SaveIcon /></IconButton>
                    </TableCell>
                  </>
                ) : (
                  <>
                    <TableCell>{loan.receiver}</TableCell>
                    <TableCell>{loan.amount}</TableCell>
                    <TableCell>{loan.interest_rate}</TableCell>
                    <TableCell>{loan.source}</TableCell>
                    <TableCell>
                      <IconButton onClick={() => handleEditLoan(index)}><EditIcon /></IconButton>
                      <IconButton onClick={() => handleDeleteLoan(loan.id)}><DeleteIcon /></IconButton>
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

export default LoansGiven;

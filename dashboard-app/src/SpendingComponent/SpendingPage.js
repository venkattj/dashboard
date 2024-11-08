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
  color: #ffd700; /* Gold color */
`;

const Spendings = () => {
  const [rows, setRows] = useState([]);
  const [newRow, setNewRow] = useState({ sno: '', expenseType: '', amount: '', spender: '', merchant: '' });
  const [editRowIndex, setEditRowIndex] = useState(null);
  const [editRowData, setEditRowData] = useState(null);

  useEffect(() => {
    const fetchSpendings = async () => {
      try {
        const response = await api.get('/api/spendings');
        const spendings = response.data.map(spending => ({
          id: spending.id,
          sno: spending.sno,  // Assuming `sno` is part of the response
          expenseType: spending.expense_type,
          amount: parseFloat(spending.amount) || 0,
          spender: spending.spender,
          merchant: spending.merchant,
        }));
        setRows(spendings);
      } catch (error) {
        console.error('Error fetching spendings:', error);
      }
    };
    fetchSpendings();
  }, []);

  // Calculate total amount of all spendings
  const totalAmount = rows.reduce((acc, row) => acc + (parseFloat(row.amount) || 0), 0);

  const handleAddSpending = async () => {
    try {
      const response = await api.post('/api/spendings', {
        expense_type: newRow.expenseType,
        amount: parseFloat(newRow.amount),
        spender: newRow.spender,
        merchant: newRow.merchant,
        sno: newRow.sno,  // Send sno as part of the request
      });
      const newRowWithSNo = {
        ...newRow,
        id: response.data.id,
        amount: parseFloat(newRow.amount),
        sno: newRow.sno,
      };
      setRows([...rows, newRowWithSNo]);
      setNewRow({ sno: '', expenseType: '', amount: '', spender: '', merchant: '' });
    } catch (error) {
      console.error('Error adding spending:', error);
    }
  };

  const handleDelete = async (id) => {
    try {
      await api.delete(`/api/spendings/${id}`);
      setRows(rows.filter((row) => row.id !== id));
    } catch (error) {
      console.error('Error deleting spending:', error);
    }
  };

  const handleEdit = (index) => {
    setEditRowIndex(index);
    setEditRowData({ ...rows[index] });
  };

  const handleSaveEdit = async () => {
    try {
      await api.put(`/api/spendings/${editRowData.id}`, {
        expense_type: editRowData.expenseType,
        amount: parseFloat(editRowData.amount),
        spender: editRowData.spender,
        merchant: editRowData.merchant,
        sno: editRowData.sno,  // Send sno as part of the request
      });
      const updatedRows = [...rows];
      updatedRows[editRowIndex] = { ...editRowData, amount: parseFloat(editRowData.amount) };
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
      <BackButton to="/">Back to Finance Dashboard</BackButton>
      <Header>Spendings</Header>
      <TotalAmount>Total Amount: ₹{totalAmount ? totalAmount.toFixed(2) : '0.00'}</TotalAmount>

      {/* Form for Adding New Spending */}
      <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', marginBottom: '20px' }}>
        <TextField label="S.No" name="sno" value={newRow.sno} onChange={(e) => handleInputChange(e, setNewRow, newRow)} />
        <TextField label="Expense Type" name="expenseType" value={newRow.expenseType} onChange={(e) => handleInputChange(e, setNewRow, newRow)} />
        <TextField label="Amount" name="amount" value={newRow.amount} onChange={(e) => handleInputChange(e, setNewRow, newRow)} />
        <TextField label="Spender" name="spender" value={newRow.spender} onChange={(e) => handleInputChange(e, setNewRow, newRow)} />
        <TextField label="Merchant" name="merchant" value={newRow.merchant} onChange={(e) => handleInputChange(e, setNewRow, newRow)} />
        <Button variant="contained" color="primary" onClick={handleAddSpending}>Add Spending</Button>
      </div>

      {/* Spendings Table */}
      <TableContainer component={Paper} style={{ borderRadius: '10px', overflow: 'hidden' }}>
        <Table>
          <TableHead>
            <TableRow style={{ backgroundColor: '#1976d2' }}>
              <TableCell style={{ color: '#fff' }}>S.No</TableCell>
              <TableCell style={{ color: '#fff' }}>Expense Type</TableCell>
              <TableCell style={{ color: '#fff' }}>Amount</TableCell>
              <TableCell style={{ color: '#fff' }}>Spender</TableCell>
              <TableCell style={{ color: '#fff' }}>Merchant</TableCell>
              <TableCell style={{ color: '#fff' }}>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map((row, index) => (
              <TableRow key={row.id}>
                {editRowIndex === index ? (
                  <>
                    <TableCell><TextField size="small" value={editRowData.sno} name="sno" onChange={(e) => handleInputChange(e, setEditRowData, editRowData)} /></TableCell>
                    <TableCell><TextField size="small" value={editRowData.expenseType} name="expenseType" onChange={(e) => handleInputChange(e, setEditRowData, editRowData)} /></TableCell>
                    <TableCell><TextField size="small" value={editRowData.amount} name="amount" onChange={(e) => handleInputChange(e, setEditRowData, editRowData)} /></TableCell>
                    <TableCell><TextField size="small" value={editRowData.spender} name="spender" onChange={(e) => handleInputChange(e, setEditRowData, editRowData)} /></TableCell>
                    <TableCell><TextField size="small" value={editRowData.merchant} name="merchant" onChange={(e) => handleInputChange(e, setEditRowData, editRowData)} /></TableCell>
                    <TableCell><IconButton onClick={handleSaveEdit}><SaveIcon /></IconButton></TableCell>
                  </>
                ) : (
                  <>
                    <TableCell>{row.sno}</TableCell> {/* Displaying S.No */}
                    <TableCell>{row.expenseType}</TableCell>
                    <TableCell>{row.amount.toFixed(2)}</TableCell>
                    <TableCell>{row.spender}</TableCell>
                    <TableCell>{row.merchant}</TableCell>
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

export default Spendings;

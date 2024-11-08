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

const Earnings = () => {
  const [rows, setRows] = useState([]);
  const [newRow, setNewRow] = useState({ incomeType: '', incomeSource: '', amount: '', earner: '' });
  const [editRowIndex, setEditRowIndex] = useState(null);
  const [editRowData, setEditRowData] = useState(null);

  useEffect(() => {
    const fetchEarnings = async () => {
      try {
        const response = await api.get('/api/earnings');
        const earnings = response.data.map(earning => ({
          id: earning.id,
          incomeType: earning.income_type,
          incomeSource: earning.income_source,
          amount: parseFloat(earning.amount) || 0,
          earner: earning.earner,
        }));
        setRows(earnings);
      } catch (error) {
        console.error('Error fetching earnings:', error);
      }
    };
    fetchEarnings();
  }, []);

  const totalAmount = rows.reduce((acc, row) => acc + row.amount, 0);

  const handleAddEarning = async () => {
    try {
      const response = await api.post('/api/earnings', {
        income_type: newRow.incomeType,
        income_source: newRow.incomeSource,
        amount: parseFloat(newRow.amount),
        earner: newRow.earner,
      });
      setRows([...rows, { ...newRow, id: response.data.id, amount: parseFloat(newRow.amount) }]);
      setNewRow({ incomeType: '', incomeSource: '', amount: '', earner: '' });
    } catch (error) {
      console.error('Error adding earning:', error);
    }
  };

  const handleDelete = async (id) => {
    try {
      await api.delete(`/api/earnings/${id}`);
      setRows(rows.filter((row) => row.id !== id));
    } catch (error) {
      console.error('Error deleting earning:', error);
    }
  };

  const handleEdit = (index) => {
    setEditRowIndex(index);
    setEditRowData({ ...rows[index] });
  };

  const handleSaveEdit = async () => {
    try {
      await api.put(`/api/earnings/${editRowData.id}`, {
        income_type: editRowData.incomeType,
        income_source: editRowData.incomeSource,
        amount: parseFloat(editRowData.amount),
        earner: editRowData.earner,
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
      <Header>Earnings</Header>
      <TotalAmount>Total Amount: ₹{totalAmount.toFixed(2)}</TotalAmount>

      {/* Form for Adding New Earning */}
      <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', marginBottom: '20px' }}>
        <TextField label="Income Type" name="incomeType" value={newRow.incomeType} onChange={(e) => handleInputChange(e, setNewRow, newRow)} />
        <TextField label="Income Source" name="incomeSource" value={newRow.incomeSource} onChange={(e) => handleInputChange(e, setNewRow, newRow)} />
        <TextField label="Amount" name="amount" value={newRow.amount} onChange={(e) => handleInputChange(e, setNewRow, newRow)} />
        <TextField label="Earner" name="earner" value={newRow.earner} onChange={(e) => handleInputChange(e, setNewRow, newRow)} />
        <Button variant="contained" color="primary" onClick={handleAddEarning}>Add Earning</Button>
      </div>

      {/* Earnings Table */}
      <TableContainer component={Paper} style={{ borderRadius: '10px', overflow: 'hidden' }}>
        <Table>
          <TableHead>
            <TableRow style={{ backgroundColor: '#1976d2' }}>
              <TableCell style={{ color: '#fff' }}>S.No</TableCell>
              <TableCell style={{ color: '#fff' }}>Income Type</TableCell>
              <TableCell style={{ color: '#fff' }}>Income Source</TableCell>
              <TableCell style={{ color: '#fff' }}>Amount</TableCell>
              <TableCell style={{ color: '#fff' }}>Earner</TableCell>
              <TableCell style={{ color: '#fff' }}>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map((row, index) => (
              <TableRow key={row.id}>
                <TableCell>{index + 1}</TableCell>
                {editRowIndex === index ? (
                  <>
                    <TableCell><TextField size="small" value={editRowData.incomeType} name="incomeType" onChange={(e) => handleInputChange(e, setEditRowData, editRowData)} /></TableCell>
                    <TableCell><TextField size="small" value={editRowData.incomeSource} name="incomeSource" onChange={(e) => handleInputChange(e, setEditRowData, editRowData)} /></TableCell>
                    <TableCell><TextField size="small" value={editRowData.amount} name="amount" onChange={(e) => handleInputChange(e, setEditRowData, editRowData)} /></TableCell>
                    <TableCell><TextField size="small" value={editRowData.earner} name="earner" onChange={(e) => handleInputChange(e, setEditRowData, editRowData)} /></TableCell>
                    <TableCell><IconButton onClick={handleSaveEdit}><SaveIcon /></IconButton></TableCell>
                  </>
                ) : (
                  <>
                    <TableCell>{row.incomeType}</TableCell>
                    <TableCell>{row.incomeSource}</TableCell>
                    <TableCell>{row.amount.toFixed(2)}</TableCell>
                    <TableCell>{row.earner}</TableCell>
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

export default Earnings;

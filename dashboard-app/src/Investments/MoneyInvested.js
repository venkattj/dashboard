import React, { useState, useEffect } from 'react';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Button, TextField, IconButton, TableSortLabel } from '@mui/material';
import { Link } from 'react-router-dom';
import { Delete as DeleteIcon, Edit as EditIcon, Save as SaveIcon, Cancel as CancelIcon } from '@mui/icons-material';
import styled from 'styled-components';
import api from '../api';
import dayjs from 'dayjs';

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
  color: #ffd700;
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

const MoneyInvested = () => {
  const [rows, setRows] = useState([]);
  const [newRow, setNewRow] = useState({ sno: '', investment_type: '', invested_amount: '', current_amount: '', sip_amount: '', sip_date: '' });
  const [editRowIndex, setEditRowIndex] = useState(null);
  const [editRowData, setEditRowData] = useState(null);

  // State for sorting
  const [order, setOrder] = useState('asc');
  const [orderBy, setOrderBy] = useState('sno');

  useEffect(() => {
    const fetchInvestments = async () => {
      try {
        const response = await api.get('/api/investments');
        setRows(response.data);
      } catch (error) {
        console.error('Error fetching investments:', error);
      }
    };
    fetchInvestments();
  }, []);

  const calculateTotalCurrentValue = () => {
    return rows.reduce((total, row) => total + parseFloat(row.current_amount), 0).toFixed(2);
  };

  const handleAddInvestment = async () => {
    try {
      const response = await api.post('/api/investments', newRow);
      setRows([...rows, response.data]);
      setNewRow({ sno: '', investment_type: '', invested_amount: '', current_amount: '', sip_amount: '', sip_date: '' });
    } catch (error) {
      console.error('Error adding investment:', error);
    }
  };

  const handleDelete = async (id) => {
    try {
      await api.delete(`/api/investments/${id}`);
      setRows(rows.filter((row) => row.id !== id));
    } catch (error) {
      console.error('Error deleting investment:', error);
    }
  };

  const handleEdit = (index) => {
    setEditRowIndex(index);
    setEditRowData({ ...rows[index] });
  };

  const handleSaveEdit = async () => {
    try {
      await api.put(`/api/investments/${editRowData.id}`, editRowData);
      const updatedRows = [...rows];
      updatedRows[editRowIndex] = editRowData;
      setRows(updatedRows);
      setEditRowIndex(null);
      setEditRowData(null);
    } catch (error) {
      console.error('Error saving investment:', error);
    }
  };

  const handleInputChange = (e, setData, data) => {
    setData({ ...data, [e.target.name]: e.target.value });
  };

  const handleRequestSort = (property) => {
    const isAsc = orderBy === property && order === 'asc';
    setOrder(isAsc ? 'desc' : 'asc');
    setOrderBy(property);
    const sortedRows = [...rows].sort((a, b) => {
      if (b[property] < a[property]) {
        return order === 'asc' ? -1 : 1;
      }
      if (b[property] > a[property]) {
        return order === 'asc' ? 1 : -1;
      }
      return 0;
    });
    setRows(sortedRows);
  };

  return (
    <DashboardContainer>
      <BackButton to="/">Back to Main Dashboard</BackButton>
      <Header>Money Invested</Header>

      <TotalAmount>Total Current Amount: ₹{calculateTotalCurrentValue()}</TotalAmount>

      <AddForm>
        <StyledTextField label="S.No" variant="outlined" size="small" name="sno" value={newRow.sno} onChange={(e) => handleInputChange(e, setNewRow, newRow)} />
        <StyledTextField label="Investment Type" variant="outlined" size="small" name="investment_type" value={newRow.investment_type} onChange={(e) => handleInputChange(e, setNewRow, newRow)} />
        <StyledTextField label="Invested Amount" variant="outlined" size="small" name="invested_amount" value={newRow.invested_amount} onChange={(e) => handleInputChange(e, setNewRow, newRow)} />
        <StyledTextField label="Current Amount" variant="outlined" size="small" name="current_amount" value={newRow.current_amount} onChange={(e) => handleInputChange(e, setNewRow, newRow)} />
        <StyledTextField label="SIP Amount" variant="outlined" size="small" name="sip_amount" value={newRow.sip_amount} onChange={(e) => handleInputChange(e, setNewRow, newRow)} />
        <StyledTextField label="SIP Date" variant="outlined" size="small" type="date" name="sip_date" value={newRow.sip_date} onChange={(e) => handleInputChange(e, setNewRow, newRow)} InputLabelProps={{ shrink: true }} />
        <Button variant="contained" color="primary" onClick={handleAddInvestment}>Add Investment</Button>
      </AddForm>

      <TableContainer component={Paper} style={{ borderRadius: '10px', overflow: 'hidden' }}>
        <Table>
          <TableHead>
            <TableRow style={{ backgroundColor: '#1976d2' }}>
              <TableCell><TableSortLabel active={orderBy === 'sno'} direction={orderBy === 'sno' ? order : 'asc'} onClick={() => handleRequestSort('sno')}>S.No</TableSortLabel></TableCell>
              <TableCell><TableSortLabel active={orderBy === 'investment_type'} direction={orderBy === 'investment_type' ? order : 'asc'} onClick={() => handleRequestSort('investment_type')}>Investment Type</TableSortLabel></TableCell>
              <TableCell><TableSortLabel active={orderBy === 'invested_amount'} direction={orderBy === 'invested_amount' ? order : 'asc'} onClick={() => handleRequestSort('invested_amount')}>Invested Amount</TableSortLabel></TableCell>
              <TableCell><TableSortLabel active={orderBy === 'current_amount'} direction={orderBy === 'current_amount' ? order : 'asc'} onClick={() => handleRequestSort('current_amount')}>Current Amount</TableSortLabel></TableCell>
              <TableCell><TableSortLabel active={orderBy === 'sip_amount'} direction={orderBy === 'sip_amount' ? order : 'asc'} onClick={() => handleRequestSort('sip_amount')}>SIP Amount</TableSortLabel></TableCell>
              <TableCell><TableSortLabel active={orderBy === 'sip_date'} direction={orderBy === 'sip_date' ? order : 'asc'} onClick={() => handleRequestSort('sip_date')}>SIP Date</TableSortLabel></TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map((row, index) => (
              <TableRow key={row.id}>
                <TableCell>
                  {editRowIndex === index ? (
                    <TextField
                      variant="outlined"
                      size="small"
                      name="sno"
                      value={editRowData.sno}
                      onChange={(e) => handleInputChange(e, setEditRowData, editRowData)}
                    />
                  ) : (
                    row.sno
                  )}
                </TableCell>
                <TableCell>
                  {editRowIndex === index ? (
                    <TextField
                      variant="outlined"
                      size="small"
                      name="investment_type"
                      value={editRowData.investment_type}
                      onChange={(e) => handleInputChange(e, setEditRowData, editRowData)}
                    />
                  ) : (
                    row.investment_type
                  )}
                </TableCell>
                <TableCell>
                  {editRowIndex === index ? (
                    <TextField
                      variant="outlined"
                      size="small"
                      name="invested_amount"
                      value={editRowData.invested_amount}
                      onChange={(e) => handleInputChange(e, setEditRowData, editRowData)}
                    />
                  ) : (
                    row.invested_amount
                  )}
                </TableCell>
                <TableCell>
                  {editRowIndex === index ? (
                    <TextField
                      variant="outlined"
                      size="small"
                      name="current_amount"
                      value={editRowData.current_amount}
                      onChange={(e) => handleInputChange(e, setEditRowData, editRowData)}
                    />
                  ) : (
                    row.current_amount
                  )}
                </TableCell>
                <TableCell>
                  {editRowIndex === index ? (
                    <TextField
                      variant="outlined"
                      size="small"
                      name="sip_amount"
                      value={editRowData.sip_amount}
                      onChange={(e) => handleInputChange(e, setEditRowData, editRowData)}
                    />
                  ) : (
                    row.sip_amount
                  )}
                </TableCell>
                <TableCell>
                  {editRowIndex === index ? (
                    <TextField
                      variant="outlined"
                      size="small"
                      type="date"
                      name="sip_date"
                      value={editRowData.sip_date}
                      onChange={(e) => handleInputChange(e, setEditRowData, editRowData)}
                      InputLabelProps={{ shrink: true }}
                    />
                  ) : (
                    dayjs(row.sip_date).format('YYYY-MM-DD')
                  )}
                </TableCell>
                <TableCell>
                  {editRowIndex === index ? (
                    <>
                      <IconButton onClick={handleSaveEdit}><SaveIcon /></IconButton>
                      <IconButton onClick={() => setEditRowIndex(null)}><CancelIcon /></IconButton>
                    </>
                  ) : (
                    <>
                      <IconButton onClick={() => handleEdit(index)}><EditIcon /></IconButton>
                      <IconButton onClick={() => handleDelete(row.id)}><DeleteIcon /></IconButton>
                    </>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </DashboardContainer>
  );
};

export default MoneyInvested;

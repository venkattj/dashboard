import React, { useState, useEffect } from 'react';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Button, TextField, IconButton, TableSortLabel } from '@mui/material';
import { Link } from 'react-router-dom';
import { Delete as DeleteIcon, Edit as EditIcon, Save as SaveIcon } from '@mui/icons-material';
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

const FixedDeposit = () => {
  const [rows, setRows] = useState([]);
  const [newRow, setNewRow] = useState({sno: '', bank: '', createdDate: '', invested: '', interest: '', maturityDate: '' });
  const [editRowIndex, setEditRowIndex] = useState(null);
  const [editRowData, setEditRowData] = useState(null);

  const parseDate = (dateString) => {
      return dayjs(dateString, 'DD-MM-YYYY'); // Modify this to match your date format
  };

  // State for sorting
  const [order, setOrder] = useState('asc');
  const [orderBy, setOrderBy] = useState('sno');

  useEffect(() => {
    const fetchDeposits = async () => {
      try {
        const response = await api.get('/api/fixed-deposits');
        console.log('API Response:', response.data);

        const deposits = response.data.map(deposit => ({
          id: deposit.id,
          sno: deposit.id,
          bank: deposit.bank,
          createdDate: deposit.created_date,
          invested: parseFloat(deposit.invested) || 0,
          interest: deposit.interest,
          maturityDate: deposit.maturity_date,
          currentValue: calculateCurrentValue(deposit).toFixed(2),
          daysDifference: calculateDaysDifference(deposit),
          daysToMature: calculateDaysToMature(deposit)
        }));

        setRows(deposits);
      } catch (error) {
        console.error('Error fetching fixed deposits:', error);
      }
    };

    fetchDeposits();
  }, []);

  const calculateCurrentValue = (deposit) => {
    const createdDate = dayjs(deposit.created_date, 'DD-MM-YYYY');
    const today = dayjs();
    const daysDifference = today.diff(createdDate, 'day');
    return (daysDifference * parseFloat(deposit.interest) * parseFloat(deposit.invested) / 36500) + parseFloat(deposit.invested);
  };

  const calculateDaysDifference = (deposit) => {
    const createdDate = dayjs(deposit.created_date, 'DD-MM-YYYY');
    const today = dayjs();
    return today.diff(createdDate, 'day');
  };

  const calculateDaysToMature = (deposit) => {
    const maturityDate = dayjs(deposit.maturity_date, 'DD-MM-YYYY');
    const today = dayjs();
    return maturityDate.diff(today, 'day');
  };

  // New function to calculate total current value
  const calculateTotalCurrentValue = () => {
    return rows.reduce((total, row) => total + parseFloat(row.currentValue), 0).toFixed(2);
  };

  const handleAddDeposit = async () => {
    try {
      const response = await api.post('/api/fixed-deposits', {
        bank: newRow.bank,
        created_date: newRow.createdDate,
        invested: parseFloat(newRow.invested),
        interest: newRow.interest,
        maturity_date: newRow.maturityDate
      });
      setRows([...rows, { ...newRow, id: response.data.id, invested: parseFloat(newRow.invested) }]);
      setNewRow({ sno: '', bank: '', createdDate: '', invested: '', interest: '', maturityDate: '' });
    } catch (error) {
      console.error('Error adding deposit:', error);
    }
  };

  const handleDelete = async (id) => {
    try {
      await api.delete(`/api/fixed-deposits/${id}`);
      setRows(rows.filter((row) => row.id !== id));
    } catch (error) {
      console.error('Error deleting deposit:', error);
    }
  };

  const handleEdit = (index) => {
    setEditRowIndex(index);
    setEditRowData({ ...rows[index] });
  };

  const handleSaveEdit = async () => {
    try {
      await api.put(`/api/fixed-deposits/${editRowData.id}`, {
        bank: editRowData.bank,
        created_date: editRowData.createdDate,
        invested: parseFloat(editRowData.invested),
        interest: editRowData.interest,
        maturity_date: editRowData.maturityDate
      });
      const updatedRows = [...rows];
      updatedRows[editRowIndex] = { ...editRowData, invested: parseFloat(editRowData.invested) };
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

  // Sorting function
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
      <BackButton to="/banking">Back to Banking Dashboard</BackButton>
      <Header>Fixed Deposits</Header>

      <TotalAmount>Total Current Value: ₹{calculateTotalCurrentValue()}</TotalAmount> {/* Display Total Current Value */}

      <AddForm>
        <StyledTextField label="S.No" variant="outlined" size="small" name="sno" value={newRow.sno} onChange={(e) => handleInputChange(e, setNewRow, newRow)} />
        <StyledTextField label="Bank" variant="outlined" size="small" name="bank" value={newRow.bank} onChange={(e) => handleInputChange(e, setNewRow, newRow)} />
        <StyledTextField label="Created Date" variant="outlined" size="small" name="createdDate" type="date" value={newRow.createdDate} onChange={(e) => handleInputChange(e, setNewRow, newRow)} InputLabelProps={{ shrink: true }} style={{ width: 'auto' }} />
        <StyledTextField label="Invested Amount" variant="outlined" size="small" name="invested" value={newRow.invested} onChange={(e) => handleInputChange(e, setNewRow, newRow)} />
        <StyledTextField label="Interest" variant="outlined" size="small" name="interest" value={newRow.interest} onChange={(e) => handleInputChange(e, setNewRow, newRow)} />
        <StyledTextField label="Maturity Date" variant="outlined" size="small" type="date" name="maturityDate" value={newRow.maturityDate} onChange={(e) => handleInputChange(e, setNewRow, newRow)} InputLabelProps={{ shrink: true }} style={{ width: 'auto' }} />
        <Button variant="contained" color="primary" onClick={handleAddDeposit}>Add Deposit</Button>
      </AddForm>

      <TableContainer component={Paper} style={{ borderRadius: '10px', overflow: 'hidden' }}>
        <Table>
          <TableHead>
            <TableRow style={{ backgroundColor: '#1976d2' }}>
              <TableCell><TableSortLabel active={orderBy === 'sno'} direction={orderBy === 'sno' ? order : 'asc'} onClick={() => handleRequestSort('sno')}>S.No</TableSortLabel></TableCell>
              <TableCell><TableSortLabel active={orderBy === 'bank'} direction={orderBy === 'bank' ? order : 'asc'} onClick={() => handleRequestSort('bank')}>Bank</TableSortLabel></TableCell>
              <TableCell><TableSortLabel active={orderBy === 'createdDate'} direction={orderBy === 'createdDate' ? order : 'asc'} onClick={() => handleRequestSort('createdDate')}>Created Date</TableSortLabel></TableCell>
              <TableCell><TableSortLabel active={orderBy === 'invested'} direction={orderBy === 'invested' ? order : 'asc'} onClick={() => handleRequestSort('invested')}>Invested Amount</TableSortLabel></TableCell>
              <TableCell><TableSortLabel active={orderBy === 'interest'} direction={orderBy === 'interest' ? order : 'asc'} onClick={() => handleRequestSort('interest')}>Interest</TableSortLabel></TableCell>
              <TableCell><TableSortLabel active={orderBy === 'maturityDate'} direction={orderBy === 'maturityDate' ? order : 'asc'} onClick={() => handleRequestSort('maturityDate')}>Maturity Date</TableSortLabel></TableCell>
              <TableCell ><TableSortLabel active={orderBy === 'currentValue'} direction={orderBy === 'currentValue' ? order : 'asc'} onClick={() => handleRequestSort('currentValue')}>Current Value</TableSortLabel></TableCell> {/* Add Current Value column */}
              <TableCell><TableSortLabel active={orderBy === 'daysDifference'} direction={orderBy === 'daysDifference' ? order : 'asc'} onClick={() => handleRequestSort('daysDifference')}>Days Difference</TableSortLabel></TableCell> {/* Add Days Difference column */}
              <TableCell><TableSortLabel active={orderBy === 'daysToMature'} direction={orderBy === 'daysToMature' ? order : 'asc'} onClick={() => handleRequestSort('daysToMature')}>Days To Mature</TableSortLabel></TableCell> {/* Add Days Difference column */}
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map((row, index) => (
              <TableRow key={row.id}>
                <TableCell>{row.sno}</TableCell>
                <TableCell>{row.bank}</TableCell>
                <TableCell>{row.createdDate}</TableCell>
                <TableCell>{row.invested.toFixed(2)}</TableCell>
                <TableCell>{row.interest}</TableCell>
                <TableCell>{row.maturityDate}</TableCell>
                <TableCell>{row.currentValue}</TableCell> {/* Show Current Value */}
                <TableCell>{row.daysDifference}</TableCell> {/* Show days Difference */}
                <TableCell>{row.daysToMature}</TableCell> {/* Show days Difference */}
                <TableCell align="center">
                  {editRowIndex === index ? (
                    <>
                      <IconButton onClick={handleSaveEdit}>
                        <SaveIcon />
                      </IconButton>
                      <IconButton onClick={() => { setEditRowIndex(null); setEditRowData(null); }}>
                        <EditIcon />
                      </IconButton>
                    </>
                  ) : (
                    <>
                      <IconButton onClick={() => handleEdit(index)}>
                        <EditIcon />
                      </IconButton>
                      <IconButton onClick={() => handleDelete(row.id)}>
                        <DeleteIcon />
                      </IconButton>
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

export default FixedDeposit;

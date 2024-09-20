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

const FixedDeposit = () => {
  const [rows, setRows] = useState([]);
  const [newRow, setNewRow] = useState({sno: '', bank: '', createdDate: '', invested: '', interest: '', maturityDate: '' });
  const [editRowIndex, setEditRowIndex] = useState(null);
  const [editRowData, setEditRowData] = useState(null);

  useEffect(() => {
    const fetchDeposits = async () => {
      try {
        const response = await api.get('/api/fixed-deposits');
        console.log('API Response:', response.data);

        // Convert snake_case to camelCase and parse numeric values
        const deposits = response.data.map(deposit => ({
          id: deposit.id,
          sno: deposit.id,
          bank: deposit.bank,
          createdDate: deposit.created_date,
          invested: parseFloat(deposit.invested) || 0,
          interest: deposit.interest,
          maturityDate: deposit.maturity_date
        }));
        setRows(deposits);
      } catch (error) {
        console.error('Error fetching fixed deposits:', error);
      }
    };

    fetchDeposits();
  }, []);

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
      setNewRow({ sno: '',bank: '', createdDate: '', invested: '', interest: '', maturityDate: '' });
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

  return (
    <DashboardContainer>
      <BackButton to="/banking">Back to Banking Dashboard</BackButton>
      <Header>Fixed Deposits</Header>

      <AddForm>
        <StyledTextField label="S.No" variant="outlined" size="small" name="sno" value={newRow.sno} onChange={(e) => handleInputChange(e, setNewRow, newRow)} />
        <StyledTextField label="Bank" variant="outlined" size="small" name="bank" value={newRow.bank} onChange={(e) => handleInputChange(e, setNewRow, newRow)} />
        <StyledTextField label="Created Date" variant="outlined" size="small" name="createdDate" value={newRow.createdDate} onChange={(e) => handleInputChange(e, setNewRow, newRow)} />
        <StyledTextField label="Invested Amount" variant="outlined" size="small" name="invested" value={newRow.invested} onChange={(e) => handleInputChange(e, setNewRow, newRow)} />
        <StyledTextField label="Interest" variant="outlined" size="small" name="interest" value={newRow.interest} onChange={(e) => handleInputChange(e, setNewRow, newRow)} />
        <StyledTextField label="Maturity Date" variant="outlined" size="small" name="maturityDate" value={newRow.maturityDate} onChange={(e) => handleInputChange(e, setNewRow, newRow)} />
        <Button variant="contained" color="primary" onClick={handleAddDeposit}>Add Deposit</Button>
      </AddForm>

      <TableContainer component={Paper} style={{ borderRadius: '10px', overflow: 'hidden' }}>
        <Table>
          <TableHead>
            <TableRow style={{ backgroundColor: '#1976d2' }}>
              <TableCell style={{ color: '#fff' }}>S.No</TableCell>
              <TableCell style={{ color: '#fff' }}>Bank</TableCell>
              <TableCell style={{ color: '#fff' }}>Created Date</TableCell>
              <TableCell style={{ color: '#fff' }}>Invested Amount</TableCell>
              <TableCell style={{ color: '#fff' }}>Interest</TableCell>
              <TableCell style={{ color: '#fff' }}>Maturity Date</TableCell>
              <TableCell style={{ color: '#fff' }}>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map((row, index) => (
              <TableRow key={row.id}>
                {editRowIndex === index ? (
                  <>
                    <TableCell><StyledTextField size="small" value={editRowData.sno} name="sno" onChange={(e) => handleInputChange(e, setEditRowData, editRowData)} /></TableCell>
                    <TableCell><StyledTextField size="small" value={editRowData.bank} name="bank" onChange={(e) => handleInputChange(e, setEditRowData, editRowData)} /></TableCell>
                    <TableCell><StyledTextField size="small" value={editRowData.createdDate} name="createdDate" onChange={(e) => handleInputChange(e, setEditRowData, editRowData)} /></TableCell>
                    <TableCell><StyledTextField size="small" value={editRowData.invested} name="invested" onChange={(e) => handleInputChange(e, setEditRowData, editRowData)} /></TableCell>
                    <TableCell><StyledTextField size="small" value={editRowData.interest} name="interest" onChange={(e) => handleInputChange(e, setEditRowData, editRowData)} /></TableCell>
                    <TableCell><StyledTextField size="small" value={editRowData.maturityDate} name="maturityDate" onChange={(e) => handleInputChange(e, setEditRowData, editRowData)} /></TableCell>
                    <TableCell>
                      <IconButton onClick={handleSaveEdit}><SaveIcon /></IconButton>
                    </TableCell>
                  </>
                ) : (
                  <>
                    <TableCell>{row.sno}</TableCell>
                    <TableCell>{row.bank}</TableCell>
                    <TableCell>{row.createdDate}</TableCell>
                    <TableCell>{row.invested.toFixed(2)}</TableCell>
                    <TableCell>{row.interest}</TableCell>
                    <TableCell>{row.maturityDate}</TableCell>
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

export default FixedDeposit;

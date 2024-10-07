import React, { useState, useEffect } from 'react';
import axios from 'axios';

const HomeLoan = () => {
  const [loans, setLoans] = useState([]);
  const [newLoan, setNewLoan] = useState({
    loan_number: '',
    area_office: '',
    date_of_sanction: '',
    sanction_amount: '',
    first_disbursement: '',
    disbursement_amount: '',
    roi: '',
    emi: '',
    fup: '',
    unpaid_installments: '',
    principal_outstanding: '',
    loan_end_date: '',
    last_emi_paid: '',
    principal_repaid_current_fy: '',
    interest_paid_current_fy: '',
    premium_paid_current_fy: ''
  });
  const [editMode, setEditMode] = useState(false);
  const [selectedLoanNumber, setSelectedLoanNumber] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');

  // Fetch all loans when the component mounts
  useEffect(() => {
    fetchLoans();
  }, []);

  const fetchLoans = () => {
    axios.get('http://localhost:5000/homeloans')
      .then(res => {
        setLoans(res.data);
      })
      .catch(err => console.error(err));
  };

  // Handle form input changes
  const handleInputChange = (e) => {
    setNewLoan({
      ...newLoan,
      [e.target.name]: e.target.value,
    });
  };

  // Create a new loan
  const createLoan = () => {
    axios.post('http://localhost:5000/homeloans', newLoan)
      .then(res => {
        alert(res.data.message);
        setLoans([...loans, newLoan]);
        clearForm();
      })
      .catch(err => {
        console.error(err);
        setErrorMessage('Error creating loan.');
      });
  };

  // Delete a loan by loan_number
  const deleteLoan = (loan_number) => {
    axios.delete(`http://localhost:5000/homeloans/${loan_number}`)
      .then(res => {
        alert(res.data.message);
        setLoans(loans.filter(loan => loan.loan_number !== loan_number));
      })
      .catch(err => {
        console.error(err);
        setErrorMessage('Error deleting loan.');
      });
  };

  // Update a loan
  const updateLoan = () => {
    axios.put(`http://localhost:5000/homeloans/${selectedLoanNumber}`, newLoan)
      .then(res => {
        alert(res.data.message);
        setLoans(loans.map(loan => (loan.loan_number === selectedLoanNumber ? newLoan : loan)));
        clearForm();
        setEditMode(false);
      })
      .catch(err => {
        console.error(err);
        setErrorMessage('Error updating loan.');
      });
  };

  // Load loan data into form for editing
  const loadLoanForEdit = (loan) => {
    setNewLoan(loan);
    setSelectedLoanNumber(loan.loan_number);
    setEditMode(true);
  };

  // Clear form after submit or cancel
  const clearForm = () => {
    setNewLoan({
      loan_number: '',
      area_office: '',
      date_of_sanction: '',
      sanction_amount: '',
      first_disbursement: '',
      disbursement_amount: '',
      roi: '',
      emi: '',
      fup: '',
      unpaid_installments: '',
      principal_outstanding: '',
      loan_end_date: '',
      last_emi_paid: '',
      principal_repaid_current_fy: '',
      interest_paid_current_fy: '',
      premium_paid_current_fy: ''
    });
    setSelectedLoanNumber(null);
    setEditMode(false);
    setErrorMessage('');
  };

  return (
    <div>
      <h1>Home Loan Management</h1>

      {errorMessage && <p style={{ color: 'red' }}>{errorMessage}</p>}

      <h2>{editMode ? 'Edit Loan' : 'Create New Loan'}</h2>
      <form>
        <input
          type="text"
          name="loan_number"
          placeholder="Loan Number"
          value={newLoan.loan_number}
          onChange={handleInputChange}
          disabled={editMode} // Loan number is not editable when in edit mode
          required
        />
        <input
          type="text"
          name="area_office"
          placeholder="Area Office"
          value={newLoan.area_office}
          onChange={handleInputChange}
          required
        />
        <input
          type="date"
          name="date_of_sanction"
          value={newLoan.date_of_sanction}
          onChange={handleInputChange}
          required
        />
        <input
          type="number"
          name="sanction_amount"
          placeholder="Sanction Amount"
          value={newLoan.sanction_amount}
          onChange={handleInputChange}
          required
        />
        <input
          type="date"
          name="first_disbursement"
          value={newLoan.first_disbursement}
          onChange={handleInputChange}
          required
        />
        <input
          type="number"
          name="disbursement_amount"
          placeholder="Disbursement Amount"
          value={newLoan.disbursement_amount}
          onChange={handleInputChange}
          required
        />
        <input
          type="number"
          name="roi"
          placeholder="Rate of Interest (%)"
          value={newLoan.roi}
          onChange={handleInputChange}
          required
        />
        <input
          type="number"
          name="emi"
          placeholder="EMI"
          value={newLoan.emi}
          onChange={handleInputChange}
          required
        />
        <input
          type="date"
          name="fup"
          value={newLoan.fup}
          onChange={handleInputChange}
          required
        />
        <input
          type="number"
          name="unpaid_installments"
          placeholder="Unpaid Installments"
          value={newLoan.unpaid_installments}
          onChange={handleInputChange}
          required
        />
        <input
          type="number"
          name="principal_outstanding"
          placeholder="Principal Outstanding"
          value={newLoan.principal_outstanding}
          onChange={handleInputChange}
          required
        />
        <input
          type="date"
          name="loan_end_date"
          value={newLoan.loan_end_date}
          onChange={handleInputChange}
          required
        />
        <input
          type="number"
          name="last_emi_paid"
          placeholder="Last EMI Paid"
          value={newLoan.last_emi_paid}
          onChange={handleInputChange}
        />
        <input
          type="number"
          name="principal_repaid_current_fy"
          placeholder="Principal Repaid Current FY"
          value={newLoan.principal_repaid_current_fy}
          onChange={handleInputChange}
        />
        <input
          type="number"
          name="interest_paid_current_fy"
          placeholder="Interest Paid Current FY"
          value={newLoan.interest_paid_current_fy}
          onChange={handleInputChange}
        />
        <input
          type="number"
          name="premium_paid_current_fy"
          placeholder="Premium Paid Current FY"
          value={newLoan.premium_paid_current_fy}
          onChange={handleInputChange}
        />

        <button type="button" onClick={editMode ? updateLoan : createLoan}>
          {editMode ? 'Update Loan' : 'Create Loan'}
        </button>
        {editMode && <button type="button" onClick={clearForm}>Cancel Edit</button>}
      </form>

      <h2>Existing Loans</h2>
      <ul>
        {loans.map((loan) => (
          <li key={loan.loan_number}>
            <strong>{loan.loan_number}</strong> - {loan.area_office} ({loan.sanction_amount})
            <button onClick={() => loadLoanForEdit(loan)}>Edit</button>
            <button onClick={() => deleteLoan(loan.loan_number)}>Delete</button>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default HomeLoan;

// Main JavaScript for DU Payroll System

document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });

    // Confirm delete actions
    const deleteButtons = document.querySelectorAll('.btn-danger[data-confirm]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm(this.dataset.confirm || 'Are you sure?')) {
                e.preventDefault();
            }
        });
    });

    // Auto-calculate payroll totals
    const payrollForm = document.querySelector('form[action*="payroll"]');
    if (payrollForm) {
        const earningsInputs = payrollForm.querySelectorAll('input[name*="allowance"], input[name*="salary"], input[name*="overtime"], input[name*="bonus"]');
        const deductionsInputs = payrollForm.querySelectorAll('input[name*="deducted"], input[name*="fund"], input[name*="gratuity"], input[name*="deduction"]');
        
        function calculateTotals() {
            let totalEarnings = 0;
            let totalDeductions = 0;
            
            earningsInputs.forEach(input => {
                totalEarnings += parseFloat(input.value) || 0;
            });
            
            deductionsInputs.forEach(input => {
                totalDeductions += parseFloat(input.value) || 0;
            });
            
            const netPay = totalEarnings - totalDeductions;
            
            // Update display if elements exist
            const grossDisplay = document.getElementById('gross-display');
            const deductionsDisplay = document.getElementById('deductions-display');
            const netDisplay = document.getElementById('net-display');
            
            if (grossDisplay) grossDisplay.textContent = totalEarnings.toFixed(2);
            if (deductionsDisplay) deductionsDisplay.textContent = totalDeductions.toFixed(2);
            if (netDisplay) netDisplay.textContent = netPay.toFixed(2);
        }
        
        earningsInputs.forEach(input => input.addEventListener('input', calculateTotals));
        deductionsInputs.forEach(input => input.addEventListener('input', calculateTotals));
    }

    // Print functionality
    const printButtons = document.querySelectorAll('.btn-print');
    printButtons.forEach(button => {
        button.addEventListener('click', function() {
            window.print();
        });
    });

    // Search functionality
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const tableRows = document.querySelectorAll('.data-table tbody tr');
            
            tableRows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        });
    }

    // Date validation
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => {
        input.addEventListener('change', function() {
            const startDate = new Date(this.value);
            const endDateInput = document.getElementById('end-date');
            
            if (endDateInput && this.id === 'start-date') {
                const endDate = new Date(endDateInput.value);
                if (endDate < startDate) {
                    alert('End date cannot be before start date');
                    endDateInput.value = '';
                }
            }
        });
    });

    // Form validation enhancement
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.style.borderColor = 'var(--danger-color)';
                } else {
                    field.style.borderColor = '#ced4da';
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                alert('Please fill in all required fields');
            }
        });
    });

    // Export to CSV
    const exportButtons = document.querySelectorAll('.btn-export');
    exportButtons.forEach(button => {
        button.addEventListener('click', function() {
            const table = document.querySelector('.data-table');
            if (!table) return;
            
            let csv = [];
            const rows = table.querySelectorAll('tr');
            
            rows.forEach(row => {
                const cols = row.querySelectorAll('td, th');
                const rowData = [];
                cols.forEach(col => {
                    rowData.push('"' + col.textContent.replace(/"/g, '""') + '"');
                });
                csv.push(rowData.join(','));
            });
            
            const csvContent = csv.join('\n');
            const blob = new Blob([csvContent], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'du_payroll_export.csv';
            a.click();
            window.URL.revokeObjectURL(url);
        });
    });

    console.log('DU Payroll System initialized');
});

// Utility functions
function formatCurrency(amount) {
    return '৳' + parseFloat(amount).toFixed(2);
}

function formatDate(dateString) {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('en-BD', options);
}

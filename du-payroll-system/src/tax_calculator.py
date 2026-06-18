"""
Bangladesh Tax Calculator Module
Implements tax calculations based on Bangladesh Income Tax Act and National Pay Scale
"""

from datetime import date


class BangladeshTaxCalculator:
    """
    Calculate income tax according to Bangladesh tax laws
    Supports gender-based rebates, age-based rebates, and investment rebates
    """
    
    # Tax slabs for FY 2023-2024 (Individual)
    TAX_SLABS = [
        (3000000, 0.0),      # First 30 lakh: 0%
        (1000000, 0.05),     # Next 10 lakh: 5%
        (1000000, 0.10),     # Next 10 lakh: 10%
        (1000000, 0.15),     # Next 10 lakh: 15%
        (1000000, 0.20),     # Next 10 lakh: 20%
        (float('inf'), 0.25) # Above 70 lakh: 25%
    ]
    
    # Minimum tax amount
    MINIMUM_TAX = 5000  # ৳5,000 minimum tax
    
    # Investment rebate percentage
    INVESTMENT_REBATE_PERCENT = 0.25  # 25% of investment
    MAX_INVESTMENT_REBATE = 1500000  # Maximum ৳15 lakh rebate
    
    # Gender-based additional tax-free allowance
    FEMALE_TAX_FREE_ALLOWANCE = 50000  # Additional ৳50,000 for female taxpayers
    
    # Age-based additional allowances
    SENIOR_CITIZON_AGE = 65
    SENIOR_CITIZEN_ALLOWANCE = 50000  # Additional ৳50,000 for senior citizens (65+)
    
    def __init__(self):
        pass
    
    def calculate_annual_tax(self, annual_income, gender='male', age=30, 
                            investment_amount=0, is_freedom_fighter=False):
        """
        Calculate annual income tax based on Bangladesh tax laws
        
        Args:
            annual_income: Total annual gross income in BDT
            gender: 'male' or 'female'
            age: Age of the taxpayer
            investment_amount: Total eligible investment (DPS, insurance, etc.)
            is_freedom_fighter: Boolean for freedom fighter status
            
        Returns:
            dict: Tax calculation details
        """
        taxable_income = annual_income
        
        # Apply additional tax-free allowances
        tax_free_allowance = 0
        
        # Female taxpayer allowance
        if gender == 'female':
            tax_free_allowance += self.FEMALE_TAX_FREE_ALLOWANCE
        
        # Senior citizen allowance
        if age >= self.SENIOR_CITIZON_AGE:
            tax_free_allowance += self.SENIOR_CITIZEN_ALLOWANCE
        
        # Freedom fighter allowance (additional benefit)
        if is_freedom_fighter:
            tax_free_allowance += 100000  # Additional ৳1 lakh
        
        # Calculate taxable income after allowances
        taxable_income = max(0, annual_income - tax_free_allowance)
        
        # Calculate investment rebate
        investment_rebate = min(
            investment_amount * self.INVESTMENT_REBATE_PERCENT,
            self.MAX_INVESTMENT_REBATE
        )
        
        # Calculate tax based on slabs
        tax = 0
        remaining_income = taxable_income
        slab_details = []
        
        for slab_limit, rate in self.TAX_SLABS:
            if remaining_income <= 0:
                break
            
            taxable_in_slab = min(remaining_income, slab_limit)
            tax_in_slab = taxable_in_slab * rate
            
            if rate > 0:  # Only add non-zero slabs to details
                slab_details.append({
                    'slab_range': f"Up to ৳{slab_limit:,.0f}" if slab_limit != float('inf') else "Above",
                    'rate': f"{rate*100:.0f}%",
                    'taxable_amount': taxable_in_slab,
                    'tax': tax_in_slab
                })
            
            tax += tax_in_slab
            remaining_income -= slab_limit
        
        # Apply investment rebate
        rebate_applied = min(investment_rebate, tax)
        tax_after_rebate = tax - rebate_applied
        
        # Apply minimum tax
        final_tax = max(tax_after_rebate, self.MINIMUM_TAX) if annual_income > 3000000 else 0
        
        # If income is below tax-free threshold, no tax
        if annual_income <= 3000000 + tax_free_allowance:
            final_tax = 0
        
        return {
            'annual_income': annual_income,
            'tax_free_allowance': tax_free_allowance,
            'taxable_income': taxable_income,
            'investment_rebate': rebate_applied,
            'gross_tax': tax,
            'final_tax': final_tax,
            'monthly_tax': final_tax / 12,
            'slab_details': slab_details,
            'effective_tax_rate': (final_tax / annual_income * 100) if annual_income > 0 else 0
        }
    
    def calculate_monthly_tax(self, monthly_salary, month_number=1, gender='male', 
                             age=30, investment_monthly=0, is_freedom_fighter=False,
                             bonus_this_month=0):
        """
        Calculate monthly tax with consideration for annual projection
        
        Args:
            monthly_salary: Monthly basic salary + allowances
            month_number: Current month (1-12)
            gender: 'male' or 'female'
            age: Age of the taxpayer
            investment_monthly: Monthly investment amount
            is_freedom_fighter: Boolean for freedom fighter status
            bonus_this_month: Any bonus received this month
            
        Returns:
            dict: Monthly tax calculation details
        """
        # Project annual income
        months_remaining = 12 - month_number
        projected_annual_salary = (monthly_salary * month_number) + (monthly_salary * months_remaining)
        projected_annual_bonus = bonus_this_month + (0 * months_remaining)  # Only current bonus
        
        total_projected_income = projected_annual_salary + projected_annual_bonus
        total_projected_investment = investment_monthly * 12
        
        # Calculate annual tax on projected income
        annual_tax_result = self.calculate_annual_tax(
            total_projected_income,
            gender=gender,
            age=age,
            investment_amount=total_projected_investment,
            is_freedom_fighter=is_freedom_fighter
        )
        
        # Calculate cumulative tax up to current month
        cumulative_tax = (annual_tax_result['final_tax'] / 12) * month_number
        
        # Calculate tax deducted so far (would need historical data in real implementation)
        # For simplicity, we'll return the monthly amount
        monthly_tax_due = annual_tax_result['final_tax'] / 12
        
        return {
            'monthly_salary': monthly_salary,
            'month_number': month_number,
            'projected_annual_income': total_projected_income,
            'monthly_tax': monthly_tax_due,
            'cumulative_tax': cumulative_tax,
            'annual_tax_projection': annual_tax_result['final_tax'],
            'details': annual_tax_result
        }
    
    def get_tax_slab_info(self):
        """Return current tax slab information"""
        return {
            'slabs': self.TAX_SLABS,
            'minimum_tax': self.MINIMUM_TAX,
            'female_allowance': self.FEMALE_TAX_FREE_ALLOWANCE,
            'senior_citizen_allowance': self.SENIOR_CITIZEN_ALLOWANCE,
            'investment_rebate_percent': self.INVESTMENT_REBATE_PERCENT,
            'max_investment_rebate': self.MAX_INVESTMENT_REBATE
        }


def calculate_tax_for_payroll(employee, payroll_record, month_number=None):
    """
    Convenience function to calculate tax for a payroll record
    
    Args:
        employee: Employee model instance
        payroll_record: Payroll model instance
        month_number: Month number (1-12), defaults to payroll_record.month
        
    Returns:
        float: Monthly tax amount to deduct
    """
    if month_number is None:
        month_number = payroll_record.month
    
    calculator = BangladeshTaxCalculator()
    
    # Determine gender from employee name/title (simplified)
    # In production, this should be a field in Employee model
    gender = 'male'  # Default
    if hasattr(employee, 'gender'):
        gender = employee.gender
    
    # Calculate age from date of birth
    age = 30  # Default
    if hasattr(employee, 'date_of_birth') and employee.date_of_birth:
        today = date.today()
        age = today.year - employee.date_of_birth.year
        if (today.month, today.day) < (employee.date_of_birth.month, employee.date_of_birth.day):
            age -= 1
    
    # Calculate monthly gross salary
    monthly_gross = (
        payroll_record.basic_salary +
        payroll_record.house_rent_allowance +
        payroll_record.medical_allowance +
        payroll_record.transport_allowance +
        payroll_record.other_allowances
    )
    
    # Assume 10% of basic salary as monthly investment (DPS, insurance, etc.)
    monthly_investment = payroll_record.basic_salary * 0.10
    
    # Calculate tax
    tax_result = calculator.calculate_monthly_tax(
        monthly_salary=monthly_gross,
        month_number=month_number,
        gender=gender,
        age=age,
        investment_monthly=monthly_investment,
        bonus_this_month=payroll_record.bonus
    )
    
    return tax_result['monthly_tax']


# Example usage and testing
if __name__ == '__main__':
    calculator = BangladeshTaxCalculator()
    
    print("=" * 60)
    print("BANGLADESH TAX CALCULATOR - DEMO")
    print("=" * 60)
    
    # Test case 1: Male employee, 35 years, 50,000 monthly salary
    print("\nTest Case 1: Male, 35 years, ৳50,000/month")
    result = calculator.calculate_monthly_tax(50000, month_number=1, gender='male', age=35)
    print(f"Projected Annual Income: ৳{result['projected_annual_income']:,.2f}")
    print(f"Monthly Tax: ৳{result['monthly_tax']:,.2f}")
    print(f"Annual Tax: ৳{result['annual_tax_projection']:,.2f}")
    
    # Test case 2: Female employee, 40 years, 80,000 monthly salary
    print("\nTest Case 2: Female, 40 years, ৳80,000/month")
    result = calculator.calculate_monthly_tax(80000, month_number=1, gender='female', age=40)
    print(f"Projected Annual Income: ৳{result['projected_annual_income']:,.2f}")
    print(f"Monthly Tax: ৳{result['monthly_tax']:,.2f}")
    print(f"Annual Tax: ৳{result['annual_tax_projection']:,.2f}")
    
    # Test case 3: Senior citizen, 67 years, 100,000 monthly salary
    print("\nTest Case 3: Senior Citizen (67), ৳100,000/month")
    result = calculator.calculate_monthly_tax(100000, month_number=1, gender='male', age=67)
    print(f"Projected Annual Income: ৳{result['projected_annual_income']:,.2f}")
    print(f"Monthly Tax: ৳{result['monthly_tax']:,.2f}")
    print(f"Annual Tax: ৳{result['annual_tax_projection']:,.2f}")
    
    print("\n" + "=" * 60)

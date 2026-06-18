"""
PDF Payslip Generator for Dhaka University Payroll System
Generates professional PDF payslips with DU branding
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from datetime import datetime
import io
import os


class DUPayslipGenerator:
    """Generate professional PDF payslips for Dhaka University"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_styles()
        
    def setup_styles(self):
        """Custom styles for DU payslip"""
        # University title style
        self.styles.add(ParagraphStyle(
            name='UniversityTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=5,
            fontName='Helvetica-Bold'
        ))
        
        # Payslip title
        self.styles.add(ParagraphStyle(
            name='PayslipTitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            alignment=TA_CENTER,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        ))
        
        # Section headers
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Normal'],
            fontSize=11,
            fontName='Helvetica-Bold',
            spaceAfter=5,
            textColor=colors.darkblue
        ))
        
        # Normal text
        self.styles.add(ParagraphStyle(
            name='NormalText',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=3
        ))
        
        # Right aligned for amounts
        self.styles.add(ParagraphStyle(
            name='AmountRight',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_RIGHT
        ))
        
        # Center aligned
        self.styles.add(ParagraphStyle(
            name='CenterText',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER
        ))
        
        # Signature style
        self.styles.add(ParagraphStyle(
            name='Signature',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            spaceBefore=30,
            fontName='Helvetica-Bold'
        ))
    
    def generate_payslip(self, payroll_record, employee, output_path=None):
        """
        Generate PDF payslip for a payroll record
        
        Args:
            payroll_record: Payroll model instance
            employee: Employee model instance
            output_path: Optional file path to save PDF
            
        Returns:
            bytes: PDF content if no output_path, else None
        """
        # Create document
        if output_path:
            doc = SimpleDocTemplate(output_path, pagesize=A4,
                                   rightMargin=0.5*inch,
                                   leftMargin=0.5*inch,
                                   topMargin=0.5*inch,
                                   bottomMargin=0.5*inch)
        else:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4,
                                   rightMargin=0.5*inch,
                                   leftMargin=0.5*inch,
                                   topMargin=0.5*inch,
                                   bottomMargin=0.5*inch)
        
        story = []
        
        # University Header
        story.append(Paragraph("University of Dhaka", self.styles['UniversityTitle']))
        story.append(Paragraph("Dhaka-1000, Bangladesh", self.styles['CenterText']))
        story.append(Paragraph("Office of the Controller of Accounts", self.styles['SectionHeader']))
        story.append(Spacer(1, 0.2*inch))
        
        # Payslip Title
        story.append(Paragraph("PAYSLIP", self.styles['PayslipTitle']))
        story.append(Paragraph(f"For the month of {payroll_record.month_name} {payroll_record.year}", 
                              self.styles['CenterText']))
        story.append(Spacer(1, 0.2*inch))
        
        # Employee Information Table
        emp_info_data = [
            ['Employee Name:', employee.full_name, 'Employee ID:', employee.employee_id],
            ['Designation:', employee.designation, 'Department:', employee.department],
            ['Bank Name:', employee.bank_name or 'N/A', 'Account No:', employee.bank_account_number or 'N/A'],
            ['Payment Date:', payroll_record.payment_date.strftime('%d %B, %Y') if payroll_record.payment_date else 'Pending', 
             'Status:', payroll_record.payment_status.upper()]
        ]
        
        emp_table = Table(emp_info_data, colWidths=[1.5*inch, 2.5*inch, 1.5*inch, 2.5*inch])
        emp_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))
        story.append(emp_table)
        story.append(Spacer(1, 0.2*inch))
        
        # Earnings Section
        story.append(Paragraph("EARNINGS", self.styles['SectionHeader']))
        earnings_data = [
            ['Description', 'Amount (BDT)'],
            ['Basic Salary', f"{payroll_record.basic_salary:,.2f}"],
            ['House Rent Allowance', f"{payroll_record.house_rent_allowance:,.2f}"],
            ['Medical Allowance', f"{payroll_record.medical_allowance:,.2f}"],
            ['Transport Allowance', f"{payroll_record.transport_allowance:,.2f}"],
            ['Other Allowances', f"{payroll_record.other_allowances:,.2f}"],
            ['Overtime Pay', f"{payroll_record.overtime_pay:,.2f}"],
            ['Bonus', f"{payroll_record.bonus:,.2f}"],
            ['<b>Gross Earnings</b>', f"<b>{payroll_record.gross_pay:,.2f}</b>"]
        ]
        
        earnings_table = Table(earnings_data, colWidths=[4*inch, 2*inch])
        earnings_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('BACKGROUND', (-2, -1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
            ('LINEBELOW', (0, -2), (-1, -2), 1.5, colors.black)
        ]))
        story.append(earnings_table)
        story.append(Spacer(1, 0.2*inch))
        
        # Deductions Section
        story.append(Paragraph("DEDUCTIONS", self.styles['SectionHeader']))
        deductions_data = [
            ['Description', 'Amount (BDT)'],
            ['Income Tax', f"{payroll_record.tax_deducted:,.2f}"],
            ['Provident Fund', f"{payroll_record.provident_fund:,.2f}"],
            ['Gratuity', f"{payroll_record.gratuity:,.2f}"],
            ['Loan Deduction', f"{payroll_record.loan_deduction:,.2f}"],
            ['Other Deductions', f"{payroll_record.other_deductions:,.2f}"],
            ['<b>Total Deductions</b>', f"<b>{payroll_record.total_deductions:,.2f}</b>"]
        ]
        
        deductions_table = Table(deductions_data, colWidths=[4*inch, 2*inch])
        deductions_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('BACKGROUND', (-2, -1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
            ('LINEBELOW', (0, -2), (-1, -2), 1.5, colors.black)
        ]))
        story.append(deductions_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Net Salary
        net_salary_data = [
            ['<b>NET SALARY PAYABLE</b>', f"<b>৳ {payroll_record.net_pay:,.2f}</b>"],
            ['', f"(Bangladeshi Taka {self.number_to_words(int(payroll_record.net_pay))} Only)"]
        ]
        
        net_table = Table(net_salary_data, colWidths=[4*inch, 2*inch])
        net_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.9, 0.95, 0.9)),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))
        story.append(net_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Additional Information
        story.append(Paragraph("IMPORTANT NOTES:", self.styles['SectionHeader']))
        notes = [
            "• This is a computer-generated payslip and does not require a physical signature.",
            "• Please verify all details and report discrepancies to the Accounts Office within 7 days.",
            "• Keep this payslip for your records and future reference.",
            f"• Generated on: {datetime.now().strftime('%d %B, %Y at %I:%M %p')}"
        ]
        for note in notes:
            story.append(Paragraph(note, self.styles['NormalText']))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Signature Block
        signature_data = [
            ['_____________________', '_____________________'],
            ['Controller of Accounts', 'Registrar'],
            ['University of Dhaka', 'University of Dhaka']
        ]
        
        sig_table = Table(signature_data, colWidths=[3*inch, 3*inch])
        sig_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, 0), 20),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5)
        ]))
        story.append(sig_table)
        
        # Footer
        story.append(Spacer(1, 0.3*inch))
        footer = Paragraph(
            "<i>University of Dhaka - Established 1921 | www.du.ac.bd | Phone: +88-02-9661900</i>",
            self.styles['CenterText']
        )
        story.append(footer)
        
        # Build PDF
        doc.build(story)
        
        if output_path:
            return None
        else:
            buffer.seek(0)
            return buffer.getvalue()
    
    def number_to_words(self, n):
        """Convert number to words (for BDT amount)"""
        if n == 0:
            return "Zero"
        
        ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
        teens = ["Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", 
                "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
        tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
        
        def two_digits(num):
            if num < 10:
                return ones[num]
            elif num < 20:
                return teens[num - 10]
            else:
                ten_digit = num // 10
                one_digit = num % 10
                if one_digit == 0:
                    return tens[ten_digit]
                else:
                    return tens[ten_digit] + " " + ones[one_digit]
        
        def three_digits(num):
            hundreds = num // 100
            remainder = num % 100
            if hundreds == 0:
                return two_digits(remainder) if remainder > 0 else ""
            elif remainder == 0:
                return ones[hundreds] + " Hundred"
            else:
                return ones[hundreds] + " Hundred " + two_digits(remainder)
        
        result = ""
        
        # Crores (10^7)
        crores = n // 10000000
        if crores > 0:
            result += two_digits(crores) + " Crore "
            n %= 10000000
        
        # Lakhs (10^5)
        lakhs = n // 100000
        if lakhs > 0:
            result += two_digits(lakhs) + " Lakh "
            n %= 100000
        
        # Thousands
        thousands = n // 1000
        if thousands > 0:
            result += three_digits(thousands) + " Thousand "
            n %= 1000
        
        # Hundreds
        hundreds = n // 100
        if hundreds > 0:
            result += three_digits(hundreds * 100) + " "
            n %= 100
        
        # Remaining
        if n > 0:
            result += two_digits(n)
        
        return result.strip()


def generate_payslip_pdf(payroll_record, employee, output_path=None):
    """
    Convenience function to generate payslip PDF
    
    Args:
        payroll_record: Payroll model instance
        employee: Employee model instance
        output_path: Optional file path to save PDF
        
    Returns:
        bytes: PDF content if no output_path, else None
    """
    generator = DUPayslipGenerator()
    return generator.generate_payslip(payroll_record, employee, output_path)

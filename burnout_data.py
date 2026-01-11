import pandas as pd
import numpy as np
import random

# Configuration
departments = {
    'Engineering': ['Backend', 'Frontend', 'DevOps', 'QA', 'Data Science'],
    'HR': ['Recruiting', 'Employee Relations', 'Payroll'],
    'Sales': ['Enterprise', 'SMB', 'Business Development'],
    'Marketing': ['Content', 'SEO', 'Social Media', 'Product Marketing'],
    'Finance': ['Accounting', 'FP&A', 'Tax']
}

# Helper to generate names
first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth", 
               "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen"]
last_names = ["Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson", "Moore", "Taylor", 
              "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin", "Thompson", "Garcia", "Martinez", "Robinson"]

def generate_name():
    return f"{random.choice(first_names)} {random.choice(last_names)}"

data = []

# Generate Data
for dept, teams in departments.items():
    for team in teams:
        # Random number of employees per team (5 to 15)
        num_employees = random.randint(5, 15)
        
        for _ in range(num_employees):
            name = generate_name()
            emp_id = f"EMP{random.randint(1000, 9999)}"
            
            # Simulate metrics
            base_hours = 40
            
            # Overtime: skewed so some work harder
            overtime = max(0, int(np.random.normal(5, 10))) 
            total_hours = base_hours + overtime
            
            # Projects completed
            projects_done = random.randint(1, 10)
            
            # Efficiency (Days saved per project avg). Positive = Early, Negative = Late.
            efficiency = np.round(np.random.normal(0.5, 2) + (overtime * 0.05), 1)
            
            # Value Score: Weighted sum of productivity
            value_score = (projects_done * 10) + (efficiency * 5) + (overtime * 2)
            value_score = round(value_score, 1)
            
            data.append([emp_id, name, dept, team, total_hours, overtime, projects_done, efficiency, value_score])

# Create DataFrame
columns = ['Employee_ID', 'Name', 'Department', 'Sub_Team', 'Total_Weekly_Hours', 'Overtime_Hours', 'Projects_Completed', 'Avg_Days_Early', 'Value_Score']
df = pd.DataFrame(data, columns=columns)

# Save to CSV
df.to_csv('burnout_data.csv', index=False)
print("Dataset Generated Successfully")
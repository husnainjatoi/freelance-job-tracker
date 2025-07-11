import pandas as pd
from datetime import datetime
import os
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

class FreelanceJobTracker:
    def __init__(self, data_file='freelance_jobs.csv'):
        self.data_file = data_file
        self.jobs = self.load_data()
        
    def load_data(self):
        """Load job data from CSV file or create new DataFrame if file doesn't exist"""
        if os.path.exists(self.data_file):
            df = pd.read_csv(self.data_file, parse_dates=['deadline', 'date_added'])

            if 'paid' in df.columns:
                df['paid'] = df['paid'].astype(bool)
            return df
        else:
            return pd.DataFrame(columns=[
                'client_name', 'project_name', 'rate', 'paid', 
                'deadline', 'date_added', 'hours', 'notes'
            ])
    
    def save_data(self):
        """Save job data to CSV file"""
        print(f"Saving to: {os.path.abspath(self.data_file)}")
        self.jobs.to_csv(self.data_file, index=False)
    
    def add_job(self, client_name, project_name, rate, deadline, hours=None, notes=None):
        """Add a new freelance job to the tracker"""
        new_job = {
            'client_name': client_name,
            'project_name': project_name,
            'rate': float(rate),
            'paid': False,
            'deadline': pd.to_datetime(deadline),
            'date_added': datetime.now(),
            'hours': float(hours) if hours else None,
            'notes': notes
        }
        
        self.jobs = pd.concat([self.jobs, pd.DataFrame([new_job])], ignore_index=True)
        self.save_data()
        print(f"Job '{project_name}' for client '{client_name}' added successfully.")
    
    def mark_as_paid(self, project_name):
        """Mark a job as paid"""
        if project_name in self.jobs['project_name'].values:
            self.jobs.loc[self.jobs['project_name'] == project_name, 'paid'] = True
            self.save_data()
            print(f"Job '{project_name}' marked as paid.")
        else:
            print(f"Job '{project_name}' not found.")
    
    def list_jobs(self, filter_unpaid=False, upcoming_deadlines=None):
        """List all jobs, with optional filters"""
        df = self.jobs.copy()
        
        if filter_unpaid:
            df = df[df['paid'] == False]
        
        if upcoming_deadlines:
            today = datetime.now()
            df = df[df['deadline'] <= today + pd.Timedelta(days=upcoming_deadlines)]
            df = df[df['deadline'] >= today]
        
        if df.empty:
            print("No jobs found matching the criteria.")
        else:
            if 'hours' in df.columns and 'rate' in df.columns:
                df['estimated_pay'] = df['hours'] * df['rate']
            
            df['deadline'] = df['deadline'].dt.strftime('%Y-%m-%d')
            df['date_added'] = df['date_added'].dt.strftime('%Y-%m-%d')
            
            print(df.to_string(index=False))
    
    def get_stats(self):
        """Display statistics about freelance jobs"""
        if self.jobs.empty:
            print("No jobs in the tracker yet.")
            return
        
        total_jobs = len(self.jobs)
        paid_jobs = self.jobs['paid'].sum()
        unpaid_jobs = total_jobs - paid_jobs
        
        total_earnings = 0
        if 'hours' in self.jobs.columns and 'rate' in self.jobs.columns:
            paid_with_hours = self.jobs[self.jobs['paid']]
            total_earnings = (paid_with_hours['hours'] * paid_with_hours['rate']).sum()
        
        potential_earnings = 0
        if 'hours' in self.jobs.columns and 'rate' in self.jobs.columns:
            unpaid_with_hours = self.jobs[~self.jobs['paid']]
            potential_earnings = (unpaid_with_hours['hours'] * unpaid_with_hours['rate']).sum()
        
        print("\nFreelance Job Statistics:")
        print(f"Total Jobs: {total_jobs}")
        print(f"Paid Jobs: {paid_jobs}")
        print(f"Unpaid Jobs: {unpaid_jobs}")
        print(f"Total Earnings: ${total_earnings:.2f}")
        print(f"Potential Earnings: ${potential_earnings:.2f}")
        
        today = datetime.now()
        upcoming = self.jobs[
            (self.jobs['deadline'] <= today + pd.Timedelta(days=7)) & 
            (self.jobs['deadline'] >= today)
        ]
        
        if not upcoming.empty:
            print("\nUpcoming Deadlines (next 7 days):")
            for _, job in upcoming.iterrows():
                print(f"{job['project_name']} for {job['client_name']}")
                print(f"  Deadline: {job['deadline'].strftime('%Y-%m-%d')}")
                if job['hours'] and job['rate']:
                    print(f"  Estimated Pay: ${job['hours'] * job['rate']:.2f}")
                print()
    
    def edit_job(self, project_name, **kwargs):
        """Edit details of an existing job"""
        if project_name not in self.jobs['project_name'].values:
            print(f"Job '{project_name}' not found.")
            return
        
        valid_columns = set(self.jobs.columns)
        valid_updates = {k: v for k, v in kwargs.items() if k in valid_columns}
        
        if not valid_updates:
            print("No valid fields provided for update.")
            return
        
        for col, value in valid_updates.items():

            if col == 'deadline':
                value = pd.to_datetime(value)
            elif col in ['rate', 'hours']:
                value = float(value)
            elif col == 'paid':
                value = bool(value)
            
            self.jobs.loc[self.jobs['project_name'] == project_name, col] = value
        
        self.save_data()
        print(f"Job '{project_name}' updated successfully.")
    
    def generate_earnings_chart(self):
        """Generate a bar chart of monthly earnings"""
        if self.jobs.empty:
            print("No jobs in the tracker yet.")
            return
        
        paid_jobs = self.jobs[(self.jobs['paid']) & (self.jobs['hours'].notna()) & (self.jobs['rate'].notna())]
        
        if paid_jobs.empty:
            print("No paid jobs with hours and rate information available.")
            return
        
        paid_jobs = paid_jobs.copy()
        paid_jobs['earnings'] = paid_jobs['hours'] * paid_jobs['rate']
        
        paid_jobs['month_year'] = paid_jobs['date_added'].dt.to_period('M')
        
        monthly_earnings = paid_jobs.groupby('month_year')['earnings'].sum().reset_index()
        monthly_earnings['month_year'] = monthly_earnings['month_year'].astype(str)
        
        if monthly_earnings.empty:
            print("No monthly earnings data available.")
            return
        
        plt.figure(figsize=(10, 6))
        bars = plt.bar(monthly_earnings['month_year'], monthly_earnings['earnings'], color='green')
        
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'${height:.2f}',
                    ha='center', va='bottom')
        
        plt.title('Monthly Earnings from Freelance Jobs')
        plt.xlabel('Month')
        plt.ylabel('Earnings ($)')
        plt.xticks(rotation=45)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))
        
        plt.tight_layout()
        plt.show()

def main():
    tracker = FreelanceJobTracker()
    
    while True:
        print("\nFreelance Job Tracker Menu:")
        print("1. Add a new job")
        print("2. List all jobs")
        print("3. List unpaid jobs")
        print("4. List upcoming deadlines")
        print("5. Mark job as paid")
        print("6. View statistics")
        print("7. Edit a job")
        print("8. View monthly earnings chart")
        print("9. Exit")
        
        choice = input("Enter your choice (1-9): ")
        
        if choice == '1':
            print("\nAdd New Job")
            client_name = input("Client name: ")
            project_name = input("Project name: ")
            rate = input("Rate per hour: $")
            deadline = input("Deadline (YYYY-MM-DD): ")
            hours = input("Estimated hours (leave blank if unknown): ")
            notes = input("Notes (optional): ")
            
            tracker.add_job(
                client_name=client_name,
                project_name=project_name,
                rate=rate,
                deadline=deadline,
                hours=hours if hours else None,
                notes=notes if notes else None
            )
        
        elif choice == '2':
            print("\nAll Jobs:")
            tracker.list_jobs()
        
        elif choice == '3':
            print("\nUnpaid Jobs:")
            tracker.list_jobs(filter_unpaid=True)
        
        elif choice == '4':
            print("\nUpcoming Deadlines (next 7 days):")
            tracker.list_jobs(upcoming_deadlines=7)
        
        elif choice == '5':
            project_name = input("Enter project name to mark as paid: ")
            tracker.mark_as_paid(project_name)
        
        elif choice == '6':
            tracker.get_stats()
        
        elif choice == '7':
            project_name = input("Enter project name to edit: ")
            
            print("\nLeave blank to keep current value")
            client_name = input(f"New client name: ")
            rate = input("New rate per hour: $")
            deadline = input("New deadline (YYYY-MM-DD): ")
            hours = input("New estimated hours: ")
            paid = input("Paid? (yes/no): ")
            notes = input("New notes: ")
            
            updates = {}
            if client_name: updates['client_name'] = client_name
            if rate: updates['rate'] = rate
            if deadline: updates['deadline'] = deadline
            if hours: updates['hours'] = hours
            if paid.lower() == 'yes': updates['paid'] = True
            if paid.lower() == 'no': updates['paid'] = False
            if notes: updates['notes'] = notes
            
            if updates:
                tracker.edit_job(project_name, **updates)
            else:
                print("No changes made.")
        
        elif choice == '8':
            tracker.generate_earnings_chart()
        
        elif choice == '9':
            print("Exiting Freelance Job Tracker. Goodbye!")
            break
        
        else:
            print("Invalid choice. Please enter a number between 1 and 9.")

if __name__ == "__main__":
    main()
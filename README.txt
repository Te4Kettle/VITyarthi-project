VIT-Yarthi Student Grade Management System


VIT-Yarthi is a Python-based Student Grade Management System with a clean and intuitive GUI built using Tkinter. It helps teachers and administrators easily manage student records, calculate grades, and visualize performance through charts and reports. The system is designed to be simple, reliable, and robust, even handling corrupted or missing student data files automatically.


Key Features
1.CRUD Operations

    Add / Update: Quickly add new students or update existing records with Roll Number, Name, and Marks.

    Delete: Remove student records safely.

    Search & Sort: Find students by Roll Number or Name and sort records by Roll, Name, or Marks.

2.Automatic Grade Calculation

    Grades are calculated based on marks:

    S: 90–100

    A: 80–89

    B: 70–79

    C: 60–69

    D: 50–59

    E: 40–49

    N: Below 40 (Fail)

3.Data Export

    CSV Export: Save student records in CSV format for sharing.

    PDF Report: Generate detailed PDF reports with statistics and charts. Logos can also be added.

4.Visualizations

    Line Chart: Shows marks by rank.

    Bar Chart: Displays marks for each student with Roll Number and Name labels.

    Pie Chart: Shows grade distribution among students.

    Charts are interactive and easy to read.

5.Theme Support

    Switch between light and dark themes for better visibility in different environments.

6.Robust and Safe

    Auto-repairs corrupted or missing students.json files.

    Validates input marks and normalizes data for consistency.

7.Dependencies

    Python 3.x

    Tkinter (GUI)

    Matplotlib (Charts)

    ReportLab (PDF Reports)

    Pillow (Image/Logo support)  ------------> (Didnt Included yet)

8.Install dependencies with:

    pip install matplotlib reportlab pillow


9.How to Use

    Run Student-Grade-Management-System.py.

    Use the left panel to add, update, delete, or search student records.

    Export data as CSV or PDF.

    View charts to analyze student performance visually.

    Toggle between light and dark themes using the button.

    

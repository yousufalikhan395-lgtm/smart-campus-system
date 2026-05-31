from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
import os
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import base64
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'smart_campus_secret_2026'

# In-memory storage (use database in production)
students_db = []
courses_db = {}
student_records = [
    {"name": "Alice", "age": 20, "grades": [85, 90, 88]},
    {"name": "Bob", "age": 21, "grades": [78, 82, 80]},
    {"name": "Charlie", "age": 19, "grades": [92, 95, 91]}
]

# ============ Q1: Student Registration & Grade Evaluation ============
def get_grade(score):
    if score > 90:
        return {"grade": "A", "remark": "Excellent"}
    elif score >= 80:
        return {"grade": "B", "remark": "Very Good"}
    elif score >= 70:
        return {"grade": "C", "remark": "Good"}
    elif score >= 60:
        return {"grade": "D", "remark": "Average"}
    else:
        return {"grade": "E", "remark": "FAIL!"}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/q1', methods=['GET', 'POST'])
def q1_registration():
    result = None
    if request.method == 'POST':
        name = request.form.get('name')
        try:
            score = int(request.form.get('score'))
            if 0 <= score <= 100:
                result = {"name": name, "score": score, **get_grade(score)}
                students_db.append({"name": name, "score": score, **get_grade(score)})
            else:
                flash("Error: Score must be between 0 and 100", "danger")
        except ValueError:
            flash("Invalid input. Score must be a number.", "danger")
    return render_template('q1_registration.html', result=result)

# ============ Q2: Course Enrollment Management ============
@app.route('/q2', methods=['GET', 'POST'])
def q2_enrollment():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'enroll':
            course_name = request.form.get('course_name').strip()
            try:
                credit = int(request.form.get('credit'))
                if course_name and credit > 0:
                    courses_db[course_name] = credit
                    flash(f"✓ Enrolled in {course_name} ({credit} credits)", "success")
                else:
                    flash("Invalid course name or credit value", "danger")
            except ValueError:
                flash("Credit must be a number", "danger")
        elif action == 'clear':
            courses_db.clear()
            flash("All courses cleared", "info")
    return render_template('q2_enrollment.html', courses=courses_db)

# ============ Q3: Student Record Data Management ============
@app.route('/q3')
def q3_records():
    event1 = {"Alice", "Bob", "David"}
    event2 = {"Alice", "Bob", "Charlie"}
    common = event1.intersection(event2)
    return render_template('q3_records.html', 
                         records=student_records,
                         event1=event1, 
                         event2=event2, 
                         common=common)

# ============ Q4: Sorting & Searching Student IDs ============
@app.route('/q4', methods=['GET', 'POST'])
def q4_sorting():
    result = {}
    if request.method == 'POST':
        ids_input = request.form.get('student_ids')
        search_id = request.form.get('search_id')
        try:
            student_ids = [int(x.strip()) for x in ids_input.split(',') if x.strip()]
            original = student_ids.copy()
            
            # Bubble Sort
            sorted_ids = student_ids.copy()
            for i in range(len(sorted_ids)):
                for j in range(0, len(sorted_ids) - i - 1):
                    if sorted_ids[j] > sorted_ids[j + 1]:
                        sorted_ids[j], sorted_ids[j + 1] = sorted_ids[j + 1], sorted_ids[j]
            
            # Linear Search
            linear_pos = None
            for i, sid in enumerate(sorted_ids):
                if sid == int(search_id):
                    linear_pos = i + 1
                    break
            
            # Binary Search
            binary_pos = None
            low, high = 0, len(sorted_ids) - 1
            while low <= high:
                mid = (low + high) // 2
                if sorted_ids[mid] == int(search_id):
                    binary_pos = mid + 1
                    break
                elif sorted_ids[mid] < int(search_id):
                    low = mid + 1
                else:
                    high = mid - 1
            
            result = {
                'original': original,
                'sorted': sorted_ids,
                'search_id': int(search_id),
                'linear_position': linear_pos,
                'binary_position': binary_pos
            }
        except ValueError:
            flash("Please enter valid numbers", "danger")
    return render_template('q4_sorting.html', result=result)

# ============ Q5: Student Fee Calculation ============
@app.route('/q5', methods=['GET', 'POST'])
def q5_fees():
    total_fee = None
    if request.method == 'POST':
        try:
            tuition = float(request.form.get('tuition') or 0)
            hostel = float(request.form.get('hostel') or 0)
            transport = float(request.form.get('transport') or 0)
            total_fee = tuition + hostel + transport
        except ValueError:
            flash("Please enter valid fee amounts", "danger")
    return render_template('q5_fees.html', total_fee=total_fee)

# ============ Q6: File Handling for Academic Records ============
DATA_FILE = 'data/students.txt'

@app.route('/q6', methods=['GET', 'POST'])
def q6_filehandling():
    message = None
    records = []
    report = None
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'write':
            try:
                n = int(request.form.get('count'))
                with open(DATA_FILE, 'w') as f:
                    for i in range(n):
                        name = request.form.get(f'name_{i}')
                        marks = request.form.get(f'marks_{i}')
                        if name and marks:
                            f.write(f"{name},{marks}\n")
                message = "✓ Records saved successfully!"
            except Exception as e:
                message = f"Error: {str(e)}"
                
        elif action == 'read':
            try:
                with open(DATA_FILE, 'r') as f:
                    for line in f:
                        if ',' in line:
                            name, marks = line.strip().split(',', 1)
                            records.append({"name": name, "marks": marks})
            except FileNotFoundError:
                message = "File not found! Write records first."
                
        elif action == 'report':
            try:
                total, count, highest, topper = 0, 0, 0, ""
                with open(DATA_FILE, 'r') as f:
                    for line in f:
                        if ',' in line:
                            name, marks = line.strip().split(',', 1)
                            marks = int(marks)
                            total += marks
                            count += 1
                            if marks > highest:
                                highest = marks
                                topper = name
                if count > 0:
                    report = {
                        'total_students': count,
                        'average': round(total/count, 2),
                        'topper': topper,
                        'highest': highest
                    }
            except FileNotFoundError:
                message = "File not found!"
                
    return render_template('q6_filehandling.html', 
                         message=message, 
                         records=records, 
                         report=report)

# ============ Q7: Directory Scanning with Exception Handling ============
class EmptyDirectoryError(Exception):
    pass

@app.route('/q7', methods=['GET', 'POST'])
def q7_directory():
    structure = None
    error = None
    
    if request.method == 'POST':
        path = request.form.get('directory_path', '').strip()
        try:
            if not os.path.exists(path):
                raise FileNotFoundError("Directory does not exist!")
            if not os.path.isdir(path):
                raise NotADirectoryError("Given path is not a directory!")
            if len(os.listdir(path)) == 0:
                raise EmptyDirectoryError("Directory is empty!")
            
            structure = []
            for root, dirs, files in os.walk(path):
                level = root.replace(path, '').count(os.sep)
                indent = '  ' * 4 * level
                structure.append({
                    'name': os.path.basename(root) or root,
                    'type': 'folder',
                    'level': level,
                    'indent': indent
                })
                for file in files:
                    structure.append({
                        'name': file,
                        'type': 'file',
                        'level': level + 1,
                        'indent': '  ' * 4 * (level + 1)
                    })
        except (FileNotFoundError, NotADirectoryError, EmptyDirectoryError) as e:
            error = str(e)
        except Exception as e:
            error = f"Unexpected Error: {str(e)}"
            
    return render_template('q7_directory.html', structure=structure, error=error)

# ============ Q8: Performance Analysis with Charts ============
@app.route('/q8')
def q8_analysis():
    data = {
        'Student': ['Asha', 'Rahul', 'Kiran', 'Sneha', 'Arjun'],
        'Maths': [85, 78, 92, 74, 88],
        'Science': [90, 82, 89, 70, 95],
        'English': [88, 76, 91, 72, 84]
    }
    df = pd.DataFrame(data)
    df['Average'] = df[['Maths', 'Science', 'English']].mean(axis=1)
    
    def plot_to_base64(fig):
        buf = BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        return img_base64
    
    subjects = ['Maths', 'Science', 'English']
    averages = [df['Maths'].mean(), df['Science'].mean(), df['English'].mean()]
    
    # Bar Chart
    fig1, ax1 = plt.subplots(figsize=(8, 5))
    ax1.bar(subjects, averages, color=['#4e79a7', '#f28e2b', '#59a14f'])
    ax1.set_title('Average Marks by Subject')
    ax1.set_xlabel('Subjects')
    ax1.set_ylabel('Average Marks')
    bar_chart = plot_to_base64(fig1)
    
    # Line Graph
    fig2, ax2 = plt.subplots(figsize=(8, 5))
    ax2.plot(df['Student'], df['Average'], marker='o', color='#e15759', linewidth=2)
    ax2.set_title('Student Average Performance')
    ax2.set_xlabel('Students')
    ax2.set_ylabel('Average Marks')
    ax2.grid(True, alpha=0.3)
    line_chart = plot_to_base64(fig2)
    
    # Pie Chart
    fig3, ax3 = plt.subplots(figsize=(6, 6))
    ax3.pie(averages, labels=subjects, autopct='%1.1f%%',
            colors=['#4e79a7', '#f28e2b', '#59a14f'])
    ax3.set_title('Subject-wise Average Contribution')
    pie_chart = plot_to_base64(fig3)
    
    topper = df.loc[df['Average'].idxmax()]
    
    return render_template('q8_analysis.html',
                         dataframe=df.to_html(classes='table table-striped', index=False),
                         bar_chart=bar_chart,
                         line_chart=line_chart,
                         pie_chart=pie_chart,
                         topper=topper,
                         stats={
                             'math_avg': round(df['Maths'].mean(), 2),
                             'science_avg': round(df['Science'].mean(), 2),
                             'english_avg': round(df['English'].mean(), 2)
                         })

@app.route('/api/students')
def api_students():
    return jsonify(students_db)

if __name__ == '__main__':
    os.makedirs('data', exist_ok=True)
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
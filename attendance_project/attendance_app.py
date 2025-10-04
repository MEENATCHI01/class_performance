from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from datetime import timedelta
from functools import wraps

app = Flask(__name__)
# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "attendance_secret_key"  
db = SQLAlchemy(app)

# Role-based access control decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user'):
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('user'):
                flash('Please log in to access this page.', 'error')
                return redirect(url_for('login'))
            if session.get('role') not in roles:
                flash(f'Access denied. This page is only for {" or ".join(roles)}.', 'error')
                return redirect(url_for('front'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# Models
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class AttendanceRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    course = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(1), nullable=False)  # 'P' or 'A'
    info = db.Column(db.String(100), nullable=True)
    student = db.relationship('Student', backref=db.backref('attendance_records', lazy=True))

# Homework models
class Homework(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20), nullable=False)
    course = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    progresses = db.relationship('HomeworkProgress', backref='homework', lazy=True)

class HomeworkProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    homework_id = db.Column(db.Integer, db.ForeignKey('homework.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    marks = db.Column(db.String(20), nullable=True)
    progress = db.Column(db.String(255), nullable=True)
    student = db.relationship('Student')

# Doubt/Question model
class HomeworkDoubt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    homework_id = db.Column(db.Integer, db.ForeignKey('homework.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.String(50), nullable=False)
    answered_at = db.Column(db.String(50), nullable=True)
    student = db.relationship('Student')
    homework = db.relationship('Homework')

# ...existing code...

# Place this route after all model/class definitions and app initialization

@app.route("/report", methods=["GET"])
@role_required('Teacher', 'Admin')
def student_report():
    students = Student.query.all()
    selected_subject = request.args.get("subject")
    selected_student = request.args.get("student")
    records = []
    if selected_subject and selected_student:
        student = Student.query.filter_by(name=selected_student).first()
        if student:
            records = AttendanceRecord.query.filter_by(student_id=student.id, course=selected_subject).order_by(AttendanceRecord.date.desc()).all()
    return render_template(
        "report.html",
        students=students,
        courses=courses,
        selected_subject=selected_subject,
        selected_student=selected_student,
        records=records
    )

# Homework storage (still in-memory for now)
courses = ["Software Engineering", "Maths", "Data Structure", "Hindhi", "Information Security", "Frontend Programming", "Mobile Application"]
homework_records = {}


# Create tables and add initial students if not exist
with app.app_context():
    db.create_all()
    initial_students = [
        "Aravind", "Aswin", "Bhavana", "Gokul", "Hariharan", "Meenatchi", "Siva Bharathi", "Visal Stephenraj"
    ]
    for name in initial_students:
        if not Student.query.filter_by(name=name).first():
            db.session.add(Student(name=name))
    db.session.commit()

@app.template_filter('dateformat')
def dateformat(value, format="%Y-%m-%d"):
    try:
        return datetime.strptime(value, "%d-%m-%Y").strftime(format)
    except:
        return datetime.now().strftime(format)



# Redirect to login if not logged in
@app.route("/", methods=["GET", "POST"])
@app.route("/registeri", methods=["GET", "POST"])
@login_required
def home():
    return redirect(url_for("front"))


# Welcome front page, require login
@app.route("/front")
@login_required
def front():
    students = Student.query.all()
    user_role = session.get('role')
    user_email = session.get('user')
    student_name = session.get('student_name', None)
    return render_template("index.html", students=students, user_role=user_role, user_email=user_email, student_name=student_name)

# ✅ Attendance marking logic now in this route (Teacher and Admin only)
@app.route("/mark", methods=["GET", "POST"])
@role_required('Teacher', 'Admin')
def mark_attendance():
    students = Student.query.all()
    success_message = None
    show_records = False
    selected_course = None
    if request.method == "POST":
        selected_date = request.form.get("date")
        selected_course = request.form.get("course")
        if not selected_date:
            selected_date = datetime.now().strftime("%d-%m-%Y")
        else:
            selected_date = datetime.strptime(selected_date, "%Y-%m-%d").strftime("%d-%m-%Y")

        for s in students:
            status = request.form.get(f"status_{s.name}", "A")
            info = request.form.get(f"info_{s.name}", "not_informed")
            record = AttendanceRecord.query.filter_by(student_id=s.id, date=selected_date, course=selected_course).first()
            if record:
                record.status = status
                record.info = info
            else:
                new_record = AttendanceRecord(student_id=s.id, date=selected_date, course=selected_course, status=status, info=info)
                db.session.add(new_record)
        db.session.commit()
        success_message = "Attendance saved successfully!"
        show_records = True
    else:
        selected_date = datetime.now().strftime("%d-%m-%Y")
        selected_course = courses[0] if courses else None

    today_attendance = {s.name: {"status": "A", "info": "N/A"} for s in students}
    records = AttendanceRecord.query.filter_by(date=selected_date, course=selected_course).all()
    for r in records:
        today_attendance[r.student.name] = {"status": r.status, "info": r.info}

    present_count = sum(1 for v in today_attendance.values() if v["status"] == "P")
    absent_count = sum(1 for v in today_attendance.values() if v["status"] == "A")

    return render_template("home.html",
                           students=students,
                           attendance=today_attendance,
                           current_date=selected_date,
                           present_count=present_count,
                           absent_count=absent_count,
                           courses=courses,
                           homework_records=homework_records,
                           success_message=success_message,
                           show_records=show_records,
                           selected_course=selected_course)


@app.route("/student/<name>")
@login_required
def student_detail(name):
    # Students can only view their own records
    if session.get('role') == 'Student':
        allowed_student_name = session.get('student_name')
        if not allowed_student_name or name != allowed_student_name:
            flash('You can only view your own attendance records.', 'error')
            return redirect(url_for('front'))
    
    student = Student.query.filter_by(name=name).first()
    if not student:
        return f"Student {name} not found", 404
    
    # Get filter parameters
    selected_course = request.args.get('course', 'all')
    date_range = request.args.get('range', 'all')
    selected_date = request.args.get('date')
    
    # Base query
    query = AttendanceRecord.query.filter_by(student_id=student.id)
    
    # Filter by course
    if selected_course != 'all':
        query = query.filter_by(course=selected_course)
    
    # Filter by date range
    if date_range != 'all' and selected_date:
        try:
            base_date = datetime.strptime(selected_date, "%Y-%m-%d")
            if date_range == 'day':
                db_date = base_date.strftime("%d-%m-%Y")
                query = query.filter_by(date=db_date)
            elif date_range == 'month':
                start_date = base_date.replace(day=1)
                if start_date.month == 12:
                    end_date = start_date.replace(year=start_date.year+1, month=1, day=1) - timedelta(days=1)
                else:
                    end_date = start_date.replace(month=start_date.month+1, day=1) - timedelta(days=1)
                start_db = start_date.strftime("%d-%m-%Y")
                end_db = end_date.strftime("%d-%m-%Y")
                query = query.filter(AttendanceRecord.date >= start_db, AttendanceRecord.date <= end_db)
            elif date_range == 'year':
                start_date = base_date.replace(month=1, day=1)
                end_date = base_date.replace(month=12, day=31)
                start_db = start_date.strftime("%d-%m-%Y")
                end_db = end_date.strftime("%d-%m-%Y")
                query = query.filter(AttendanceRecord.date >= start_db, AttendanceRecord.date <= end_db)
        except Exception:
            pass
    
    records = query.all()
    records_list = [(r.date, r.status, r.course) for r in records]
    records_list.sort(reverse=True)
    
    total_days = len(records_list)
    present_count = sum(1 for _, s, _ in records_list if s == "P")
    absent_count = sum(1 for _, s, _ in records_list if s == "A")
    percentage = round((present_count / total_days) * 100, 2) if total_days > 0 else 0
    
    return render_template("student_detail.html",
                           name=name,
                           records=records_list,
                           total_days=total_days,
                           present_count=present_count,
                           absent_count=absent_count,
                           percentage=percentage,
                           courses=courses,
                           selected_course=selected_course,
                           date_range=date_range,
                           selected_date=selected_date or datetime.now().strftime("%Y-%m-%d"))

@app.route("/attendance/<date>")
@role_required('Teacher', 'Admin')
def view_attendance(date):
    students = Student.query.all()
    records = AttendanceRecord.query.filter_by(date=date).all()
    daily_att = {s.name: "A" for s in students}
    for r in records:
        daily_att[r.student.name] = r.status
    return render_template("daily_attendance.html",
                           date=date,
                           students=students,
                           attendance=daily_att)


@app.route("/students", methods=["GET", "POST"])
@role_required('Admin')
def manage_students():
    success_message = None
    student_message = None
    subject_message = None
    if request.method == "POST":
        if "delete_student" in request.form:
            student_name = request.form.get("delete_student")
            student = Student.query.filter_by(name=student_name).first()
            if student:
                AttendanceRecord.query.filter_by(student_id=student.id).delete()
                db.session.delete(student)
                db.session.commit()
        elif "add_student" in request.form:
            new_student = request.form.get("add_student").strip()
            if new_student and not Student.query.filter_by(name=new_student).first():
                db.session.add(Student(name=new_student))
                db.session.commit()
                student_message = f"Student '{new_student}' added successfully."
        elif "course_name" in request.form:
            new_course = request.form.get("course_name").strip()
            if new_course and new_course not in courses:
                courses.append(new_course)
                subject_message = f"Subject '{new_course}' added successfully."
        return redirect(url_for("manage_students", student_message=student_message, subject_message=subject_message))
    student_message = request.args.get("student_message")
    subject_message = request.args.get("subject_message")
    students = Student.query.all()
    return render_template("students.html", students=students, courses=courses, student_message=student_message, subject_message=subject_message)


from flask import request  # make sure to import request

@app.route("/attendance-records")
@role_required('Teacher', 'Admin')
def view_attendance_records():
    from datetime import timedelta
    selected_date = request.args.get("date")
    selected_course = request.args.get("course")
    range_type = request.args.get("range", "day")
    records_dict = {}
    records = []
    db_date = None
    if selected_date:
        try:
            db_date = datetime.strptime(selected_date, "%Y-%m-%d").strftime("%d-%m-%Y")
        except Exception:
            db_date = selected_date
    if db_date and selected_course:
        if range_type == "day":
            records = AttendanceRecord.query.filter_by(date=db_date, course=selected_course).all()
        else:
            base_date = datetime.strptime(selected_date, "%Y-%m-%d")
            if range_type == "week":
                start_date = base_date - timedelta(days=base_date.weekday())
                end_date = start_date + timedelta(days=6)
            elif range_type == "month":
                start_date = base_date.replace(day=1)
                if start_date.month == 12:
                    end_date = start_date.replace(year=start_date.year+1, month=1, day=1) - timedelta(days=1)
                else:
                    end_date = start_date.replace(month=start_date.month+1, day=1) - timedelta(days=1)
            elif range_type == "year":
                start_date = base_date.replace(month=1, day=1)
                end_date = base_date.replace(month=12, day=31)
            else:
                start_date = end_date = base_date
            start_db_date = start_date.strftime("%d-%m-%Y")
            end_db_date = end_date.strftime("%d-%m-%Y")
            records = AttendanceRecord.query.filter(
                AttendanceRecord.course==selected_course,
                AttendanceRecord.date >= start_db_date,
                AttendanceRecord.date <= end_db_date
            ).all()
        for r in records:
            if r.student.name not in records_dict:
                records_dict[r.student.name] = []
            records_dict[r.student.name].append({'date': r.date, 'status': r.status, 'info': r.info})
    return render_template(
        "attendance_records.html",
        courses=courses,
        selected_date=selected_date,
        selected_course=selected_course,
        records=records_dict,
        range_type=range_type
    )



@app.route("/homework", methods=["GET", "POST"])
@role_required('Teacher', 'Admin')
def homework():

    students = Student.query.all()
    success_message = None
    selected_course = None
    # Handle POST (save homework and answer doubts)
    if request.method == "POST":
        # Check if it's a doubt answer
        if 'doubt_id' in request.form:
            doubt_id = request.form.get("doubt_id")
            answer = request.form.get("answer", "").strip()
            if doubt_id and answer:
                doubt = HomeworkDoubt.query.get(doubt_id)
                if doubt:
                    doubt.answer = answer
                    doubt.answered_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    db.session.commit()
                    success_message = "Answer submitted successfully!"
        else:
            # Save homework
            selected_date = request.form.get("date")
            selected_course = request.form.get("course")
            description = request.form.get("description", "").strip()
            homework = Homework.query.filter_by(date=selected_date, course=selected_course).first()
            if not homework:
                homework = Homework(date=selected_date, course=selected_course, description=description)
                db.session.add(homework)
            else:
                homework.description = description
            db.session.commit()
            for student in students:
                mark = request.form.get(f"{student.name}_marks", "").strip()
                progress = request.form.get(f"{student.name}_progress", "").strip()
                hw_progress = HomeworkProgress.query.filter_by(homework_id=homework.id, student_id=student.id).first()
                if not hw_progress:
                    hw_progress = HomeworkProgress(homework_id=homework.id, student_id=student.id)
                    db.session.add(hw_progress)
                hw_progress.marks = mark
                hw_progress.progress = progress
            db.session.commit()
            success_message = "Homework and Exercism progress saved!"

    # Handle GET (filter records)
    filter_date = request.args.get("filter_date")
    filter_course = request.args.get("filter_course")
    filter_range = request.args.get("filter_range", "day")
    homework_records = {}
    query = Homework.query
    # Date filtering logic
    if filter_date:
        try:
            base_date = datetime.strptime(filter_date, "%Y-%m-%d")
            if filter_range == "day":
                start_date = end_date = base_date
            elif filter_range == "week":
                start_date = base_date - timedelta(days=base_date.weekday())
                end_date = start_date + timedelta(days=6)
            elif filter_range == "month":
                start_date = base_date.replace(day=1)
                if start_date.month == 12:
                    end_date = start_date.replace(year=start_date.year+1, month=1, day=1) - timedelta(days=1)
                else:
                    end_date = start_date.replace(month=start_date.month+1, day=1) - timedelta(days=1)
            elif filter_range == "year":
                start_date = base_date.replace(month=1, day=1)
                end_date = base_date.replace(month=12, day=31)
            else:
                start_date = end_date = base_date
            start_db_date = start_date.strftime("%Y-%m-%d")
            end_db_date = end_date.strftime("%Y-%m-%d")
            query = query.filter(Homework.date >= start_db_date, Homework.date <= end_db_date)
        except Exception:
            pass
    if filter_course:
        query = query.filter_by(course=filter_course)
    all_homeworks = query.order_by(Homework.date.desc()).all()
    # Only add records that match the filter
    for hw in all_homeworks:
        # If filtering by date and range, only include matching dates
        if filter_date and filter_range == "day":
            if hw.date != filter_date:
                continue
            if filter_course and hw.course != filter_course:
                continue
        if hw.date not in homework_records:
            homework_records[hw.date] = {}
        # Only add the selected course for 'Today' filter
        if filter_date and filter_range == "day" and filter_course:
            if hw.course != filter_course:
                continue
        homework_records[hw.date][hw.course] = {
            "description": hw.description,
            "marks": {},
            "progress": {}
        }
        for prog in hw.progresses:
            student_name = prog.student.name if prog.student else "Unknown"
            homework_records[hw.date][hw.course]["marks"][student_name] = prog.marks or "N/A"
            homework_records[hw.date][hw.course]["progress"][student_name] = prog.progress or "N/A"

    # Get all unanswered doubts
    unanswered_doubts = HomeworkDoubt.query.filter_by(answer=None).order_by(HomeworkDoubt.created_at.desc()).all()
    
    return render_template(
        "homework.html",
        students=students,
        courses=courses,
        homework_records=homework_records,
        selected_course=selected_course,
        current_date=datetime.now().strftime("%Y-%m-%d"),
        success_message=success_message,
        unanswered_doubts=unanswered_doubts
    )



# --- LOGIN & LOGOUT ROUTES ---

# Dummy user data for demonstration (replace with real DB queries)
# Format: email -> {'password': 'xxx', 'student_name': 'xxx'}
USERS = {
    'Student': {
        'aravind@example.com': {'password': 'student123', 'student_name': 'Aravind'},
        'aswin@example.com': {'password': 'student123', 'student_name': 'Aswin'},
        'bhavana@example.com': {'password': 'student123', 'student_name': 'Bhavana'},
        'gokul@example.com': {'password': 'student123', 'student_name': 'Gokul'},
        'hariharan@example.com': {'password': 'student123', 'student_name': 'Hariharan'},
        'meenatchi@example.com': {'password': 'student123', 'student_name': 'Meenatchi'},
        'sivabharathi@example.com': {'password': 'student123', 'student_name': 'Siva Bharathi'},
        'visal@example.com': {'password': 'student123', 'student_name': 'Visal Stephenraj'},
    },
    'Teacher': {'teacher@example.com': {'password': 'teacher123'}},
    'Admin': {'admin@example.com': {'password': 'admin123'}},
}

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        role = request.form.get("role")
        email = request.form.get("email")
        password = request.form.get("password")
        user_group = USERS.get(role, {})
        user = user_group.get(email)
        if user and user["password"] == password:
            session["user"] = email
            session["role"] = role
            # Store student name for easy access
            if role == 'Student' and 'student_name' in user:
                session["student_name"] = user['student_name']
            # Redirect to main page after login
            return redirect(url_for("front"))
        else:
            error = "Invalid credentials. Please try again."
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))

# --- STUDENT HOMEWORK ROUTES ---
@app.route("/student-homework", methods=["GET", "POST"])
@role_required('Student')
def student_homework():
    student_name = session.get('student_name')
    student = Student.query.filter_by(name=student_name).first()
    
    if not student:
        flash('Student profile not found.', 'error')
        return redirect(url_for('front'))
    
    # Handle doubt submission
    if request.method == "POST":
        homework_id = request.form.get("homework_id")
        question = request.form.get("question", "").strip()
        
        if homework_id and question:
            new_doubt = HomeworkDoubt(
                homework_id=homework_id,
                student_id=student.id,
                question=question,
                created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            db.session.add(new_doubt)
            db.session.commit()
            flash('Your question has been submitted successfully!', 'success')
        return redirect(url_for('student_homework'))
    
    # Get filter parameters
    filter_course = request.args.get("filter_course")
    
    # Query homework
    query = Homework.query
    if filter_course:
        query = query.filter_by(course=filter_course)
    
    all_homeworks = query.order_by(Homework.date.desc()).all()
    
    # Build homework records with student's progress and doubts
    homework_data = []
    for hw in all_homeworks:
        progress = HomeworkProgress.query.filter_by(homework_id=hw.id, student_id=student.id).first()
        doubts = HomeworkDoubt.query.filter_by(homework_id=hw.id, student_id=student.id).all()
        
        homework_data.append({
            'homework': hw,
            'marks': progress.marks if progress else 'Not graded',
            'progress': progress.progress if progress else 'Not submitted',
            'doubts': doubts
        })
    
    return render_template("student_homework.html",
                           homework_data=homework_data,
                           courses=courses,
                           filter_course=filter_course,
                           student_name=student_name)

# --- END LOGIN/LOGOUT ROUTES ---


if __name__ == "__main__":
    app.secret_key = 'your_secret_key_here'  # Set a real secret key in production
    app.run(host="0.0.0.0", port=5000, debug=True)

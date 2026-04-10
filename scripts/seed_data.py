import os
import sys
import random
from datetime import datetime, timedelta
import psycopg2
from werkzeug.security import generate_password_hash

# Add the parent directory to sys.path to import from local modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import get_db_connection
from config import settings

def clear_data(cur):
    print("Clearing existing dynamic data...")
    tables = [
        "student_interventions", "notifications", "student_badges", "goal_milestones",
        "student_goals", "student_skills", "mock_tests", "attendance", "marks",
        "notices", "study_resources", "students"
    ]
    for table in tables:
        cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
        
    # Re-run consistency checks to recreate tables correctly
    from services.student_service import ensure_student_table_consistency
    from services.subject_service import ensure_subject_table_consistency
    from services.marks_service import ensure_marks_table_consistency
    from services.attendance_service import ensure_attendance_table_consistency
    from services.mock_service import ensure_mock_tests_table_consistency
    from services.skills_service import ensure_skills_table_consistency
    from services.goals_service import ensure_goals_tables
    from services.notice_board_service import NoticeBoardService
    from services.resources_service import ResourcesService
    
    ensure_student_table_consistency()
    ensure_subject_table_consistency()
    ensure_marks_table_consistency()
    ensure_attendance_table_consistency()
    ensure_mock_tests_table_consistency()
    ensure_skills_table_consistency()
    ensure_goals_tables()
    NoticeBoardService.ensure_notices_table()
    ResourcesService.ensure_resources_table()

def seed_faculty(cur):
    print("Seeding faculty user...")
    password_hash = generate_password_hash("password123")
    cur.execute("""
        INSERT INTO users (name, email, password_hash, role)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (email) DO UPDATE SET role = 'Faculty'
        RETURNING id
    """, ("Dr. Sarah Smith", "faculty@smartcampus.edu", password_hash, "Faculty"))
    return cur.fetchone()[0]

def seed_departments(cur):
    print("Seeding departments...")
    departments = ["Computer Science", "Information Technology", "Electronic Engineering", "Mechanical Engineering"]
    for dept in departments:
        cur.execute("INSERT INTO departments (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (dept,))

def seed_subjects(cur):
    print("Seeding subjects...")
    subjects = [
        ("Data Structures", "CS101", "Computer Science"),
        ("Algorithms", "CS102", "Computer Science"),
        ("Database Systems", "CS201", "Computer Science"),
        ("Operating Systems", "CS202", "Computer Science"),
        ("Web Development", "IT101", "Information Technology"),
        ("Cloud Computing", "IT201", "Information Technology"),
        ("Digital Circuits", "EE101", "Electronic Engineering"),
        ("Microprocessors", "EE201", "Electronic Engineering"),
        ("Thermodynamics", "ME101", "Mechanical Engineering"),
        ("Fluid Mechanics", "ME201", "Mechanical Engineering"),
    ]
    cur.execute("SELECT id, name FROM subjects")
    existing = {name: id for id, name in cur.fetchall()}
    
    for name, code, dept in subjects:
        if name not in existing:
            cur.execute("INSERT INTO subjects (name, code, department) VALUES (%s, %s, %s) RETURNING id", (name, code, dept))
            existing[name] = cur.fetchone()[0]
    return existing

def seed_students(cur, count=55):
    print(f"Seeding {count} students...")
    first_names = ["Arjun", "Neha", "Rohan", "Sanya", "Vikram", "Anjali", "Kabir", "Ishani", "Arav", "Meera", "Ishaan", "Zoya", "Aditya", "Riya", "Aaryan", "Ananya"]
    last_names = ["Sharma", "Verma", "Gupta", "Malhotra", "Kapoor", "Joshi", "Patel", "Reddy", "Nair", "Iyer", "Mehta", "Singh"]
    depts = ["Computer Science", "Information Technology", "Electronic Engineering", "Mechanical Engineering"]
    
    students = []
    for i in range(count):
        fname = random.choice(first_names)
        lname = random.choice(last_names)
        email = f"{fname.lower()}.{lname.lower()}.{i}@example.edu"
        roll = f"2024{random.randint(1000, 9999)}"
        dept = random.choice(depts)
        
        cur.execute("""
            INSERT INTO students (name, email, department, roll_number)
            VALUES (%s, %s, %s, %s) RETURNING id
        """, (f"{fname} {lname}", email, dept, roll))
        student_id = cur.fetchone()[0]
        students.append({"id": student_id, "dept": dept})
    return students

def seed_marks_and_attendance(cur, students, subject_map):
    print("Seeding marks and attendance...")
    for student in students:
        # Pick 4 random subjects
        picked_subjects = random.sample(list(subject_map.values()), 4)
        
        for sub_id in picked_subjects:
            # Seed 3-5 marks per subject
            for _ in range(random.randint(3, 5)):
                marks = random.uniform(40, 98)
                cur.execute("INSERT INTO marks (student_id, subject_id, marks) VALUES (%s, %s, %s)", (student['id'], sub_id, marks))
            
            # Seed 20-30 attendance records per subject
            end_date = datetime.now()
            for day in range(30):
                date = end_date - timedelta(days=day)
                status = "Present" if random.random() < 0.85 else "Absent"
                cur.execute("INSERT INTO attendance (student_id, subject_id, date, status) VALUES (%s, %s, %s, %s)", 
                           (student['id'], sub_id, date.date(), status))

def seed_notices_and_resources(cur, faculty_id):
    print("Seeding notices and resources...")
    notices = [
        ("Campus Recruitment 2024", "Top companies are visiting next month. Keep your profiles updated.", "All"),
        ("Mid-Term Exam Schedule", "Exams start from 20th October. Check the portal for details.", "Student"),
        ("Hackathon Announcement", "Annual 24-hour hackathon registrations are open now.", "Student"),
    ]
    for title, content, target in notices:
        cur.execute("""
            INSERT INTO notices (title, content, target_role, author_id)
            VALUES (%s, %s, %s, %s)
        """, (title, content, target, faculty_id))
    
    resources = [
        ("Advanced Data Structures PDF", "Comprehensive guide to trees and graphs", "https://example.com/ds", "Algorithms"),
        ("Machine Learning Basics", "Introductory slides for ML", "https://example.com/ml", "Cloud Computing"),
    ]
    for title, desc, link, sub_name in resources:
        cur.execute("SELECT id FROM subjects WHERE name = %s LIMIT 1", (sub_name,))
        sub_id = cur.fetchone()
        if sub_id:
            cur.execute("""
                INSERT INTO study_resources (title, description, resource_link, subject_id, uploaded_by)
                VALUES (%s, %s, %s, %s, %s)
            """, (title, desc, link, sub_id[0], faculty_id))

def run_seed():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        clear_data(cur)
        faculty_id = seed_faculty(cur)
        seed_departments(cur)
        subject_map = seed_subjects(cur)
        students = seed_students(cur, count=60)
        seed_marks_and_attendance(cur, students, subject_map)
        seed_notices_and_resources(cur, faculty_id)
        
        conn.commit()
        print("Success: Database successfully enriched with production-ready data!")
    except Exception as e:
        conn.rollback()
        print(f"Error during seeding: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    run_seed()

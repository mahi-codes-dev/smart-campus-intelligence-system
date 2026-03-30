"""
Recommendation Engine Service

Provides ML-based recommendations for:
- Course/subject suggestions based on performance
- Study resources and learning paths
- Career guidance based on skills and performance
- Performance improvement strategies
"""

import logging
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
from database import get_db_connection
from collections import defaultdict

logger = logging.getLogger(__name__)


class RecommendationService:
    """ML-powered recommendation engine for personalized student guidance"""

    # Performance thresholds
    EXCELLENT_THRESHOLD = 80
    GOOD_THRESHOLD = 70
    AVERAGE_THRESHOLD = 60
    POOR_THRESHOLD = 50

    # Recommendation weights
    WEIGHT_RECENT_MARKS = 0.4
    WEIGHT_ATTENDANCE = 0.2
    WEIGHT_SUBJECT_PERFORMANCE = 0.3
    WEIGHT_SKILL_LEVEL = 0.1

    @staticmethod
    def analyze_student_performance(student_id: int) -> Dict[str, Any]:
        """
        Comprehensive analysis of student's academic performance

        Args:
            student_id: Student ID

        Returns:
            Dictionary with performance metrics and analysis
        """
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # Get student info
            cur.execute(
                """
                SELECT id, name, email, cgpa, enrollment_date
                FROM students WHERE id = %s
            """,
                (student_id,),
            )
            student = cur.fetchone()

            if not student:
                return {"error": "Student not found"}

            # Get recent marks (last 3 months)
            three_months_ago = datetime.now() - timedelta(days=90)
            cur.execute(
                """
                SELECT m.subject_id, s.name, 
                       AVG(CAST(m.marks AS FLOAT)) as avg_marks,
                       COUNT(*) as count,
                       MAX(m.date) as last_exam
                FROM marks m
                JOIN subjects s ON m.subject_id = s.id
                WHERE m.student_id = %s AND m.date >= %s
                GROUP BY m.subject_id, s.name
                ORDER BY avg_marks DESC
            """,
                (student_id, three_months_ago),
            )
            subject_performance = [
                {
                    "subject_id": row[0],
                    "subject_name": row[1],
                    "average_marks": round(float(row[2]) if row[2] else 0, 2),
                    "exam_count": row[3],
                    "last_exam_date": str(row[4]) if row[4] else None,
                }
                for row in cur.fetchall()
            ]

            # Calculate overall average
            if subject_performance:
                overall_avg = sum(s["average_marks"] for s in subject_performance) / len(
                    subject_performance
                )
            else:
                overall_avg = 0

            # Get attendance
            cur.execute(
                """
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present
                FROM attendance
                WHERE student_id = %s
            """,
                (student_id,),
            )
            attendance_result = cur.fetchone()
            total_classes = attendance_result[0] if attendance_result and attendance_result[0] else 1
            present_classes = attendance_result[1] if attendance_result and attendance_result[1] else 0
            attendance_percentage = (present_classes / total_classes * 100) if total_classes > 0 else 0

            # Get skill proficiencies
            cur.execute(
                """
                SELECT skill_name, proficiency_level, last_updated
                FROM student_skills
                WHERE student_id = %s
                ORDER BY proficiency_level DESC
            """,
                (student_id,),
            )
            skills = [
                {
                    "skill": row[0],
                    "proficiency": row[1],
                    "last_updated": str(row[2]) if row[2] else None,
                }
                for row in cur.fetchall()
            ]

            cur.close()
            conn.close()

            return {
                "student_id": student_id,
                "student_name": student[1],
                "email": student[2],
                "cgpa": float(student[3]) if student[3] else 0,
                "overall_average_marks": round(overall_avg, 2),
                "attendance_percentage": round(attendance_percentage, 2),
                "subject_performance": subject_performance,
                "skills": skills,
                "analysis_timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Performance analysis error: {str(e)}")
            return {"error": str(e)}

    @staticmethod
    def get_subject_recommendations(student_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Recommend challenging subjects to focus on

        Args:
            student_id: Student ID
            limit: Number of recommendations

        Returns:
            List of subject recommendations with reasoning
        """
        try:
            performance = RecommendationService.analyze_student_performance(student_id)

            if "error" in performance:
                return []

            subject_perf = performance.get("subject_performance", [])

            # Identify weak subjects (below average)
            weak_subjects = [s for s in subject_perf if s["average_marks"] < 60]
            strong_subjects = [s for s in subject_perf if s["average_marks"] >= 80]

            recommendations = []

            # Recommend high-demand skills in weak subjects
            for subject in weak_subjects[:limit]:
                strength_score = 100 - subject["average_marks"]
                recommendations.append(
                    {
                        "subject_id": subject["subject_id"],
                        "subject_name": subject["subject_name"],
                        "current_average": subject["average_marks"],
                        "priority": "High" if subject["average_marks"] < 50 else "Medium",
                        "reason": f"Performance needs improvement ({subject['average_marks']:.1f}%)",
                        "suggested_action": "Schedule tutoring sessions or form study group",
                        "strength_score": strength_score,
                    }
                )

            # Sort by strength score
            recommendations.sort(key=lambda x: x["strength_score"], reverse=True)

            return recommendations[:limit]

        except Exception as e:
            logger.error(f"Subject recommendation error: {str(e)}")
            return []

    @staticmethod
    def get_career_recommendations(student_id: int) -> Dict[str, Any]:
        """
        Provide career guidance based on performance and skills

        Args:
            student_id: Student ID

        Returns:
            Career recommendation with paths and required skills
        """
        try:
            performance = RecommendationService.analyze_student_performance(student_id)

            if "error" in performance:
                return {"error": "Could not analyze performance"}

            overall_avg = performance["overall_average_marks"]
            skills = performance.get("skills", [])
            subjects = performance.get("subject_performance", [])

            # Calculate performance category
            if overall_avg >= 80:
                category = "High Achiever"
                career_paths = ["Research", "Academia", "Tech Leadership", "Product Management"]
            elif overall_avg >= 70:
                category = "Above Average"
                career_paths = ["Software Engineering", "Data Analysis", "Project Management"]
            elif overall_avg >= 60:
                category = "Average"
                career_paths = ["Software Development", "Technical Support", "Business Analysis"]
            else:
                category = "Needs Support"
                career_paths = ["Technical Training", "Skill Development Programs"]

            # Identify strong technical subjects
            top_subjects = sorted(subjects, key=lambda x: x["average_marks"], reverse=True)[:3]

            # Identify skill gaps
            skill_levels = {s["skill"]: s["proficiency"] for s in skills}
            missing_skills = []

            required_technical_skills = [
                "Python",
                "Database Management",
                "Problem Solving",
                "Communication",
            ]
            for skill in required_technical_skills:
                if skill not in skill_levels and overall_avg >= 60:
                    missing_skills.append(skill)

            return {
                "student_id": student_id,
                "performance_category": category,
                "performance_score": round(overall_avg, 2),
                "recommended_careers": career_paths,
                "strong_subjects": [
                    {"name": s["subject_name"], "score": s["average_marks"]}
                    for s in top_subjects
                ],
                "current_skills": [
                    {"name": s["skill"], "level": s["proficiency"]} for s in skills[:5]
                ],
                "skills_to_develop": missing_skills,
                "next_steps": RecommendationService._generate_career_path(
                    overall_avg, missing_skills
                ),
            }

        except Exception as e:
            logger.error(f"Career recommendation error: {str(e)}")
            return {"error": str(e)}

    @staticmethod
    def _generate_career_path(score: float, missing_skills: List[str]) -> List[str]:
        """
        Generate actionable next steps for career development

        Args:
            score: Overall performance score
            missing_skills: List of skills to develop

        Returns:
            List of recommended actions
        """
        steps = []

        if score < 60:
            steps.append("Focus on improving core academic subjects first")
            steps.append("Attend remedial classes and get tutoring support")

        if "Python" in missing_skills:
            steps.append("Enroll in Python programming course")

        if "Database Management" in missing_skills:
            steps.append("Learn SQL and database design principles")

        steps.append("Complete at least one internship before graduation")
        steps.append("Build a portfolio of personal projects")
        steps.append("Develop soft skills through workshops and mentoring")

        return steps

    @staticmethod
    def get_peer_recommendations(student_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Find peers with similar performance levels and skill sets

        Args:
            student_id: Student ID
            limit: Number of peer recommendations

        Returns:
            List of recommended peers for collaboration
        """
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # Get student's performance metrics
            cur.execute(
                """
                SELECT AVG(CAST(m.marks AS FLOAT)) as avg_marks
                FROM marks m
                WHERE m.student_id = %s
            """,
                (student_id,),
            )
            result = cur.fetchone()
            student_avg = float(result[0]) if result and result[0] else 0

            # Find peers with similar performance (within 10 points)
            cur.execute(
                """
                SELECT DISTINCT s.id, s.name, s.email,
                       AVG(CAST(m.marks AS FLOAT)) as peer_avg
                FROM students s
                LEFT JOIN marks m ON s.id = m.student_id
                WHERE s.id != %s
                GROUP BY s.id, s.name, s.email
                HAVING AVG(CAST(m.marks AS FLOAT)) BETWEEN %s AND %s
                ORDER BY ABS(AVG(CAST(m.marks AS FLOAT)) - %s)
                LIMIT %s
            """,
                (student_id, student_avg - 10, student_avg + 10, student_avg, limit),
            )

            peers = []
            for row in cur.fetchall():
                peers.append(
                    {
                        "peer_id": row[0],
                        "peer_name": row[1],
                        "peer_email": row[2],
                        "performance_score": round(float(row[3]) if row[3] else 0, 2),
                        "collaboration_type": "Study Partner" if abs(student_avg - float(row[3] or 0)) < 5 else "Mentee",
                    }
                )

            cur.close()
            conn.close()

            return peers

        except Exception as e:
            logger.error(f"Peer recommendation error: {str(e)}")
            return []

    @staticmethod
    def predict_at_risk_status(student_id: int) -> Dict[str, Any]:
        """
        Predict if student is at risk of academic failure

        Args:
            student_id: Student ID

        Returns:
            Risk assessment with intervention recommendations
        """
        try:
            performance = RecommendationService.analyze_student_performance(student_id)

            if "error" in performance:
                return {"error": "Could not assess risk"}

            overall_avg = performance["overall_average_marks"]
            attendance = performance["attendance_percentage"]
            subjects = performance.get("subject_performance", [])

            # Risk factors
            risk_score = 0
            risk_factors = []

            # Low marks (0-30% of total risk)
            if overall_avg < 50:
                risk_score += 30
                risk_factors.append("Critical: Overall marks below 50%")
            elif overall_avg < 60:
                risk_score += 20
                risk_factors.append("Warning: Overall marks below 60%")

            # Poor attendance (0-25% of total risk)
            if attendance < 75:
                risk_score += 25
                risk_factors.append(f"Critical: Attendance below 75% ({attendance:.1f}%)")
            elif attendance < 85:
                risk_score += 15
                risk_factors.append(f"Warning: Attendance below 85% ({attendance:.1f}%)")

            # Failing subjects (0-25% of total risk)
            failing_subjects = [s for s in subjects if s["average_marks"] < 40]
            if len(failing_subjects) > 0:
                risk_score += min(25, 10 * len(failing_subjects))
                risk_factors.append(f"Critical: Failing in {len(failing_subjects)} subject(s)")

            # Deteriorating trend (0-20% of total risk)
            if len(subjects) > 1:
                recent = [s["average_marks"] for s in subjects[:2]]
                older = [s["average_marks"] for s in subjects[2:4]] if len(subjects) > 3 else [overall_avg]

                if recent and older:
                    recent_avg = sum(recent) / len(recent)
                    older_avg = sum(older) / len(older)

                    if recent_avg < older_avg - 10:
                        risk_score += 20
                        risk_factors.append("Warning: Performance is declining")

            # Determine risk level
            if risk_score >= 75:
                risk_level = "Critical"
            elif risk_score >= 50:
                risk_level = "High"
            elif risk_score >= 25:
                risk_level = "Medium"
            else:
                risk_level = "Low"

            # Generate interventions
            interventions = RecommendationService._generate_interventions(
                risk_level, risk_factors, overall_avg, attendance
            )

            return {
                "student_id": student_id,
                "risk_level": risk_level,
                "risk_score": min(100, risk_score),  # Cap at 100
                "risk_factors": risk_factors,
                "interventions": interventions,
                "assessment_timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Risk prediction error: {str(e)}")
            return {"error": str(e)}

    @staticmethod
    def _generate_interventions(
        risk_level: str, risk_factors: List[str], avg_marks: float, attendance: float
    ) -> List[Dict[str, str]]:
        """
        Generate intervention recommendations based on risk level

        Args:
            risk_level: Overall risk level
            risk_factors: List of identified risk factors
            avg_marks: Average marks
            attendance: Attendance percentage

        Returns:
            List of intervention recommendations with priority
        """
        interventions = []

        if risk_level in ["Critical", "High"]:
            interventions.append(
                {
                    "priority": "Critical",
                    "action": "Schedule meeting with academic advisor",
                    "timeline": "Within 3 days",
                }
            )
            interventions.append(
                {
                    "priority": "Critical",
                    "action": "Enroll in tutoring program",
                    "timeline": "Immediately",
                }
            )

        if attendance < 75:
            interventions.append(
                {
                    "priority": "High",
                    "action": "Meet with attendance counselor",
                    "timeline": "Within 1 week",
                }
            )

        if any("failing" in factor.lower() for factor in risk_factors):
            interventions.append(
                {
                    "priority": "High",
                    "action": "Focus on failing subjects with targeted study plans",
                    "timeline": "Starting immediately",
                }
            )

        if risk_level not in ["Critical", "High"] and avg_marks < 70:
            interventions.append(
                {
                    "priority": "Medium",
                    "action": "Join peer study groups",
                    "timeline": "Within 2 weeks",
                }
            )

        interventions.append(
            {
                "priority": "Medium",
                "action": "Complete weekly progress check-ins",
                "timeline": "Ongoing",
            }
        )

        return interventions

    @staticmethod
    def get_learning_resources(student_id: int, subject_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Recommend learning resources based on performance and weak areas

        Args:
            student_id: Student ID
            subject_id: Optional subject ID for targeted recommendations

        Returns:
            List of recommended learning resources
        """
        try:
            performance = RecommendationService.analyze_student_performance(student_id)

            if "error" in performance:
                return []

            resources = []

            # Identify weak subjects
            weak_subjects = [
                s for s in performance.get("subject_performance", [])
                if s["average_marks"] < 60
            ]

            # Online courses
            online_courses = {
                "Data Structures": "https://www.coursera.org/courses/data-structures",
                "Database Design": "https://www.udemy.com/course/database-design",
                "Web Development": "https://www.coursera.org/courses/web-development",
                "Machine Learning": "https://www.github.com/learn/ml-basics",
                "Python Programming": "https://www.codecademy.com/learn/python",
            }

            for subject in weak_subjects[:3]:
                subject_name = subject["subject_name"]
                if subject_name in online_courses:
                    resources.append(
                        {
                            "type": "Online Course",
                            "subject": subject_name,
                            "title": f"Master {subject_name}",
                            "url": online_courses[subject_name],
                            "difficulty": "Beginner to Intermediate",
                            "estimated_hours": 40,
                            "priority": "High" if subject["average_marks"] < 50 else "Medium",
                        }
                    )

            # Add general resources
            resources.extend(
                [
                    {
                        "type": "Study Guide",
                        "subject": "General",
                        "title": "Effective Study Techniques",
                        "url": "https://www.example.com/study-techniques",
                        "difficulty": "Beginner",
                        "estimated_hours": 2,
                        "priority": "Medium",
                    },
                    {
                        "type": "Textbook",
                        "subject": "General",
                        "title": "Introduction to Computer Science",
                        "url": "https://www.example.com/textbooks",
                        "difficulty": "Intermediate",
                        "estimated_hours": 100,
                        "priority": "High",
                    },
                ]
            )

            return resources

        except Exception as e:
            logger.error(f"Learning resource error: {str(e)}")
            return []

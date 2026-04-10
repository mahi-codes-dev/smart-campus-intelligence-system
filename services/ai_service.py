import google.generativeai as genai
from config import settings
from services.student_dashboard_service import get_student_dashboard_data
from services.student_service import get_student_profile

class AIService:
    _instance = None
    _model = None

    @classmethod
    def _get_model(cls):
        if cls._model is None:
            if not settings.gemini_api_key:
                return None
            genai.configure(api_key=settings.gemini_api_key)
            cls._model = genai.GenerativeModel(settings.gemini_model)
        return cls._model

    @classmethod
    def get_student_advice(cls, student_id, user_message):
        model = cls._get_model()
        if not model:
            return "AI Assistant is currently unavailable (API Key missing)."

        # Fetch student context
        profile = get_student_profile(student_id)
        data = get_student_dashboard_data(student_id)

        context = f"""
        User Role: Student
        Name: {profile['name']}
        Department: {profile['department']}
        
        Academic Performance:
        - Readiness Score: {data['readiness_score']}/100
        - Status: {data['status']}
        - Risk Level: {data['risk_level']}
        - Attendance: {data['attendance']}%
        - Average Marks: {data['marks']}
        - Mock Test Score: {data['mock_score']}
        - Skills Count: {data['skills_count']}
        
        Insights from System:
        {", ".join(data['insights'][:3])}
        
        Alerts from System:
        {", ".join(data['alerts'][:3])}

        Please provide personalized, encouraging, and actionable advice based on this data. 
        If the student is 'At Risk', focus on attendance and marks. 
        If they are 'Placement Ready', suggest advanced skills or mock interview practice.
        """

        try:
            chat = model.start_chat(history=[])
            full_prompt = f"Context: {context}\n\nStudent Question: {user_message}"
            response = chat.send_message(full_prompt)
            return response.text
        except Exception as e:
            return f"Error communicating with AI: {str(e)}"

    @classmethod
    def get_faculty_insights(cls, faculty_name, class_data, query):
        model = cls._get_model()
        if not model:
            return "AI Assistant is currently unavailable (API Key missing)."

        context = f"""
        User Role: Faculty
        Faculty Name: {faculty_name}
        
        Class Summary Data:
        - Total Students: {class_data['summary']['total_students']}
        - Average Marks: {class_data['summary']['average_marks']}
        - At Risk Count: {class_data['summary']['at_risk_count']}
        - Intervention Cases: {class_data['intervention_summary']['open_cases']}
        
        The faculty is asking: {query}
        Please provide a data-driven response to help the faculty improve class performance.
        """

        try:
            response = model.generate_content(context)
            return response.text
        except Exception as e:
            return f"Error communicating with AI: {str(e)}"

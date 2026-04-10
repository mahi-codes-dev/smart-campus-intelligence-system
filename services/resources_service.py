import logging
from datetime import datetime
from database import get_db_connection

logger = logging.getLogger(__name__)

class ResourcesService:
    @staticmethod
    def ensure_resources_table():
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS study_resources (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    resource_link VARCHAR(1000) NOT NULL,
                    subject_id INTEGER REFERENCES subjects(id) ON DELETE CASCADE,
                    uploaded_by INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
            cur.close()
            conn.close()
            logger.info("Resources table ensured")
        except Exception as e:
            logger.error(f"Error ensuring resources table: {e}")
            raise

    @staticmethod
    def add_resource(title: str, description: str, resource_link: str, subject_id: int, uploaded_by: int):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO study_resources (title, description, resource_link, subject_id, uploaded_by)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (title, description, resource_link, subject_id, uploaded_by))
            resource_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
            return resource_id
        except Exception as e:
            logger.error(f"Error adding resource: {e}")
            return None

    @staticmethod
    def get_resources(subject_id=None):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            query = """
                SELECT r.id, r.title, r.description, r.resource_link, r.created_at, 
                       s.name as subject_name, u.name as uploader_name
                FROM study_resources r
                LEFT JOIN subjects s ON r.subject_id = s.id
                JOIN users u ON r.uploaded_by = u.id
            """
            params = []
            
            if subject_id:
                query += " WHERE r.subject_id = %s"
                params.append(subject_id)
                
            query += " ORDER BY r.created_at DESC"
            
            cur.execute(query, params)
            rows = cur.fetchall()
            cur.close()
            conn.close()
            
            resources = []
            for row in rows:
                resources.append({
                    "id": row[0],
                    "title": row[1],
                    "description": row[2],
                    "resource_link": row[3],
                    "created_at": row[4].strftime("%Y-%m-%d %H:%M:%S") if row[4] else "",
                    "subject_name": row[5] or "General",
                    "uploader_name": row[6]
                })
            return resources
        except Exception as e:
            logger.error(f"Error getting resources: {e}")
            return []

    @staticmethod
    def delete_resource(resource_id: int):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM study_resources WHERE id = %s", (resource_id,))
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error deleting resource: {e}")
            return False

"""
Theme Service - Manage user theme preferences
Supports light and dark mode with persistence
"""

from database import get_db_connection
from typing import Optional, Dict, Any


class ThemeService:
    """Service for managing user theme preferences"""
    
    VALID_THEMES = ['light', 'dark']
    DEFAULT_THEME = 'light'
    
    @staticmethod
    def ensure_theme_table():
        """Create theme_preferences table if it doesn't exist"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS theme_preferences (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER UNIQUE NOT NULL,
                    theme VARCHAR(20) NOT NULL DEFAULT 'light',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_user_id FOREIGN KEY (user_id) 
                        REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Create index on user_id for faster lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_theme_user_id 
                ON theme_preferences(user_id)
            """)
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Theme table creation error: {e}")
            return False
    
    @staticmethod
    def get_user_theme(user_id: int) -> str:
        """
        Get user's theme preference
        
        Args:
            user_id: User ID
            
        Returns:
            Theme name ('light' or 'dark')
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT theme FROM theme_preferences WHERE user_id = %s",
                (user_id,)
            )
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result:
                return result[0]
            return ThemeService.DEFAULT_THEME
        except Exception as e:
            print(f"Error fetching user theme: {e}")
            return ThemeService.DEFAULT_THEME
    
    @staticmethod
    def set_user_theme(user_id: int, theme: str) -> bool:
        """
        Set user's theme preference
        
        Args:
            user_id: User ID
            theme: Theme name ('light' or 'dark')
            
        Returns:
            Success status
        """
        if theme not in ThemeService.VALID_THEMES:
            return False
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Use INSERT ... ON CONFLICT approach (PostgreSQL specific)
            # If user exists, update; if not, insert
            cursor.execute("""
                INSERT INTO theme_preferences (user_id, theme, updated_at)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) DO UPDATE
                SET theme = %s, updated_at = CURRENT_TIMESTAMP
            """, (user_id, theme, theme))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Error setting user theme: {e}")
            return False
    
    @staticmethod
    def toggle_user_theme(user_id: int) -> Dict[str, Any]:
        """
        Toggle user's theme between light and dark
        
        Args:
            user_id: User ID
            
        Returns:
            Dict with new theme and success status
        """
        current_theme = ThemeService.get_user_theme(user_id)
        new_theme = 'dark' if current_theme == 'light' else 'light'
        
        success = ThemeService.set_user_theme(user_id, new_theme)
        
        return {
            'success': success,
            'theme': new_theme if success else current_theme,
            'previous_theme': current_theme
        }
    
    @staticmethod
    def initialize_user_theme(user_id: int, theme: str = DEFAULT_THEME) -> bool:
        """
        Initialize theme for new user
        
        Args:
            user_id: User ID
            theme: Initial theme (default: 'light')
            
        Returns:
            Success status
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO theme_preferences (user_id, theme)
                VALUES (%s, %s)
                ON CONFLICT (user_id) DO NOTHING
            """, (user_id, theme))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Error initializing user theme: {e}")
            return False
    
    @staticmethod
    def get_theme_stats() -> Dict[str, int]:
        """
        Get statistics on theme usage across users
        
        Returns:
            Dict with counts of light/dark theme users
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT theme, COUNT(*) as count
                FROM theme_preferences
                GROUP BY theme
            """)
            
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            stats = {'light': 0, 'dark': 0}
            for theme, count in results:
                if theme in stats:
                    stats[theme] = count
            
            return stats
        except Exception as e:
            print(f"Error fetching theme stats: {e}")
            return {'light': 0, 'dark': 0}


# Initialize table on module load
ThemeService.ensure_theme_table()

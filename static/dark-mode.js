/**
 * Dark Mode Module
 * Manages theme switching with localStorage and server persistence
 */

class DarkModeManager {
    constructor() {
        this.STORAGE_KEY = 'smartcampus_theme';
        this.DARK_CLASS = 'dark-mode';
        this.API_ENDPOINT = '/api/theme';
        this.init();
    }

    /**
     * Initialize dark mode on page load
     */
    init() {
        // Check if user is authenticated
        const token = localStorage.getItem('token');
        
        if (token) {
            // Fetch theme from server
            this.loadThemeFromServer();
        } else {
            // Load from localStorage only (for non-authenticated pages)
            this.loadThemeFromStorage();
        }
        
        // Listen for preference changes in other tabs
        window.addEventListener('storage', (e) => {
            if (e.key === this.STORAGE_KEY) {
                this.applyTheme(e.newValue || 'light');
            }
        });
    }

    /**
     * Load theme from server (authenticated users)
     */
    async loadThemeFromServer() {
        try {
            const response = await fetch(`${this.API_ENDPOINT}/get-theme`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                const theme = data.theme || 'light';
                this.applyTheme(theme);
                localStorage.setItem(this.STORAGE_KEY, theme);
            } else {
                // Fallback to localStorage if request fails
                this.loadThemeFromStorage();
            }
        } catch (error) {
            console.warn('Failed to load theme from server:', error);
            this.loadThemeFromStorage();
        }
    }

    /**
     * Load theme from localStorage (fallback/non-authenticated)
     */
    loadThemeFromStorage() {
        const theme = localStorage.getItem(this.STORAGE_KEY) || this.getSystemPreference();
        this.applyTheme(theme);
    }

    /**
     * Get system/OS theme preference
     */
    getSystemPreference() {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        return 'light';
    }

    /**
     * Apply theme to document
     */
    applyTheme(theme) {
        if (theme === 'dark') {
            document.body.classList.add(this.DARK_CLASS);
            document.documentElement.setAttribute('data-theme', 'dark');
        } else {
            document.body.classList.remove(this.DARK_CLASS);
            document.documentElement.setAttribute('data-theme', 'light');
        }
        
        // Update any toggle buttons to reflect current theme
        this.updateToggleButtons(theme);
    }

    /**
     * Update toggle button icons
     */
    updateToggleButtons(theme) {
        const buttons = document.querySelectorAll('.toggle-theme-btn');
        buttons.forEach(btn => {
            const icon = btn.querySelector('i');
            if (icon) {
                if (theme === 'dark') {
                    // Show sun icon in dark mode (click to switch to light)
                    icon.className = 'fas fa-sun';
                } else {
                    // Show moon icon in light mode (click to switch to dark)
                    icon.className = 'fas fa-moon';
                }
            }
        });
    }

    /**
     * Toggle between light and dark mode
     */
    async toggle() {
        const token = localStorage.getItem('token');
        
        if (token) {
            // Send toggle request to server
            await this.toggleOnServer();
        } else {
            // Toggle locally (non-authenticated)
            this.toggleLocal();
        }
    }

    /**
     * Toggle theme locally (localStorage only)
     */
    toggleLocal() {
        const currentTheme = localStorage.getItem(this.STORAGE_KEY) || 'light';
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        localStorage.setItem(this.STORAGE_KEY, newTheme);
        this.applyTheme(newTheme);
        
        console.log(`Theme toggled to ${newTheme}`);
    }

    /**
     * Toggle theme on server (authenticated users)
     */
    async toggleOnServer() {
        try {
            const response = await fetch(`${this.API_ENDPOINT}/toggle-theme`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                const newTheme = data.theme;
                
                // Update localStorage to match server
                localStorage.setItem(this.STORAGE_KEY, newTheme);
                this.applyTheme(newTheme);
                
                console.log(`Theme toggled to ${newTheme} (synced with server)`);
                return true;
            } else {
                console.error('Failed to toggle theme on server:', response.status);
                // Fallback to local toggle
                this.toggleLocal();
                return false;
            }
        } catch (error) {
            console.warn('Error toggling theme on server:', error);
            // Fallback to local toggle
            this.toggleLocal();
            return false;
        }
    }

    /**
     * Set theme explicitly
     */
    async setTheme(theme) {
        if (!['light', 'dark'].includes(theme)) {
            console.error(`Invalid theme: ${theme}`);
            return false;
        }

        const token = localStorage.getItem('token');
        
        if (token) {
            return await this.setThemeOnServer(theme);
        } else {
            localStorage.setItem(this.STORAGE_KEY, theme);
            this.applyTheme(theme);
            return true;
        }
    }

    /**
     * Set theme on server
     */
    async setThemeOnServer(theme) {
        try {
            const response = await fetch(`${this.API_ENDPOINT}/set-theme`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ theme })
            });

            if (response.ok) {
                localStorage.setItem(this.STORAGE_KEY, theme);
                this.applyTheme(theme);
                console.log(`Theme set to ${theme}`);
                return true;
            } else {
                console.error('Failed to set theme on server:', response.status);
                return false;
            }
        } catch (error) {
            console.error('Error setting theme on server:', error);
            return false;
        }
    }

    /**
     * Get current theme
     */
    getCurrentTheme() {
        return document.body.classList.contains(this.DARK_CLASS) ? 'dark' : 'light';
    }

    /**
     * Watch for system theme changes
     */
    watchSystemTheme() {
        if (window.matchMedia) {
            const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
            darkModeQuery.addEventListener('change', (e) => {
                // Only apply if user hasn't set preference
                if (!localStorage.getItem(this.STORAGE_KEY)) {
                    this.applyTheme(e.matches ? 'dark' : 'light');
                }
            });
        }
    }
}

// Initialize dark mode manager globally
window.darkModeManager = new DarkModeManager();

/**
 * Global function for toggle button
 */
window.toggleTheme = function() {
    window.darkModeManager.toggle();
};

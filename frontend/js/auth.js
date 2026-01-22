// Authentication utilities
class Auth {
    constructor() {
        this.currentUser = null;
        this.credentials = null;
        this.loadStoredAuth();
    }

    // Store authentication in localStorage
    storeAuth(username, password, user) {
        const auth = btoa(`${username}:${password}`);
        localStorage.setItem('auth', auth);
        localStorage.setItem('user', JSON.stringify(user));
        this.currentUser = user;
        this.credentials = auth;
    }

    // Load stored authentication
    loadStoredAuth() {
        const auth = localStorage.getItem('auth');
        const user = localStorage.getItem('user');
        
        if (auth && user) {
            this.credentials = auth;
            this.currentUser = JSON.parse(user);
            this.updateUIState();
        }
    }

    // Clear authentication
    logout() {
        localStorage.removeItem('auth');
        localStorage.removeItem('user');
        this.currentUser = null;
        this.credentials = null;
        this.updateUIState();
        showPage('home');
    }

    // Get authorization header
    getAuthHeaders() {
        if (!this.credentials) {
            throw new Error('Not authenticated');
        }
        return {
            'Authorization': `Basic ${this.credentials}`
        };
    }

    // Check if user is authenticated
    isAuthenticated() {
        return this.currentUser !== null;
    }

    // Check if user is admin
    isAdmin() {
        return this.currentUser && this.currentUser.tier === 'admin';
    }

    // Check if user is developer or above
    isDeveloper() {
        return this.currentUser && ['admin', 'developer'].includes(this.currentUser.tier);
    }

    // Update UI based on authentication state
    updateUIState() {
        const authBtn = document.getElementById('auth-btn');
        const userInfo = document.querySelector('.user-info');
        const usernameSpan = document.getElementById('current-username');

        if (this.isAuthenticated()) {
            authBtn.textContent = 'Logout';
            authBtn.onclick = () => this.logout();
            userInfo.style.display = 'flex';
            usernameSpan.textContent = this.currentUser.username;

            // Show admin-only elements
            if (this.isAdmin()) {
                document.body.classList.add('show-admin');
            }
        } else {
            authBtn.textContent = 'Login';
            authBtn.onclick = () => openModal('login-modal');
            userInfo.style.display = 'none';
            document.body.classList.remove('show-admin');
        }
    }

    // Require authentication for an action
    requireAuth(action) {
        if (!this.isAuthenticated()) {
            openModal('login-modal');
            return false;
        }
        return true;
    }

    // Require developer role or above
    requireDeveloper(action) {
        if (!this.isDeveloper()) {
            showNotification('You need developer permissions for this action', 'error');
            return false;
        }
        return true;
    }

    // Require admin role
    requireAdmin(action) {
        if (!this.isAdmin()) {
            showNotification('You need admin permissions for this action', 'error');
            return false;
        }
        return true;
    }
}

// Initialize authentication
const auth = new Auth();

// Login function
async function login(username, password) {
    try {
        showLoading(true);
        
        // Verify credentials by making an authenticated request
        const encodedCredentials = btoa(`${username}:${password}`);
        const response = await fetch(`${API_BASE}/auth/me`, {
            method: 'GET',
            headers: {
                'Authorization': `Basic ${encodedCredentials}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            showNotification('Invalid username or password', 'error');
            return false;
        }

        // Parse user info from response
        const userData = await response.json();
        
        // Create user object from successful login
        const user = {
            username: username,
            user_id: userData.user_id,
            tier: userData.tier || 'developer'
        };
        
        auth.storeAuth(username, password, user);
        closeModal('login-modal');
        showNotification('Logged in successfully!', 'success');
        
        // Refresh current page if needed
        const currentPage = document.querySelector('.page.active').id.replace('page-', '');
        if (currentPage !== 'home') {
            loadPageContent(currentPage);
        }
        
        return true;
    } catch (error) {
        console.error('Login error:', error);
        showNotification('Login failed. Please try again.', 'error');
        return false;
    } finally {
        showLoading(false);
    }
}

// Handle login form submission
document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    
    const success = await login(username, password);
    if (success) {
        document.getElementById('login-form').reset();
    }
});

// Handle sign up button
document.getElementById('show-signup').addEventListener('click', () => {
    closeModal('login-modal');
    openModal('user-modal');
});

// Initialize auth state when page loads
document.addEventListener('DOMContentLoaded', () => {
    auth.updateUIState();
});
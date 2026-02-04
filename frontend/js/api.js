// API Configuration
const API_BASE = 'http://localhost:8080';

// API utility functions
class API {
    // Make authenticated request
    static async request(endpoint, options = {}) {
        const url = `${API_BASE}${endpoint}`;
        
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        // Add authentication if available
        if (auth.isAuthenticated()) {
            config.headers = {
                ...config.headers,
                ...auth.getAuthHeaders()
            };
        }

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                if (response.status === 401) {
                    auth.logout();
                    showNotification('Session expired. Please log in again.', 'error');
                    throw new Error('Authentication required');
                }
                
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP ${response.status}`);
            }

            // Handle empty responses
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }
            
            return await response.text();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    // GET request
    static async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        return this.request(url);
    }

    // POST request
    static async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    // PATCH request
    static async patch(endpoint, data) {
        return this.request(endpoint, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    }

    // DELETE request
    static async delete(endpoint) {
        return this.request(endpoint, {
            method: 'DELETE'
        });
    }
}

// Repository API functions
const RepoAPI = {
    async list(page = 1, size = 20) {
        return API.get('/repos', { page, size });
    },

    async create(repoData) {
        return API.post('/repos', repoData);
    },

    async getCloneInfo(repoName) {
        // For now, return a constructed clone URL
        return {
            clone_url: `${window.location.protocol}//${window.location.hostname}:8080/${repoName}.git`
        };
    },

    async getFiles(repoId) {
        return API.get(`/repos/${repoId}/files`);
    },

    async fork(repoId, forkData) {
        return API.post(`/repos/${repoId}/fork`, forkData);
    },

    async delete(repoId) {
        return API.delete(`/repos/${repoId}`);
    }
};

// Access Log API functions
const AccessLogAPI = {
    async listRepoLogs(repoId, page = 1, size = 20) {
        return API.get(`/repos/${repoId}/logs`, { page, size });
    },

    async listMyLogs(page = 1, size = 20) {
        return API.get(`/users/me/logs`, { page, size });
    }
};

// Issue API functions
const IssueAPI = {
    async list(repoId, page = 1, size = 20) {
        return API.get(`/repos/${repoId}/issues`, { page, size });
    },

    async get(repoId, issueNum) {
        return API.get(`/repos/${repoId}/issues/${issueNum}`);
    },

    async create(repoId, issueData) {
        return API.post(`/repos/${repoId}/issues`, issueData);
    },

    async addComment(repoId, issueNum, commentData) {
        return API.post(`/repos/${repoId}/issues/${issueNum}/comments`, commentData);
    },

    async updateStatus(repoId, issueNum, status) {
        return API.patch(`/repos/${repoId}/issues/${issueNum}/status?status=${status}`, {});
    }
};

// User API functions
const UserAPI = {
    async list(page = 1, size = 20) {
        return API.get('/users', { page, size });
    },

    async create(userData) {
        return API.post('/users', userData);
    },

    async updateTier(userId, tierData) {
        return API.patch(`/users/${userId}/tier`, tierData);
    }
};

// Roles & Access API functions
const RoleAPI = {
    async list() {
        return API.get('/roles');
    }
};

const AccessAPI = {
    async grant(userId, repoId, roleId) {
        return API.post('/access', { user_id: userId, repo_id: repoId, role_id: roleId });
    },
    async revoke(userId, repoId, roleId = null) {
        const endpoint = roleId ? `/access?role_id=${roleId}` : '/access';
        return API.request(endpoint, { method: 'DELETE', body: JSON.stringify({ user_id: userId, repo_id: repoId }) });
    },
    async searchUsers(repoId, q, page = 1, size = 20) {
        return API.get(`/repos/${repoId}/users`, { q, page, size });
    },
    async getMembers(repoId) {
        return API.get(`/repos/${repoId}/members`);
    }
};

// Utility functions for handling API responses
function formatDate(dateString) {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return 'Invalid date';
    
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatRelativeTime(dateString) {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return 'Invalid date';
    
    const now = new Date();
    const diffMs = now - date;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);

    if (diffSec < 60) return 'just now';
    if (diffMin < 60) return `${diffMin} minute${diffMin !== 1 ? 's' : ''} ago`;
    if (diffHour < 24) return `${diffHour} hour${diffHour !== 1 ? 's' : ''} ago`;
    if (diffDay < 7) return `${diffDay} day${diffDay !== 1 ? 's' : ''} ago`;
    
    return formatDate(dateString);
}

// Error handling utility
function handleAPIError(error, context = '') {
    console.error(`API Error${context ? ` (${context})` : ''}:`, error);
    
    let message = 'An error occurred';
    
    if (error.message) {
        if (error.message.includes('Authentication required')) {
            return; // Auth error already handled
        }
        message = error.message;
    }
    
    showNotification(message, 'error');
}

// Loading state management
function showLoading(show = true) {
    const overlay = document.getElementById('loading-overlay');
    overlay.classList.toggle('active', show);
}

// Notification system
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${getNotificationIcon(type)}"></i>
            <span>${message}</span>
        </div>
    `;

    // Add to page
    document.body.appendChild(notification);

    // Trigger animation
    setTimeout(() => notification.classList.add('show'), 10);

    // Remove after delay
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 4000);
}

function getNotificationIcon(type) {
    switch (type) {
        case 'success': return 'check-circle';
        case 'error': return 'exclamation-circle';
        case 'warning': return 'exclamation-triangle';
        default: return 'info-circle';
    }
}

// Add notification styles
const notificationStyles = `
    .notification {
        position: fixed;
        top: 20px;
        right: 20px;
        background: white;
        border-radius: 8px;
        padding: 1rem 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 4000;
        transform: translateX(100%);
        transition: transform 0.3s ease;
        border-left: 4px solid #007bff;
        max-width: 400px;
    }

    .notification.show {
        transform: translateX(0);
    }

    .notification-success {
        border-left-color: #28a745;
    }

    .notification-error {
        border-left-color: #dc3545;
    }

    .notification-warning {
        border-left-color: #ffc107;
    }

    .notification-content {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .notification-success .notification-content i {
        color: #28a745;
    }

    .notification-error .notification-content i {
        color: #dc3545;
    }

    .notification-warning .notification-content i {
        color: #ffc107;
    }

    .notification .notification-content i {
        color: #007bff;
    }
`;

// Add styles to head
if (!document.querySelector('#notification-styles')) {
    const style = document.createElement('style');
    style.id = 'notification-styles';
    style.textContent = notificationStyles;
    document.head.appendChild(style);
}
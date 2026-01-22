# CornHub Frontend

A modern web interface for the CornHub private repository management system.

## Features

- 🌽 **Repository Management**: Create, browse, and manage Git repositories
- 🐛 **Issue Tracking**: Create issues, add comments, and track progress
- 👥 **User Management**: Admin interface for managing users and permissions
- 🔐 **Authentication**: Secure login with role-based access control
- 📱 **Responsive Design**: Works on desktop and mobile devices

## Getting Started

### Prerequisites

1. Make sure the CornHub backend is running:
   ```bash
   cd /path/to/hitgub
   source dbms/bin/activate
   uvicorn app.main:app --reload --log-level=debug --port 8080
   ```

2. Ensure you have a PostgreSQL database running and MongoDB running for the backend.

### Accessing the Frontend

1. **Via Backend Integration** (Recommended):
   - The frontend is automatically served by the FastAPI backend
   - Visit: http://localhost:8080/
   - The backend serves the frontend files and API from the same port

2. **Via Simple HTTP Server** (Development):
   ```bash
   cd frontend
   python3 -m http.server 3000
   ```
   - Visit: http://localhost:3000/
   - Note: You may need to update API_BASE in `js/api.js` if using different ports

## Default Credentials

Create a user through the signup form, or if you have admin access to the database, you can create an admin user:

```sql
-- Connect to your PostgreSQL database
INSERT INTO "user" (username, email, password_hash, tier) 
VALUES ('admin', 'admin@cornhub.local', '$2b$12$encrypted_password_hash', 'admin');
```

Or create a user via the API:
```bash
curl -X POST "http://localhost:8080/users" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "password123"}'
```

## File Structure

```
frontend/
├── index.html          # Main HTML file with all pages
├── css/
│   └── style.css      # Complete styling for the application
├── js/
│   ├── app.js         # Main application logic and page management
│   ├── api.js         # API communication and utilities
│   └── auth.js        # Authentication and user management
└── README.md          # This file
```

## Features Overview

### Home Page
- Welcome screen with feature overview
- Quick access to login and repository browsing

### Repository Management
- Browse all repositories with pagination
- Create new repositories (Developer+ role required)
- View repository details and clone URLs
- Browse repository issues

### Issue Tracking
- View all issues in a repository
- Create new issues with title and description
- View issue details with full conversation thread
- Add comments to issues

### User Management (Admin Only)
- View all system users
- Create new user accounts
- Update user permission tiers (admin/developer/tester)
- Manage user roles and repository access

### Authentication
- HTTP Basic Authentication integration
- Persistent login sessions via localStorage
- Role-based UI features (admin-only sections)
- Automatic session handling and renewal

## API Integration

The frontend communicates with the CornHub FastAPI backend using these endpoints:

- `GET /repos` - List repositories
- `POST /repos` - Create repository
- `GET /repos/{id}/issues` - List issues
- `POST /repos/{id}/issues` - Create issue
- `GET /repos/{id}/issues/{num}` - Get issue details
- `POST /repos/{id}/issues/{num}/comments` - Add comment
- `GET /users` - List users (admin only)
- `POST /users` - Create user

## Customization

### Styling
Edit `css/style.css` to customize the appearance. The design uses:
- CSS Grid and Flexbox for layouts
- CSS Custom Properties for consistent theming
- Responsive breakpoints for mobile support

### API Configuration
Update `API_BASE` in `js/api.js` to point to your backend server:
```javascript
const API_BASE = 'http://your-backend-server:8080';
```

### Features
The application is built with a modular architecture:
- Add new pages by extending the page routing in `app.js`
- Add new API endpoints by extending the API classes in `api.js`
- Add new authentication features in `auth.js`

## Browser Compatibility

- Modern browsers with ES6+ support
- Chrome 60+, Firefox 60+, Safari 12+, Edge 79+
- Requires JavaScript enabled
- Uses fetch API for HTTP requests

## Development

### Adding New Features

1. **New API Endpoints**: Add to appropriate API class in `api.js`
2. **New Pages**: Add page section to `index.html` and routing to `app.js`
3. **New Modals**: Add modal HTML to `index.html` and logic to `app.js`
4. **New Styles**: Add to `css/style.css` following the existing pattern

### Debugging

- Open browser developer tools (F12)
- Check console for JavaScript errors
- Check Network tab for API request/response details
- Use Application tab to inspect localStorage for auth data

## Security Notes

- Authentication uses HTTP Basic Auth over HTTPS (in production)
- User credentials are base64 encoded and stored in localStorage
- CORS is enabled for frontend-backend communication
- Role-based access control enforced on both frontend and backend

## Troubleshooting

### Cannot Connect to API
- Verify backend is running on port 8080
- Check CORS settings in backend
- Verify network connectivity

### Login Issues
- Check username/password combination
- Verify user exists in database
- Check browser console for auth errors

### Page Not Loading
- Verify all JavaScript files are loading
- Check browser console for errors
- Ensure proper file permissions on frontend files
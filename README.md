# CornHub
where repositories are kernels on a corn cob. Better than github fr fr

## 🚀 Quick Start

1. **Start the application:**
   ```bash
   ./start.sh
   ```

2. **Access the web interface:**
   - Frontend: http://localhost:8080/
   - API Documentation: http://localhost:8080/docs

3. **Create demo data (optional):**
   ```bash
   python3 create_demo_data.py
   ```

## 📁 Project Structure
```
cornhub/
├── app/                     # FastAPI backend application
│   ├── main.py             # FastAPI app & API endpoints
│   ├── models.py           # SQLAlchemy database models  
│   ├── json_dto.py         # Pydantic schemas (DTOs)
│   ├── crud.py             # Database operations & business logic
│   ├── auth.py             # Authentication & authorization
│   ├── git_ops.py          # Git operations (GitPython wrapper)
│   ├── mongo_store.py      # MongoDB operations for issues
│   ├── database_sessions.py # Database configuration
│   └── dependency_injector.py # Dependency injection
├── frontend/               # Web frontend interface
│   ├── index.html         # Main HTML application
│   ├── css/style.css      # Complete styling
│   ├── js/
│   │   ├── app.js         # Main application logic
│   │   ├── api.js         # API communication
│   │   └── auth.js        # Authentication handling
│   └── README.md          # Frontend documentation
├── tests/                  # Test files
├── dbms/                   # Python virtual environment
├── requirements.txt        # Python dependencies
├── start.sh               # Application startup script
├── create_demo_data.py    # Demo data creation script
└── README.md              # This file
```

## 🎯 Features

### Backend (FastAPI)
- **Repository Management**: Create and manage Git repositories
- **Issue Tracking**: Full issue lifecycle with threaded comments
- **User Management**: Role-based access control (admin/developer/tester)
- **Git Operations**: Clone, push, pull via Git protocol
- **Hybrid Database**: PostgreSQL + MongoDB architecture
- **API Documentation**: Auto-generated OpenAPI/Swagger docs

### Frontend (Web Interface)
- **Modern UI**: Responsive design with clean interface
- **Repository Browser**: Browse and create repositories
- **Issue Tracker**: Create issues, add comments, view threads
- **User Dashboard**: User management for administrators
- **Authentication**: Persistent login with role-based features
- **Real-time Updates**: Dynamic content loading and notifications

## 🛠️ Technology Stack

**Backend:**
- FastAPI (Python web framework)
- PostgreSQL (structured data)
- MongoDB (issue threads & comments) 
- SQLAlchemy (ORM)
- GitPython (Git operations)
- bcrypt (password hashing)

**Frontend:**
- Vanilla JavaScript (ES6+)
- HTML5 & CSS3
- Font Awesome icons
- Responsive CSS Grid/Flexbox

## 📋 Manual Setup

If you prefer manual setup instead of using `./start.sh`:

### Prerequisites
- Python 3.8+
- PostgreSQL
- MongoDB
- Git

### Backend Setup

1. **Create virtual environment:**
   ```bash
   python3 -m venv dbms
   source dbms/bin/activate
   pip install -r requirements.txt
   ```

2. **Setup databases:**
   ```bash
   # PostgreSQL (adjust credentials as needed)
   createdb devdb
   createuser devuser
   
   # MongoDB (usually runs as service)
   sudo systemctl start mongodb
   ```

3. **Start the application:**
   ```bash
   uvicorn app.main:app --reload --log-level=debug --port 8080
   ```

### Frontend Access
The frontend is automatically served by FastAPI at http://localhost:8080/

## 🔐 Authentication

### Default Users
Use the demo data script to create sample users, or create manually:

```bash
# Create a user via API
curl -X POST "http://localhost:8080/users" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "email": "admin@example.com", "password": "admin123"}'
```

### User Tiers
- **Admin**: Full system access, user management
- **Developer**: Create repositories, manage own repos
- **Tester**: View repositories, create/comment on issues

## 🐛 API Endpoints

### Repository Management
- `GET /repos` - List all repositories
- `POST /repos` - Create new repository (Developer+)
- `GET /repos/{id}/issues` - List repository issues
- `POST /repos/{id}/issues` - Create new issue

### Issue Tracking  
- `GET /repos/{id}/issues/{num}` - Get issue details
- `POST /repos/{id}/issues/{num}/comments` - Add comment

### User Management
- `GET /users` - List users (Admin only)
- `POST /users` - Create user
- `PATCH /users/{id}/tier` - Update user tier (Admin only)

### Git Operations
- `GET /git/{repo}.git/*` - Git HTTP protocol support
- Clone: `git clone http://localhost:8080/git/{repo}.git`

## 📊 Database Schema

### PostgreSQL Tables
- `user` - User accounts and permissions
- `repository` - Repository metadata 
- `issue` - Issue basic information
- `role` - Permission roles
- `user_repo_roles` - Repository access control

### MongoDB Collections
- `issue_threads` - Issue content and comment threads

## 🧪 Development

### Running Tests
```bash
python tests/test_auth.py
python tests/test_full_tiers.py
```

### API Documentation
Visit http://localhost:8080/docs for interactive API documentation.

### Project Architecture
- **main.py**: FastAPI routes and endpoint definitions
- **crud.py**: Business logic and database operations  
- **models.py**: SQLAlchemy database models
- **auth.py**: Authentication and authorization
- **git_ops.py**: Git repository operations
- **mongo_store.py**: MongoDB operations for flexible data

## 🚀 Production Deployment

1. **Environment Variables:**
   ```bash
   export POSTGRES_URL="postgresql://user:pass@host:5432/db"
   export MONGODB_URL="mongodb://host:27017" 
   ```

2. **HTTPS Setup:**
   Update CORS settings in main.py for your domain

3. **Database Security:**
   Configure proper database authentication and SSL

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Submit pull request

## 📝 License

This project is for educational purposes. Feel free to use and modify.

---

**CornHub** - *Where repositories are kernels on a corn cob* 🌽
UI


New feature


server.ip/repo.git

join user, repo, role

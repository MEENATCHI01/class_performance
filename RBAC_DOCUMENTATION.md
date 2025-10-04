# Role-Based Access Control (RBAC) Documentation

## Overview
Your Class Performance Tracking System now has comprehensive role-based access control implemented. The system supports three user roles with different permission levels.

## User Roles & Permissions

### 🔴 Admin (Full Access)
**Login Credentials:**
- Email: `admin@example.com`
- Password: `admin123`

**Permissions:**
- ✅ Mark attendance
- ✅ Enter and manage homework
- ✅ View attendance records (all ranges)
- ✅ View student reports
- ✅ Manage students (add/delete)
- ✅ Manage subjects (add/remove)
- ✅ View all student details

### 🔵 Teacher (Teaching Access)
**Login Credentials:**
- Email: `teacher@example.com`
- Password: `teacher123`

**Permissions:**
- ✅ Mark attendance
- ✅ Enter and manage homework
- ✅ View attendance records (all ranges)
- ✅ View student reports
- ✅ View all student details
- ❌ Cannot manage students/subjects

### 🟢 Student (Read-Only Access)
**Login Credentials:**
- Email: `student@example.com`
- Password: `student123`

**Permissions:**
- ✅ View their own attendance records only
- ❌ Cannot mark attendance
- ❌ Cannot enter homework
- ❌ Cannot view other students' records
- ❌ Cannot manage students/subjects

## Technical Implementation

### 1. Authentication Decorators

#### `@login_required`
Ensures user is logged in before accessing any protected route.

```python
@app.route("/front")
@login_required
def front():
    # Only accessible if user is logged in
```

#### `@role_required(*roles)`
Restricts access to specific roles only.

```python
@app.route("/mark")
@role_required('Teacher', 'Admin')
def mark_attendance():
    # Only Teachers and Admins can access
```

### 2. Route Protection Summary

| Route | Access Level |
|-------|-------------|
| `/login` | Public |
| `/logout` | Authenticated users |
| `/front` | All authenticated users |
| `/mark` | Teacher, Admin |
| `/homework` | Teacher, Admin |
| `/attendance-records` | Teacher, Admin |
| `/report` | Teacher, Admin |
| `/students` | Admin only |
| `/student/<name>` | All (Students see own only) |

### 3. Session Management

User information is stored in Flask sessions:
- `session['user']` - User email
- `session['role']` - User role (Student/Teacher/Admin)

### 4. Template-Level Access Control

The main template (`index.html`) dynamically shows/hides menu items based on user role:

```jinja2
{% if user_role == 'Admin' %}
    <!-- Show all options -->
{% elif user_role == 'Teacher' %}
    <!-- Show teaching options -->
{% elif user_role == 'Student' %}
    <!-- Show limited student options -->
{% endif %}
```

## Security Features

1. **Session-based authentication** - Secure session management
2. **Flash messages** - User feedback for unauthorized access attempts
3. **Automatic redirects** - Unauthorized users redirected to appropriate pages
4. **Logout functionality** - Secure session clearing on logout
5. **Role validation** - Server-side role checking on every protected route

## User Interface Enhancements

1. **Role badge display** - Visual indicator of current user role
2. **Logout button** - Easy access to logout functionality
3. **Flash messages** - Error and success notifications
4. **Conditional menus** - Role-appropriate navigation options
5. **User email display** - Shows currently logged-in user

## Testing the RBAC System

### Test as Admin:
1. Login with `admin@example.com` / `admin123`
2. Verify access to all features including "Manage Students & Subjects"
3. Try accessing all routes

### Test as Teacher:
1. Login with `teacher@example.com` / `teacher123`
2. Verify access to teaching features
3. Try accessing `/students` - should be denied

### Test as Student:
1. Login with `student@example.com` / `student123`
2. Verify limited access (only view own attendance)
3. Try accessing `/mark` or `/homework` - should be denied

## Adding New Users

To add new users, modify the `USERS` dictionary in `attendance_app.py`:

```python
USERS = {
    'Student': {
        'student@example.com': {'password': 'student123'},
        'newstudent@example.com': {'password': 'newpass123'}
    },
    'Teacher': {
        'teacher@example.com': {'password': 'teacher123'}
    },
    'Admin': {
        'admin@example.com': {'password': 'admin123'}
    },
}
```

**Note:** For production use, implement proper password hashing and database storage.

## Future Enhancements

Consider implementing:
1. Password hashing (bcrypt/werkzeug.security)
2. User management interface for admins
3. Database-backed user storage
4. Password reset functionality
5. Multi-factor authentication
6. Audit logging for sensitive operations
7. Session timeout settings
8. Remember me functionality

## Error Messages

Users will see appropriate flash messages when:
- Attempting to access pages without login
- Trying to access restricted pages
- Successfully logging out
- Invalid credentials during login

## Troubleshooting

**Issue:** User can't access expected pages
- **Solution:** Verify role is correctly set in session
- Check login credentials match the USERS dictionary

**Issue:** Flash messages not displaying
- **Solution:** Ensure templates include flash message block
- Verify Flask's secret_key is set

**Issue:** Session not persisting
- **Solution:** Check browser cookies are enabled
- Verify secret_key is consistent across restarts

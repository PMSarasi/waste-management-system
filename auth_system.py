"""
AUTHENTICATION SYSTEM - Login, Signup, Logout, Session Management
"""

import streamlit as st
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime

def init_auth_db():
    conn = sqlite3.connect("auth.db")
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        email TEXT,
        password TEXT,
        role TEXT,
        department TEXT,
        points INTEGER DEFAULT 0,
        correct_sorts INTEGER DEFAULT 0,
        total_scans INTEGER DEFAULT 0,
        created_at TEXT,
        last_login TEXT
    )''')
    
    conn.commit()
    conn.close()
    return True

def register_user(username, email, password, role, department):
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    if '@' not in email or '.' not in email:
        return False, "Please enter a valid email address"
    
    conn = sqlite3.connect("auth.db")
    c = conn.cursor()
    
    c.execute("SELECT id FROM users WHERE username=?", (username,))
    if c.fetchone():
        conn.close()
        return False, "Username already exists"
    
    c.execute("SELECT id FROM users WHERE email=?", (email,))
    if c.fetchone():
        conn.close()
        return False, "Email already registered"
    
    hashed = hashlib.sha256(password.encode()).hexdigest()
    try:
        c.execute("""INSERT INTO users (username, email, password, role, department, created_at, points) 
                     VALUES (?,?,?,?,?,?,?)""",
                  (username, email, hashed, role, department, datetime.now().isoformat(), 0))
        conn.commit()
        
        c.execute("SELECT id, username, role, department, points FROM users WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()
        return True, {'id': user[0], 'username': user[1], 'role': user[2], 'department': user[3], 'points': user[4]}
    except Exception as e:
        conn.close()
        return False, f"Error: {str(e)}"

def login_user(username, password):
    conn = sqlite3.connect("auth.db")
    c = conn.cursor()
    hashed = hashlib.sha256(password.encode()).hexdigest()
    c.execute("SELECT id, username, role, department, points FROM users WHERE username=? AND password=?", (username, hashed))
    user = c.fetchone()
    
    if user:
        c.execute("UPDATE users SET last_login=? WHERE id=?", (datetime.now().isoformat(), user[0]))
        conn.commit()
        conn.close()
        return True, {'id': user[0], 'username': user[1], 'role': user[2], 'department': user[3], 'points': user[4]}
    
    conn.close()
    return False, None

def get_leaderboard(limit=10):
    conn = sqlite3.connect("auth.db")
    df = pd.read_sql_query(f"SELECT username, department, points, correct_sorts, total_scans FROM users ORDER BY points DESC LIMIT {limit}", conn)
    conn.close()
    return df

def update_user_points(user_id, points_to_add, is_correct=True):
    conn = sqlite3.connect("auth.db")
    c = conn.cursor()
    if is_correct:
        c.execute("UPDATE users SET points = points + ?, correct_sorts = correct_sorts + 1, total_scans = total_scans + 1 WHERE id=?", (points_to_add, user_id))
    else:
        c.execute("UPDATE users SET total_scans = total_scans + 1 WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect("auth.db")
    df = pd.read_sql_query("SELECT id, username, email, role, department, points, created_at FROM users", conn)
    conn.close()
    return df

def init_session():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user = None
        st.session_state.role = None
        st.session_state.user_id = None
        st.session_state.username = None

def logout():
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.role = None
    st.session_state.user_id = None
    st.session_state.username = None

def is_authenticated():
    return st.session_state.get('logged_in', False)

def get_current_user():
    return st.session_state.get('user', None)

def get_user_role():
    return st.session_state.get('role', None)

def show_login_signup_ui():
    st.title("🏆 Ultimate AI Waste Management System")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])
        
        with tab1:
            st.markdown("### Welcome Back!")
            login_username = st.text_input("Username", key="login_username")
            login_password = st.text_input("Password", type="password", key="login_password")
            
            if st.button("Login", type="primary", use_container_width=True, key="login_btn"):
                if login_username and login_password:
                    success, user = login_user(login_username, login_password)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.user = user
                        st.session_state.role = user['role']
                        st.session_state.user_id = user['id']
                        st.session_state.username = user['username']
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
                else:
                    st.warning("Please enter username and password")
        
        with tab2:
            st.markdown("### Create New Account")
            
            with st.form("signup_form", clear_on_submit=True):
                signup_username = st.text_input("Username*", help="Minimum 3 characters")
                signup_email = st.text_input("Email*", help="Valid email address")
                signup_password = st.text_input("Password*", type="password", help="Minimum 6 characters")
                signup_confirm = st.text_input("Confirm Password*", type="password")
                signup_department = st.selectbox("Department", ["General", "Facilities", "Operations", "IT", "Management"])
                signup_role = st.selectbox("Role", ["worker", "manager"])
                
                submitted = st.form_submit_button("Create Account", type="primary", use_container_width=True)
                
                if submitted:
                    if not signup_username or not signup_email or not signup_password:
                        st.error("❌ Please fill all required fields")
                    elif signup_password != signup_confirm:
                        st.error("❌ Passwords do not match")
                    else:
                        success, result = register_user(signup_username, signup_email, signup_password, signup_role, signup_department)
                        if success:
                            st.session_state.logged_in = True
                            st.session_state.user = result
                            st.session_state.role = result['role']
                            st.session_state.user_id = result['id']
                            st.session_state.username = result['username']
                            st.success(f"✅ Welcome {signup_username}!")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(f"❌ {result}")

def show_logout_button():
    if st.sidebar.button("🚪 Logout", use_container_width=True, key="logout_btn"):
        logout()
        st.rerun()

def show_user_info():
    if is_authenticated():
        user = get_current_user()
        st.sidebar.markdown(f"### 👤 {user['username']}")
        st.sidebar.write(f"Role: {user['role']}")
        st.sidebar.write(f"Department: {user['department']}")
        st.sidebar.write(f"⭐ Points: {user['points']}")
        st.sidebar.markdown("---")

init_auth_db()
init_session()
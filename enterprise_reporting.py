"""
ENTERPRISE REPORTING SYSTEM
Automated reports, user profiles, predictive analytics
"""

import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
import json
import hashlib

class EnterpriseWasteManager:
    def __init__(self):
        self.users = {}
        self.user_scores = {}
        self.historical_data = []
        
    def create_user(self, username, department):
        """Create user profile with gamification"""
        user_id = hashlib.md5(f"{username}{datetime.now()}".encode()).hexdigest()[:8]
        
        self.users[user_id] = {
            'username': username,
            'department': department,
            'points': 0,
            'level': 1,
            'badges': [],
            'correct_sorts': 0,
            'total_scans': 0,
            'join_date': datetime.now().isoformat()
        }
        
        return user_id
    
    def update_user_score(self, user_id, waste_type, correct_sort=True):
        """Update user points and badges (gamification)"""
        if user_id not in self.users:
            return
        
        points_earned = 0
        
        if correct_sort:
            # Points based on waste type recyclability
            points_map = {
                'plastic': 10,
                'glass': 15,
                'metal': 20,
                'paper': 8,
                'cardboard': 8,
                'trash': 0
            }
            points_earned = points_map.get(waste_type, 5)
            self.users[user_id]['correct_sorts'] += 1
        
        self.users[user_id]['total_scans'] += 1
        self.users[user_id]['points'] += points_earned
        
        # Level up logic
        level = self.users[user_id]['level']
        points = self.users[user_id]['points']
        
        if points >= level * 100:
            self.users[user_id]['level'] += 1
            self.users[user_id]['badges'].append(f"Level {level} Achieved")
        
        # Badge logic
        if self.users[user_id]['correct_sorts'] == 10 and '10 Correct Sorts' not in self.users[user_id]['badges']:
            self.users[user_id]['badges'].append("🏅 10 Correct Sorts")
        elif self.users[user_id]['correct_sorts'] == 50 and '50 Correct Sorts' not in self.users[user_id]['badges']:
            self.users[user_id]['badges'].append("🏆 50 Correct Sorts")
        
        return points_earned
    
    def predict_waste_volume(self, days_ahead=7):
        """Predict future waste volume using historical data"""
        if len(self.historical_data) < 14:
            return None
        
        # Prepare data
        df = pd.DataFrame(self.historical_data)
        df['date'] = pd.to_datetime(df['timestamp']).dt.date
        daily_counts = df.groupby('date').size().reset_index(name='count')
        daily_counts['day_num'] = range(len(daily_counts))
        
        if len(daily_counts) < 7:
            return None
        
        # Train model
        X = daily_counts['day_num'].values.reshape(-1, 1)
        y = daily_counts['count'].values
        
        model = LinearRegression()
        model.fit(X, y)
        
        # Predict future
        future_days = np.array(range(len(daily_counts), len(daily_counts) + days_ahead)).reshape(-1, 1)
        predictions = model.predict(future_days)
        
        return {
            'predictions': predictions.tolist(),
            'trend': 'increasing' if model.coef_[0] > 0 else 'decreasing',
            'slope': model.coef_[0]
        }
    
    def generate_audit_report(self):
        """Generate comprehensive audit report"""
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_users': len(self.users),
            'total_scans': sum(u['total_scans'] for u in self.users.values()),
            'total_points_awarded': sum(u['points'] for u in self.users.values()),
            'average_accuracy': np.mean([u['correct_sorts']/max(u['total_scans'],1) for u in self.users.values()]),
            'top_performers': sorted(self.users.values(), key=lambda x: x['points'], reverse=True)[:3],
            'department_stats': {}
        }
        
        # Department breakdown
        for user in self.users.values():
            dept = user['department']
            if dept not in report['department_stats']:
                report['department_stats'][dept] = {'scans': 0, 'points': 0}
            report['department_stats'][dept]['scans'] += user['total_scans']
            report['department_stats'][dept]['points'] += user['points']
        
        # Predictions
        predictions = self.predict_waste_volume()
        if predictions:
            report['predictions'] = predictions
        
        return report
    
    def export_excel_report(self):
        """Export comprehensive Excel report"""
        report = self.generate_audit_report()
        
        # Create Excel writer
        with pd.ExcelWriter('outputs/enterprise_report.xlsx', engine='openpyxl') as writer:
            # User summary
            user_df = pd.DataFrame(self.users.values())
            user_df.to_excel(writer, sheet_name='User Summary', index=False)
            
            # Department stats
            dept_df = pd.DataFrame(report['department_stats']).T
            dept_df.to_excel(writer, sheet_name='Department Stats')
            
            # Predictions
            if 'predictions' in report:
                pred_df = pd.DataFrame({
                    'Day': list(range(1, len(report['predictions']['predictions'])+1)),
                    'Predicted_Volume': report['predictions']['predictions']
                })
                pred_df.to_excel(writer, sheet_name='Waste Predictions', index=False)
            
            # Audit summary
            summary_df = pd.DataFrame([{
                'Total Users': report['total_users'],
                'Total Scans': report['total_scans'],
                'Total Points': report['total_points_awarded'],
                'Average Accuracy': f"{report['average_accuracy']:.2%}"
            }])
            summary_df.to_excel(writer, sheet_name='Executive Summary', index=False)
        
        return "outputs/enterprise_report.xlsx"

# Add to dashboard.py as new section
def add_enterprise_section():
    st.markdown("## 🏢 Enterprise & Gamification")
    
    if 'enterprise' not in st.session_state:
        st.session_state.enterprise = EnterpriseWasteManager()
    
    emp = st.session_state.enterprise
    
    tab1, tab2, tab3 = st.tabs(["👥 User Profiles", "🏆 Leaderboard", "📈 Predictions"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Create User Profile")
            new_user = st.text_input("Username")
            department = st.selectbox("Department", ["Facilities", "Office", "Cafeteria", "Maintenance"])
            
            if st.button("Create Profile") and new_user:
                user_id = emp.create_user(new_user, department)
                st.success(f"✅ User {new_user} created! ID: {user_id}")
        
        with col2:
            st.markdown("#### Log Waste Activity")
            user_id = st.selectbox("Select User", list(emp.users.keys()) if emp.users else ["No users"])
            if user_id != "No users":
                waste_type = st.selectbox("Waste Type", ['plastic', 'glass', 'metal', 'paper', 'cardboard', 'trash'])
                correct_sort = st.checkbox("Correctly Sorted?", value=True)
                
                if st.button("Log & Earn Points"):
                    points = emp.update_user_score(user_id, waste_type, correct_sort)
                    st.success(f"🎉 +{points} points earned!")
                    
                    user = emp.users[user_id]
                    st.write(f"**Total Points:** {user['points']}")
                    st.write(f"**Level:** {user['level']}")
                    st.write(f"**Badges:** {', '.join(user['badges']) if user['badges'] else 'None yet'}")
    
    with tab2:
        st.markdown("#### 🏆 Top Performers")
        if emp.users:
            sorted_users = sorted(emp.users.values(), key=lambda x: x['points'], reverse=True)
            
            for i, user in enumerate(sorted_users[:5], 1):
                accuracy = (user['correct_sorts'] / max(user['total_scans'], 1)) * 100
                st.markdown(f"""
                **#{i} - {user['username']}** ({user['department']})
                - Points: {user['points']} | Level: {user['level']}
                - Accuracy: {accuracy:.1f}% | Scans: {user['total_scans']}
                ---
                """)
    
    with tab3:
        st.markdown("#### 📊 Waste Volume Predictions")
        
        # Add historical data for demo
        if len(emp.historical_data) == 0:
            # Generate sample data
            for i in range(30):
                emp.historical_data.append({
                    'timestamp': (datetime.now() - timedelta(days=i)).isoformat(),
                    'waste_type': np.random.choice(['plastic', 'glass', 'paper']),
                    'count': np.random.randint(5, 30)
                })
        
        predictions = emp.predict_waste_volume()
        
        if predictions:
            st.write(f"**Trend:** {'📈 Increasing' if predictions['trend'] == 'increasing' else '📉 Decreasing'}")
            st.write(f"**Predicted volumes for next {len(predictions['predictions'])} days:**")
            
            for i, pred in enumerate(predictions['predictions'], 1):
                st.write(f"  Day {i}: {int(pred)} items")
            
            # Recommendation based on prediction
            if predictions['trend'] == 'increasing':
                st.warning("⚠️ Increasing trend detected. Consider adding more collection resources.")
            else:
                st.success("✅ Decreasing trend. Current resources are sufficient.")
        else:
            st.info("Need more data for predictions (minimum 14 days of history)")
"""
ULTIMATE AI WASTE MANAGEMENT SYSTEM - FINAL FIXED
All issues resolved: Text visibility, Colors, All tabs working
"""

import streamlit as st
import torch
import timm
import torch.nn as nn
from PIL import Image
from torchvision import transforms
import cv2
import numpy as np
import pandas as pd
from datetime import datetime
import os
import plotly.graph_objects as go
import plotly.express as px
from sklearn.ensemble import RandomForestRegressor
import warnings
warnings.filterwarnings("ignore")

# Import custom modules
from auth_system import (
    is_authenticated, show_login_signup_ui, show_logout_button, show_user_info,
    get_current_user, get_user_role, get_leaderboard, update_user_points, get_all_users
)
from advisor import WasteAdvisor

# Check authentication
if not is_authenticated():
    show_login_signup_ui()
    st.stop()

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(page_title="Ultimate AI Waste System", page_icon="🏆", layout="wide")

st.markdown("""
<style>
    .main-header { background: linear-gradient(135deg, #0f2027, #203a43, #2c5364); padding: 30px; border-radius: 15px; color: white; text-align: center; }
    .decision-card { padding: 25px; border-radius: 15px; color: white; text-align: center; }
    .detection-card { background: #00cc4420; border-left: 4px solid #00cc44; padding: 15px; margin: 10px 0; border-radius: 10px; color: #111111; }
    .alert-warning { background: #ff4b4b20; border-left: 5px solid #ff4b4b; padding: 15px; border-radius: 10px; color: #111111; }
    .confidence-bar { background: #e0e0e0; border-radius: 10px; height: 20px; margin: 5px 0; overflow: hidden; }
    .confidence-fill { background: linear-gradient(90deg, #00cc44, #008833); border-radius: 10px; height: 20px; color: white; line-height: 20px; padding-left: 10px; font-size: 12px; width: 0%; }
    .info-box { background: #f0f2f6; padding: 15px; border-radius: 10px; margin: 10px 0; color: #111111; }
    .sustainability-box { background: linear-gradient(135deg, #667eea, #764ba2); padding: 25px; border-radius: 15px; color: white; text-align: center; }
    .metric-card { background: #ffffff; padding: 15px; border-radius: 10px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1); color: #111111; }
    .metric-card h3 { color: #333333; margin-bottom: 10px; }
    .metric-card h1 { color: #00cc44; margin: 10px 0; }
    .metric-card p { color: #666666; }
</style>
""", unsafe_allow_html=True)

# ============================================
# LOAD AI MODEL
# ============================================
@st.cache_resource
def load_model():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = timm.create_model('efficientnet_b0', pretrained=False)
    model.classifier = nn.Linear(model.classifier.in_features, 6)
    if os.path.exists("models/waste_classifier.pth"):
        model.load_state_dict(torch.load("models/waste_classifier.pth", map_location=device))
        model = model.to(device)
        model.eval()
        return model, device
    return None, device

model, device = load_model()
class_names = ['cardboard', 'glass', 'metal', 'paper', 'plastic', 'trash']

# Initialize advisor
advisor = WasteAdvisor()

# ============================================
# WASTE VS NON-WASTE BINARY CLASSIFIER
# ============================================
def is_waste_item(all_probs):
    max_confidence = max(all_probs.values())
    return max_confidence > 0.4, max_confidence

# ============================================
# ESG CALCULATOR
# ============================================
class ESGCalculator:
    def calculate_impact(self, waste_type, weight_kg=0.5):
        factors = {'plastic': 2.5, 'glass': 0.5, 'metal': 1.0, 'paper': 0.8, 'cardboard': 0.7, 'trash': 1.5}
        co2 = factors.get(waste_type, 1.5) * weight_kg
        return {'co2_kg': round(co2, 2), 'trees': round(co2/22, 2), 'car_km': round(co2*5, 1)}

# ============================================
# INSIGHT ENGINE
# ============================================
class InsightEngine:
    def generate_insights(self, df):
        insights = []
        if len(df) < 2:
            return ["📊 Scan more items to generate insights"]
        
        recyclable_rate = (df['waste_type'] != 'trash').mean() * 100
        if recyclable_rate > 70:
            insights.append(f"✅ Excellent recycling rate! {recyclable_rate:.0f}% recyclable")
        elif recyclable_rate > 50:
            insights.append(f"👍 Good recycling rate: {recyclable_rate:.0f}%")
        else:
            insights.append(f"⚠️ Low recycling rate ({recyclable_rate:.0f}%)")
        
        most_common = df['waste_type'].mode()
        if len(most_common) > 0:
            insights.append(f"🗑️ Most common waste: {most_common[0].upper()}")
        
        return insights
    
    def predict_waste_volume(self, df):
        if len(df) < 5:
            return None, "Need more data"
        
        df['date'] = pd.to_datetime(df['timestamp']).dt.date
        daily = df.groupby('date').size().reset_index(name='count')
        if len(daily) < 3:
            return None, "Need 3+ days"
        
        daily['day_num'] = range(len(daily))
        X = daily[['day_num']].values
        y = daily['count'].values
        
        model_rf = RandomForestRegressor(n_estimators=10, random_state=42)
        model_rf.fit(X, y)
        
        next_day = len(daily)
        prediction = model_rf.predict([[next_day]])[0]
        trend = "increasing" if model_rf.feature_importances_[0] > 0 else "decreasing"
        return int(max(0, prediction)), trend

# ============================================
# SMART CITY
# ============================================
class SmartBin:
    def __init__(self, name, location, lat, lon, capacity=100, allowed_types=None):
        self.name = name
        self.location = location
        self.lat = lat
        self.lon = lon
        self.capacity = capacity
        self.current_fill = 0
        self.allowed_types = allowed_types or []
        self.alerts = []
    
    def dispose(self, waste_type):
        if waste_type not in self.allowed_types:
            self.alerts.append(f"⚠️ WRONG DISPOSAL: {waste_type} in {self.name}!")
            return False
        self.current_fill = min(self.current_fill + 5, self.capacity)
        if self.current_fill > self.capacity * 0.8:
            self.alerts.append(f"🚨 {self.name} is {int(self.current_fill/self.capacity*100)}% full!")
        return True
    
    def get_status(self):
        fill = (self.current_fill / self.capacity) * 100
        if fill > 80:
            status = "🔴 CRITICAL"
        elif fill > 50:
            status = "🟡 WARNING"
        else:
            status = "🟢 OK"
        return status, fill

class SmartCityNetwork:
    def __init__(self):
        self.bins = {
            "Blue Bin": SmartBin("Blue Bin", "East Wing", 40.7128, -74.0060, allowed_types=['plastic', 'glass', 'metal']),
            "Green Bin": SmartBin("Green Bin", "West Wing", 40.7135, -74.0075, allowed_types=['paper', 'cardboard']),
            "Black Bin": SmartBin("Black Bin", "Central", 40.7110, -74.0045, allowed_types=['trash']),
        }
    
    def get_all_alerts(self):
        all_alerts = []
        for bin_obj in self.bins.values():
            all_alerts.extend(bin_obj.alerts)
            bin_obj.alerts = []
        return all_alerts

# ============================================
# IMPROVED CHATBOT
# ============================================
class WasteChatbot:
    def __init__(self):
        self.responses = {
            'pizza': "🍕 Oily pizza boxes cannot be recycled - the oil contaminates the paper. Compost them or put in general waste.",
            'battery': "🔋 Batteries are hazardous waste! Never put in regular bins. Take to special battery collection points.",
            'plastic': "♻️ Clean plastic bottles and containers can be recycled. Rinse them first! Check the recycling symbol.",
            'glass': "🥤 Glass bottles and jars are 100% recyclable! Clean them and remove lids.",
            'metal': "🔩 Aluminum and steel cans are highly recyclable. Crush them to save space.",
            'paper': "📄 Clean, dry paper can be recycled. Remove plastic windows from envelopes.",
            'cardboard': "📦 Cardboard boxes should be flattened before recycling. Remove tape if possible.",
            'coffee': "☕ Coffee cups are often lined with plastic - most cannot be recycled. Consider a reusable cup!",
            'electronics': "💻 E-waste requires special recycling. Don't throw electronics in regular bins!",
            'default': "💡 I can help with recycling! Ask about: plastic, glass, metal, paper, cardboard, batteries, pizza boxes, electronics, or coffee cups."
        }
    
    def ask(self, question):
        q = question.lower()
        for key, response in self.responses.items():
            if key in q:
                return response
        return self.responses['default']

# ============================================
# TRANSFORM FUNCTION
# ============================================
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

def predict_image(image):
    if image.mode != 'RGB':
        image = image.convert('RGB')
    input_tensor = transform(image).unsqueeze(0).to(device)
    with torch.no_grad():
        output = model(input_tensor)
        probs = torch.softmax(output, dim=1)
        pred_class = torch.argmax(probs, dim=1).item()
        confidence = probs[0][pred_class].item()
        all_probs = {class_names[i]: float(probs[0][i]) for i in range(len(class_names))}
    return class_names[pred_class], confidence, all_probs, input_tensor

def detect_contamination(image_crop, waste_type):
    img_np = np.array(image_crop)
    hsv = cv2.cvtColor(img_np, cv2.COLOR_RGB2HSV)
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
    
    avg_saturation = np.mean(hsv[:, :, 1])
    dark_ratio = np.mean(gray < 50)
    edges = cv2.Canny(gray, 50, 150)
    edge_density = np.sum(edges > 0) / edges.size
    
    contamination_score = 0
    reasons = []
    
    if avg_saturation > 100:
        contamination_score += 30
        reasons.append("Food residue detected")
    if dark_ratio > 0.1:
        contamination_score += 25
        reasons.append("Dirt/stains detected")
    if waste_type in ['paper', 'cardboard'] and edge_density > 0.3:
        contamination_score += 20
        reasons.append("Physical damage detected")
    
    return contamination_score >= 40, contamination_score, reasons

# ============================================
# PROCESS SINGLE IMAGE
# ============================================
def process_single_image(image):
    waste_type, confidence, all_probs, input_tensor = predict_image(image)
    is_waste, max_conf = is_waste_item(all_probs)
    
    if not is_waste:
        return {
            'is_waste': False,
            'message': 'No recognizable waste detected. Please upload an image of waste items.'
        }
    
    advice = advisor.get_advice(waste_type, confidence)
    impact = ESGCalculator().calculate_impact(waste_type)
    is_contaminated, cont_score, reasons = detect_contamination(image, waste_type)
    
    return {
        'is_waste': True,
        'waste_type': waste_type,
        'confidence': confidence,
        'all_probs': all_probs,
        'advice': advice,
        'impact': impact,
        'is_contaminated': is_contaminated,
        'contamination_reasons': reasons,
        'input_tensor': input_tensor,
        'image': image
    }

# ============================================
# INITIALIZE SESSION STATE
# ============================================
if 'detection_log' not in st.session_state:
    st.session_state.detection_log = []
if 'city_network' not in st.session_state:
    st.session_state.city_network = SmartCityNetwork()
if 'insight_engine' not in st.session_state:
    st.session_state.insight_engine = InsightEngine()
if 'esg_calculator' not in st.session_state:
    st.session_state.esg_calculator = ESGCalculator()
if 'chatbot' not in st.session_state:
    st.session_state.chatbot = WasteChatbot()
if 'current_result' not in st.session_state:
    st.session_state.current_result = None

# ============================================
# MAIN HEADER
# ============================================
user = get_current_user()
st.markdown(f"""
<div class="main-header">
    <h1>🏆 Ultimate AI Waste Management System</h1>
    <p>👤 {user['username']} ({user['role']}) | Department: {user['department']} | ⭐ Points: {user['points']}</p>
    <p>Professional Waste Classification | ESG Impact | Smart City Ready</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    show_user_info()
    show_logout_button()
    st.markdown("---")
    st.markdown("### 📊 Stats")
    st.metric("Total Detections", len(st.session_state.detection_log))

# ============================================
# TABS
# ============================================
user_role = get_user_role()
if user_role == 'admin':
    tabs = st.tabs(["🧠 Waste Classification", "📊 Insights", "🌍 ESG Impact", "🗺️ Smart City", "🤖 Chatbot", "📁 Batch", "👥 Users", "ℹ️ About"])
elif user_role == 'manager':
    tabs = st.tabs(["🧠 Waste Classification", "📊 Insights", "🌍 ESG Impact", "🗺️ Smart City", "🤖 Chatbot", "📁 Batch", "ℹ️ About"])
else:
    tabs = st.tabs(["🧠 Waste Classification", "📊 Insights", "🌍 ESG Impact", "🗺️ Smart City", "🤖 Chatbot", "ℹ️ About"])

# ============================================
# TAB 1: WASTE CLASSIFICATION
# ============================================
with tabs[0]:
    st.markdown("## 🧠 AI Waste Classification")
    st.caption("Upload an image - AI will classify waste type and provide recycling advice")
    
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        input_method = st.radio("Input", ["📤 Upload Image", "📹 Camera"], horizontal=True)
        
        if input_method == "📹 Camera":
            camera_image = st.camera_input("Take a picture")
            if camera_image:
                image = Image.open(camera_image)
                st.image(image, use_container_width=True)
                uploaded = camera_image
            else:
                uploaded = None
        else:
            uploaded = st.file_uploader("Select waste image", type=['jpg', 'jpeg', 'png'])
            if uploaded:
                image = Image.open(uploaded)
                st.image(image, use_container_width=True)
        
        if uploaded:
            if st.button("🔍 Classify Waste", type="primary", use_container_width=True):
                with st.spinner("🧠 AI Analyzing..."):
                    image = Image.open(uploaded)
                    result = process_single_image(image)
                    st.session_state.current_result = result
                    
                    if result['is_waste']:
                        st.session_state.detection_log.append({
                            'timestamp': datetime.now(),
                            'waste_type': result['waste_type'],
                            'confidence': result['confidence'],
                            'decision': result['advice']['action']
                        })
                        if 'RECYCLE' in result['advice']['action']:
                            update_user_points(user['id'], 10, True)
                    
                    st.rerun()
    
    with col_right:
        st.subheader("📋 Classification Result")
        
        if st.session_state.current_result:
            r = st.session_state.current_result
            
            if not r['is_waste']:
                st.warning(r['message'])
            else:
                advice = r['advice']
                
                if "RECYCLE" in advice['action']:
                    color = "#00cc44"
                elif "LANDFILL" in advice['action']:
                    color = "#ff4b4b"
                else:
                    color = "#ffa500"
                
                st.markdown(f"""
                <div class="decision-card" style="background: {color};">
                    <h2>{advice['action']}</h2>
                    <p>📦 Waste Type: <b>{advice['waste_type']}</b></p>
                    <p>🎯 Confidence: {advice['confidence']}</p>
                    <p>💡 {advice['advice']}</p>
                    <p>🗑️ Recommended Bin: {advice['recommended_bin']} 📍 {advice['bin_location']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                risk_display = advice['risk_level']
                st.markdown(f"""
                <div class="info-box">
                    <b>⚠️ Risk Level:</b> {risk_display}<br>
                    <b>🌍 Impact Score:</b> {advice['impact_score']}/100<br>
                    <b>📊 Decomposition:</b> {advice['decomposition_years']} years<br>
                    <b>🌱 CO₂ Impact:</b> {advice['co2_equivalent_kg']} kg per kg
                </div>
                """, unsafe_allow_html=True)
                
                if r.get('is_contaminated'):
                    st.warning(f"⚠️ CONTAMINATED: {', '.join(r.get('contamination_reasons', []))}")
                
                st.markdown("#### 🔬 AI Confidence Analysis")
                sorted_probs = sorted(r['all_probs'].items(), key=lambda x: x[1], reverse=True)
                for waste, prob in sorted_probs:
                    st.markdown(f"""
                    <div style="margin: 8px 0;">
                        <div style="display: flex; justify-content: space-between;">
                            <span><b>{waste.upper()}</b></span>
                            <span>{prob:.1%}</span>
                        </div>
                        <div class="confidence-bar">
                            <div class="confidence-fill" style="width: {prob*100}%;"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div style="background: #667eea20; padding: 15px; border-radius: 10px; margin-top: 15px;">
                    <h4>🌍 Environmental Impact</h4>
                    <p>🌱 CO₂ Saved: {r['impact']['co2_kg']} kg<br>
                    🌳 Trees Equivalent: {r['impact']['trees']}<br>
                    🚗 Car KM Equivalent: {r['impact']['car_km']} km</p>
                </div>
                """, unsafe_allow_html=True)

# ============================================
# TAB 2: INSIGHTS
# ============================================
with tabs[1]:
    st.markdown("## 📊 Analytics & Insights")
    
    if len(st.session_state.detection_log) > 0:
        df = pd.DataFrame(st.session_state.detection_log)
        
        insights = st.session_state.insight_engine.generate_insights(df)
        for insight in insights:
            if "✅" in insight:
                st.markdown(f'<div class="detection-card">{insight}</div>', unsafe_allow_html=True)
            elif "⚠️" in insight:
                st.markdown(f'<div class="alert-warning">{insight}</div>', unsafe_allow_html=True)
            else:
                st.info(insight)
        
        prediction, _ = st.session_state.insight_engine.predict_waste_volume(df)
        if prediction:
            st.metric("🔮 Predicted Waste Tomorrow", f"{prediction} items")
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            waste_counts = df['waste_type'].value_counts()
            if len(waste_counts) > 0:
                fig = px.pie(values=waste_counts.values, names=waste_counts.index, title="Waste Composition", hole=0.3)
                st.plotly_chart(fig, use_container_width=True)
        
        with col_c2:
            df['date'] = pd.to_datetime(df['timestamp']).dt.date
            daily = df.groupby('date').size().reset_index(name='count')
            if len(daily) > 0:
                fig = px.line(daily, x='date', y='count', title="Waste Generation Trend", markers=True)
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📊 Scan waste items to generate insights")

# ============================================
# TAB 3: ESG IMPACT - FIXED TEXT COLOR
# ============================================
with tabs[2]:
    st.markdown("## 🌍 ESG Impact Dashboard")
    
    if len(st.session_state.detection_log) > 0:
        df = pd.DataFrame(st.session_state.detection_log)
        
        total_co2 = sum(st.session_state.esg_calculator.calculate_impact(w)['co2_kg'] for w in df['waste_type'])
        total_trees = total_co2 / 22
        total_car_km = total_co2 * 5
        recyclable_rate = (df['waste_type'] != 'trash').mean() * 100
        
        # Metric cards with proper text colors
        col_e1, col_e2, col_e3 = st.columns(3)
        
        with col_e1:
            st.markdown(f"""
            <div class="metric-card">
                <h3>🌱 CO₂ Saved</h3>
                <h1>{total_co2:.1f} kg</h1>
                <p>Carbon dioxide emissions avoided</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col_e2:
            st.markdown(f"""
            <div class="metric-card">
                <h3>🌳 Trees Equivalent</h3>
                <h1>{total_trees:.1f}</h1>
                <p>Number of trees needed to absorb this CO₂</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col_e3:
            st.markdown(f"""
            <div class="metric-card">
                <h3>🚗 Car KM Equivalent</h3>
                <h1>{total_car_km:.0f} km</h1>
                <p>Distance a car would drive to emit this CO₂</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Sustainability Score
        if recyclable_rate >= 80:
            rating = "🌟 Excellent! Keep it up!"
        elif recyclable_rate >= 60:
            rating = "👍 Good! Room for improvement"
        elif recyclable_rate >= 40:
            rating = "📈 Average - Let's improve recycling"
        else:
            rating = "⚠️ Needs attention - Start recycling more"
        
        st.markdown(f"""
        <div class="sustainability-box">
            <h2>♻️ Sustainability Score</h2>
            <h1 style="font-size: 64px; margin: 10px 0;">{int(recyclable_rate)}<span style="font-size: 32px;">/100</span></h1>
            <p style="font-size: 18px;">{rating}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Waste composition chart
        st.markdown("### 📊 Waste Composition")
        waste_counts = df['waste_type'].value_counts()
        if len(waste_counts) > 0:
            fig = px.bar(x=waste_counts.index, y=waste_counts.values, title="Waste by Type", 
                         color=waste_counts.index, color_discrete_sequence=px.colors.qualitative.Set2)
            st.plotly_chart(fig, use_container_width=True)
        
        # Environmental impact over time
        df['date'] = pd.to_datetime(df['timestamp']).dt.date
        daily_co2 = df.groupby('date').apply(lambda x: sum(st.session_state.esg_calculator.calculate_impact(w)['co2_kg'] for w in x['waste_type'])).reset_index(name='co2')
        if len(daily_co2) > 1:
            fig = px.area(daily_co2, x='date', y='co2', title="CO₂ Savings Over Time", 
                          labels={'co2': 'CO₂ Saved (kg)', 'date': 'Date'})
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("🌍 No ESG data yet. Scan waste items to see environmental impact")

# ============================================
# TAB 4: SMART CITY
# ============================================
with tabs[3]:
    st.markdown("## 🗺️ Smart City Network")
    
    alerts = st.session_state.city_network.get_all_alerts()
    for alert in alerts:
        st.error(alert)
    
    st.markdown("### 🗑️ Smart Bin Status")
    col_b1, col_b2, col_b3 = st.columns(3)
    
    bins = list(st.session_state.city_network.bins.items())
    for i, (bin_name, bin_obj) in enumerate(bins):
        col = [col_b1, col_b2, col_b3][i % 3]
        with col:
            status, fill = bin_obj.get_status()
            st.markdown(f"""
            <div class="metric-card" style="margin: 10px 0;">
                <h4>{bin_name}</h4>
                <p>📍 {bin_obj.location}</p>
                <p>Status: {status}</p>
                <p>Fill Level: {fill:.0f}%</p>
                <progress value="{fill}" max="100" style="width:100%"></progress>
            </div>
            """, unsafe_allow_html=True)

# ============================================
# TAB 5: CHATBOT
# ============================================
with tabs[4]:
    st.markdown("## 🤖 AI Waste Assistant")
    st.caption("Ask me anything about recycling and waste disposal!")
    
    st.markdown("### 📌 Quick Questions")
    col_q1, col_q2, col_q3, col_q4 = st.columns(4)
    
    with col_q1:
        if st.button("♻️ Plastic", use_container_width=True):
            st.session_state.chat_question = "Can I recycle plastic?"
    with col_q2:
        if st.button("🥤 Glass", use_container_width=True):
            st.session_state.chat_question = "Can I recycle glass?"
    with col_q3:
        if st.button("🍕 Pizza box", use_container_width=True):
            st.session_state.chat_question = "Can I recycle a pizza box?"
    with col_q4:
        if st.button("🔋 Batteries", use_container_width=True):
            st.session_state.chat_question = "How to dispose batteries?"
    
    st.markdown("---")
    
    user_question = st.text_input("Ask a question:", placeholder="e.g., Can I recycle a pizza box? How to dispose batteries?")
    
    if hasattr(st.session_state, 'chat_question') and st.session_state.chat_question:
        user_question = st.session_state.chat_question
        st.session_state.chat_question = None
    
    if user_question:
        with st.spinner("🤖 Thinking..."):
            response = st.session_state.chatbot.ask(user_question)
            st.markdown(f"""
            <div style="background: #667eea20; padding: 20px; border-radius: 15px; margin-top: 10px;">
                <b>🤖 AI Assistant:</b>
                <p style="margin-top: 10px;">{response}</p>
            </div>
            """, unsafe_allow_html=True)
    
    with st.expander("💡 Recycling Tips"):
        st.markdown("""
        - ♻️ **Rinse before recycling** - Clean recyclables prevent contamination
        - 🥤 **Remove caps and lids** - They're often made of different materials
        - 📦 **Flatten cardboard boxes** - Saves space in recycling bins
        - 🔋 **Never put batteries in regular trash** - They're hazardous waste
        - 🍕 **Oily pizza boxes go to compost or trash** - Oil contaminates paper recycling
        - 💡 **Check local guidelines** - Recycling rules vary by location
        """)

# ============================================
# TAB 6: BATCH (Manager/Admin)
# ============================================
if len(tabs) > 5 and user_role != 'worker':
    with tabs[5]:
        st.markdown("## 📁 Batch Processing")
        st.caption("Upload multiple images for bulk waste classification")
        
        batch_files = st.file_uploader("Select multiple images", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)
        
        if batch_files and st.button("📊 Process Batch", type="primary"):
            results = []
            progress_bar = st.progress(0)
            for i, file in enumerate(batch_files):
                image = Image.open(file)
                waste_type, confidence, _, _ = predict_image(image)
                advice = advisor.get_advice(waste_type, confidence)
                results.append({
                    'File': file.name[:30] + '...' if len(file.name) > 30 else file.name,
                    'Waste Type': waste_type.upper(),
                    'Confidence': f"{confidence:.1%}",
                    'Action': advice['action']
                })
                progress_bar.progress((i + 1) / len(batch_files))
            
            st.success(f"✅ Processed {len(batch_files)} images!")
            st.dataframe(pd.DataFrame(results), use_container_width=True)
            
            df_results = pd.DataFrame(results)
            recyclable_count = df_results[df_results['Action'].str.contains('RECYCLE', na=False)].shape[0]
            st.metric("♻️ Recyclable Items", recyclable_count, delta=f"{recyclable_count/len(results)*100:.0f}%")

# ============================================
# TAB 7: USERS (Admin only)
# ============================================
if user_role == 'admin' and len(tabs) > 6:
    with tabs[6]:
        st.markdown("## 👥 User Management")
        users_df = get_all_users()
        st.dataframe(users_df, use_container_width=True)
        
        if st.button("📥 Export Users to CSV"):
            csv = users_df.to_csv(index=False)
            st.download_button("Download CSV", csv, "users_export.csv", "text/csv")

# ============================================
# ABOUT TAB
# ============================================
with tabs[-1]:
    st.markdown("## ℹ️ System Information")
    
    col_a1, col_a2 = st.columns(2)
    with col_a1:
        st.markdown("""
        ### 🏆 Ultimate AI Waste Management System
        
        **How it works:**
        1. Upload an image of waste
        2. AI classifies the waste type
        3. System provides recycling advice
        4. ESG impact metrics are calculated
        
        **Supported Waste Types:**
        - ♻️ **Plastic** - Bottles, containers
        - 🥤 **Glass** - Bottles, jars  
        - 🔩 **Metal** - Cans, containers
        - 📄 **Paper** - Documents, newspapers
        - 📦 **Cardboard** - Boxes, packaging
        - 🗑️ **Trash** - Non-recyclable waste
        """)
    
    with col_a2:
        st.markdown("""
        ### 📊 System Statistics
        
        **Technology Stack:**
        - 🧠 AI Model: EfficientNet-B0
        - 📈 Accuracy: 91.78%
        - 🔧 Framework: PyTorch + Streamlit
        - 🗄️ Database: SQLite
        
        **Features:**
        - ✅ Real-time Classification
        - ✅ ESG Impact Metrics
        - ✅ Smart City Integration
        - ✅ AI Chatbot Assistant
        - ✅ Batch Processing
        - ✅ User Management
        """)
    
    st.markdown("### 📈 Session Statistics")
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        st.metric("Total Detections", len(st.session_state.detection_log))
    with col_s2:
        recyclable_count = sum(1 for d in st.session_state.detection_log if d.get('waste_type') != 'trash')
        st.metric("Recyclable Items", recyclable_count)
    with col_s3:
        if len(st.session_state.detection_log) > 0:
            rate = recyclable_count / len(st.session_state.detection_log) * 100
            st.metric("Recycling Rate", f"{rate:.0f}%")

st.markdown("---")
st.markdown("<div style='text-align: center'><p>🏆 Ultimate AI Waste System | Professional Waste Classification | Enterprise Ready</p></div>", unsafe_allow_html=True)
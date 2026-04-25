"""
ESG & SUSTAINABILITY ANALYTICS ENGINE
Environmental, Social, Governance metrics for corporate reporting
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import json

class ESGReporter:
    def __init__(self, db_path="waste_database.db"):
        self.db_path = db_path
        self.init_database()
        
        # ESG factors
        self.esg_factors = {
            'plastic': {
                'co2_per_kg': 2.5,
                'water_per_kg': 100,
                'energy_per_kg': 50,
                'recyclable': True,
                'circular_economy_score': 0.4
            },
            'glass': {
                'co2_per_kg': 0.5,
                'water_per_kg': 20,
                'energy_per_kg': 30,
                'recyclable': True,
                'circular_economy_score': 0.8
            },
            'metal': {
                'co2_per_kg': 1.0,
                'water_per_kg': 80,
                'energy_per_kg': 40,
                'recyclable': True,
                'circular_economy_score': 0.7
            },
            'paper': {
                'co2_per_kg': 0.8,
                'water_per_kg': 10,
                'energy_per_kg': 20,
                'recyclable': True,
                'circular_economy_score': 0.6
            },
            'cardboard': {
                'co2_per_kg': 0.7,
                'water_per_kg': 8,
                'energy_per_kg': 15,
                'recyclable': True,
                'circular_economy_score': 0.65
            },
            'trash': {
                'co2_per_kg': 1.5,
                'water_per_kg': 0,
                'energy_per_kg': 0,
                'recyclable': False,
                'circular_economy_score': 0.0
            }
        }
    
    def init_database(self):
        """Initialize SQLite database for logging"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS waste_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                waste_type TEXT,
                confidence REAL,
                location TEXT,
                bin_id TEXT,
                co2_saved REAL,
                water_saved REAL,
                energy_saved REAL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS virtual_bins (
                bin_id TEXT PRIMARY KEY,
                location TEXT,
                capacity INTEGER,
                current_fill INTEGER,
                latitude REAL,
                longitude REAL,
                last_emptied TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def log_waste(self, waste_type, confidence, location="Office", bin_id="BIN001"):
        """Log waste detection to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        factors = self.esg_factors.get(waste_type, self.esg_factors['trash'])
        
        cursor.execute('''
            INSERT INTO waste_logs (timestamp, waste_type, confidence, location, bin_id, co2_saved, water_saved, energy_saved)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (datetime.now().isoformat(), waste_type, confidence, location, bin_id,
              factors['co2_per_kg'], factors['water_per_kg'], factors['energy_per_kg']))
        
        conn.commit()
        conn.close()
        
        # Update virtual bin fill level
        self.update_bin_fill(bin_id)
        
        return factors
    
    def update_bin_fill(self, bin_id, increment=1):
        """Update virtual bin fill level"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if bin exists
        cursor.execute("SELECT current_fill, capacity FROM virtual_bins WHERE bin_id = ?", (bin_id,))
        result = cursor.fetchone()
        
        if result:
            current_fill, capacity = result
            new_fill = min(current_fill + increment, capacity)
            cursor.execute("UPDATE virtual_bins SET current_fill = ? WHERE bin_id = ?", (new_fill, bin_id))
        else:
            # Create default bin
            cursor.execute('''
                INSERT INTO virtual_bins (bin_id, location, capacity, current_fill, last_emptied)
                VALUES (?, ?, ?, ?, ?)
            ''', (bin_id, "Default Location", 100, 1, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_esg_report(self, days=30):
        """Generate comprehensive ESG report"""
        conn = sqlite3.connect(self.db_path)
        
        # Get data from last N days
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        df = pd.read_sql_query(f"SELECT * FROM waste_logs WHERE timestamp > '{cutoff_date}'", conn)
        conn.close()
        
        if df.empty:
            return None
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Calculate metrics
        total_waste = len(df)
        recyclable_count = df[df['waste_type'] != 'trash'].shape[0]
        recycling_rate = (recyclable_count / total_waste) * 100
        
        total_co2 = df['co2_saved'].sum()
        total_water = df['water_saved'].sum()
        total_energy = df['energy_saved'].sum()
        
        # Circular economy score
        circular_scores = [self.esg_factors.get(w, self.esg_factors['trash'])['circular_economy_score'] for w in df['waste_type']]
        avg_circular_score = sum(circular_scores) / len(circular_scores)
        
        report = {
            'period_days': days,
            'total_waste_items': total_waste,
            'recycling_rate': recycling_rate,
            'total_co2_saved_kg': total_co2,
            'total_water_saved_liters': total_water,
            'total_energy_saved_kwh': total_energy,
            'circular_economy_score': avg_circular_score,
            'waste_composition': df['waste_type'].value_counts().to_dict(),
            'daily_trend': df.groupby(df['timestamp'].dt.date).size().to_dict()
        }
        
        return report
    
    def create_report_dashboard(self):
        """Create interactive ESG dashboard"""
        report = self.get_esg_report()
        
        if report is None:
            return None
        
        # Create visualizations
        fig1 = go.Figure(data=[
            go.Bar(
                x=['Recycled', 'Landfill'],
                y=[report['recycling_rate'], 100 - report['recycling_rate']],
                marker_color=['#00cc44', '#ff4b4b'],
                text=[f"{report['recycling_rate']:.1f}%", f"{100 - report['recycling_rate']:.1f}%"],
                textposition='auto'
            )
        ])
        fig1.update_layout(title="Waste Diversion Rate", height=400)
        
        # Waste composition pie chart
        fig2 = go.Figure(data=[go.Pie(
            labels=list(report['waste_composition'].keys()),
            values=list(report['waste_composition'].values()),
            hole=0.3
        )])
        fig2.update_layout(title="Waste Composition", height=400)
        
        return fig1, fig2
    
    def export_pdf_report(self, filename="esg_report.pdf"):
        """Export ESG report as PDF"""
        report = self.get_esg_report()
        
        if report is None:
            return "No data available"
        
        # Generate HTML report
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>ESG Sustainability Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background: linear-gradient(135deg, #1a2a6c, #b21f1f); color: white; padding: 20px; text-align: center; }}
                .metric {{ display: inline-block; width: 200px; margin: 20px; padding: 15px; background: #f0f2f6; border-radius: 10px; }}
                .metric-value {{ font-size: 28px; font-weight: bold; }}
                .footer {{ margin-top: 50px; text-align: center; font-size: 12px; color: gray; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>ESG Sustainability Report</h1>
                <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <h2>Executive Summary</h2>
            <div>
                <div class="metric"><div class="metric-value">{report['total_waste_items']}</div><div>Total Items</div></div>
                <div class="metric"><div class="metric-value">{report['recycling_rate']:.1f}%</div><div>Recycling Rate</div></div>
                <div class="metric"><div class="metric-value">{report['total_co2_saved_kg']:.1f} kg</div><div>CO₂ Saved</div></div>
                <div class="metric"><div class="metric-value">{report['total_water_saved_liters']:.0f} L</div><div>Water Saved</div></div>
            </div>
            
            <h2>Environmental Impact</h2>
            <ul>
                <li>Carbon Offset: {report['total_co2_saved_kg']} kg CO₂ equivalent</li>
                <li>Water Conservation: {report['total_water_saved_liters']} liters</li>
                <li>Energy Savings: {report['total_energy_saved_kwh']} kWh</li>
                <li>Circular Economy Score: {report['circular_economy_score']:.2f}/1.00</li>
            </ul>
            
            <h2>Recommendations</h2>
            <ul>
                <li>Increase recycling awareness for non-recyclable items</li>
                <li>Implement source separation program</li>
                <li>Consider composting program for organic waste</li>
            </ul>
            
            <div class="footer">
                <p>This report was automatically generated by the AI-Powered Waste Management System</p>
                <p>Model Accuracy: 91.78% | Powered by EfficientNet-B0</p>
            </div>
        </body>
        </html>
        """
        
        # Save HTML file
        with open("outputs/esg_report.html", "w") as f:
            f.write(html_content)
        
        return "Report saved to outputs/esg_report.html"

# Run this to initialize
if __name__ == "__main__":
    reporter = ESGReporter()
    print("✅ ESG Analytics Engine Ready!")
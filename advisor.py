"""
WASTE ADVISOR ENGINE - Provides recycling advice and recommendations
"""

class WasteAdvisor:
    def __init__(self):
        self.waste_data = {
            'plastic': {
                'action': '♻️ Recycle',
                'impact_score': 85,
                'advice': 'Rinse thoroughly before recycling. Avoid single-use plastics.',
                'decomposition_years': 450,
                'co2_impact': 2.5,
                'recommended_bin': 'Blue Bin',
                'bin_location': 'East Wing'
            },
            'glass': {
                'action': '♻️ Recycle',
                'impact_score': 75,
                'advice': 'Clean and sort by color. Glass is infinitely recyclable.',
                'decomposition_years': 4000,
                'co2_impact': 0.5,
                'recommended_bin': 'Blue Bin',
                'bin_location': 'East Wing'
            },
            'metal': {
                'action': '♻️ Recycle',
                'impact_score': 65,
                'advice': 'Crush to save space. Highly valuable for recycling.',
                'decomposition_years': 100,
                'co2_impact': 1.0,
                'recommended_bin': 'Blue Bin',
                'bin_location': 'East Wing'
            },
            'paper': {
                'action': '📄 Recycle',
                'impact_score': 30,
                'advice': 'Keep dry and clean. Remove any plastic windows.',
                'decomposition_years': 0.2,
                'co2_impact': 0.8,
                'recommended_bin': 'Green Bin',
                'bin_location': 'West Wing'
            },
            'cardboard': {
                'action': '📦 Recycle or Compost',
                'impact_score': 25,
                'advice': 'Flatten boxes. Can be composted if not coated.',
                'decomposition_years': 0.1,
                'co2_impact': 0.7,
                'recommended_bin': 'Green Bin',
                'bin_location': 'West Wing'
            },
            'trash': {
                'action': '🗑️ Landfill',
                'impact_score': 90,
                'advice': 'Try to reduce mixed waste. Separate recyclables next time.',
                'decomposition_years': 500,
                'co2_impact': 1.5,
                'recommended_bin': 'Black Bin',
                'bin_location': 'Central'
            }
        }
    
    def get_advice(self, waste_type, confidence):
        data = self.waste_data.get(waste_type, self.waste_data['trash'])
        
        # Risk level based on impact score
        if data['impact_score'] >= 70:
            risk = '🔴 HIGH RISK'
        elif data['impact_score'] >= 40:
            risk = '🟡 MEDIUM RISK'
        else:
            risk = '🟢 LOW RISK'
        
        return {
            'waste_type': waste_type.upper(),
            'confidence': f"{confidence:.1%}",
            'action': data['action'],
            'impact_score': data['impact_score'],
            'risk_level': risk,
            'advice': data['advice'],
            'decomposition_years': data['decomposition_years'],
            'co2_equivalent_kg': data['co2_impact'],
            'recommended_bin': data['recommended_bin'],
            'bin_location': data['bin_location']
        }

# Test the advisor
if __name__ == "__main__":
    advisor = WasteAdvisor()
    result = advisor.get_advice('plastic', 0.94)
    print("\n📋 ADVISOR OUTPUT:")
    for key, value in result.items():
        print(f"  {key}: {value}")
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
import dash
from dash import html, dcc, Input, Output, State, callback_context
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import warnings
import random
import time
import os
import io
from datetime import datetime, timedelta

warnings.filterwarnings('ignore')

# Initialize Flask app
server = Flask(__name__)
server.secret_key = 'hospital-portal-secret-key-2024'

# Sample user data
users = {
    'admin@hospital.com': {'password': 'admin123', 'role': 'admin', 'name': 'Hospital Admin'},
    'patient@hospital.com': {'password': 'patient123', 'role': 'user', 'name': 'John Patient', 'mobile': '1234567890'}
}

# Store OTPs temporarily
otp_storage = {}

# Sample data for appointments, records, and billing
appointments_data = {
    'upcoming': [
        {'id': 1, 'doctor': 'Dr. Sarah Johnson', 'specialty': 'Cardiology', 'date': 'Today, 2:30 PM', 'datetime': datetime.now().replace(hour=14, minute=30)},
        {'id': 2, 'doctor': 'Dr. Michael Chen', 'specialty': 'Dermatology', 'date': 'Tomorrow, 10:00 AM', 'datetime': datetime.now() + timedelta(days=1)},
        {'id': 3, 'doctor': 'Dr. Emily Davis', 'specialty': 'General Checkup', 'date': 'Dec 28, 11:15 AM', 'datetime': datetime.now().replace(month=12, day=28, hour=11, minute=15)}
    ],
    'past': [
        {'id': 4, 'doctor': 'Dr. Robert Wilson', 'specialty': 'Orthopedics', 'date': 'Dec 10, 2024 - 3:00 PM', 'summary': 'Follow-up for knee pain. Recommended physical therapy and prescribed anti-inflammatory medication.'},
        {'id': 5, 'doctor': 'Dr. Lisa Garcia', 'specialty': 'Pediatrics', 'date': 'Nov 25, 2024 - 9:30 AM', 'summary': 'Annual checkup. Patient is healthy and developing normally.'},
        {'id': 6, 'doctor': 'Dr. James Brown', 'specialty': 'Dentistry', 'date': 'Nov 15, 2024 - 1:15 PM', 'summary': 'Routine dental cleaning. No cavities detected.'}
    ]
}

payment_history = [
    {'id': 'nov-2024', 'date': 'Nov 15, 2024', 'description': 'Cardiology Consultation', 'amount': 150.00, 'status': 'Paid'},
    {'id': 'oct-2024', 'date': 'Oct 10, 2024', 'description': 'Laboratory Tests', 'amount': 85.50, 'status': 'Paid'},
    {'id': 'sep-2024', 'date': 'Sep 5, 2024', 'description': 'Primary Care Visit', 'amount': 75.00, 'status': 'Paid'},
    {'id': 'aug-2024', 'date': 'Aug 20, 2024', 'description': 'Prescription Medication', 'amount': 45.25, 'status': 'Paid'},
    {'id': 'jul-2024', 'date': 'Jul 12, 2024', 'description': 'Annual Physical', 'amount': 120.00, 'status': 'Paid'}
]

# =====================
# YOUR DASH APP INTEGRATION
# =====================

# Load data - for CodeSandbox, we'll create sample data if file doesn't exist
try:
    # Try to load your actual data file
    merged_data = pd.read_excel(r'merged_data.xlsx')
    print('Data Loaded')
except:
    # Create sample data for demo purposes
    print("Creating sample data for demo...")
    np.random.seed(42)
    sample_size = 1000
    
    merged_data = pd.DataFrame({
        'patient_id': range(1, sample_size + 1),
        'month': np.random.choice(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'], sample_size),
        'clinic': np.random.choice(['Cardiology', 'Pediatrics', 'Orthopedics', 'Dermatology'], sample_size),
        'age_group': np.random.choice(['18-30', '31-45', '46-60', '61+'], sample_size),
        'gender': np.random.choice(['Male', 'Female'], sample_size),
        'logins': np.random.poisson(8, sample_size),
        'secure_messages': np.random.poisson(3, sample_size),
        'appointments_scheduled': np.random.poisson(2, sample_size),
        'prescription_refills': np.random.poisson(1, sample_size),
        'telehealth_visits': np.random.poisson(1, sample_size),
        'portal_satisfaction_1_5': np.random.choice([1, 2, 3, 4, 5], sample_size, p=[0.05, 0.15, 0.3, 0.4, 0.1]),
        'prefers_mobile_app': np.random.choice([True, False], sample_size, p=[0.6, 0.4]),
        'barrier_primary': np.random.choice(['None', 'Technical Issues', 'Privacy Concerns', 'Complex Interface', 'Lack of Need'], sample_size)
    })
    
    # Calculate total engagement
    merged_data['total_engagement'] = (
        merged_data['logins'] + 
        merged_data['secure_messages'] + 
        merged_data['appointments_scheduled'] +
        merged_data['prescription_refills'] +
        merged_data['telehealth_visits']
    )

# Initialize your Dash app
dash_app = dash.Dash(
    __name__,
    server=server,
    url_base_pathname='/admin-dashboard/',
    suppress_callback_exceptions=True
)

# =====================
# YOUR CHART CREATION FUNCTIONS
# =====================

def create_trend_chart(data, size='large'):
    monthly = data.groupby('month').agg({
        'logins': 'sum',
        'secure_messages': 'sum',
        'appointments_scheduled': 'sum',
        'patient_id': 'nunique'
    }).reset_index()

    height = 500 if size == 'large' else 140
    show_legend = size == 'large'

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=monthly['month'], y=monthly['logins'],
                            name='Logins', line=dict(color='#3498db', width=3)))
    fig.add_trace(go.Scatter(x=monthly['month'], y=monthly['secure_messages'],
                            name='Messages', line=dict(color='#e74c3c', width=3)))
    fig.add_trace(go.Scatter(x=monthly['month'], y=monthly['appointments_scheduled'],
                            name='Appointments', line=dict(color='#27ae60', width=3)))

    fig.update_layout(
        title='📈 Monthly Trends' if size == 'small' else '📈 Monthly Portal Usage Trends',
        template='plotly_white',
        hovermode='x unified',
        height=height,
        showlegend=show_legend,
        margin=dict(l=40, r=20, t=50, b=40) if size == 'large' else dict(l=20, r=20, t=40, b=20),
        font=dict(size=12 if size == 'large' else 10)
    )

    if size == 'small':
        fig.update_layout(
            xaxis=dict(showticklabels=False, title=None),
            yaxis=dict(showticklabels=False, title=None)
        )
    else:
        fig.update_layout(
            xaxis_title='Month',
            yaxis_title='Count'
        )

    return fig

def create_clinic_chart(data, size='large'):
    clinic_stats = data.groupby('clinic').agg({
        'total_engagement': 'mean',
        'portal_satisfaction_1_5': 'mean',
        'patient_id': 'nunique'
    }).reset_index()

    height = 500 if size == 'large' else 140

    fig = px.bar(clinic_stats, x='clinic', y='total_engagement',
                 title='🏥 Clinic Performance' if size == 'small' else '🏥 Average Engagement by Clinic',
                 color='portal_satisfaction_1_5',
                 color_continuous_scale='Viridis')

    fig.update_layout(
        template='plotly_white',
        height=height,
        margin=dict(l=40, r=20, t=50, b=40) if size == 'large' else dict(l=20, r=20, t=40, b=20),
        font=dict(size=12 if size == 'large' else 10)
    )

    if size == 'small':
        fig.update_layout(
            xaxis=dict(showticklabels=False, title=None),
            yaxis=dict(showticklabels=False, title=None),
            coloraxis_showscale=False
        )

    return fig

def create_feature_chart(data, size='large'):
    feature_totals = {
        'Feature': ['Logins', 'Secure Messages', 'Appointments', 'Prescription Refills', 'Telehealth'],
        'Count': [
            data['logins'].sum(),
            data['secure_messages'].sum(),
            data['appointments_scheduled'].sum(),
            data['prescription_refills'].sum(),
            data['telehealth_visits'].sum()
        ]
    }
    feature_df = pd.DataFrame(feature_totals)

    height = 500 if size == 'large' else 140

    fig = px.pie(feature_df, values='Count', names='Feature',
                 title='🎯 Feature Usage' if size == 'small' else '🎯 Portal Feature Usage Distribution',
                 color_discrete_sequence=px.colors.qualitative.Set3)

    fig.update_layout(
        template='plotly_white',
        height=height,
        margin=dict(l=40, r=20, t=50, b=40) if size == 'large' else dict(l=20, r=20, t=40, b=20),
        font=dict(size=12 if size == 'large' else 10),
        showlegend=size == 'large'
    )

    return fig

def create_demographic_chart(data, size='large'):
    demo_stats = data.groupby('age_group').agg({
        'total_engagement': 'mean',
        'portal_satisfaction_1_5': 'mean'
    }).reset_index()

    height = 500 if size == 'large' else 140

    fig = px.bar(demo_stats, x='age_group', y='total_engagement',
                 title='👥 Demographics' if size == 'small' else '👥 Engagement by Age Group',
                 color='portal_satisfaction_1_5',
                 color_continuous_scale='Plasma')

    fig.update_layout(
        template='plotly_white',
        height=height,
        margin=dict(l=40, r=20, t=50, b=40) if size == 'large' else dict(l=20, r=20, t=40, b=20),
        font=dict(size=12 if size == 'large' else 10)
    )

    if size == 'small':
        fig.update_layout(
            xaxis=dict(showticklabels=False, title=None),
            yaxis=dict(showticklabels=False, title=None),
            coloraxis_showscale=False
        )

    return fig

def create_satisfaction_chart(data, size='large'):
    sat_dist = data['portal_satisfaction_1_5'].value_counts().sort_index()

    height = 500 if size == 'large' else 140

    fig = px.bar(x=sat_dist.index, y=sat_dist.values,
                 title='😊 Satisfaction' if size == 'small' else '😊 Satisfaction Score Distribution',
                 color=sat_dist.values,
                 color_continuous_scale='RdYlGn')

    fig.update_layout(
        template='plotly_white',
        height=height,
        margin=dict(l=40, r=20, t=50, b=40) if size == 'large' else dict(l=20, r=20, t=40, b=20),
        font=dict(size=12 if size == 'large' else 10)
    )

    if size == 'small':
        fig.update_layout(
            xaxis=dict(showticklabels=False, title=None),
            yaxis=dict(showticklabels=False, title=None),
            coloraxis_showscale=False
        )
    else:
        fig.update_layout(
            xaxis_title='Satisfaction Score (1-5)',
            yaxis_title='Number of Patients'
        )

    return fig

def create_barriers_chart(data, size='large'):
    barrier_counts = data['barrier_primary'].value_counts()

    height = 500 if size == 'large' else 140

    fig = px.bar(x=barrier_counts.values, y=barrier_counts.index, orientation='h',
                 title='🚧 Barriers' if size == 'small' else '🚧 Primary Barriers to Portal Usage',
                 color=barrier_counts.values,
                 color_continuous_scale='Reds')

    fig.update_layout(
        template='plotly_white',
        height=height,
        margin=dict(l=40, r=20, t=50, b=40) if size == 'large' else dict(l=20, r=20, t=40, b=20),
        font=dict(size=12 if size == 'large' else 10)
    )

    if size == 'small':
        fig.update_layout(
            xaxis=dict(showticklabels=False, title=None),
            yaxis=dict(showticklabels=False, title=None),
            coloraxis_showscale=False
        )
    else:
        fig.update_layout(
            xaxis_title='Number of Patients',
            yaxis_title='Barrier Type'
        )

    return fig

# =====================
# YOUR DASH LAYOUT
# =====================

dash_app.index_string = '''
<!DOCTYPE html>
<html>
<head>
    {%metas%}
    <title>Patient Portal Analytics Dashboard</title>
    {%favicon%}
    {%css%}
    <style>
        body {
            margin: 0;
            font-family: "Segoe UI", Roboto, Arial, sans-serif;
            background: linear-gradient(135deg, #0f766e 0%, #4338ca 100%);
            color: #e6eef8;
        }

        .header {
            padding: 22px 24px;
            text-align: center;
            background: linear-gradient(90deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
            margin-bottom: 8px;
            box-shadow: 0 6px 18px rgba(0,0,0,0.15);
        }

        .filter-card {
            position: fixed;
            left: 24px;
            top: 120px;
            width: 240px;
            padding: 18px;
            background: rgba(255,255,255,0.12);
            border-radius: 20px;
            box-shadow: 0 8px 30px rgba(0,0,0,0.25);
            color: #050505;
            z-index: 1100;
        }
        .filter-card label { color: #f0f7fb; font-weight: 600; font-size: 13px; }

        .kpi-row { display:flex; gap:18px; justify-content:center; margin-left: 300px; padding: 8px 20px; }
        .kpi-card {
            min-width: 200px;
            background: rgba(255,255,255,0.9);
            color: #0b2545;
            border-radius: 10px;
            padding: 14px;
            text-align:center;
            box-shadow: 0 8px 24px rgba(0,0,0,0.15);
            transition: transform 0.25s ease, box-shadow 0.25s ease;
        }
        .kpi-card:hover { transform: translateY(-6px); box-shadow: 0 14px 30px rgba(0,0,0,0.25); }

        .content {
            display: flex;
            gap: 20px;
            margin-left: 300px;
            padding: 18px 28px 40px 28px;
        }

        .main-card {
            flex: 1.6;
            background: rgba(255,255,255,0.98);
            border-radius: 12px;
            padding: 14px;
            box-shadow: 0 10px 28px rgba(2,6,23,0.2);
        }

        .thumb-row {
            display:flex;
            gap:20px;
            justify-content: center;
            margin-top: 12px;
            flex-wrap: nowrap;
            overflow-x: auto;
            margin-left: 260px;
            margin-right: 36px;
            padding-bottom: 28px;
        }

        .thumb-graph {
            min-width: 220px;
            height: 140px;
            background: rgba(255,255,255,0.95);
            border-radius: 8px;
            padding: 6px;
            box-shadow: 0 6px 18px rgba(0,0,0,0.12);
            transition: transform 0.25s ease, box-shadow 0.25s ease;
            cursor: pointer;
        }
        .thumb-graph:hover { transform: translateY(-6px); box-shadow: 0 12px 28px rgba(0,0,0,0.18); }

        @keyframes fadeZoom {
          0%   { opacity: 0; transform: scale(0.98); }
          100% { opacity: 1; transform: scale(1); }
        }
        .graph-animate { animation: fadeZoom 0.5s cubic-bezier(.2,.8,.2,1); }

        @media (max-width: 1000px) {
            .content { flex-direction: column; margin-left: 20px; }
            .kpi-row { margin-left: 20px; flex-wrap:wrap; }
            .filter-card { position: static; width: auto; margin: 10px; }
            .thumb-row { margin-left: 20px; margin-right: 20px; }
        }
    </style>
</head>
<body>
    {%app_entry%}
    <footer>
        {%config%}
        {%scripts%}
        {%renderer%}
    </footer>
</body>
</html>
'''

dash_app.layout = html.Div([
    html.Div([
        html.H1("Patient Portal Analytics Dashboard", style={'margin': 0, 'color': '#eaf6ff'}),
        html.P("Interactive analysis of patient engagement, satisfaction, and portal usage",
               style={'margin': 0, 'color': 'rgba(234,246,255,0.85)', 'fontSize': 14})
    ], className='header'),

    dcc.Store(id='main-chart-index', data=0),

    html.Div([
        html.H4("Filters", style={'marginTop': 0, 'color': '#fff'}),
        html.Label("Clinic:", style={'display': 'block', 'marginTop': '8px'}),
        dcc.Dropdown(
            id='clinic-filter',
            options=[{'label': 'All Clinics', 'value': 'all'}] +
                    [{'label': c, 'value': c} for c in merged_data['clinic'].unique()],
            value='all', clearable=False
        ),
        html.Label("Age Group:", style={'display': 'block', 'marginTop': '10px'}),
        dcc.Dropdown(
            id='age-filter',
            options=[{'label': 'All Ages', 'value': 'all'}] +
                    [{'label': a, 'value': a} for a in merged_data['age_group'].unique()],
            value='all', clearable=False
        ),
        html.Label("Gender:", style={'display': 'block', 'marginTop': '10px'}),
        dcc.Dropdown(
            id='gender-filter',
            options=[{'label': 'All Genders', 'value': 'all'}] +
                    [{'label': g, 'value': g} for g in merged_data['gender'].unique()],
            value='all', clearable=False
        ),
    ], className='filter-card'),

    html.Div([
        html.Div([
            html.Div([
                html.Div("Total Patients", style={'fontWeight': 700}),
                html.Div(id="kpi-total-patients", style={'fontSize': 22, 'marginTop': 6}),
                html.Div("Active Portal Users", style={'fontSize': 12, 'color': '#5b6b84', 'marginTop': 6})
            ], className='kpi-card')
        ]),
        html.Div([
            html.Div([
                html.Div("Avg Monthly Logins", style={'fontWeight': 700}),
                html.Div(id="kpi-avg-logins", style={'fontSize': 22, 'marginTop': 6}),
                html.Div("Per Patient", style={'fontSize': 12, 'color': '#5b6b84', 'marginTop': 6})
            ], className='kpi-card')
        ]),
        html.Div([
            html.Div([
                html.Div("Satisfaction Score", style={'fontWeight': 700}),
                html.Div(id="kpi-satisfaction", style={'fontSize': 22, 'marginTop': 6}),
                html.Div("Portal Experience", style={'fontSize': 12, 'color': '#5b6b84', 'marginTop': 6})
            ], className='kpi-card')
        ]),
        html.Div([
            html.Div([
                html.Div("Mobile Preference", style={'fontWeight': 700}),
                html.Div(id="kpi-mobile", style={'fontSize': 22, 'marginTop': 6}),
                html.Div("Mobile App Users", style={'fontSize': 12, 'color': '#5b6b84', 'marginTop': 6})
            ], className='kpi-card')
        ]),
        # NEW KPI CARD ADDED HERE
        html.Div([
            html.Div([
                html.Div("Feature Utilization", style={'fontWeight': 700}),
                html.Div(id="kpi-feature-utilization", style={'fontSize': 22, 'marginTop': 6}),
                html.Div("Portal Feature Usage", style={'fontSize': 12, 'color': '#5b6b84', 'marginTop': 6})
            ], className='kpi-card')
        ])
    ], className='kpi-row'),

    html.Div([
        html.Div([
            dcc.Graph(id='main-graph', className='graph-animate', config={'displayModeBar': False})
        ], className='main-card'),
    ], className='content'),

    html.Div([
        html.Div([
            html.Div([dcc.Graph(id='thumb-1', config={'displayModeBar': False})], className='thumb-graph', id='thumb-container-1'),
            html.Div([dcc.Graph(id='thumb-2', config={'displayModeBar': False})], className='thumb-graph', id='thumb-container-2'),
            html.Div([dcc.Graph(id='thumb-3', config={'displayModeBar': False})], className='thumb-graph', id='thumb-container-3'),
            html.Div([dcc.Graph(id='thumb-4', config={'displayModeBar': False})], className='thumb-graph', id='thumb-container-4'),
            html.Div([dcc.Graph(id='thumb-5', config={'displayModeBar': False})], className='thumb-graph', id='thumb-container-5'),
        ], className='thumb-row')
    ]),

    html.Div([
        html.Hr(style={'borderColor': 'rgba(255,255,255,0.06)'}),
        html.P("🔒 HIPAA Compliance: De-identified aggregate data only. Access restricted to authorized personnel.",
               style={'color': 'rgba(234,246,255,0.75)', 'textAlign': 'center', 'fontSize': 12, 'paddingBottom': 30})
    ], style={'marginLeft': 260, 'marginRight': 36})
])

# =====================
# YOUR CALLBACKS
# =====================

@dash_app.callback(
    Output('main-chart-index', 'data'),
    [Input(f'thumb-container-{i}', 'n_clicks') for i in range(1,6)],
    State('main-chart-index', 'data'),
    prevent_initial_call=True
)
def on_thumb_click(click1, click2, click3, click4, click5, current_main):
    ctx = callback_context
    if not ctx.triggered:
        return current_main

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    thumb_index = int(triggered_id.split('-')[-1]) - 1

    all_indices = list(range(6))
    available_indices = [i for i in all_indices if i != current_main]

    if thumb_index < len(available_indices):
        new_main_index = available_indices[thumb_index]
        return new_main_index

    return current_main

@dash_app.callback(
    [Output('main-graph', 'figure')] +
    [Output(f'thumb-{i}', 'figure') for i in range(1,6)] +
    [Output('kpi-total-patients', 'children'),
     Output('kpi-avg-logins', 'children'),
     Output('kpi-satisfaction', 'children'),
     Output('kpi-mobile', 'children'),
     Output('kpi-feature-utilization', 'children')],  # NEW OUTPUT ADDED
    [Input('clinic-filter','value'), Input('age-filter','value'), Input('gender-filter','value'),
     Input('main-chart-index', 'data')]
)
def render_charts(clinic_val, age_val, gender_val, main_idx):
    df = merged_data.copy()
    if clinic_val != 'all':
        df = df[df['clinic'] == clinic_val]
    if age_val != 'all':
        df = df[df['age_group'] == age_val]
    if gender_val != 'all':
        df = df[df['gender'] == gender_val]

    total_patients = df['patient_id'].nunique()
    avg_logins = df.groupby('patient_id')['logins'].mean().mean()
    avg_satisfaction = df['portal_satisfaction_1_5'].mean()
    mobile_users = df['prefers_mobile_app'].mean() * 100
    
    # NEW CALCULATION: Portal Feature Utilization Rate
    # Count patients who used at least one of the 4 key features
    feature_columns = ['secure_messages', 'appointments_scheduled', 'prescription_refills', 'telehealth_visits']
    patients_with_feature_usage = df[df[feature_columns].sum(axis=1) > 0]['patient_id'].nunique()
    feature_utilization_rate = (patients_with_feature_usage / total_patients) * 100 if total_patients > 0 else 0

    # Create all charts
    chart_functions = [
        create_trend_chart,
        create_clinic_chart,
        create_feature_chart,
        create_demographic_chart,
        create_satisfaction_chart,
        create_barriers_chart
    ]

    main_fig = chart_functions[main_idx](df, 'large')
    main_fig.update_layout(transition={'duration': 500, 'easing': 'cubic-in-out'})

    thumb_indices = [i for i in range(6) if i != main_idx]
    thumb_figs = [chart_functions[i](df, 'small') for i in thumb_indices]

    return [main_fig] + thumb_figs + [
        f"{total_patients:,}",
        f"{avg_logins:.1f}",
        f"{avg_satisfaction:.1f}/5",
        f"{mobile_users:.1f}%",
        f"{feature_utilization_rate:.1f}%"  # NEW KPI VALUE
    ]

# =====================
# NEW FLASK ROUTES FOR FUNCTIONALITY
# =====================

@server.route('/reschedule-appointment', methods=['POST'])
def reschedule_appointment():
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    data = request.json
    appointment_id = data.get('appointment_id')
    new_date = data.get('new_date')
    
    try:
        # Parse the ISO format datetime from frontend
        new_datetime = datetime.fromisoformat(new_date.replace('Z', '+00:00'))
        
        # Format it for display
        formatted_date = new_datetime.strftime('%b %d, %Y - %I:%M %p')
        
        # Find and update appointment
        for appointment in appointments_data['upcoming']:
            if appointment['id'] == appointment_id:
                appointment['date'] = formatted_date
                appointment['datetime'] = new_datetime
                return jsonify({
                    'success': True, 
                    'message': f'Appointment rescheduled to {formatted_date}'
                })
        
        return jsonify({'success': False, 'message': 'Appointment not found'})
        
    except ValueError as e:
        print(f"Date parsing error: {e}")
        return jsonify({
            'success': False, 
            'message': 'Invalid date format. Please try again.'
        })
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({
            'success': False, 
            'message': 'An error occurred while rescheduling.'
        })

@server.route('/cancel-appointment', methods=['POST'])
def cancel_appointment():
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    data = request.json
    appointment_id = data.get('appointment_id')
    
    # Find and remove appointment
    for i, appointment in enumerate(appointments_data['upcoming']):
        if appointment['id'] == appointment_id:
            cancelled_appointment = appointments_data['upcoming'].pop(i)
            appointments_data['past'].append({
                **cancelled_appointment,
                'summary': 'Appointment was cancelled by patient.',
                'date': f"Cancelled - {cancelled_appointment['date']}"
            })
            return jsonify({'success': True, 'message': 'Appointment cancelled successfully'})
    
    return jsonify({'success': False, 'message': 'Appointment not found'})

@server.route('/get-appointment-summary', methods=['POST'])
def get_appointment_summary():
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    data = request.json
    appointment_id = data.get('appointment_id')
    
    # Find appointment summary
    for appointment in appointments_data['past']:
        if appointment['id'] == appointment_id:
            return jsonify({
                'success': True, 
                'summary': appointment.get('summary', 'No summary available'),
                'doctor': appointment['doctor'],
                'specialty': appointment['specialty'],
                'date': appointment['date']
            })
    
    return jsonify({'success': False, 'message': 'Appointment summary not found'})

@server.route('/download-record/<record_type>/<int:record_id>')
def download_record(record_type, record_id):
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    # Create a simple text file for demo purposes
    content = f"Medical Record - {record_type.upper()}\n"
    content += f"Patient: {session.get('name', 'Unknown')}\n"
    content += f"Download Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    content += "="*50 + "\n"
    
    # Add record-specific content
    if record_type == 'visit':
        content += "VISIT SUMMARY\n"
        content += "This would contain detailed visit information in a real system.\n"
    elif record_type == 'lab':
        content += "LABORATORY REPORT\n"
        content += "This would contain lab results in a real system.\n"
    elif record_type == 'imaging':
        content += "IMAGING REPORT\n"
        content += "This would contain imaging findings in a real system.\n"
    
    content += "\nThis is a demo file. In a real system, this would be a properly formatted medical document."
    
    # Create file in memory
    file_like = io.BytesIO(content.encode('utf-8'))
    
    return send_file(
        file_like,
        as_attachment=True,
        download_name=f"{record_type}_record_{record_id}.txt",
        mimetype='text/plain'
    )

@server.route('/download-all-records')
def download_all_records():
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    # Create comprehensive record file
    content = f"COMPLETE MEDICAL RECORDS\n"
    content += f"Patient: {session.get('name', 'Unknown')}\n"
    content += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    content += "="*50 + "\n\n"
    
    content += "This file contains a summary of all medical records.\n"
    content += "In a real system, this would include:\n"
    content += "- Complete visit histories\n"
    content += "- Laboratory results\n"
    content += "- Imaging reports\n"
    content += "- Prescription history\n"
    content += "- Immunization records\n"
    content += "- Medical history\n\n"
    content += "For security and privacy, actual medical records would be properly formatted and encrypted."
    
    file_like = io.BytesIO(content.encode('utf-8'))
    
    return send_file(
        file_like,
        as_attachment=True,
        download_name=f"complete_medical_records_{datetime.now().strftime('%Y%m%d')}.txt",
        mimetype='text/plain'
    )

@server.route('/download-receipt/<receipt_id>')
def download_receipt(receipt_id):
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    # Find the payment
    payment = next((p for p in payment_history if p['id'] == receipt_id), None)
    if not payment:
        return jsonify({'success': False, 'message': 'Receipt not found'})
    
    # Create receipt content
    content = f"MEDICAL PAYMENT RECEIPT\n"
    content += "="*50 + "\n"
    content += f"Patient: {session.get('name', 'Unknown')}\n"
    content += f"Receipt ID: {receipt_id}\n"
    content += f"Date: {payment['date']}\n"
    content += f"Description: {payment['description']}\n"
    content += f"Amount: ${payment['amount']:.2f}\n"
    content += f"Status: {payment['status']}\n"
    content += "="*50 + "\n"
    content += "Thank you for your payment!\n"
    content += "Hospital Billing Department\n"
    content += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    
    file_like = io.BytesIO(content.encode('utf-8'))
    
    return send_file(
        file_like,
        as_attachment=True,
        download_name=f"receipt_{receipt_id}.txt",
        mimetype='text/plain'
    )

@server.route('/view-statements')
def view_statements():
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    # Create statements content
    content = f"BILLING STATEMENTS\n"
    content += "="*50 + "\n"
    content += f"Patient: {session.get('name', 'Unknown')}\n"
    content += f"Period: January 2024 - December 2024\n"
    content += "="*50 + "\n\n"
    
    total_amount = sum(p['amount'] for p in payment_history)
    
    for payment in payment_history:
        content += f"Date: {payment['date']}\n"
        content += f"Service: {payment['description']}\n"
        content += f"Amount: ${payment['amount']:.2f}\n"
        content += f"Status: {payment['status']}\n"
        content += "-" * 30 + "\n"
    
    content += f"\nTotal Amount: ${total_amount:.2f}\n"
    content += "All payments are complete and up to date.\n"
    
    file_like = io.BytesIO(content.encode('utf-8'))
    
    return send_file(
        file_like,
        as_attachment=True,
        download_name=f"billing_statements_{datetime.now().strftime('%Y%m')}.txt",
        mimetype='text/plain'
    )

@server.route('/payment-methods')
def payment_methods():
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    # Return available payment methods
    return jsonify({
        'success': True,
        'payment_methods': [
            {'type': 'credit_card', 'name': 'Credit Card', 'last4': '4242', 'expiry': '12/25'},
            {'type': 'bank_account', 'name': 'Bank Account', 'last4': '8637'},
            {'type': 'paypal', 'name': 'PayPal', 'email': 'patient@example.com'}
        ]
    })

@server.route('/billing-alerts', methods=['POST'])
def billing_alerts():
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    data = request.json
    alert_type = data.get('alert_type')
    enabled = data.get('enabled')
    
    return jsonify({
        'success': True,
        'message': f'{alert_type} alerts {"enabled" if enabled else "disabled"} successfully'
    })

# =====================
# EXISTING FLASK ROUTES
# =====================

@server.route('/')
def login_page():
    return render_template('login.html')

@server.route('/get-otp', methods=['POST'])
def get_otp():
    mobile = request.json.get('mobile')
    
    if not mobile or len(mobile) != 10 or not mobile.isdigit():
        return jsonify({'success': False, 'message': 'Please enter a valid 10-digit mobile number'})
    
    # Only allow the specific demo patient
    if mobile != '1234567890':
        return jsonify({
            'success': False, 
            'message': 'Your phone number is not valid as it is not registered with us. Please contact admin if you think there is a mistake'
        })
    
    otp = str(random.randint(1000, 999999))
    otp_storage[mobile] = {
        'otp': otp,
        'timestamp': time.time(),
        'verified': False
    }
    
    print(f"OTP for {mobile}: {otp}")  # For testing
    
    return jsonify({'success': True, 'message': 'OTP sent successfully', 'otp': otp})  # Return OTP for demo

@server.route('/verify-otp', methods=['POST'])
def verify_otp():
    mobile = request.json.get('mobile')
    otp_entered = request.json.get('otp')
    remember_me = request.json.get('remember_me', False)
    
    if mobile in otp_storage:
        stored_otp = otp_storage[mobile]
        
        if time.time() - stored_otp['timestamp'] > 300:
            return jsonify({'success': False, 'message': 'OTP expired'})
        
        if stored_otp['otp'] == otp_entered:
            session['user'] = f"user_{mobile}"
            session['role'] = 'user'
            session['name'] = f"Patient {mobile}"
            session['mobile'] = mobile
            session['remember_me'] = remember_me
            
            otp_storage[mobile]['verified'] = True
            return jsonify({'success': True, 'message': 'Login successful'})
    
    return jsonify({'success': False, 'message': 'Invalid OTP'})

@server.route('/admin-login', methods=['POST'])
def admin_login():
    email = request.form['email']
    password = request.form['password']
    
    if email in users and users[email]['password'] == password:
        session['user'] = email
        session['role'] = users[email]['role']
        session['name'] = users[email]['name']
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'message': 'Invalid credentials'})

@server.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')
    return render_template('dashboard.html', user=session)

@server.route('/appointments')
def appointments():
    if 'user' not in session:
        return redirect('/')
    return render_template('appointments.html', user=session)

@server.route('/messages')
def messages():
    if 'user' not in session:
        return redirect('/')
    return render_template('messages.html', user=session)

@server.route('/records')
def records():
    if 'user' not in session:
        return redirect('/')
    return render_template('records.html', user=session)

@server.route('/bill-pay')
def bill_pay():
    if 'user' not in session:
        return redirect('/')
    return render_template('bill_pay.html', user=session)

@server.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@server.route('/admin-dashboard')
def admin_dashboard_auth():
    if 'user' not in session or session['role'] != 'admin':
        return redirect('/')
    return dash_app.index()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    server.run(debug=False, host='0.0.0.0', port=port)

from flask import Flask, render_template, request, jsonify
from .tracker import fetch_chart_data, analyze_indicators, ALLOWED_RANGES

app = Flask(__name__)
app.config.from_mapping(SECRET_KEY="dev")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stock/<symbol>/chart')
def api_chart(symbol):
    range_key = request.args.get('range','1d')
    try:
        data = fetch_chart_data(symbol, range_key)
        return jsonify({'symbol': symbol.upper(), 'range': range_key, 'data': data})
    except ValueError:
        return jsonify({'error': 'טווח לא נתמך'}), 400

@app.route('/api/stock/<symbol>/analysis')
def api_analysis(symbol):
    range_key = request.args.get('range','1d')
    analysis = analyze_indicators(symbol, range_key)
    return jsonify(analysis)

@app.route('/health')
def health():
    return jsonify({'status':'ok'})

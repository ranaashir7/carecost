from flask import Flask, render_template, request, jsonify, Response
from main import (
    get_icd10_codes_with_descriptions, 
    get_complete_cost_analysis, 
    is_valid_zip,
    chatbot
)
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

@app.route('/')
def index():
    """Main page with symptom input form"""
    return render_template('index.html')

@app.route('/api/search-icd', methods=['POST'])
def search_icd_codes():
    """API endpoint to search for ICD-10 codes based on symptom"""
    try:
        data = request.get_json()
        symptom = data.get('symptom', '').strip()
        
        if not symptom:
            return jsonify({'error': 'Symptom is required'}), 400
        
        # Get ICD codes with descriptions
        icd_codes = get_icd10_codes_with_descriptions(symptom)
        
        if not icd_codes:
            return jsonify({'error': 'No matching ICD-10 codes found for this symptom'}), 404
        
        return jsonify({
            'success': True,
            'symptom': symptom,
            'icd_codes': icd_codes
        })
        
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/api/validate-zip', methods=['POST'])
def validate_zip_code():
    """API endpoint to validate zip code"""
    try:
        data = request.get_json()
        zip_code = data.get('zip_code', '').strip()
        
        if not zip_code:
            return jsonify({'error': 'Zip code is required'}), 400
        
        is_valid = is_valid_zip(zip_code)
        
        return jsonify({
            'valid': is_valid,
            'zip_code': zip_code
        })
        
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/api/analyze-costs', methods=['POST'])
def analyze_costs():
    """API endpoint to perform complete cost analysis"""
    try:
        data = request.get_json()
        symptom = data.get('symptom', '').strip()
        icd_selection_index = data.get('icd_selection_index')
        zip_code = data.get('zip_code', '').strip()
        
        # Validate inputs
        if not symptom:
            return jsonify({'error': 'Symptom is required'}), 400
        
        if icd_selection_index is None:
            return jsonify({'error': 'ICD selection is required'}), 400
        
        if not zip_code:
            return jsonify({'error': 'Zip code is required'}), 400
        
        # Perform analysis
        result = get_complete_cost_analysis(symptom, icd_selection_index, zip_code)
        
        if 'error' in result:
            return jsonify({'error': result['error']}), 400
        
        return jsonify({
            'success': True,
            'analysis': result
        })
        
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/results')
def results():
    """Results page template"""
    return render_template('results.html')

@app.route('/api/chatbot', methods=['POST'])
def chatbot_api():
    """API endpoint for chatbot interactions"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Get chatbot response
        response = chatbot(query)
        
        return jsonify({
            'success': True,
            'query': query,
            'response': response
        })
        
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/chatbot')
def chatbot_page():
    """Chatbot page template"""
    return render_template('chatbot.html')

@app.route('/feedback')
def feedback_page():
    """Feedback page template"""
    return render_template('feedback.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

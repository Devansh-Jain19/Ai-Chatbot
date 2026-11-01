import os
import uuid
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from src.nlp_engine import NLPProcessor
from src.database import init_db, log_interaction, log_feedback, get_analytics

app = Flask(__name__, template_folder='../templates', static_folder='../static')
CORS(app)

# Initialize Database and NLP Engine
init_db()
nlp = NLPProcessor()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    user_message = data.get('message', '').strip()
    session_id = data.get('session_id') or str(uuid.uuid4())
    
    if not user_message:
        return jsonify({'error': 'Message cannot be empty'}), 400
        
    result = nlp.predict_intent(user_message, session_id=session_id)
    
    log_id = log_interaction(
        session_id=session_id,
        user_message=user_message,
        bot_response=result['response'],
        intent=result['tag'],
        confidence=result['confidence'],
        context=result['context'],
        sentiment=result['sentiment']
    )
    
    return jsonify({
        'log_id': log_id,
        'session_id': session_id,
        'response': result['response'],
        'intent': result['tag'],
        'confidence': result['confidence'],
        'context': result['context'],
        'sentiment': result['sentiment']
    })

@app.route('/api/feedback', methods=['POST'])
def feedback():
    data = request.get_json() or {}
    session_id = data.get('session_id')
    log_id = data.get('log_id')
    rating = data.get('rating') # 1 for thumbs up, -1 for thumbs down
    comment = data.get('comment', '')
    
    if rating not in [1, -1]:
        return jsonify({'error': 'Invalid rating value'}), 400
        
    log_feedback(session_id, log_id, rating, comment)
    return jsonify({'status': 'success', 'message': 'Feedback recorded'})

@app.route('/api/analytics', methods=['GET'])
def analytics():
    stats = get_analytics()
    return jsonify(stats)

@app.route('/api/reset-session', methods=['POST'])
def reset_session():
    data = request.get_json() or {}
    session_id = data.get('session_id')
    if session_id:
        nlp.reset_context(session_id)
    return jsonify({'status': 'success', 'message': 'Session context cleared'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

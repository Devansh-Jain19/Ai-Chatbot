import unittest
import json
import os
import sys

# Ensure root directory is on python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app import app
from src.nlp_engine import NLPProcessor
from src.database import init_db, log_interaction, get_analytics

class ChatbotSystemTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = app.test_client()
        cls.nlp = NLPProcessor()

    def test_nlp_intent_classification(self):
        """Test NLP recognition for FAQ queries"""
        queries = [
            ("Where is my order?", "order_tracking"),
            ("What payment options do you support?", "payment_methods"),
            ("How do I request a refund?", "refund_policy"),
            ("Can I speak with a customer agent?", "human_support")
        ]
        for query, expected_tag in queries:
            result = self.nlp.predict_intent(query)
            self.assertEqual(result['tag'], expected_tag, f"Failed on query: {query}")
            self.assertGreater(result['confidence'], 0.25)

    def test_context_flow(self):
        """Test multi-turn context tracking"""
        session_id = "test_context_session"
        # Turn 1: user asks to track order
        res1 = self.nlp.predict_intent("I want to track my order", session_id=session_id)
        self.assertEqual(res1['context'], "awaiting_order_id")

        # Turn 2: user provides order number
        res2 = self.nlp.predict_intent("Here is my tracking ORD-94821", session_id=session_id)
        self.assertEqual(res2['tag'], "order_id_provided")

    def test_chat_api_endpoint(self):
        """Test Flask /api/chat endpoint and SQLite logging"""
        response = self.client.post('/api/chat', json={
            'message': 'What is your refund policy?',
            'session_id': 'test_api_sess'
        })
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('response', data)
        self.assertEqual(data['intent'], 'refund_policy')
        self.assertIn('log_id', data)

    def test_analytics_endpoint(self):
        """Test /api/analytics endpoint"""
        response = self.client.get('/api/analytics')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('total_messages', data)
        self.assertIn('intents_breakdown', data)

if __name__ == '__main__':
    unittest.main()

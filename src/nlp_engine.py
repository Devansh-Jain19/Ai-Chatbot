import json
import os
import re
import math
import random
from collections import Counter
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords

class NLPProcessor:
    def __init__(self, intents_path=None):
        if intents_path is None:
            intents_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'intents.json')
        self.intents_path = intents_path
        self.lemmatizer = WordNetLemmatizer()
        
        try:
            self.stop_words = set(stopwords.words('english'))
        except Exception:
            self.stop_words = {"a", "an", "the", "in", "on", "at", "to", "for", "is", "it"}
            
        self.intents = []
        self.documents = []  # list of (lemmatized_tokens, tag)
        self.vocabulary = []
        self.idf = {}
        self.pattern_vectors = [] # list of (vector, tag)
        
        self.context_memory = {} # session_id -> current context state
        
        self.load_intents()
        self.train_model()

    def clean_and_tokenize(self, sentence):
        """Tokenize, lowercase, strip punctuation, and lemmatize tokens."""
        # Clean regex
        sentence = re.sub(r'[^a-zA-Z0-9\s]', ' ', sentence.lower())
        tokens = sentence.split()
        lemmas = [self.lemmatizer.lemmatize(w) for w in tokens if w not in self.stop_words]
        if not lemmas:
            # Fallback if sentence was entirely short stopwords like "Hi" or "How is it"
            lemmas = [self.lemmatizer.lemmatize(w) for w in tokens]
        return lemmas

    def load_intents(self):
        with open(self.intents_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.intents = data.get('intents', [])

    def train_model(self):
        """Build TF-IDF representations for all intent patterns."""
        self.documents = []
        all_words = set()
        
        for intent in self.intents:
            tag = intent['tag']
            for pattern in intent['patterns']:
                tokens = self.clean_and_tokenize(pattern)
                if tokens:
                    self.documents.append((tokens, tag))
                    for t in tokens:
                        all_words.add(t)

        self.vocabulary = sorted(list(all_words))
        N = len(self.documents)
        
        # Calculate IDF
        self.idf = {}
        for word in self.vocabulary:
            doc_count = sum(1 for doc_tokens, _ in self.documents if word in doc_tokens)
            self.idf[word] = math.log((N + 1) / (doc_count + 1)) + 1.0

        # Build TF-IDF vectors for documents
        self.pattern_vectors = []
        for doc_tokens, tag in self.documents:
            vec = self.compute_tfidf(doc_tokens)
            self.pattern_vectors.append((vec, tag))

    def compute_tfidf(self, tokens):
        """Compute normalized TF-IDF vector for given tokens."""
        tf = Counter(tokens)
        total_tokens = len(tokens) if tokens else 1
        vec = []
        norm_sq = 0.0
        
        for word in self.vocabulary:
            term_freq = tf.get(word, 0) / total_tokens
            tfidf_val = term_freq * self.idf.get(word, 1.0)
            vec.append(tfidf_val)
            norm_sq += tfidf_val ** 2
            
        norm = math.sqrt(norm_sq)
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec

    def cosine_similarity(self, vec1, vec2):
        return sum(a * b for a, b in zip(vec1, vec2))

    def analyze_sentiment(self, text):
        """Rule-based lexicon sentiment analyzer."""
        positive_words = {'good', 'great', 'awesome', 'excellent', 'happy', 'love', 'helpful', 'thanks', 'wonderful', 'perfect', 'fast', 'nice'}
        negative_words = {'bad', 'terrible', 'worst', 'horrible', 'angry', 'hate', 'unhappy', 'broken', 'slow', 'fail', 'error', 'wrong', 'sucks', 'poor'}
        
        tokens = set(re.findall(r'\b\w+\b', text.lower()))
        pos_matches = len(tokens & positive_words)
        neg_matches = len(tokens & negative_words)
        
        if pos_matches > neg_matches:
            return "positive"
        elif neg_matches > pos_matches:
            return "negative"
        return "neutral"

    def predict_intent(self, user_message, session_id="default"):
        """Classify input message into intent using Cosine Similarity on TF-IDF + Context matching."""
        tokens = self.clean_and_tokenize(user_message)
        if not tokens:
            return {
                "tag": "unknown",
                "confidence": 0.0,
                "response": "Could you please rephrase or elaborate on that? I'm here to help!",
                "context": self.context_memory.get(session_id, ""),
                "sentiment": "neutral"
            }

        input_vec = self.compute_tfidf(tokens)
        current_context = self.context_memory.get(session_id, "")
        
        scored_intents = []
        for vec, tag in self.pattern_vectors:
            sim = self.cosine_similarity(input_vec, vec)
            scored_intents.append((sim, tag))
            
        scored_intents.sort(key=lambda x: x[0], reverse=True)
        top_score, best_tag = scored_intents[0] if scored_intents else (0.0, "unknown")

        # Fuzzy check for direct order IDs or numbers if currently awaiting_order_id
        if current_context == "awaiting_order_id" and (re.search(r'\d{3,}', user_message) or "ord" in user_message.lower()):
            best_tag = "order_id_provided"
            top_score = max(top_score, 0.95)

        sentiment = self.analyze_sentiment(user_message)

        # Confidence threshold
        threshold = 0.28
        matched_intent = None
        
        if top_score >= threshold:
            for intent in self.intents:
                if intent['tag'] == best_tag:
                    # Check context filter if required
                    if 'context_filter' in intent and intent['context_filter']:
                        if intent['context_filter'] == current_context:
                            matched_intent = intent
                            break
                    else:
                        matched_intent = intent
                        break

        # Fallback if no intent or under threshold
        if not matched_intent:
            response_text = (
                "I'm not quite sure I understand. Could you please provide more details, "
                "or type 'human support' to connect directly with a representative?"
            )
            return {
                "tag": "fallback",
                "confidence": round(float(top_score), 3),
                "response": response_text,
                "context": current_context,
                "sentiment": sentiment
            }

        # Update context state
        new_context = matched_intent.get('context_set', '')
        if new_context is not None:
            self.context_memory[session_id] = new_context

        chosen_response = random.choice(matched_intent['responses'])
        return {
            "tag": matched_intent['tag'],
            "confidence": round(float(top_score), 3),
            "response": chosen_response,
            "context": self.context_memory[session_id],
            "sentiment": sentiment
        }

    def reset_context(self, session_id):
        if session_id in self.context_memory:
            del self.context_memory[session_id]

# NexusAI - Intelligent NLP-Powered Customer Support Chatbot

An enterprise-ready, intelligent customer service chatbot built with **Natural Language Processing (NLP)**, **Python (NLTK)**, **Flask**, and **SQLite**. Designed to automate FAQs, handle order tracking, remember conversation context across turns, and log interactions with real-time feedback and metrics.

---

## 🌟 Key Features

- **Natural Language Processing (NLP) Engine**:
  - WordNet Lemmatization, Stopword Filtering, and Custom Tokenization via **NLTK**.
  - Term Frequency-Inverse Document Frequency (**TF-IDF**) vectorization for intent classification.
  - Cosine Similarity scoring with adaptive confidence thresholds and fallback handling.
- **Contextual Memory & Multi-Turn Conversations**:
  - Stateful session tracking enabling follow-up questions (e.g. asking to track an order $\rightarrow$ awaiting order ID $\rightarrow$ confirming package status).
- **Sentiment Analysis**:
  - Lexicon-based sentiment detection on each query (Positive, Neutral, Negative).
- **SQLite Interaction Logging & Analytics**:
  - Automatic persistence of conversation logs, predicted intent, confidence score, sentiment, and timestamp.
  - User feedback system (thumbs up / thumbs down) linked directly to response logs.
  - In-app interactive SQLite log viewer modal and real-time analytics dashboard.
- **Modern Glassmorphic UI**:
  - Ultra-sleek dark theme with gradients, micro-animations, quick FAQ chips, responsive layout, and mobile-friendly design.

---

## 📁 Project Architecture

```
Ai-Chatbot/
├── data/
│   ├── intents.json          # Knowledge base of support intents, patterns, and responses
│   └── chatbot.db            # SQLite database (auto-generated on first run)
├── src/
│   ├── app.py                # Flask application & REST API endpoints
│   ├── database.py           # SQLite connection, schema, logging & analytics
│   └── nlp_engine.py         # NLTK tokenization, TF-IDF, sentiment & context engine
├── static/
│   ├── app.js                # Frontend client logic, state management, & API handling
│   └── style.css             # Glassmorphism dark aesthetic styling
├── templates/
│   └── index.html            # Main web interface
├── tests/
│   └── test_chatbot.py       # Automated unit and integration test suite
├── .gitignore                # Ignored files (virtualenvs, SQLite db, cache)
├── requirements.txt          # Python dependencies
└── README.md                 # Project documentation
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
Ensure you have **Python 3.9+** installed.

### 2. Clone the Repository
```bash
git clone https://github.com/Devansh-Jain19/Ai-Chatbot.git
cd Ai-Chatbot
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Download NLTK Corpora (if not already downloaded)
```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab'); nltk.download('wordnet'); nltk.download('stopwords')"
```

### 5. Run the Application
```bash
python src/app.py
```
Open your browser and navigate to:
```
http://localhost:5000
```

---

## 🧪 Running Automated Tests

Run the complete test suite:
```bash
python -m unittest tests/test_chatbot.py
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Renders the customer support chat interface |
| `POST` | `/api/chat` | Receives `{ message, session_id }`, returns `{ response, intent, confidence, context, sentiment, log_id }` |
| `POST` | `/api/feedback` | Records user satisfaction rating (`1` for 👍, `-1` for 👎) |
| `GET` | `/api/analytics` | Returns total messages, sessions, feedback stats, and intent distribution |
| `POST` | `/api/reset-session` | Clears conversation context memory for the session |

---

## 🛡️ License
Open-source and available under the [MIT License](LICENSE).
// State management
let sessionId = localStorage.getItem('nexus_session_id');
if (!sessionId) {
  sessionId = 'sess_' + Math.random().toString(36).substring(2, 9);
  localStorage.setItem('nexus_session_id', sessionId);
}

const chatMessages = document.getElementById('chat-messages');
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
const sessionTag = document.getElementById('session-tag');
const currentContextTag = document.getElementById('current-context-tag');
const sentimentVal = document.getElementById('sentiment-val');
const btnClearChat = document.getElementById('btn-clear-chat');
const btnViewLogs = document.getElementById('btn-view-logs');
const logsModal = document.getElementById('logs-modal');
const btnCloseModal = document.getElementById('btn-close-modal');
const modalLogsBody = document.getElementById('modal-logs-body');

sessionTag.textContent = `Session: ${sessionId}`;

// Fetch and refresh analytics
async function fetchAnalytics() {
  try {
    const res = await fetch('/api/analytics');
    const data = await res.json();
    
    document.getElementById('stat-messages').textContent = data.total_messages || 0;
    document.getElementById('stat-sessions').textContent = data.total_sessions || 0;
    document.getElementById('stat-positive').textContent = data.feedback_stats?.positive || 0;
    document.getElementById('stat-negative').textContent = data.feedback_stats?.negative || 0;

    const intentsContainer = document.getElementById('intents-container');
    if (data.intents_breakdown && data.intents_breakdown.length > 0) {
      intentsContainer.innerHTML = data.intents_breakdown.map(item => `
        <div class="intent-item">
          <span>${item.intent}</span>
          <span class="intent-badge">${item.count}</span>
        </div>
      `).join('');
    } else {
      intentsContainer.innerHTML = '<div style="font-size:0.8rem;color:var(--text-muted);">Awaiting interactions...</div>';
    }
  } catch (err) {
    console.error('Failed to load analytics:', err);
  }
}

// Append message bubble
function appendMessage(sender, text, meta = {}) {
  const row = document.createElement('div');
  row.className = `message-row ${sender}`;
  
  const avatar = document.createElement('div');
  avatar.className = 'avatar';
  avatar.textContent = sender === 'bot' ? '🤖' : '👤';

  const wrap = document.createElement('div');
  wrap.className = 'msg-bubble-wrap';

  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.textContent = text;

  const footer = document.createElement('div');
  footer.className = 'msg-footer';

  const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  let footerHtml = `<span>${timeStr}</span>`;

  if (sender === 'bot') {
    if (meta.intent) {
      footerHtml += ` &bull; <span class="tag-badge">${meta.intent} (${Math.round((meta.confidence || 0) * 100)}%)</span>`;
    }
    if (meta.log_id) {
      footerHtml += `
        &bull; 
        <button class="feedback-btn" onclick="sendFeedback(${meta.log_id}, 1)" title="Helpful">👍</button>
        <button class="feedback-btn" onclick="sendFeedback(${meta.log_id}, -1)" title="Not helpful">👎</button>
      `;
    }
  }

  footer.innerHTML = footerHtml;
  wrap.appendChild(bubble);
  wrap.appendChild(footer);

  row.appendChild(avatar);
  row.appendChild(wrap);
  chatMessages.appendChild(row);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Show typing indicator
function showTyping() {
  const typingRow = document.createElement('div');
  typingRow.id = 'typing-indicator-row';
  typingRow.className = 'message-row bot';
  typingRow.innerHTML = `
    <div class="avatar">🤖</div>
    <div class="msg-bubble-wrap">
      <div class="bubble typing-dots">
        <span></span><span></span><span></span>
      </div>
    </div>
  `;
  chatMessages.appendChild(typingRow);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeTyping() {
  const elem = document.getElementById('typing-indicator-row');
  if (elem) elem.remove();
}

// Send user query
async function handleSendMessage(messageText) {
  if (!messageText.trim()) return;

  appendMessage('user', messageText);
  userInput.value = '';
  userInput.disabled = true;
  sendButton.disabled = true;

  showTyping();

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: messageText,
        session_id: sessionId
      })
    });

    const data = await response.json();
    removeTyping();

    if (response.ok) {
      appendMessage('bot', data.response, {
        intent: data.intent,
        confidence: data.confidence,
        log_id: data.log_id
      });

      // Update context memory in UI
      currentContextTag.textContent = data.context ? data.context : 'None (Ready)';
      
      // Update sentiment UI
      sentimentVal.textContent = data.sentiment.toUpperCase();
      if (data.sentiment === 'positive') sentimentVal.style.color = '#10b981';
      else if (data.sentiment === 'negative') sentimentVal.style.color = '#ef4444';
      else sentimentVal.style.color = '#38bdf8';

      fetchAnalytics();
    } else {
      appendMessage('bot', '⚠️ Error: ' + (data.error || 'Unable to process request.'));
    }
  } catch (err) {
    removeTyping();
    appendMessage('bot', '⚠️ Network error: Could not reach backend server.');
  } finally {
    userInput.disabled = false;
    sendButton.disabled = false;
    userInput.focus();
  }
}

// Send rating feedback
window.sendFeedback = async function(logId, rating) {
  try {
    await fetch('/api/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        log_id: logId,
        rating: rating
      })
    });
    alert(rating === 1 ? 'Thank you for your positive feedback!' : 'Feedback noted. We will continue to improve our answers.');
    fetchAnalytics();
  } catch (err) {
    console.error('Feedback error:', err);
  }
};

// Form submit
chatForm.addEventListener('submit', (e) => {
  e.preventDefault();
  handleSendMessage(userInput.value);
});

// Quick suggestion chips
document.querySelectorAll('.quick-chip').forEach(btn => {
  btn.addEventListener('click', () => {
    const text = btn.getAttribute('data-msg');
    handleSendMessage(text);
  });
});

// Clear conversation / Reset context
btnClearChat.addEventListener('click', async () => {
  if (confirm('Start a new chat session?')) {
    sessionId = 'sess_' + Math.random().toString(36).substring(2, 9);
    localStorage.setItem('nexus_session_id', sessionId);
    sessionTag.textContent = `Session: ${sessionId}`;
    currentContextTag.textContent = 'None (Ready)';
    sentimentVal.textContent = 'Neutral';
    sentimentVal.style.color = '#38bdf8';
    
    await fetch('/api/reset-session', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId })
    });

    chatMessages.innerHTML = `
      <div class="message-row bot">
        <div class="avatar">🤖</div>
        <div class="msg-bubble-wrap">
          <div class="bubble">
            Hello! 👋 New chat started. How can I help you today?
          </div>
          <div class="msg-footer">
            <span>Just now</span> &bull;
            <span class="tag-badge">greeting</span>
          </div>
        </div>
      </div>
    `;
    fetchAnalytics();
  }
});

// SQLite Logs Viewer Modal
btnViewLogs.addEventListener('click', async () => {
  logsModal.classList.add('active');
  modalLogsBody.innerHTML = '<p>Loading logs...</p>';
  try {
    const res = await fetch('/api/analytics');
    const data = await res.json();
    if (data.recent_logs && data.recent_logs.length > 0) {
      modalLogsBody.innerHTML = data.recent_logs.map(log => `
        <div class="live-log-item">
          <div><strong style="color:#6366f1;">User:</strong> ${escapeHtml(log.user_message)}</div>
          <div style="margin-top:2px;"><strong style="color:#10b981;">Bot:</strong> ${escapeHtml(log.bot_response)}</div>
          <div style="font-size:0.75rem; color:var(--text-muted); margin-top:3px;">
            Intent: <strong>${log.intent}</strong> &bull; Conf: ${(log.confidence*100).toFixed(0)}% &bull; Sentiment: ${log.sentiment} &bull; ${log.timestamp}
          </div>
        </div>
      `).join('');
    } else {
      modalLogsBody.innerHTML = '<p style="color:var(--text-muted);">No interactions recorded yet.</p>';
    }
  } catch (err) {
    modalLogsBody.innerHTML = '<p style="color:#ef4444;">Failed to load logs.</p>';
  }
});

btnCloseModal.addEventListener('click', () => {
  logsModal.classList.remove('active');
});

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// Initial fetch
fetchAnalytics();

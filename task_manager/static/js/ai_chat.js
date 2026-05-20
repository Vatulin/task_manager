'use strict';

document.addEventListener('DOMContentLoaded', function () {
    const chatWindow = document.getElementById('chat-window');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const chatLoader = document.getElementById('chat-loader');

    // Безопасное извлечение CSRF-токена из куки для закрытого контура Django
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function formatAIResponse(text) {
        const thinkingRegex = /<thinking>([\s\S]*?)<\/thinking>/gi;
        let formatted = text.replace(thinkingRegex, function(match, thoughts) {
            return `<details class="mb-3 p-2 rounded bg-body-secondary border border-secondary-subtle">
                        <summary class="ai-thoughts-summary">Ход мыслей системы</summary>
                        <div class="mt-2 text-muted ai-thoughts-body">${thoughts.trim()}</div>
                    </details>`;
        });
        
        // Превращение маркдауна **текст** в теги строгой жирности
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        formatted = formatted.replace(/\n/g, '<br>');
        
        return formatted;
    }

    function appendMessage(text, className) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `msg ${className}`;
        
        if (className === 'msg-ai') {
            msgDiv.innerHTML = formatAIResponse(text);
        } else {
            msgDiv.innerText = text;
        }
        
        chatWindow.appendChild(msgDiv);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;

        appendMessage(message, 'msg-user');
        userInput.value = '';

        // Корректное переключение состояния интерфейса при генерации
        if (chatLoader) chatLoader.style.display = 'flex';
        sendBtn.disabled = true;
        userInput.disabled = true;

        fetch('/ai/api/chat/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ message: message })
        })
        .then(response => {
            if (!response.ok) throw new Error('Ошибка сервера или таймаут генерации');
            return response.json();
        })
        .then(data => {
            if (chatLoader) chatLoader.style.display = 'none';
            sendBtn.disabled = false;
            userInput.disabled = false;
            userInput.focus();

            if (data.response) {
                appendMessage(data.response, 'msg-ai');
            } else if (data.error) {
                appendMessage(`Ошибка конфигурации: ${data.error}`, 'msg-system');
            }
        })
        .catch(error => {
            if (chatLoader) chatLoader.style.display = 'none';
            sendBtn.disabled = false;
            userInput.disabled = false;
            appendMessage('Не удалось получить ответ. Превышено время ожидания локальной модели. Сформулируйте запрос более конкретно.', 'msg-system');
            console.error(error);
        });
    }

    if (sendBtn && userInput) {
        sendBtn.addEventListener('click', sendMessage);
        userInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }
});
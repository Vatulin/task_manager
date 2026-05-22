import json
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .services import talk_to_corporate_ai
from django.core.exceptions import PermissionDenied

@login_required
def ai_chat(request):
    profile = getattr(request.user, 'profile', None)
    
    if not profile or profile.role != 'admin':
        raise PermissionDenied

    request.session['chat_history'] = []
    return render(request, "ai/chat.html")

@login_required
@csrf_exempt
def ai_chat_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get("message", "").strip()
            
            if not user_message:
                return JsonResponse({"error": "Сообщение не может быть пустым"}, status=400)
        
            if 'chat_history' not in request.session:
                request.session['chat_history'] = []
                
            history = request.session['chat_history']
            
            if len(history) > 12:
                history = history[-12:]
            
            ai_response = talk_to_corporate_ai(user_message, history, user=request.user)
            
            history.append({"role": "user", "content": user_message})
            history.append({"role": "assistant", "content": ai_response})
            request.session['chat_history'] = history
            request.session.modified = True
            return JsonResponse({"response": ai_response})
            
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
            
    return JsonResponse({"error": "Разрешены только POST-запросы"}, status=405)
from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

import json

from chat.models import Message, Chat
from chat.utils import json_response

# Create your views here.

def home(request):
    if not request.user.is_authenticated():
        return redirect('/accounts/login')

    return render(request, 'index.html', {})



def get_current_user_api(request):
    user = request.user

    context = {
        'user_id': user.id,
        'userrname': user.username
    }

    return json_response(context)


def get_all_users_api(request):
    if not request.user.is_authenticated():
        return HttpResponse('You are not loged in')

    all_users = User.objects.all()
    users = list(all_users.exclude(username=request.user).values('username'))

    context = {
        'users': users
    }

    return json_response(context)


def get_user_chats_api(request):
    if not request.user.is_authenticated():
        return HttpResponse('You are not loged in')

    user_chats = Chat.objects.filter(participants=request.user)

    chats = {}
    if user_chats:
        for user_chat in user_chats:
            chat_id = user_chat.id

            interlocutor = user_chat.participants.exclude(id=request.user.id).first()

            last_message = user_chat.messages.latest('timestamp')

            chat = {
                'chat_id': chat_id,
                'last_message': last_message.text,
                'last_message_sender_id': last_message.sender.id,
                'last_message_timestamp': last_message.timestamp,
                'last_message_is_read': last_message.is_read,
                'interlocutor_id': interlocutor.id,
                'interlocutor_username': interlocutor.username
            }

            chats[chat_id] = chat

    context = {
        'chats': chats
    }

    return json_response(context)


def create_chat_api(request):
    if not request.user.is_authenticated():
        return HttpResponse('You are not loged in')

    username = request.GET.get('username')

    recipient = User.objects.get(username=username)

    chat = Chat.objects.create()
    chat.participants.add(request.user, recipient)
    initial_message = Message(text='{} started the conversation!'.format(request.user.username), sender=request.user)
    initial_message.save()
    chat.messages.add(initial_message)

    return json_response({'chat_id': chat.id})


def load_chat_messages_api(request):
    if not request.user.is_authenticated():
        return HttpResponse('You are not loged in')

    chat_id = request.GET.get('chat_id')

    chat = Chat.objects.get(id=chat_id)
    chat_messages = list(chat.messages.all().values('text', 'timestamp', 'is_read'))

    context = {
        'chat_messages': chat_messages
    }

    return json_response(context)


@csrf_exempt
def send_message_api(request):
    api_key = request.POST.get('api_key')

    if api_key != settings.API_KEY:
        return json_response({'error': 'Please pass a correct API key.'})

    sender_id = request.POST.get('sender_id')
    sender = User.objects.get(id=sender_id)
    message_text = request.POST.get('message')

    message_instance = Message()
    message_instance.sender = sender
    message_instance.text = message_text
    message_instance.save()

    chat_id = request.POST.get('chat_id')
    chat = Chat.objects.get(id=chat_id)
    chat.messages.add(message_instance)

    return json_response({'status': 'ok'})


@csrf_exempt
def read_chat_message_api(request):
    reader_id = request.POST.get('reader_id')
    chat_id = request.POST.get('chat_id')

    reader = User.objects.get(id=reader_id)
    chat = Chat.objects.get(id=chat_id)

    unread_messages = chat.messages.filter(is_read=False).exclude(sender=reader)

    for message in unread_messages:
        message.is_read = True
        message.save()

    return json_response({'status': 'ok'})

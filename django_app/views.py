from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import HttpResponse
from .models import Room, Topic, Message, UserProfile
from .forms import RoomForm, UserForm, UserProfileForm


def loginPage(request):
    page = 'login'
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username').lower()
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, 'User does not exist')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request,user)
            return redirect('home')
        else:
            messages.error(request, 'Username and password does not match')
    context = {'page': page}
    return render(request, 'django_app/login_register.html', context)

def logOutUser(request):
    logout(request)
    return redirect('home')

def registerUser(request):
    page = 'register'
    form = UserCreationForm()

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            messages.success(request, 'User registration was successful')
            login(request, user)
            return redirect('home')
        else:
            # print(form.errors)
            messages.error(request, 'An error occured during registeration')
            messages.error(request, 'Use a better password and try again')
            messages.error(request, 'Password should have a mix of numbers and letters')
            messages.error(request, 'If problem persists, contact the developers')
    context = {'page': page, 'form': form}
    return render(request, 'django_app/login_register.html', context)

def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(desc__icontains=q),
    )
    
    topics_count = Topic.objects.all().count()
    topics = Topic.objects.all()[0:5]
    room_count = rooms.count()
    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q))[0:10]
    context = {'rooms': rooms, 'topics': topics, 'topics_count': topics_count, 'room_count': room_count, 'room_messages': room_messages}
    return render(request, 'django_app/home.html', context)

def room(request, pk):
    room = Room.objects.get(id=pk)
    room_messages = room.message_set.all()
    participants = room.participants.all()

    if request.method == 'POST':
        message = Message.objects.create(
            user = request.user,
            room = room,
            body = request.POST.get('body'),
        )
        room.participants.add(request.user)
        return redirect('room', pk=room.id)
    context = {'room': room, 'pk': pk, 'room_messages': room_messages, "participants": participants}
    return render(request, 'django_app/room.html', context)

def navbar(request):
    return render(request, 'django_app/navbar.html')

def userProfile(request, pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    room_messages = user.message_set.all()
    topics_count = Topic.objects.all().count()
    topics = Topic.objects.all()[0:5]
    context = {'user': user, 'rooms': rooms, 'room_messages': room_messages, 'topics': topics, 'topics_count': topics_count}
    return render(request, 'django_app/profile.html', context)
    
@login_required(login_url='login')
def createRoom(request):
    form = RoomForm()
    topics = Topic.objects.all()
    if request.method == 'POST':
        topic_name = request.POST.get("topic")
        topic, created = Topic.objects.get_or_create(name=topic_name)

        Room.objects.create(
            host = request.user,
            topic = topic,
            name = request.POST.get("name"),
            desc = request.POST.get("description")
        )
        return redirect('home')
    
    context = {'form': form, 'topics': topics}
    return render(request, 'django_app/room_form.html', context)

@login_required(login_url='login')
def updateRoom(request, pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)
    topics = Topic.objects.all()
    if request.user != room.host:
        return HttpResponse("You are not allowed here!")
    
    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        topic_name = request.POST.get("topic")
        topic, created = Topic.objects.get_or_create(name=topic_name)
        room.name = request.POST.get("name")
        room.topic = topic
        room.desc = request.POST.get("description")
        room.save()
        return redirect('home')

    context = {'form': form, 'topics': topics, 'room': room}
    return render(request, 'django_app/room_form.html', context)

@login_required(login_url='login')
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)

    if request.user != room.host:
        return HttpResponse("This action is prohibited for this user!")
    if request.method == 'POST':
        room.delete()
        return redirect('home')
        
    
    return render(request, 'django_app/delete.html', {'obj': room})


@login_required(login_url='login')
def deleteMessage(request, pk):
    message = Message.objects.get(id=pk)

    if request.user != message.user:
        return HttpResponse("This action is prohibited for this user!")
    if request.method == 'POST':
        message.delete()
        return redirect('home')
        
    
    return render(request, 'django_app/delete.html', {'obj': message})

@login_required(login_url='login')
def updateUser(request):
    user = request.user
    user_profile = UserProfile.objects.get_or_create(user=user)[0]
    user_form = UserForm(request.POST or None, instance=user)
    profile_form = UserProfileForm(request.POST or None, request.FILES or None, instance=user_profile)
    # form = UserForm(instance=user)

    if request.method == 'POST':
        # form = UserForm(request.POST, request.FILES, instance=user)
        if user_form.is_valid() and profile_form.is_valid():
            try:
                user_form.save()
                profile_form.save()
                return redirect('user-profile', pk=user.id)
            except ValidationError as e:
                user_form.add_error('image', e)
                print(e)
        else:
            print(user_form.error)
            print(profile_form.error)
    context = {"user_form": user_form, "profile_form": profile_form}
    return render(request, 'django_app/update-user.html', context)

def topicsPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    topics = Topic.objects.filter(name__icontains=q)
    context = {"topics": topics}
    return render(request, 'django_app/topics.html', context)

def recentActivities(request):
    room_messages = Message.objects.all()
    context = {"room_messages": room_messages}
    return render(request, 'django_app/activity.html', context)
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

def login_view(request):
    """Vista de login personalizada"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'¡Bienvenido, {username}!')
                
                # Redirigir a la página anterior o al dashboard
                next_url = request.GET.get('next', 'home')
                return redirect(next_url)
            else:
                messages.error(request, 'Usuario o contraseña incorrectos.')
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'core/auth/login.html', {
        'form': form,
        'title': 'Iniciar Sesión'
    })

def register_view(request):
    """Vista de registro personalizada"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'¡Cuenta creada exitosamente! Bienvenido, {user.username}.')
            return redirect('home')
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario.')
    else:
        form = UserCreationForm()
    
    return render(request, 'core/auth/register.html', {
        'form': form,
        'title': 'Registrarse'
    })

def logout_view(request):
    """Vista de logout personalizada"""
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        messages.success(request, f'Has cerrado sesión exitosamente. ¡Hasta luego, {username}!')
    return redirect('login')

@login_required
def profile_view(request):
    """Vista del perfil de usuario"""
    return render(request, 'core/auth/profile.html', {
        'title': 'Mi Perfil'
    })

@login_required
def change_password_view(request):
    """Vista para cambiar contraseña"""
    if request.method == 'POST':
        user = request.user
        current_password = request.POST.get('current_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        
        if not user.check_password(current_password):
            messages.error(request, 'La contraseña actual es incorrecta.')
        elif new_password1 != new_password2:
            messages.error(request, 'Las nuevas contraseñas no coinciden.')
        elif len(new_password1) < 8:
            messages.error(request, 'La nueva contraseña debe tener al menos 8 caracteres.')
        else:
            user.set_password(new_password1)
            user.save()
            messages.success(request, 'Contraseña cambiada exitosamente.')
            return redirect('profile')
    
    return render(request, 'core/auth/change_password.html', {
        'title': 'Cambiar Contraseña'
    })

# API endpoints para AJAX
@csrf_exempt
def login_api(request):
    """API endpoint para login via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return JsonResponse({
                    'success': True,
                    'message': f'¡Bienvenido, {username}!',
                    'redirect_url': reverse('home')
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Usuario o contraseña incorrectos.'
                })
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Datos inválidos.'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido.'
    })

@csrf_exempt
def register_api(request):
    """API endpoint para registro via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password1 = data.get('password1')
            password2 = data.get('password2')
            
            if password1 != password2:
                return JsonResponse({
                    'success': False,
                    'message': 'Las contraseñas no coinciden.'
                })
            
            if len(password1) < 8:
                return JsonResponse({
                    'success': False,
                    'message': 'La contraseña debe tener al menos 8 caracteres.'
                })
            
            # Verificar si el usuario ya existe
            from django.contrib.auth.models import User
            if User.objects.filter(username=username).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'El nombre de usuario ya existe.'
                })
            
            # Crear usuario
            user = User.objects.create_user(username=username, password=password1)
            login(request, user)
            
            return JsonResponse({
                'success': True,
                'message': f'¡Cuenta creada exitosamente! Bienvenido, {username}.',
                'redirect_url': reverse('home')
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Datos inválidos.'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido.'
    }) 
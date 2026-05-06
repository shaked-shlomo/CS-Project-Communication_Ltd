from functools import wraps
from django.shortcuts import redirect
from accounts.models import Worker


def login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        worker_id = request.session.get('worker_id')
        if not worker_id:
            return redirect('/login/')
        try:
            request.worker = Worker.objects.get(id=worker_id)
        except Worker.DoesNotExist:
            del request.session['worker_id']
            return redirect('/login/')
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        worker_id = request.session.get('worker_id')
        if not worker_id:
            return redirect('/login/')
        try:
            request.worker = Worker.objects.get(id=worker_id)
        except Worker.DoesNotExist:
            del request.session['worker_id']
            return redirect('/login/')
        if request.worker.role != 'admin':
            return redirect('/customers/')
        return view_func(request, *args, **kwargs)
    return wrapper

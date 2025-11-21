from functools import wraps
from django.shortcuts import render

def permission_required_custom(perm):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not request.user.has_perm(perm):
                return render(request, "403.html", status=403)
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator

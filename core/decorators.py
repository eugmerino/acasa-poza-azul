from django.shortcuts import render

def permission_required_custom(permission_name):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.has_perm(permission_name):
                return render(request, "403.html", status=403)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
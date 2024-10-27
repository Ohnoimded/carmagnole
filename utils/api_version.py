from django.http import JsonResponse


def api_version(version):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            response = view_func(request, *args, **kwargs)
            if isinstance(response, JsonResponse):
                response['API-Version'] = version
            elif hasattr(response, 'headers'):
                response.headers['API-Version'] = version
            return response
        return wrapper
    return decorator
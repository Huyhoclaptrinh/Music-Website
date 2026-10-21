def username_context_processor(request):
    username = None
    if request.user.is_authenticated:
        username = request.user.username
    return {'username': username}
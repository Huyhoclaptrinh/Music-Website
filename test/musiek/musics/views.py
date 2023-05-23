from django.shortcuts import render
from .models import UserHistory
import datetime
# Create your views here.


def Library(request):
    return render(request, "main_page/library.html")


def History(request):
    user = request.user
    user_history = UserHistory.objects.filter(user_id=user)
    selected_date = request.GET.get(
        "selected_date"
    )  # Get the selected date from the request

    if selected_date:
        selected_datetime = datetime.datetime.strptime(selected_date, "%m/%d/%Y %I:%M %p")
        selected_date = selected_datetime.strftime("%Y-%m-%d")
        user_history = user_history.filter(history_id__date=selected_date)
    return render(
        request,
        "main_page/history.html",
        {"user_history": user_history, "selected_date": selected_date},
    )

from django.shortcuts import render

def dash_view(request):
    return render(request,'user/dashboard.html')

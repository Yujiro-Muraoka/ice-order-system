from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import ShavedIceOrder

# views.py

def shavedice_register(request):
    print("--- shavedice_register ---")
    temp_ice = request.session.get("shavedice_temp", [])
    print("Session temp_ice (in register view):", temp_ice) # この出力
    flavors = [f[0] for f in ShavedIceOrder.FLAVOR_CHOICES]
    return render(request, "shavedice/shavedice_register.html", {
        "temp_ice": temp_ice,
        "flavors": flavors
    })

@csrf_exempt
def add_temp_ice(request):
    if request.method == "POST":
        temp = request.session.get("shavedice_temp", [])
        temp.append({
            "size": "S",
            "container": "cup",
            "flavor1": request.POST.get("flavor1"),
            "flavor2": None,
            "is_pudding": False
        })
        request.session["shavedice_temp"] = temp
        request.session.modified = True # ★この行を追加★
        return JsonResponse({"status": "ok"})



def shavedice_kitchen(request):
    return render(request, "shavedice/shavedice_kitchen.html", {})

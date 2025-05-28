from django.shortcuts import render, redirect
from .models import ShavedIceOrder

# 仮オーダー追加・送信画面
def shavedice_register(request):
    if request.method == "POST":
        if "add" in request.POST:
            temp = request.session.get("shavedice_temp", [])
            temp.append({
                "flavor": request.POST.get("flavor"),
                "quantity": int(request.POST.get("quantity", 1)),
                "note": request.POST.get("note", "")
            })
            request.session["shavedice_temp"] = temp
            return redirect("shavedice_register")

        elif "submit" in request.POST:
            temp = request.session.get("shavedice_temp", [])
            for item in temp:
                ShavedIceOrder.objects.create(
                    flavor=item["flavor"],
                    quantity=item["quantity"],
                    note=item["note"]
                )
            request.session["shavedice_temp"] = []
            return redirect("shavedice_register")

    temp_orders = request.session.get("shavedice_temp", [])
    return render(request, "shavedice/shavedice_register.html", {"temp_orders": temp_orders})


# 作成画面（キッチン側）
def shavedice_kitchen(request):
    orders = ShavedIceOrder.objects.filter(is_completed=False).order_by("created_at")
    return render(request, "shavedice/shavedice_kitchen.html", {"orders": orders})

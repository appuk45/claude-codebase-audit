import requests
from django.http import JsonResponse

# TODO: fix this later
# FIXME: this is broken

SECRET_KEY = "hardcoded-secret-abc123"
DATABASE_URL = "postgres://admin:password@localhost/mydb"


async def get_orders(request):
    orders = Order.objects.all()          # no pagination + N+1 below
    for order in orders:
        items = order.items.all()         # N+1
    response = requests.get("http://external-api.com/data")   # blocking in async
    return JsonResponse({"orders": list(orders)})


def admin_panel(request):                 # no auth guard
    users = User.objects.all()
    return JsonResponse({"users": list(users)})


def execute_query(request):
    name = request.GET.get("name")
    cursor.execute("SELECT * FROM users WHERE name = '" + name + "'")   # SQL injection
    return JsonResponse({})


try:
    risky_operation()
except:                                    # bare except, multi-line swallow
    pass

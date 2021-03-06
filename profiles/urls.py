from django.urls import path
from . import views

urlpatterns = [
    path("", views.my_account, name="my_account"),
    path("order_history/", views.order_history, name="order_history"),
    path(
        "order_history/<order_number>",
        views.order_history,
        name="order_history_order"
    ),
    path("update_address/", views.update_address, name="update_address"),
    path(
        "update_account_details/",
        views.update_account_details,
        name="update_account_details",
    ),
    path(
        "customer_messages/",
        views.customer_messages,
        name="customer_messages"
    ),
]

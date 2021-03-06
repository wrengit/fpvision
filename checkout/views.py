from django.shortcuts import render, reverse, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.contrib import messages
from django.conf import settings

from .forms import OrderForm
from profiles.forms import UserProfileForm
from profiles.models import UserProfile
from products.models import Product
from basket.context import basket_contents
from .models import OrderLineItem, Order

import stripe
import json


@require_POST
def cache_checkout_data(request):
    try:
        pid = request.POST.get("client_secret").split("_secret")[0]
        stripe.api_key = settings.STRIPE_SECRET_KEY
        stripe.PaymentIntent.modify(
            pid,
            metadata={
                "basket": json.dumps(request.session.get("basket", {})),
                "save_info": request.POST.get("save_info"),
                "username": request.user,
            },
        )
        return HttpResponse(status=200)
    except Exception as e:
        messages.error(
            request,
            "Sorry, your payment cannot be processed right now. \
            Please try again later.",
        )
        return HttpResponse(content=e, status=400)


def checkout(request):
    """
    Checkout view, pulling info from forms to
    post to Stripe
    """

    stripe_public_key = settings.STRIPE_PUBLIC_KEY
    stripe_secret_key = settings.STRIPE_SECRET_KEY

    if request.method == "POST":
        basket = request.session.get("basket", {})

        form_data = {
            "full_name": request.POST["full_name"],
            "email": request.POST["email"],
            "phone_number": request.POST["phone_number"],
            "country": request.POST["country"],
            "postcode": request.POST["postcode"],
            "post_town": request.POST["post_town"],
            "address_1": request.POST["address_1"],
            "address_2": request.POST["address_2"],
            "county": request.POST["county"],
        }
        order_form = OrderForm(form_data)
        if order_form.is_valid():
            order = order_form.save(commit=False)
            pid = request.POST.get("client_secret").split("_secret")[0]
            order.stripe_pid = pid
            order.original_basket = json.dumps(basket)
            order.save()
            for item_id, item_data in basket.items():
                try:
                    product = Product.objects.get(id=item_id)
                    order_line_item = OrderLineItem(
                        order=order, product=product, quantity=item_data,
                    )
                    order_line_item.save()
                except Product.DoesNotExist:
                    messages.error(
                        request,
                        (
                            "One of the products in your order was not \
                                found in our database."
                            "Please call us for assitance"
                        ),
                    )
                    order.delete()
                    return redirect(reverse("view_basket"))

            request.session["save_info"] = "save-info" in request.POST
            return redirect(
                reverse("checkout_success", args=[order.order_number])
            )
        else:
            messages.error(
                request,
                "There was an error with your form. \
                Please double check your information",
            )
    else:
        basket = request.session.get("basket", {})
        if not basket:
            messages.error(request, "Your basket is empty")
            return redirect(reverse("all_products"))

        current_basket = basket_contents(request)
        total = current_basket["grand_total"]
        stripe_total = round(total * 100)
        stripe.api_key = stripe_secret_key
        intent = stripe.PaymentIntent.create(
            amount=stripe_total,
            currency=settings.STRIPE_CURRENCY,
            payment_method_types=["card"],
        )

        if request.user.is_authenticated:
            try:
                profile = UserProfile.objects.get(user=request.user)
                saved_info = {
                    "full_name": profile.user.get_full_name(),
                    "email": profile.user.email,
                    "phone_number": profile.default_phone_number,
                    "country": profile.default_country,
                    "postcode": profile.default_postcode,
                    "post_town": profile.default_post_town,
                    "address_1": profile.default_address_1,
                    "address_2": profile.default_address_2,
                    "county": profile.default_county,
                }
                order_form = OrderForm(initial=saved_info)
            except UserProfile.DoesNotExist:
                order_form = OrderForm()
        else:
            order_form = OrderForm()

    if not stripe_public_key:
        messages.warning(
            request,
            "Stripe public key is missing. \
            Did you forget to set it in your environment?",
        )
    template = "checkout/checkout.html"
    context = {
        "order_form": order_form,
        "stripe_public_key": stripe_public_key,
        "client_secret": intent.client_secret,
    }

    return render(request, template, context)


def checkout_success(request, order_number):
    """
    View after a successful checkout.
    """
    save_info = request.session.get("save_info")
    order = get_object_or_404(Order, order_number=order_number)

    if request.user.is_authenticated:
        profile = UserProfile.objects.get(user=request.user)
        order.user_profile = profile
        order.save()

        """
        Saves user info for later use if selected
        """
        if save_info:
            profile_data = {
                "default_phone_number": order.phone_number,
                "default_country": order.country,
                "default_postcode": order.postcode,
                "default_post_town": order.post_town,
                "default_address_1": order.address_1,
                "default_address_2": order.address_2,
                "default_county": order.county,
            }
            user_profile_form = UserProfileForm(profile_data, instance=profile)
            if user_profile_form.is_valid():
                user_profile_form.save()

    messages.success(
        request,
        f"Order successfully processed \
        Your order number is {order_number}. A confirmation \
            email will be sent to {order.email}.",
    )

    if "basket" in request.session:
        del request.session["basket"]

    template = "checkout/checkout_success.html"
    context = {
        "order": order,
    }

    return render(request, template, context)

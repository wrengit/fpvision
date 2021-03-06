from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib import messages
from products.models import Product
from .models import Wishlist, WishlistItem
from django.contrib.auth.decorators import login_required


@login_required
def view_wishlist(request):
    """View products saved to the wishlist"""

    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    wishlist_products = WishlistItem.objects.filter(wishlist=wishlist)
    context = {"wishlist_products": wishlist_products, "wishlist": wishlist}
    return render(request, "profiles/wishlist.html", context)


@login_required
def add_to_wishlist(request, product_id):
    """Add a product to the wishlist"""

    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    product = get_object_or_404(Product, pk=product_id)
    redirect_url = request.POST.get("redirect_url")
    quantity = int(request.POST.get("quantity"))
    wishlist_item, created = WishlistItem.objects.get_or_create(
        product=product, wishlist=wishlist,
    )
    if wishlist_item.quantity == 0:
        wishlist_item.quantity = quantity
        wishlist_item.save()
    else:
        wishlist_item.quantity += quantity
        wishlist_item.save()
    wishlist.update_total()
    messages.success(request, f"{product.name} was added to your wishlist")
    return redirect(redirect_url)


@login_required
def adjust_wishlist(request, product_id):
    """Adjust the quantity of the specified product to the specified amount"""

    product = get_object_or_404(Product, pk=product_id)
    quantity = int(request.POST.get("quantity"))
    wishlist = Wishlist.objects.get(user=request.user)
    wishlist_item = WishlistItem.objects.get(product=product, wishlist=wishlist)
    if quantity > 0:
        wishlist_item.quantity = quantity
        wishlist_item.save()
        wishlist.update_total()
        messages.info(
            request,
            f"{product.name} quantity was changed to {quantity}\
                 in your wishlist",
        )
    else:
        wishlist_item.delete()
        wishlist.update_total()
        messages.info(
            request,
            f"{product.name} was\
             removed from your wishlist",
        )
    return redirect(reverse("view_wishlist"))


@login_required
def remove_from_wishlist(request, product_id):
    """Remove the product from the wishlist"""

    product = get_object_or_404(Product, pk=product_id)
    wishlist = Wishlist.objects.get(user=request.user)
    wishlist_item = WishlistItem.objects.get(product=product, wishlist=wishlist)
    wishlist_item.delete()
    wishlist.update_total()
    messages.success(request, f"Removed {product.name} from your wishlist")

    return redirect(reverse("view_wishlist"))


@login_required
def add_wishlist_to_basket(request):
    """
    Add all products in the wishlist to the basket.
    Check if the product is in the basket, and if product stock is
    sufficient add to basket and remove from watchlist
    """

    wishlist = Wishlist.objects.get(user=request.user)
    wishlist_products = WishlistItem.objects.filter(wishlist=wishlist)
    basket = request.session.get("basket", {})

    for item in wishlist_products:
        id = str(item.product.id)
        if id in list(basket.keys()):
            if item.product.stock >= item.quantity + basket[id]:
                basket[id] += item.quantity
                messages.success(
                    request,
                    f"Added {item.product.name} x \
                        {item.quantity} to your basket",
                )
                item.delete()
            else:
                messages.warning(
                    request,
                    f"You cannot add {item.product.name} X {item.quantity}\
                     to the basket - we have {item.product.stock} in stock\
                     and you already have {basket[id]} in your basket",
                )
        else:
            basket[item.product.id] = item.quantity
            messages.success(request, f"Added {item.product.name} to your basket")
            item.delete()

    if wishlist_products is True:
        request.session["basket"] = basket
        return redirect(reverse("view_wishlist"))
    else:
        request.session["basket"] = basket
        return redirect(reverse("view_basket"))

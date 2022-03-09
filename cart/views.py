
from django.shortcuts import get_object_or_404, render,redirect
from django.http import HttpResponse
from .models import Cart, CartItem
from store.models import Product, Variation
from django.contrib.auth.decorators import login_required

# Create your views here.
def _cart_id(request):
    cart=request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart 



def add_cart(request,product_id):
    current_user = request.user
    product = Product.objects.get(id=product_id)
    # print(product)
    product_variation = []
    # print('abnhj')
    if current_user.is_authenticated:
        if request.method =='POST':
        # print(123654)
        # print(request.POST)
            for key,value in request.POST.items():
                # key=item
                # value=request.POST[key]
                # print(key)
                # print(value)
                # print(Variation.object.get(product=product))
                try:
                    variation = Variation.object.get(product=product, variation_category__iexact=key,variation_value__iexact=value)        
                    # print(25963)
                    product_variation.append(variation)
                    # print(product_variation)
                    # print('bhnj')
                except:
                    # print('abcd')
                    pass 
        
    
   

        is_cart_item_exists = CartItem.objects.filter(product=product, user = current_user).exists() 
        print(is_cart_item_exists)
        if is_cart_item_exists:
            cart_item = CartItem.objects.filter(product=product, user=current_user)
            print(cart_item)
            # check if current product variation exists in existing variation (in database)
            ex_var_lst=[]
            id=[]
            for item in cart_item:
                existing_variation = item.variations.all()
                print(existing_variation)
                ex_var_lst.append(list(existing_variation))
                print(ex_var_lst)
                id.append(item.id)

            if product_variation in ex_var_lst:
                # increase the quantity
                # print(1)
                index = ex_var_lst.index(product_variation)
                id_index = id[index]
                item = CartItem.objects.get(product=product,id=id_index)
                print(item)
                item.quantity += 1
                item.save()


            else:
                item = CartItem.objects.create(product=product,quantity=1,user=current_user)
                if len(product_variation)>0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
            # cart_item.quantity+=1
                    item.save()
                    print(item.variations.all())
        else:
            cart_item = CartItem.objects.create(product=product, user=current_user, quantity=1)   
            if len(product_variation)>0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)
            cart_item.save()
            print(cart_item.variations.all())

        return redirect('cart')
    else:

        if request.method =='POST':
            # print(123654)
            # print(request.POST)
            for key,value in request.POST.items():
                # key=item
                # value=request.POST[key]
                # print(key)
                # print(value)
                # print(Variation.object.get(product=product))
                try:
                    variation = Variation.object.get(product=product, variation_category__iexact=key,variation_value__iexact=value)        
                    # print(25963)
                    product_variation.append(variation)
                    # print(product_variation)
                    # print('bhnj')
                except:
                    # print('abcd')
                    pass 
            
        
        try:
            cart=Cart.objects.get(cart_id=_cart_id(request))
        except Cart.DoesNotExist:    
            cart = Cart.objects.create(cart_id=_cart_id(request))
        cart.save()

        is_cart_item_exists = CartItem.objects.filter(product=product, cart=cart).exists() 
        print(is_cart_item_exists)
        if is_cart_item_exists:
            cart_item = CartItem.objects.filter(product=product, cart=cart)
            print(cart_item)
            # check if current product variation exists in existing variation (in database)
            ex_var_lst=[]
            id=[]
            for item in cart_item:
                existing_variation = item.variations.all()
                print(existing_variation)
                ex_var_lst.append(list(existing_variation))
                print(ex_var_lst)
                id.append(item.id)

            if product_variation in ex_var_lst:
                # increase the quantity
                print(1)
                index = ex_var_lst.index(product_variation)
                id_index = id[index]
                item = CartItem.objects.get(product=product,id=id_index)
                print(item)
                item.quantity += 1
                item.save()


            else:
                item = CartItem.objects.create(product=product,quantity=1,cart=cart)
                if len(product_variation)>0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
            # cart_item.quantity+=1
                    item.save()
                    print(item.variations.all())
        else:
            cart_item = CartItem.objects.create(product=product, cart=cart, quantity=1)   
            if len(product_variation)>0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)
            cart_item.save()
            print(cart_item.variations.all())

        return redirect('cart')

def remove_cart(request,product_id,cart_item_id):
    
    product = get_object_or_404(Product,id=product_id)
    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=request.user,id=cart_item_id)
        else:    
            cart = Cart.objects.get(cart_id = _cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart=cart,id=cart_item_id)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1 
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass
    return redirect('cart')  

def remove(request,product_id):
   
    product = get_object_or_404(Product,id=product_id)
    if request.user.is_authenticated:
        cart_item = CartItem.objects.get(product=product, user=request.user)
    else:
        cart = Cart.objects.get(cart_id = _cart_id(request))
        cart_item = CartItem.objects.get(product=product, cart=cart)
    cart_item.delete()

    return redirect('cart')



def cart(request,total=0,quantity=0,cart_items=None,tax=0,grand_total=0):
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id = _cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for item in cart_items:
            total += item.product.price * item.quantity
            quantity += item.quantity
            tax = 0.02*total
            grand_total = total + tax 
    except Cart.DoesNotExist:
        pass 

    context = {
        'total':total,
        'quantity':quantity,
        'cart_items':cart_items,
        'tax':tax,
        'grand_total':grand_total
    }


    return render(request,'store/cart.html',context)

@login_required(login_url='login')    
def checkout(request,total=0,quantity=0,cart_items=None,tax=0,grand_total=0):
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id = _cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for item in cart_items:
            total += item.product.price * item.quantity
            quantity += item.quantity
            tax = 0.02*total
            grand_total = total + tax 
    except Cart.DoesNotExist:
        pass 

    context = {
        'total':total,
        'quantity':quantity,
        'cart_items':cart_items,
        'tax':tax,
        'grand_total':grand_total
    }
    return render(request,'store/checkout.html',context)
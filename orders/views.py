from django.http import HttpResponse, JsonResponse
from django.shortcuts import render,redirect
from cart.models import CartItem
from orders.forms import OrderForm
from orders.models import Order, OrderProduct, Payment
import datetime
import json

from store.models import Product
from django.core.mail import EmailMessage
from django.template.loader import render_to_string 

# Create your views here.
def payments(request):
    body = json.loads(request.body)
    order = Order.objects.get(user=request.user,is_ordered=False,order_number=body['orderID'])
    
    #store transaction details inside payment model
    payment = Payment(
        user = request.user,
        payment_id = body['transId'],
        payment_method = body['payment_method'],
        amount_paid = order.order_total,
        status = body['status']
    )
    payment.save()

    order.payment = payment
    order.is_ordered = True
    order.save()

    #Move the cart items to Order Product table
    cart_items = CartItem.objects.filter(user=request.user)

    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order_id=order.id
        orderproduct.payment = payment 
        orderproduct.user_id = request.user.id
        orderproduct.product_id = item.product_id
        orderproduct.quantity = item.quantity
        orderproduct.product_price = item.product.price
        orderproduct.ordered = True 
        orderproduct.save()

        cart_item = CartItem.objects.get(id=item.id)
        product_variations = cart_item.variations.all()
        orderproduct = OrderProduct.objects.get(id=orderproduct.id)
        orderproduct.variations.set(product_variations)
        orderproduct.save()


        #Reduce the quantity of sold products
        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()


    #Clear cart
    CartItem.objects.filter(user=request.user).delete()


    #Send order recieved email to customer
    mail_subject = 'Thank You for your order' #Email subject
    message = render_to_string('orders/order_recieved_email.html',{
        'user':request.user,  #to get user details in html template
        'order':order,
    })
    to_email = request.user.email
    send_email = EmailMessage(mail_subject,message,to=[to_email])
    send_email.send()

    #Send order no and transaction id back to send data method via json response
    data = {
        'order_number':order.order_number,
        'transId': payment.payment_id,
    }



    return JsonResponse(data)


def place_order(request,total=0,quantity=0):
    current_user =request.user
    
    #If cart count is less than or equla to zero
    #Then redirect back to store

    cart_items = CartItem.objects.filter(user = current_user)
    cart_count = cart_items.count()
    if cart_count <= 0 :
        return redirect('store')

    grand_total = 0
    tax = 0
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity

    tax = (2*total)/100
    grand_total = total + tax 
    # print('yup')
    if request.method == 'POST':
        form =OrderForm(request.POST)
        # print('ko')
        # print(form.is_valid())
        # print(form.errors) 
        if form.is_valid():
            print('ok')
            #Store all billing information in order table
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2= form.cleaned_data['address_line_2']
            data.country = form.cleaned_data['country']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR') #give user ip
            data.save()

            #Generate Order number

            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr,mt,dt)
            current_date = d.strftime("%Y%m%d") 

            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            order =Order.objects.get(user = current_user,is_ordered=False,order_number=order_number)
            context={
                'order':order,
                'cart_items':cart_items,
                'total':total,
                'tax':tax,
                'grand_total':grand_total

            }
            return render(request,'orders/payments.html',context)
        else:
            # print('yahoo')
            return redirect('checkout')

def order_complete(request):
    order_number = request.GET.get('order_number')
    transId = request.GET.get('payment_id')
    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)

        subtotal =0

        for i in ordered_products:
            subtotal += i.product_price * i.quantity


        payment = Payment.objects.get(payment_id=transId)

        context ={
            'order':order,
            'ordered_products':ordered_products,
            'order_number':order.order_number,
            'transId':payment.payment_id,
            'payment':payment,
            'subtotal':subtotal,
        }
        return render(request,'orders/order_complete.html',context)
    except (Payment.DoesNotExist,Order.DoesNotExist):
        return redirect('home')







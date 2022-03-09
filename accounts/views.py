from django.contrib import messages,auth
from django.shortcuts import render,redirect
from .forms import RegistrationForm, PasswordChangeForm
from .models import Account
from django.contrib.auth.decorators import login_required

#verification
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string 
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage #mail_admins 
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.contrib.auth import update_session_auth_hash
import requests

from cart.models import Cart,CartItem
from cart.views import _cart_id
# Create your views here.
@csrf_exempt
def register(request):
    if request.method=='POST':
        form = RegistrationForm(request.POST)
        
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            phone_no = form.cleaned_data['phone_no']
            password = form.cleaned_data['password']
            username = email.split('@')[0] 

            user = Account.objects.create_user(first_name=first_name, last_name=last_name,email=email,username=username,password=password)
            user.phone_no=phone_no 
            user.save()

            #Verification email
            current_site = get_current_site(request) #Now we are using local host but in future may be something else
            mail_subject = 'Please activate your account.' #Email subject
            message = render_to_string('accounts/account_verification_email.html',{
                'user':user,  #to get user details in html template
                'domain': current_site, 
                'uid' : urlsafe_base64_encode(force_bytes(user.pk)), #primary key encoded
                'token' : default_token_generator.make_token(user), #token which will be sending in activation link and itself gets destroyed after activation of link
            })
            to_email = email
            send_email = EmailMessage(mail_subject,message,to=[to_email])
            send_email.send()
            # messages.success(request,'Registration successful')
            # subject='Okay'
            # message2='Lets see'
            # mail_admins(subject,message2)
            return redirect('/accounts/login/?command=verification&email='+email)




    else:       
        form = RegistrationForm()
    context = {
        'form' : form
    }
    return render(request,'accounts/register.html',context)

def login(request):
    if request.method=='POST':
        email=request.POST['email']
        password=request.POST['password']
        user = auth.authenticate(email=email,password=password)
        if user is not None:
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                is_cart_item_exists = CartItem.objects.filter(cart=cart).exists()
                if is_cart_item_exists:
                    cart_item = CartItem.objects.filter(cart=cart)

                    # Getting the product variations by cart id
                    product_variation = []
                    for item in cart_item:
                        variation = item.variations.all()
                        product_variation.append(list(variation))

                    # Get the cart items from the user to access his product variations
                    cart_item = CartItem.objects.filter(user=user)
                    ex_var_list = []
                    id = []
                    for item in cart_item:
                        existing_variation = item.variations.all()
                        ex_var_list.append(list(existing_variation))
                        id.append(item.id)

                    # product_variation = [1, 2, 3, 4, 6]
                    # ex_var_list = [4, 6, 3, 5]

                    for pr in product_variation:
                        if pr in ex_var_list:
                            index = ex_var_list.index(pr)
                            item_id = id[index]
                            item = CartItem.objects.get(id=item_id)
                            item.quantity += 1
                            item.user = user
                            item.save()
                        else:
                            cart_item = CartItem.objects.filter(cart=cart)
                            for item in cart_item:
                                item.user = user
                                item.save()
            except:
                pass    
            auth.login(request,user)
            messages.success(request,"You are now logged in!")
            url = request.META.get('HTTP_REFERER')
            try:
                query = requests.utils.urlparse(url).query
                # next=/cart/checkout/
                params = dict(x.split('=') for x in query.split('&'))
                if 'next' in params:
                    nextPage = params['next']
                    return redirect(nextPage)
            except:
                return redirect('dashboard')
            
        else:
            messages.error(request,'Invalid Credentials')    
            
    return render(request,'accounts/login.html')

@login_required(login_url='login')
def logout(request):
    auth.logout(request)
    messages.success(request,'You are successfully logged out.')
    return redirect('login')


def activate(request,uidb64,token):
    try:
        uid= urlsafe_base64_decode(uidb64).decode() #Primary key decoded
        user = Account._default_manager.get(pk=uid)

    except(TypeError,ValueError,OverflowError,Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user,token):
        user.is_active= True
        user.save()
        messages.success(request,'Congratulations, Your account has been activated!')
        return redirect('login')
    else:
        messages.error(request,'Invalid activation link')
        return redirect('register')    

@login_required(login_url='login')
def dashboard(request):
    return render(request,'accounts/dashboard.html')


'''Send password change link on his email with token and uid(pk) 
and redirect him to reset password page which just a comment 
'''
def forgotPassword(request):
    if request.method=='POST':
        email = request.POST['email']
        
        if Account.objects.filter(email__exact=email).exists():
            user=Account.objects.get(email=email)
            current_site =get_current_site(request)
            subject = 'Passsword Change'
            body = render_to_string('accounts/password_verification.html',{
                'domain':current_site,
                'user':user,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token' : default_token_generator.make_token(user)
            })
            to_email = email
            send_email = EmailMessage(subject,body,to=[to_email])
            send_email.send()
            # messages.success(request,"Password change link sent")
            return redirect('/accounts/resetPassword/?command=verification&email='+email)
        else:
            messages.error(request,'Account does not exists!')
            return redirect('forgotPassword')

    return render(request,'accounts/forgotPassword.html')

'''
It decodes the token in the activation link
and then stores the uid in session to restore 
the session after password change
''' 
def changePassword(request,uidb64,token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(ValueError,TypeError,OverflowError,Account.DoesNotExist):
        user = None 

    if user is not None and default_token_generator.check_token(user,token):
        request.session['uid']=uid
        messages.success(request,'Please reset your password!')
        return redirect('resetPassword')
    else:
        messages.error(request,'Link has been expired')
        return redirect('login')


'''
It takes password from resetPassword html form
and also uid from session 
and from uid it takes user from database
and set passsword for user
and save the user
'''
def resetPassword(request):
    if request.method=='POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            uid = request.session.get('uid')
            user = Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request,'Password is succcessfully changed!')
            return redirect('login')

        else:
            messages.error(request,"Password do not match!")
            return redirect("resetPassword") 
    else:
        return render(request,'accounts/resetPassword.html')          




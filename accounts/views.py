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
            auth.login(request,user)
            messages.success(request,"You are now logged in!")
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




from django.shortcuts import redirect, render
from django.conf import settings
from django.contrib.auth import logout
import requests
import jwt

def index(request):
    token_info = request.session.get('token_info')
    discipline = token_info.get('discipline') if token_info else None
    return render(request, 'main/home.html', {'discipline': discipline})

def login_view(request):
    auth_url = settings.OIDC_OP_AUTHORIZATION_ENDPOINT
    return redirect(
        f"{auth_url}?client_id={settings.OIDC_RP_CLIENT_ID}"
        f"&response_type=code&scope=openid discipline"
        f"&redirect_uri={settings.KEYCLOAK_REDIRECT_URI}"
    )

def logout_view(request):
    # Полностью очищаем локальную Django-сессию
    logout(request)
    request.session.flush()

    # Полный редирект в Keycloak для завершения SSO
    keycloak_logout = (
        "http://localhost:8080/realms/MyLabRealm/protocol/openid-connect/logout"
        "?post_logout_redirect_uri=http://localhost:8000/"
        "&client_id=my-spa-app"
    )

    print("LOGOUT URL →", keycloak_logout)  # проверка URL
    return redirect(keycloak_logout)

def callback(request):
    code = request.GET.get('code')
    token_url = settings.OIDC_OP_TOKEN_ENDPOINT

    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': settings.KEYCLOAK_REDIRECT_URI,
        'client_id': settings.OIDC_RP_CLIENT_ID
    }

    r = requests.post(token_url, data=data)
    token_info = r.json()

    access_token = token_info.get('access_token')
    payload = jwt.decode(access_token, options={"verify_signature": False})

    request.session['token_info'] = {
        'discipline': payload.get('discipline')
    }

    return redirect('home')

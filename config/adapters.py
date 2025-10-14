from allauth.account.adapter import DefaultAccountAdapter

print(">>> [DEBUG] MyAccountAdapter loaded ✅")

class MyAccountAdapter(DefaultAccountAdapter):
    # 로그인 성공 후 리다이렉트만 기본 동작대로 처리
    def get_login_redirect_url(self, request):
        return super().get_login_redirect_url(request)
        # 항상 홈('/')으로 고정하고 싶으면 위 한 줄 대신:
        # return "/"


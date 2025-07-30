class AllowAllHostsMiddleware:
    """모든 호스트를 허용하는 미들웨어"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Host 헤더 검증을 우회
        request.META['HTTP_HOST'] = 'localhost'
        return self.get_response(request) 
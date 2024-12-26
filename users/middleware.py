from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.urls import resolve
from .models import KYC

class KYCVerificationMiddleware(MiddlewareMixin):
    def  process_view(self,request,view_func,view_args,view_kwargs):
        """
            Block users with unverified KYC from accessing restricted endpoints.
        """
        
        exempted_paths = [
            '/api/auth/login/',
            '/api/auth/register/',
            '/api/kyc/',
        ]
        #alllow admin paths
        if request.path.startswith('/admin/'):
            return None
        
        #allow for paths that are in the list
        if request.path in exempted_paths:
            return None
        
        #ignore id user is authenticated
        if not request.user.is_authenticated:
            return None
        
        try:
            kyc = KYC.objects.get(user=request.user)
            if kyc.status != 'verified':
                return JsonResponse({"detail":"Access denied. Verify KYC"},status=403,)
        except KYC.DoesNotExist:
                return JsonResponse({"detail":"KYC information missing"})

        #allow if kyc is verified 
        return None
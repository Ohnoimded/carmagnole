from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes,authentication_classes
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import AllowAny

@api_view(['GET'])
@permission_classes([AllowAny])
@authentication_classes([BasicAuthentication])
def test_request(request):
    client_ip = request.META.get('HTTP_X_FORWARDED_FOR')
    return Response({'client_ip': client_ip})


from django.test import RequestFactory
from shortdeck.views import home  
import cProfile

def run(*args):
    # Create an instance of the request factory
    factory = RequestFactory()
    # Create a request object using the factory
    request = factory.get('/') 
    
    from django.contrib.auth.models import AnonymousUser
    request.user = AnonymousUser() 

    cProfile.runctx('home(request)', globals(), locals(), filename="home_view_profile.stats")

from django.test import RequestFactory
from shortdeck.views import home  # Replace with your actual view
import cProfile

def run(*args):
    # Create an instance of the request factory
    factory = RequestFactory()
    # Create a request object using the factory
    request = factory.get('/') 

    cProfile.runctx('home(request)', globals(), locals(), filename="home_view_profile.stats")

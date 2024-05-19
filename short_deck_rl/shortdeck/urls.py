from django.urls import path
from . import views
from .views import start_game, end_game, hand_review, decision_data_view, hand_review_page, logout_view, get_pot, change_password

urlpatterns = [
    path('register/', views.register, name='register'),
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('shortdeck/', views.shortdeck, name='shortdeck'),
    path('profile/manage/', views.manage_profile, name='manage_profile'),
    path('start_game/', start_game, name='start_game'),
    path('end_game/', end_game, name='end_game'),
    path('hand_review/', hand_review, name='hand_review'),
    path('decision-data/<int:action_id>/', decision_data_view, name='decision-data'),
    path('change_avatar/', views.change_avatar, name='change_avatar'),
    path('profile/change_avatar/', views.change_avatar, name='change_avatar'),
    path('hand_review_page/', views.hand_review_page, name='hand_review_page'),
    path('hand_review_page/<int:hand_id>/', views.hand_review_page, name='hand_review_detail'),
    path('logout/', views.logout_view, name='logout'),
    path('get_pot/', views.get_pot, name='get_pot'),
    path('change-password/', views.change_password, name='change_password'),
]
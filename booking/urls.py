
# urls.py
from django.urls import path
from .views import room_list, booking_create, booking_list, booking_detail, download_pdf, edit_booking, delete_booking, add_room, delete_room

urlpatterns = [
    path('add_room/', add_room, name='add_room'),
    path('delete_room/<int:room_id>/', delete_room, name='delete_room'),
    path('', room_list, name='room_list'),
    path('booking/create/', booking_create, name='booking_create'),
    path('edit-booking/<int:booking_id>/', edit_booking, name='edit_booking'),
    path('delete-booking/<int:booking_id>/', delete_booking, name='delete_booking'),
    path('booking/list/', booking_list, name='booking_list'),
    path('booking/<int:booking_id>/', booking_detail, name='booking_detail'),
    path('booking/<int:booking_id>/download-pdf/', download_pdf, name='download_pdf'),
   
]

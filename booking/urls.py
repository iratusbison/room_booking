
# urls.py
from django.urls import path
from .views import room_list, booking_create, booking_list, booking_detail, download_pdf, edit_booking, delete_booking #download_pdf_report  download_pdf_range

urlpatterns = [
    path('', room_list, name='room_list'),
    path('booking/create/', booking_create, name='booking_create'),
    path('edit-booking/<int:booking_id>/', edit_booking, name='edit_booking'),
    path('delete-booking/<int:booking_id>/', delete_booking, name='delete_booking'),
    path('booking/list/', booking_list, name='booking_list'),
    path('booking/<int:booking_id>/', booking_detail, name='booking_detail'),
    path('booking/<int:booking_id>/download-pdf/', download_pdf, name='download_pdf'),
    # path('download-pdf-report/', download_pdf_report, name='download_pdf_report'),
    #path('download_pdf/<str:start_date>/<str:end_date>/', download_pdf_range, name='download_pdf_range'),
]

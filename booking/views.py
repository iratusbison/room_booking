# views.py
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from reportlab.pdfgen import canvas
from io import BytesIO
from .models import Room, Booking
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse
from django.shortcuts import redirect
from django.utils.timezone import make_aware
from reportlab.pdfgen import canvas
from io import BytesIO
from decimal import Decimal

def make_aware_with_time(value):
    # Assuming that time is 00:00:00 for start_date and 23:59:59 for end_date
    return make_aware(datetime.combine(value, datetime.min.time()))


def room_list(request):
    rooms = Room.objects.all()
    return render(request, 'room_list.html', {'rooms': rooms})

def booking_create(request):
    if request.method == 'POST':
        room_ids = request.POST.getlist('rooms')
        start_date = request.POST['start_date']
        end_date = request.POST['end_date']
        price = request.POST['price']

        rooms = Room.objects.filter(pk__in=room_ids)
        booking = Booking.objects.create(start_date=start_date, end_date=end_date, price=price)
        booking.rooms.set(rooms)

        # Calculate GST (18%)
        gst = float(price) * 0.18
        booking.gst = gst
        booking.save()

        return render(request, 'booking_details.html', {'booking': booking})

    else:
        rooms = Room.objects.all()
        return render(request, 'booking_create.html', {'rooms': rooms})

from decimal import Decimal

# views.py
from django.db.models import Sum
from django.utils.timezone import make_aware
from datetime import datetime, timedelta

def booking_list(request):
    # Check if a date range is provided in the request
    start_date_str = request.GET.get('start_date', '')
    end_date_str = request.GET.get('end_date', '')

    # Default to the last 30 days if no date range is provided
    if not start_date_str or not end_date_str:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
    else:
        start_date = make_aware(datetime.strptime(start_date_str, '%Y-%m-%d'))
        end_date = make_aware(datetime.strptime(end_date_str, '%Y-%m-%d'))

    bookings = Booking.objects.filter(start_date__range=(start_date, end_date))

    # Calculate total revenue for the given date range
    total_revenue = bookings.aggregate(Sum('price'))['price__sum']

    # Prepare a list to hold each booking along with its details
    bookings_with_details = []

    for booking in bookings:
        # Calculate GST for the booking
        price = float(booking.price)
        gst = price * 0.18

        # Collect room details for the booking
        room_details = ", ".join([room.name for room in booking.rooms.all()])

        # Construct a dictionary with booking details
        booking_details = {
            'booking': booking,
            'start_date': booking.start_date,
            'end_date': booking.end_date,
            'price': price,
            'gst': gst,
            'total_price': price + gst,
            'rooms': room_details,
        }

        bookings_with_details.append(booking_details)
    
    return render(request, 'booking_list.html', {
        'bookings': bookings_with_details,
        'start_date': start_date,
        'end_date': end_date,
        'total_revenue': total_revenue,
        
    })


def booking_detail(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)

    # Calculate GST for the booking
    price = float(booking.price)
    gst = price * 0.18
    total_price = price + gst

    # Collect room details for the booking
    room_details = ", ".join([room.name for room in booking.rooms.all()])

    context = {
        'booking': booking,
        'start_date': booking.start_date.strftime('%Y-%m-%d %H:%M:%S'),
        'end_date': booking.end_date.strftime('%Y-%m-%d %H:%M:%S'),
        'price': price,
        'gst': gst,
        'total_price' : total_price,
        'rooms': room_details,
    }

    return render(request, 'booking_details.html', context)



def generate_pdf_bill(booking):
    buffer = BytesIO()
    p = canvas.Canvas(buffer)

    # Add content to the PDF
    p.drawString(100, 800, f"Booking ID: {booking.id}")
    p.drawString(100, 780, f"Start Date: {booking.start_date.strftime('%Y-%m-%d %H:%M:%S')}")
    p.drawString(100, 760, f"End Date: {booking.end_date.strftime('%Y-%m-%d %H:%M:%S')}")
    p.drawString(100, 740, f"Price: {booking.price}")

    # Calculate GST dynamically
    price = Decimal(booking.price)  # Convert to Decimal
    gst = price * Decimal('0.18')  # Assuming GST is 18%
    total_price = price + gst 
    p.drawString(100, 720, f"GST (18%): {gst} - total :{total_price}" )

    # Add room details
    y_position = 700
    for room in booking.rooms.all():
        p.drawString(100, y_position, f"Room: {room.name} - {room.description}")
        y_position -= 20

    # Close the PDF object cleanly, and we're done.
    p.showPage()
    p.save()

    # File is done, rewind the buffer.
    buffer.seek(0)
    return buffer

def download_pdf(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)
    pdf_buffer = generate_pdf_bill(booking)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=booking_{booking.id}_bill.pdf'
    response.write(pdf_buffer.read())

    return response

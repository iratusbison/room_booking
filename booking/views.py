# views.py
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
from .models import Room, Booking
from django.http import HttpResponse
from django.utils.html import strip_tags
from django.urls import reverse
from django.shortcuts import redirect
from django.utils.timezone import make_aware
from decimal import Decimal
from django.db.models import Sum
from datetime import datetime, timedelta
from django.db import transaction


def make_aware_with_time(value):
    # Assuming that time is 00:00:00 for start_date and 23:59:59 for end_date
    return make_aware(datetime.combine(value, datetime.min.time()))

@transaction.atomic
def booking_create(request):
    if request.method == 'POST':
        room_ids = request.POST.getlist('rooms')
        start_date = request.POST['start_date']
        end_date = request.POST['end_date']
        price = request.POST['price']

        rooms = Room.objects.filter(pk__in=room_ids)
        
        # Check room availability and update status
        if not update_room_availability(rooms, start_date, end_date):
            # Rollback the transaction if rooms are not available
            return HttpResponse("Selected rooms are not available for the specified dates.")

        booking = Booking.objects.create(start_date=start_date, end_date=end_date, price=price)
        booking.rooms.set(rooms)

        # Calculate GST (18%)
        gst = float(price) * 0.18
        booking.gst = gst
        booking.save()

        # Redirect to the booking details page after creating the booking
        return redirect('booking_detail', booking_id=booking.id)

    else:
        rooms = Room.objects.all()
        return render(request, 'booking_create.html', {'rooms': rooms})


def update_room_availability(rooms, start_date, end_date):
    try:
        with transaction.atomic():
            # Check if rooms are available for the specified dates
            for room in rooms:
                bookings_for_room = Booking.objects.filter(
                    rooms=room,
                    start_date__lte=end_date,
                    end_date__gte=start_date
                )
                if bookings_for_room.exists():
                    # Room is not available for the specified dates
                    return False

            # If all rooms are available, update their availability status
            for room in rooms:
                room.available = False
                room.unavailable = True
                room.save()

            return True
    except:
        return False



def room_list(request):
    rooms = Room.objects.all()
    return render(request, 'room_list.html', {'rooms': rooms})





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



from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from io import BytesIO
from reportlab.pdfgen import canvas
from decimal import Decimal

def generate_pdf_bill(booking):
    buffer = BytesIO()

    p = canvas.Canvas(buffer, pagesize=letter)

    # Add SV Mahal and contact details
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, 750, "SV Mahal")
    p.drawString(50, 735, "123 Street, City, Country")
    p.drawString(50, 720, "Phone: +1234567890")
    p.drawString(70, 650, "Booking Bill")
    # Add a line under the SV Mahal details
    p.line(50, 710, 550, 710)
    p.line(70, 645, 300, 645)


    
    

    # Add content to the PDF
    p.drawString(80, 620, f"Booking ID: {booking.id}")
    p.drawString(80, 600, f"Start Date: {booking.start_date.strftime('%Y-%m-%d')}")
    p.drawString(80, 580, f"End Date: {booking.end_date.strftime('%Y-%m-%d')}")
    p.drawString(80, 560, f"Price: {booking.price}")

    # Calculate GST dynamically
    price = Decimal(booking.price)  # Convert to Decimal
    gst = price * Decimal('0.18')  # Assuming GST is 18%
    total_price = price + gst
    p.drawString(80, 540, f"GST (18%): {gst} - Total: {total_price}")

    # Add room details
    y_position = 520
    room_details = ', '.join([room.name for room in booking.rooms.all()])

    p.drawString(80, y_position, "Room Details:")
    p.setFont("Courier", 10)
    text_object = p.beginText(80, y_position - 20)
    text_object.textLines(room_details)
    p.drawText(text_object)

    # Add a border around the content
    p.rect(50, y_position - 40, 540, 200)

    # Add Murugan photo
    murugan_photo_path = "murugan.jpg"  # Path to your Murugan photo
    p.drawImage(murugan_photo_path, 350, 500, width=150, height=150)

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

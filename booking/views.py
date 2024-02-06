# views.py
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
from .models import Room, Booking
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.timezone import make_aware
from decimal import Decimal
from django.db.models import Sum
from datetime import datetime, timedelta
from django.db import transaction
from reportlab.lib.pagesizes import letter
from io import BytesIO
from reportlab.pdfgen import canvas
from decimal import Decimal
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle

def make_aware_with_time(value):
    
    return make_aware(datetime.combine(value, datetime.min.time()))


def add_room(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        available = request.POST.get('available') == 'on'  # Convert 'on' string to True
        unavailable = request.POST.get('unavailable') == 'on'  # Convert 'on' string to True
        room = Room.objects.create(name=name, description=description, available=available, unavailable=unavailable)
        return redirect('room_list')  # Redirect to the room list page after adding a room
    return render(request, 'add_room.html')

def delete_room(request, room_id):
    room = Room.objects.get(id=room_id)
    room.delete()
    return redirect('room_list')

def update_room_availability(rooms, start_date, end_date):
    try:
        with transaction.atomic():
            for room in rooms:
                # Check if there are any bookings that overlap with the specified date range
                bookings_for_room = Booking.objects.filter(
                    rooms=room,
                    start_date__lte=end_date,
                    end_date__gte=start_date
                )
                if bookings_for_room.exists():
                    # Room is not available for the specified dates
                    return False

            return True
    except:
        return False

@transaction.atomic
def booking_create(request):
    if request.method == 'POST':
        room_ids = request.POST.getlist('rooms')
        name = request.POST['name']
        address = request.POST['address']
        phone = request.POST['phone']
        aadhar = request.POST['aadhar']
        email = request.POST['email']
        start_date = request.POST['start_date']
        end_date = request.POST['end_date']
        price = request.POST['price']

        rooms = Room.objects.filter(pk__in=room_ids)

        # Check room availability and update status
        if not update_room_availability(rooms, start_date, end_date):
            # Rollback the transaction if rooms are not available
            return HttpResponse("Selected rooms are not available for the specified dates.")
        # Check if end_date is before start_date
        if end_date < start_date:
            return HttpResponse("End date cannot be before the start date.")

        booking = Booking.objects.create(
            start_date=start_date, 
            end_date=end_date, 
            price=price, 
            name=name, 
            address=address, 
            aadhar=aadhar, 
            email=email, 
            phone=phone
        )
        booking.rooms.set(rooms)

        # Mark rooms as unavailable only if the start date is in the future
        if datetime.strptime(start_date, '%Y-%m-%d').date() > datetime.now().date():
            for room in rooms:
                room.available = False
                room.save()

        # Calculate GST (18%)
        gst = Decimal(price) * Decimal('0.18')
        booking.gst = gst
        booking.save()

        # Redirect to the booking details page after creating the booking
        return redirect('booking_detail', booking_id=booking.id)

    else:
        rooms = Room.objects.filter(available=True)
        return render(request, 'booking_create.html', {'rooms': rooms})

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
    price = booking.price
    gst = price * Decimal('0.18')
    total_price = price + gst

    # Collect room details for the booking
    room_details = ", ".join([room.name for room in booking.rooms.all()])

    context = {
        'booking': booking,
        'start_date': booking.start_date.strftime('%Y-%m-%d %H:%M:%S'),
        'end_date': booking.end_date.strftime('%Y-%m-%d %H:%M:%S'),
        'name': booking.name,
        'address': booking.address,
        'aadhar': booking.aadhar,
        'phone': booking.phone,
        'price': price,
        'gst': gst,
        'email' : booking.email,
        'total_price': total_price,
        'rooms': room_details,
    }

    return render(request, 'booking_details.html', context)


def edit_booking(request, booking_id):
    booking = Booking.objects.get(id=booking_id)
    if request.method == 'POST':
        booking.checkin_datetime = request.POST.get('checkin_datetime')
        booking.checkout_datetime = request.POST.get('checkout_datetime')
        booking.name = request.POST.get('name')
        booking.address = request.POST.get('address')
        booking.phone = request.POST.get('phone')
        booking.aadhar = request.POST.get('aadhar')
        booking.price = request.POST.get('price')

        booking.save()
        return redirect('room_list')
    else:
        return render(request, 'edit_booking.html', {'booking': booking})

@transaction.atomic
def delete_booking(request, booking_id):
    booking = Booking.objects.get(id=booking_id)
    rooms = booking.rooms.all()  # Retrieve all rooms associated with the booking
    for room in rooms:
        room.available = True  # Update each room's availability
        room.save()
    booking.delete()  # Delete the booking
    return redirect('booking_list')

def generate_pdf_bill(booking):
    buffer = BytesIO()

    p = canvas.Canvas(buffer, pagesize=letter)

    # Customize SV Mahal and contact details design
   # p.setFont("Helvetica-Bold", 12)
    p.drawString(50, 750, "SV Mahal")
    p.drawString(50, 735, "456 Main Street, Cityville, Countryland")
    p.drawString(50, 720, "Phone: +9876543210")

    # Calculate GST dynamically
    price = Decimal(booking.price)  # Convert to Decimal
    gst = price * Decimal('0.18')  # Assuming GST is 18%
    total_price = price + gst
    p.drawString(80, 540, f"GST (18%): {gst} - Total: {total_price}")

    # Add booking details in a table
    booking_data = [
     
        ['Booking ID', booking.id],
        ['Start Date', booking.start_date.strftime('%Y-%m-%d')],
        ['End Date', booking.end_date.strftime('%Y-%m-%d')],
        ['Price', f"{booking.price}"],
        ['GST (18%)', f"{gst}"],
        ['Total Price', f"{total_price}"],
        ['Name', booking.name],
        ['Address', booking.address],
        ['Aadhar', booking.aadhar],
        ['Phone', booking.phone],
        ['Email', booking.email],
    ]

    booking_table = Table(booking_data, colWidths=[200, 200])
    booking_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
    ]))

    booking_table.wrapOn(p, 400, 300)
    booking_table.drawOn(p, 80, 400)

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




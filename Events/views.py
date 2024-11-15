from datetime import datetime, timedelta
import logging
import qrcode
import re
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import models
from django.db.models import Q
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import csrf_exempt
from .forms import EventForm, EventSelectionForm
from .models import BarcodeScan, Event, EventRegistration,AboutSection
from account.models import Profile

# Set up logging
logger = logging.getLogger(__name__)


@staff_member_required
@login_required
def create_event(request):
    """
    View function for creating an event.

    Only staff members (admins) can access this view.

    Parameters:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: HTTP response containing the event creation form.
    """
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()
            return redirect('event_list')  # Redirect to event list after event creation
    else:
        form = EventForm()
    return render(request, 'create_event.html', {'form': form})

@login_required
def event_list(request):
    """
    View function for displaying a list of events.

    Parameters:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: HTTP response containing the list of events.
    """
    events = Event.objects.all()
    registered_events_id_list = []
    registered_events_list = EventRegistration.objects.filter(user=request.user.id)
    if registered_events_list:
        for registered_event in registered_events_list:
            registered_events_id_list.append(registered_event.event.id)
    registered_events = registered_events_list if registered_events_list else None
    return render(request, 'event_list.html', {'events': events, 'registered_events': registered_events, 'registered_events_id_list': registered_events_id_list})

@login_required
def event_detail(request, event_id):
    """
    View function for displaying event details and actions.

    Parameters:
        request (HttpRequest): The HTTP request object.
        event_id (int): The ID of the event.

    Returns:
        HttpResponse: HTTP response containing the event details and actions.
    """
    event = get_object_or_404(Event, id=event_id)
    registered_users = EventRegistration.objects.filter(event=event)

    return render(request, 'event_detail.html', {
        'event': event,
        'registered_users': registered_users,
    })

@login_required
def register_for_event(request, event_id):
    """
    View function for registering for an event.

    Only logged-in users can access this view.

    Parameters:
        request (HttpRequest): The HTTP request object.
        event_id (int): The ID of the event to register for.

    Returns:
        HttpResponse: HTTP response redirecting to the event list page after registration.
    """
    event = get_object_or_404(Event, id=event_id)

    # Prevent registration if the event has been stopped
    if event.stop_time and timezone.now() > event.stop_time:
        messages.error(request, 'The event has already ended. Registration is closed.')
        return redirect('event_list')

    # Check if the user is already registered for the event
    if EventRegistration.objects.filter(event=event, user=request.user).exists():
        messages.warning(request, 'You are already registered for this event.')
    else:
        # Add the logged-in user to the attendees of the event
        EventRegistration.objects.create(event=event, user=request.user)
        messages.success(request, 'Successfully registered for the event.')

    return redirect('event_list')  # Redirect to event list after registration

@login_required
def unregister_event(request, event_id):
    """
    View function for unregistering from an event.

    Only logged-in users can access this view.

    Parameters:
        request (HttpRequest): The HTTP request object.
        event_id (int): The ID of the event to unregister from.

    Returns:
        HttpResponse: HTTP response redirecting to the event list page after unregistration.
    """
    # Get the event object from the database
    event = get_object_or_404(Event, id=event_id)
    
    # Check if the user is registered for the event
    registration = EventRegistration.objects.filter(event=event, user=request.user).first()
    if registration:
        registration.delete()
        messages.success(request, 'Successfully unregistered from the event.')
    else:
        messages.warning(request, 'You are not registered for this event.')
    
    return redirect('event_list')

@staff_member_required
@login_required
def delete_event(request, event_id):
    """
    View function for deleting an event.

    Only staff members (admins) can access this view.

    Parameters:
        request (HttpRequest): The HTTP request object.
        event_id (int): The ID of the event to delete.

    Returns:
        HttpResponse: HTTP response redirecting to the event list page after deletion.
    """
    event = get_object_or_404(Event, id=event_id)
    if event:
        event.delete()
        messages.success(request, 'Event deleted successfully.')
        return redirect('event_list')
    else:
        messages.error(request, 'Error deleting event.')
        return redirect('event_list')


@staff_member_required
@login_required
def edit_event(request, event_id):
    """
    View function for editing an event.

    Only staff members (admins) can access this view.

    Parameters:
        request (HttpRequest): The HTTP request object.
        event_id (int): The ID of the event to edit.

    Returns:
        HttpResponse: HTTP response containing the event edit form.
    """
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'Event updated successfully.')
            return redirect('event_list')
    else:
        form = EventForm(instance=event)
    return render(request, 'create_event.html', {'form': form, 'event': event,"event_mode":"edit"})


@staff_member_required
@login_required
def view_event_attendees(request, event_id):
    """
    View function for viewing all users registered for an event.

    Only staff members (admins) can access this view.

    Parameters:
        request (HttpRequest): The HTTP request object.
        event_id (int): The ID of the event.

    Returns:
        HttpResponse: HTTP response containing the list of users registered for the event.
    """
    event = Event.objects.filter(id=event_id).all()
    attendees = event
    return render(request, 'event_attendees.html', {'event': event, 'attendees': event})

@staff_member_required
@login_required
def view_registered_users(request, event_id):
    """
    View function for displaying users registered for a specific event.

    Parameters:
        request (HttpRequest): The HTTP request object.
        event_id (int): The ID of the event for which registered users are to be displayed.

    Returns:
        HttpResponse: HTTP response containing the list of registered users for the event.
    """
    event = Event.objects.get(id=event_id)
    registered_users = EventRegistration.objects.filter(event=event)
    return render(request, 'registered_users.html', {'event': event, 'registered_users': registered_users})

def scan_barcode(request):
    last_scan_time = request.session.get('last_scan_time')
    if last_scan_time and (timezone.now() - datetime.fromisoformat(last_scan_time)) < timedelta(seconds=4):
        return JsonResponse({'message':None, 'time_taken': None, 'error': None})
    request.session['last_scan_time'] = timezone.now().isoformat()
    if request.method == 'POST':
        barcode_value_ob =  request.POST.get("barcode_value")
        try:
            barcode_value = ''.join(filter(str.isdigit, barcode_value_ob))
        except Exception as e:
            pass
        print("barcode vale is:",barcode_value)
        barcode_data = Profile.objects.filter(barcode_value=barcode_value).first()
        if barcode_data:
            barcode_scan = BarcodeScan.objects.filter(user=barcode_data.user).first()
            if barcode_scan is None:
                # First scan
                scan = BarcodeScan(user=barcode_data.user, scan_time=timezone.now())
                scan.save()
                return JsonResponse({'message': 'Please enjoy your race!', 'time_taken': None, 'error': None})
            else:
                # Subsequent scan
                if barcode_scan.time_taken:
                    message = f'This user {barcode_data.user.username} already participated Time taken: {barcode_scan.time_taken} seconds.'
                    time_taken = f'Time taken: {barcode_scan.time_taken} seconds.'
                    return JsonResponse({'message': message, 'time_taken': time_taken, 'error': None})

                scan_time = timezone.now()
                time_taken = (scan_time - barcode_scan.scan_time).total_seconds()
                barcode_scan.scan_time = scan_time
                barcode_scan.time_taken = time_taken
                barcode_scan.save()

                return JsonResponse({'message': None, 'time_taken': f'Time taken: {time_taken} seconds.', 'error': None})
        else:
            return JsonResponse({'message': None, 'time_taken': None, 'error': 'Scan Only Registered Users!'})
    else:
        return render(request, 'scan.html', {'current_url': request.path})
        
def scan_QR_code_mobile(request):
    """
    Handles the QR code scanning for mobile devices, ensuring that the scan is processed correctly 
    based on the user’s event registration status and the time taken for the scan.

    Args:
        request (HttpRequest): The HTTP request object containing POST data with the barcode value 
                               and event ID.

    Returns:
        JsonResponse: A JSON response containing a message, the time taken, or an error message, 
                      depending on the scan outcome.
    
    Workflow:
        - If the request method is POST, the barcode value and event ID are retrieved from the form data.
        - A QR code is generated based on the barcode value.
        - The barcode value is validated against the user's profile.
        - If the user is registered for the selected event:
            - If the user has not previously scanned for the event, the scan is recorded as the start time.
            - If the user has already scanned, the finish time is calculated, and the time taken is returned.
        - If the user is not registered or the barcode value is invalid, an error message is returned.
        - If the request method is not POST, the available events are rendered in a form for user selection.
    """
    last_scan_time = request.session.get('last_scan_time')
    if last_scan_time and (timezone.now() - datetime.fromisoformat(last_scan_time)) < timedelta(seconds=3):
        return JsonResponse({'message': None, 'time_taken': None, 'error': None})
    request.session['last_scan_time'] = timezone.now().isoformat()

    if request.method == 'POST':
        barcode_value = request.POST.get('barcode_value', '')
        event_id = request.POST.get('event_id')  # Get the selected event ID from the form
        event = get_object_or_404(Event, id=event_id)  # Get the event object
        
        qr_code = qrcode.QRCode()
        qr_code.add_data(barcode_value)
        
        try:
            qr_code_data = qr_code.make_image(fill_color="black", back_color="white")
            qr_code_data.save('qr_code.png')
        except Exception as e:
            return JsonResponse({'message': None, 'time_taken': None, 'error': str(e)})

        if re.match(r".*[a-z]$", barcode_value, re.IGNORECASE):
            barcode_value = barcode_value[:-1]
        barcode_data = Profile.objects.filter(barcode_value=barcode_value).first()

        if barcode_data:
            registered_events = EventRegistration.objects.filter(user=barcode_data.user, event=event)
            if registered_events:
                barcode_scan = BarcodeScan.objects.filter(user=barcode_data.user, event=event).first()
                if barcode_scan is None:
                    # start scan
                    scan = BarcodeScan(user=barcode_data.user, event=event, scan_time=timezone.now())
                    scan.save()
                    return JsonResponse({'message': 'Race start, Please enjoy your race!', 'time_taken': None, 'error': None})
                else:
                    # finish scan
                    if barcode_scan.time_taken:
                        message = f'This user {barcode_data.user.username} already participated in {event.name}, Time taken: {barcode_scan.time_taken} seconds.'
                        return JsonResponse({'message': message, 'time_taken': None, 'error': None})

                    scan_time = timezone.now()
                    time_taken = (scan_time - barcode_scan.scan_time).total_seconds()
                    barcode_scan.scan_time = scan_time
                    barcode_scan.time_taken = time_taken
                    barcode_scan.save()
                    return JsonResponse({'message': None, 'time_taken': f'Time taken: {time_taken} seconds.', 'error': None})
            else:
                return JsonResponse({'message': None, 'time_taken': None, 'error': 'User not registered for the selected event.'})
        else:
            return JsonResponse({'message': None, 'time_taken': None, 'error': 'No user Found.'})
    else:
        events = Event.objects.all()
        return render(request, 'qr_code_scan.html', {'events': events})

@csrf_exempt
def scan_barcode_mobile(request, event_id):
    try:
        selected_event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        return JsonResponse({'message': None, 'time_taken': None, 'error': 'Selected event not found.'})

    if request.method == 'POST':
        barcode_value = request.POST.get("barcode_value")
        
        try:
            barcode_value = ''.join(filter(str.isdigit, barcode_value))
        except Exception as e:
            return JsonResponse({'message': None, 'time_taken': None, 'error': 'Invalid barcode value.'})
        
        barcode_data = Profile.objects.filter(barcode_value=barcode_value).first()
        
        if barcode_data:
            registered_event = EventRegistration.objects.filter(
                user=barcode_data.user,
                event=selected_event
            ).exists()

            if registered_event:
                barcode_scan = BarcodeScan.objects.filter(
                    user=barcode_data.user,
                    event=selected_event
                ).first()

                current_time = timezone.now()

                if barcode_scan is None:
                    # Start scan
                    scan = BarcodeScan(user=barcode_data.user, event=selected_event, scan_time=current_time)
                    scan.save()
                    return JsonResponse({
                        'message': f'{barcode_data.user.username} scanned successfully. Enjoy your race!',
                        'time_taken': None,
                        'error': None
                    })
                else:
                    # Check if 30 seconds have passed since the start scan
                    if current_time - barcode_scan.scan_time < timedelta(seconds=3):
                        return JsonResponse({
                            'message': f'{barcode_data.user.username} scanned successfully.',
                            'time_taken': None,
                            'error': None
                        })

                    # Finish scan
                    if barcode_scan.time_taken:
                        message = f'User {barcode_data.user.username} has already completed {selected_event.name}. Time taken: {barcode_scan.time_taken}'
                        return JsonResponse({'message': message, 'time_taken': None, 'error': None})
                    
                    time_taken = current_time - barcode_scan.scan_time
                    time_taken_str = format_timedelta(time_taken)
                    barcode_scan.time_taken = time_taken_str
                    barcode_scan.save()
                    return JsonResponse({
                        'message': f'Race Finished for {barcode_data.user.username} in {selected_event.name}',
                        'time_taken': f'Time taken: {time_taken_str}',
                        'error': None
                    })
            else:
                return JsonResponse({
                    'message': None,
                    'time_taken': None,
                    'error': f'User not registered for {selected_event.name}.'
                })
        else:
            return JsonResponse({'message': None, 'time_taken': None, 'error': 'No user found with this barcode.'})

    # Render the mobile scan page if the request method is GET
    return render(request, 'mobile_scan.html', {'event': selected_event})

def format_timedelta(td):
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = td.microseconds // 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{milliseconds:03d}"


@csrf_exempt
def camera_scan_barcode2(request, event_id):
    try:
        selected_event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        return JsonResponse({'message': None, 'time_taken': None, 'error': 'Selected event not found.'})

    if request.method == 'POST':
        action = request.POST.get('action')

        # Check if the event has a stop time and if it has been reached
        if selected_event.stop_time and timezone.now() > selected_event.stop_time:
            return JsonResponse({'message': None, 'time_taken': None, 'error': 'Event has been stopped. No further actions allowed.'})

        if action == 'start_race':
            # Start the race and save the start time
            selected_event.start_time = timezone.now()
            selected_event.save()
            return JsonResponse({'message': 'Race started!', 'start_time': selected_event.start_time.isoformat()})
        
        elif action == 'scan_barcode':
            barcode_value = request.POST.get("barcode_value")
            
            if not selected_event.start_time:
                return JsonResponse({'message': None, 'time_taken': None, 'error': 'Race has not started yet.'})
            
            try:
                barcode_value = ''.join(filter(str.isdigit, barcode_value))
            except Exception:
                return JsonResponse({'message': None, 'time_taken': None, 'error': 'Invalid barcode value.'})
            
            # Retrieve user profile associated with the barcode
            barcode_data = Profile.objects.filter(barcode_value=barcode_value).first()
            
            if barcode_data:
                # Check if user is registered for the selected event
                registered_event = EventRegistration.objects.filter(
                    user=barcode_data.user,
                    event=selected_event
                ).exists()

                if registered_event:
                    # Check if a scan record already exists for this user and event
                    existing_scan = BarcodeScan.objects.filter(
                        user=barcode_data.user,
                        event=selected_event
                    ).first()

                    if existing_scan:
                        # Return message if the user has already finished the race
                        return JsonResponse({
                            'message': f'This user {barcode_data.user.username} has already finished the race.',
                            'time_taken': f'Time taken: {existing_scan.time_taken}',
                            'error': None
                        })
                    else:
                        # Calculate and save time taken if no previous record exists
                        scan_time = timezone.now()
                        time_taken_delta = scan_time - selected_event.start_time
                        time_taken_formatted = str(time_taken_delta)

                        # Save the new scan entry
                        scan = BarcodeScan(
                            user=barcode_data.user,
                            event=selected_event,
                            scan_time=scan_time,
                            time_taken=time_taken_formatted
                        )
                        scan.save()
                        return JsonResponse({
                            'message': f'Race finished for {barcode_data.user.username}',
                            'time_taken': f'Time taken: {time_taken_formatted}',
                            'error': None
                        })
                else:
                    return JsonResponse({
                        'message': None,
                        'time_taken': None,
                        'error': f'User not registered for {selected_event.name}.'
                    })
            else:
                return JsonResponse({'message': None, 'time_taken': None, 'error': 'No user found with this barcode.'})

    return render(request, 'mobile_scan2.html', {'event': selected_event})

def select_event(request):
    """
    Displays a form for selecting an event and handles form submissions.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Renders a form for selecting an event or redirects to the barcode scan page based on form submission.
    """
    if request.method == 'POST':
        form = EventSelectionForm(request.POST)
        if form.is_valid():
            event_id = form.cleaned_data['event'].id
            request.session['selected_event_id'] = event_id
            return redirect('camera_scan_barcode2', event_id=event_id)
    else:
        form = EventSelectionForm()
    
    return render(request, 'select_event.html', {'form': form})

def stop_event(request):
    """
    Stops an event by setting its stop time to the current time.

    Args:
        request (HttpRequest): The HTTP request object containing the event ID in POST data.

    Returns:
        JsonResponse: A JSON response with a success or error message.
        HttpResponseBadRequest: If the request method is not POST.
    """
    if request.method == 'POST':
        # Get the event ID from the POST data
        event_id = request.POST.get('event_id')

        if event_id:
            try:
                # Fetch the event using the event ID
                event = Event.objects.get(id=event_id)

                # Set the stop_time to the current time to stop the event
                event.stop_time = timezone.now()
                event.save()

                return JsonResponse({'message': 'Event stopped successfully.'})
            except Event.DoesNotExist:
                return JsonResponse({'error': 'Event not found.'}, status=404)
        else:
            return JsonResponse({'error': 'Event ID is required.'}, status=400)
    else:
        return HttpResponseBadRequest('Invalid request method.')

@user_passes_test(lambda u: u.is_superuser)
def send_email_user(request):
    """
    Sends an email to all users with their race scan details.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponseRedirect: Redirects to the 'send_email' page after processing.
        HttpResponse: Renders the email sending page if the request method is not POST.
    """
    if request.method == 'POST':
        try:
            users = User.objects.all()
            from_email = settings.EMAIL_HOST_USER

            for user in users:
                # Filter scans for the current user that have a non-null time_taken value
                scans = BarcodeScan.objects.filter(user=user, time_taken__isnull=False)
                if scans.exists():
                    subject = 'OCR Time Details'
                    message = (
                        f"Hello {user.username},\n\n"
                        "Congratulations on completing your race! We are thrilled to share your scan details with you.\n\n"
                        "Here are your scan details:\n"
                    )
                    for scan in scans:
                        message += f"Scan Time: {scan.scan_time}, Time Taken: {scan.time_taken} seconds\n"
                    message += (
                        "\nYour performance was outstanding, and we are proud of your achievement.\n\n"
                        "Best Regards,\n"
                        "OCR"
                    )
                    recipient_list = [user.email]

                    # Log the email details before sending
                    logger.info(f'Sending email to {user.email} with subject "{subject}"')
                    send_mail(subject, message, from_email, recipient_list, fail_silently=False)
                    messages.success(request, f'Email sent to {user.email}')
            
            return redirect('send_email')  # Redirect to avoid resubmission
        except Exception as e:
            logger.error("Error sending emails: %s", e)
            messages.error(request, 'An error occurred while sending emails.')
    
    return render(request, 'send_email.html')

@user_passes_test(lambda u: u.is_superuser)
def event_results(request, event_id):
    """
    Displays the results of an event and allows sending email to all users with their scan details.

    Args:
        request (HttpRequest): The HTTP request object.
        event_id (int): The ID of the event for which to display results.

    Returns:
        HttpResponse: Renders the event results page with the event and its scan records.
    """
    # Get the event based on the event_id
    event = get_object_or_404(Event, id=event_id)

    # Filter the BarcodeScan records for the selected event
    results = BarcodeScan.objects.filter(event=event).order_by('scan_time')

    # Check if form is submitted to send emails
    if request.method == 'POST':
        try:
            users = User.objects.all()
            from_email = settings.EMAIL_HOST_USER

            for user in users:
                # Filter scans for the current user that have a non-null time_taken value
                scans = BarcodeScan.objects.filter(user=user, event=event, time_taken__isnull=False)
                if scans.exists():
                    subject = 'OCR Time Details for Event: {}'.format(event.name)
                    message = (
                        f"Hello {user.username},\n\n"
                        "Congratulations on completing your OCR race! We are thrilled to share your scan details with you.\n\n"
                        "Here are your scan details:\n"
                    )
                    for scan in scans:
                        message += f"Scan Time: {scan.scan_time}, Time Taken: {scan.time_taken} seconds\n"
                    message += (
                        "\nYour performance was outstanding, and we are proud of your achievement.\n\n"
                        "Best Regards,\n"
                        "OCR"
                    )
                    recipient_list = [user.email]

                    # Log the email details before sending
                    logger.info(f'Sending email to {user.email} with subject "{subject}"')
                    send_mail(subject, message, from_email, recipient_list, fail_silently=False)
                    messages.success(request, mark_safe(f'<strong>Results for the Event <strong style="font-weight: 900;">{event.name}</strong>  have been successfully sent to all the users.</strong>'))
            
        except Exception as e:
            logger.error("Error sending emails: %s", e)
            messages.error(request, 'An error occurred while sending emails.')

    context = {
        'event': event,
        'results': results,
    }
    
    return render(request, 'event_results.html', context)

def about_us(request):
    # Fetch the first entry in AboutSection (assuming only one entry)
    about_section = AboutSection.objects.first()

    if about_section is None:
        # Handle the case where no AboutSection entry exists
        return render(request, 'about_us.html', {'error': 'No About Us section found.'})

    context = {
       
        'subtitle': about_section.subtitle,
        'description': about_section.description.strip().split('\n'),  # Split description into paragraphs
        'image': about_section.image.url if about_section.image else None,  # Check if image exists
        'stats': about_section.stats.all(),
    }
    return render(request, 'about_us.html', context)

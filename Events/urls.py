# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('create-event/', views.create_event, name='create_event'),
    path('events/', views.event_list, name='event_list'),
    path('register/<int:event_id>/', views.register_for_event, name='register_for_event'),
     path('events/<int:event_id>/attendees/', views.view_event_attendees, name='view_event_attendees'),
     path('events/event/<int:event_id>/registered_users/', views.view_registered_users, name='view_registered_users'),
    path('events/<int:event_id>/unregister/', views.unregister_event, name='unregister_event'),
    path('scan/', views.scan_barcode, name='scan_barcode'),
  
    path('events/<int:event_id>/scan/', views.scan_barcode_mobile, name='camera_scan_barcode'),
    path('qr_decode_profile/', views.scan_QR_code_mobile, name='camera_scan_qrcode'),
    path('edit-event/<int:event_id>', views.edit_event, name='edit_event'),
    path('delete-event/<int:event_id>', views.delete_event, name='delete_event'),
   
    # Add more URLs as needed


    path('select-event/', views.select_event, name='select_event'),


    

    path('events/<int:event_id>/scan-at-one/', views.camera_scan_barcode2, name='camera_scan_barcode2'),
    

    path('stop_event/', views.stop_event, name='stop_event'),

 
    path('send_email', views.send_email_user, name='send_email'),





    path('events/<int:event_id>/', views.event_detail, name='event_detail'),

     path('event/<int:event_id>/results/', views.event_results, name='event_results'),

     path('about/', views.about_us, name='about_us'),


]

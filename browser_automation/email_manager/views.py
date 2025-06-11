from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import CustomUser  
from django.contrib import messages
from django.http import JsonResponse
from django.core.management import call_command
from io import TextIOWrapper
import csv
import tempfile
import logging
from django.db import transaction, IntegrityError
from django.contrib.auth.hashers import make_password

logger = logging.getLogger(__name__)


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'email_manager/login.html', {
                'error': 'Invalid username or password'
            })
    return render(request, 'email_manager/login.html')


@login_required
def dashboard(request):
    # Handle add user form submission
    if request.method == 'POST' and request.POST.get('action') == 'add_user':
        try:
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            proxy_address = request.POST.get('proxy_address', '').strip()
            is_connected = request.POST.get('is_connected') == 'on'
            is_active_profile = request.POST.get('is_active_profile') == 'on'
            temp_password = request.POST.get('temp_password', '').strip()
            
            if not username or not email:
                messages.error(request, "Username and email are required.")
            elif CustomUser.objects.filter(username=username).exists():
                messages.error(request, f"Username '{username}' already exists.")
            elif CustomUser.objects.filter(email=email).exists():
                messages.error(request, f"Email '{email}' already exists.")
            else:
                # Create user
                user = CustomUser.objects.create(
                    username=username,
                    email=email,
                    proxy_address=proxy_address if proxy_address else None,
                    is_connected=is_connected,
                    is_active_profile=is_active_profile,
                    profile_id=f"{username}_{CustomUser.objects.count() + 1}"
                )
                
                if temp_password:
                    user.set_password(temp_password)
                    user.save()
                
                messages.success(request, f"User '{username}' created successfully.")
                return redirect('dashboard')
                
        except Exception as e:
            messages.error(request, f"Error creating user: {str(e)}")
    
    # Get all users except the currently logged-in user
    users = CustomUser.objects.exclude(id=request.user.id)
    return render(request, 'email_manager/dashboard.html', {
        'users': users,
        'current_user': request.user
    })


def logout_view(request):
    logout(request)
    return redirect('login')


def _process_merged_csv(uploaded_file):
  
    results = {
        'success_count': 0,
        'error_count': 0,
        'errors': [],
        'duplicates': []
    }
    
    try:
        # Handle both file objects and file paths
        if isinstance(uploaded_file, str):
            # It's a file path
            csv_file = open(uploaded_file, 'r', encoding='utf-8-sig')
            reader = csv.DictReader(csv_file)
        else:
            # It's an uploaded file object
            uploaded_file.seek(0)
            csv_file = TextIOWrapper(uploaded_file.file, encoding='utf-8-sig')
            reader = csv.DictReader(csv_file)
        
        # DEBUG: Print the actual fieldnames found in CSV
        print(f"DEBUG: CSV fieldnames: {reader.fieldnames}")
        
        # Validate required headers
        required_fields = ['username', 'email', 'is_connected', 'is_active_profile']
        
        # Check for exact matches and potential whitespace issues
        actual_fields = [field.strip() if field else field for field in reader.fieldnames] if reader.fieldnames else []
        print(f"DEBUG: Stripped fieldnames: {actual_fields}")
        
        missing_fields = []
        for required_field in required_fields:
            if required_field not in actual_fields:
                missing_fields.append(required_field)
        
        if missing_fields:
            raise ValueError(f"Missing required CSV headers: {missing_fields}. Found headers: {reader.fieldnames}")
        
        # Process in batches for better performance
        batch_size = 1000
        users_to_create = []
        row_count = 0
        
        with transaction.atomic():
            for row in reader:
                row_count += 1
                
                # DEBUG: Print first few rows to see the actual data structure
                if row_count <= 3:
                    print(f"DEBUG: Row {row_count} data: {dict(row)}")
                
                try:
                    # Clean the row keys (remove whitespace from column names)
                    cleaned_row = {key.strip(): value for key, value in row.items() if key}
                    
                    # Validate required fields exist in this specific row
                    missing_in_row = [field for field in required_fields if field not in cleaned_row or not cleaned_row[field].strip()]
                    if missing_in_row:
                        error_msg = f"Row {row_count}: Missing or empty required fields: {missing_in_row}. Row data: {cleaned_row}"
                        results['errors'].append(error_msg)
                        results['error_count'] += 1
                        print(f"DEBUG: {error_msg}")
                        continue
                    
                    # Validate and clean data
                    username = cleaned_row['username'].strip()
                    email = cleaned_row['email'].strip().lower()
                    
                    if not username or not email:
                        results['errors'].append(f"Row {row_count}: Username and email cannot be empty")
                        results['error_count'] += 1
                        continue
                    
                    # Check for duplicates in database
                    if CustomUser.objects.filter(username=username).exists():
                        results['duplicates'].append(f"Row {row_count}: Username '{username}' already exists")
                        results['error_count'] += 1
                        continue
                        
                    if CustomUser.objects.filter(email=email).exists():
                        results['duplicates'].append(f"Row {row_count}: Email '{email}' already exists")
                        results['error_count'] += 1
                        continue
                    
                    # Prepare user data
                    user_data = {
                        'username': username,
                        'email': email,
                        'proxy_address': cleaned_row.get('proxy_address', '').strip() or None,
                        'is_connected': cleaned_row['is_connected'].strip().lower() in ['true', '1', 'yes'],
                        'is_active_profile': cleaned_row['is_active_profile'].strip().lower() in ['true', '1', 'yes'],
                    }
                    
                    user_data['profile_id'] = f"{username}_{row_count}"
                    
                    temp_password = cleaned_row.get('temp_password', '').strip()
                    if temp_password:
                        user_data['password'] = make_password(temp_password)
                    else:
                        # Generate a random password if none provided
                        import secrets
                        import string
                        random_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
                        user_data['password'] = make_password(random_password)
                    
                    # DEBUG: Print user data for first few rows
                    if row_count <= 3:
                        print(f"DEBUG: Creating user with data: {user_data}")
                    
                    users_to_create.append(CustomUser(**user_data))
                    
                    # Batch insert when we reach batch_size
                    if len(users_to_create) >= batch_size:
                        CustomUser.objects.bulk_create(users_to_create, ignore_conflicts=False)
                        results['success_count'] += len(users_to_create)
                        users_to_create = []
                    
                except KeyError as e:
                    error_msg = f"Row {row_count}: Missing required field {e}. Available fields: {list(cleaned_row.keys()) if 'cleaned_row' in locals() else list(row.keys())}"
                    results['errors'].append(error_msg)
                    results['error_count'] += 1
                    logger.warning(error_msg)
                    print(f"DEBUG: {error_msg}")
                    continue
                    
                except IntegrityError as e:
                    error_msg = f"Row {row_count}: Database integrity error for user '{cleaned_row.get('username', 'unknown') if 'cleaned_row' in locals() else row.get('username', 'unknown')}': {str(e)}"
                    results['errors'].append(error_msg)
                    results['error_count'] += 1
                    logger.error(error_msg)
                    continue
                    
                except Exception as e:
                    error_msg = f"Row {row_count}: Error processing user '{cleaned_row.get('username', 'unknown') if 'cleaned_row' in locals() else row.get('username', 'unknown')}': {str(e)}"
                    results['errors'].append(error_msg)
                    results['error_count'] += 1
                    logger.error(error_msg)
                    print(f"DEBUG: {error_msg}")
                    continue
            
            # Insert remaining users
            if users_to_create:
                CustomUser.objects.bulk_create(users_to_create, ignore_conflicts=False)
                results['success_count'] += len(users_to_create)
        
        logger.info(f"CSV processing completed. Success: {results['success_count']}, Errors: {results['error_count']}")
        
    except Exception as e:
        error_msg = f"CSV processing failed: {str(e)}"
        logger.error(error_msg)
        results['errors'].append(error_msg)
        results['error_count'] += 1
        print(f"DEBUG: {error_msg}")
    
    finally:
        # Clean up file resources
        if 'csv_file' in locals():
            csv_file.close()
    
    return results


@login_required
def delete_user(request, user_id):
    if request.method == 'POST':
        try:
            user = CustomUser.objects.get(id=user_id)
            username = user.username
            user.delete()
            messages.success(request, f"User '{username}' deleted successfully.")
        except CustomUser.DoesNotExist:
            messages.error(request, "User not found.")
        except Exception as e:
            messages.error(request, f"Error deleting user: {str(e)}")
    
    return redirect('dashboard')


@login_required
def add_user(request):
    if request.method == 'POST':
        try:
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            proxy_address = request.POST.get('proxy_address', '').strip()
            is_connected = request.POST.get('is_connected') == 'on'
            is_active_profile = request.POST.get('is_active_profile') == 'on'
            temp_password = request.POST.get('temp_password', '').strip()
            
            if not username or not email:
                messages.error(request, "Username and email are required.")
                return render(request, 'email_manager/add_user.html')
            
            if CustomUser.objects.filter(username=username).exists():
                messages.error(request, f"Username '{username}' already exists.")
                return render(request, 'email_manager/add_user.html')
                
            if CustomUser.objects.filter(email=email).exists():
                messages.error(request, f"Email '{email}' already exists.")
                return render(request, 'email_manager/add_user.html')
            
            # Create user
            user = CustomUser.objects.create(
                username=username,
                email=email,
                proxy_address=proxy_address if proxy_address else None,
                is_connected=is_connected,
                is_active_profile=is_active_profile,
                profile_id=f"{username}_{CustomUser.objects.count() + 1}"
            )
            
            if temp_password:
                user.set_password(temp_password)
                user.save()
            
            messages.success(request, f"User '{username}' created successfully.")
            return redirect('dashboard')
            
        except Exception as e:
            messages.error(request, f"Error creating user: {str(e)}")
    
    return render(request, 'email_manager/add_user.html')


@login_required
def edit_user(request, user_id):
    # For now, just redirect back to dashboard
    # You can implement a proper edit form later
    messages.info(request, "Edit functionality coming soon!")
    return redirect('dashboard')



@login_required
def upload_users_csv(request):
    """Handle single merged CSV file upload"""
    if request.method == 'POST' and 'csv_file' in request.FILES:
        uploaded_file = request.FILES['csv_file']
        
        # Validate file type
        if not uploaded_file.name.endswith('.csv'):
            return JsonResponse({'error': 'Please upload a CSV file'}, status=400)
        
        results = _process_merged_csv(uploaded_file)
        
        return JsonResponse({
            'message': f"Processing complete. {results['success_count']} users created, {results['error_count']} errors",
            'results': results
        })
    
    return JsonResponse({'error': 'No CSV file provided'}, status=400)


def bulk_import(request):
    """Handle bulk import via form - supports both separate files and merged file"""
    context = {}
    
    if request.method == 'POST':
        try:
            # Check if separate files were uploaded
            if all(key in request.FILES for key in ['emails_file', 'proxies_file', 'statuses_file']):
                # Handle separate CSV uploads - merge them first
                with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.csv') as merged_file:
                    try:
                        # Call your CSV merger management command
                        call_command(
                            'csv_merger',
                            emails=request.FILES['emails_file'].temporary_file_path(),
                            proxies=request.FILES['proxies_file'].temporary_file_path(),
                            statuses=request.FILES['statuses_file'].temporary_file_path(),
                            output=merged_file.name
                        )
                        
                        # Process the merged file
                        results = _process_merged_csv(merged_file.name)
                        
                    finally:
                        # Clean up temporary file
                        import os
                        if os.path.exists(merged_file.name):
                            os.unlink(merged_file.name)
            
            elif 'merged_file' in request.FILES:
                # Handle pre-merged CSV
                results = _process_merged_csv(request.FILES['merged_file'])
            
            else:
                messages.error(request, 'Please provide either separate CSV files or a merged CSV file.')
                return render(request, 'email_manager/bulk_import.html', context)
            
            # Add results to context for display
            context['results'] = results
            
            # Add success/error messages
            if results['success_count'] > 0:
                messages.success(request, f"Successfully imported {results['success_count']} users.")
                if results['error_count'] > 0:
                    messages.warning(request, f"Failed to import {results['error_count']} users.")
                return redirect('dashboard')

            if results['error_count'] > 0:
                messages.warning(request, f"Failed to import {results['error_count']} users. Check details below.")

                
        except Exception as e:
            messages.error(request, f"Import failed: {str(e)}")
            logger.error(f"Bulk import error: {str(e)}")
    
    return render(request, 'email_manager/bulk_import.html', context)
from PIL import Image
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import os
import uuid
import tempfile
import shutil
import zipfile
import time
import logging
import traceback
import fitz  # PyMuPDF
import io
import re
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
import tempfile
import subprocess
from pdf2docx import Converter
import ocrmypdf
import sys
import fitz
import PIL


def index(request):
    # Define all the PDF tools available on the site
    tools = [
        {
            'name': 'WebP to PNG',
            'description': 'Convert WebP images to PNG format',
            'icon': 'fa-file-image',
            'url': 'webp-to-png'
        },
        {
            'name': 'PNG to WebP',
            'description': 'Convert PNG images to WebP format for smaller file sizes',
            'icon': 'fa-file-image',
            'url': 'png-to-webp'
        },
        {
            'name': 'PDF to PNG',
            'description': 'Convert PDF pages to high-quality PNG images',
            'icon': 'fa-file-pdf',
            'url': 'pdf-to-png'
        },
        {
            'name': 'PNG to PDF',
            'description': 'Convert PNG images into professional PDF documents',
            'icon': 'fa-file-pdf',
            'url': 'png-to-pdf'
        },
        {
            'name': 'JPG to PNG',
            'description': 'Convert JPG images to lossless PNG format',
            'icon': 'fa-file-image',
            'url': 'jpg-to-png'
        },
        {
            'name': 'PNG to JPG',
            'description': 'Convert PNG images to JPG format',
            'icon': 'fa-file-image',
            'url': 'png-to-jpg'
        },
        {
            'name': 'Word to PDF',
            'description': 'Convert Word documents to PDF format',
            'icon': 'fa-file-word',
            'url': 'word-to-pdf'
        },
        {
            'name': 'JPG to PDF',
            'description': 'Convert JPG images to PDF documents',
            'icon': 'fa-file-image',
            'url': 'jpg-to-pdf'
        },
        {
            'name': 'PDF to Word',
            'description': 'Convert PDFs to editable Word documents',
            'icon': 'fa-file-word',
            'url': 'pdf-to-word'
        },
        {
            'name': 'PDF to JPG',
            'description': 'Convert each PDF page to a JPG image',
            'icon': 'fa-file-image',
            'url': 'pdf-to-jpg'
        },
    ]
    
    # Pass the tools to the template
    context = {
        'tools': tools,
    }
    return render(request, 'core/index.html', context)

def privacy_policy(request):
    return render(request, 'privacy_policy.html')

def terms_of_service(request):
    return render(request, 'terms_of_service.html')


from django.core.mail import send_mail
from django.conf import settings

def contact(request):
    """View for contact form processing"""
    form_submitted = False
    
    if request.method == 'POST':
        # Get form data
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        subject = request.POST.get('subject', '')
        message = request.POST.get('message', '')
        
        # Create email message with form data
        email_subject = f"Contact Form: {subject}"
        email_message = f"""
        New message from the contact form:
        
        Name: {name}
        Email: {email}
        Subject: {subject}
        
        Message:
        {message}
        """
        
        # Send email
        try:
            send_mail(
                email_subject,
                email_message,
                settings.DEFAULT_FROM_EMAIL,  # From email
                [settings.CONTACT_EMAIL],     # To email
                fail_silently=False,
            )
            form_submitted = True
        except Exception as e:
            # In production, log this error
            print(f"Error sending email: {e}")
    
    return render(request, 'contact.html', {'form_submitted': form_submitted})

def about_us(request):
    """View for the About Us page"""
    return render(request, 'about_us.html')


def webp_to_png(request):
    """View for WebP to PNG conversion tool page"""
    return render(request, 'core/webp_to_png.html')

logger = logging.getLogger(__name__)

@csrf_exempt
def webp_to_png_convert(request):
    """API endpoint for WebP to PNG conversion with improved error handling for Windows"""
    if request.method == 'POST' and request.FILES.getlist('files'):
        files = request.FILES.getlist('files')
        temp_dir = None
        
        try:
            # Create a temporary directory for processing files
            temp_dir = tempfile.mkdtemp()
            output_dir = os.path.join(temp_dir, 'output')
            os.makedirs(output_dir, exist_ok=True)
            
            # Process each file
            converted_files = []
            
            logger.info(f"Received {len(files)} files for conversion")
            
            # Debug: Print file details
            for i, file in enumerate(files):
                logger.info(f"File {i+1}: {file.name}, Size: {file.size}, Content Type: {file.content_type}")
            
            for file in files:
                # Check if the file is a WebP image
                if not file.name.lower().endswith('.webp'):
                    logger.warning(f"Skipping non-WebP file: {file.name}")
                    continue
                
                # Generate a unique filename for the output PNG
                original_name = os.path.splitext(file.name)[0]
                output_filename = f"{original_name}.png"
                output_path = os.path.join(output_dir, output_filename)
                
                logger.info(f"Converting {file.name} to {output_filename}")
                
                try:
                    # Save the uploaded file to a temporary location
                    temp_file_path = os.path.join(temp_dir, file.name)
                    with open(temp_file_path, 'wb+') as destination:
                        for chunk in file.chunks():
                            destination.write(chunk)
                    
                    # Use PIL to convert WebP to PNG
                    from PIL import Image
                    img = Image.open(temp_file_path)
                    img.save(output_path, 'PNG')
                    img.close()  # Explicitly close the image
                    
                    converted_files.append({
                        'original_name': file.name,
                        'converted_name': output_filename,
                        'path': output_path
                    })
                    
                    logger.info(f"Successfully converted {file.name} to PNG")
                except Exception as e:
                    logger.error(f"Error converting file {file.name}: {str(e)}")
                    logger.error(traceback.format_exc())
                    return JsonResponse({'error': f"Error converting {file.name}: {str(e)}"}, status=500)
            
            # If only one file was converted, return it directly
            if len(converted_files) == 1:
                logger.info(f"Returning single converted file: {converted_files[0]['converted_name']}")
                try:
                    # Read the file content into memory first, then close it
                    with open(converted_files[0]['path'], 'rb') as f:
                        file_content = f.read()
                    
                    # Create the response with the file content from memory
                    response = HttpResponse(file_content, content_type='image/png')
                    response['Content-Disposition'] = f'attachment; filename="{converted_files[0]["converted_name"]}"'
                    
                    # We'll clean up the temp directory after the response is sent
                    # Using a delayed cleanup mechanism would be better, but for now, we'll skip cleanup
                    # to avoid the Windows file lock issue
                    return response
                except Exception as e:
                    logger.error(f"Error serving single converted file: {str(e)}")
                    logger.error(traceback.format_exc())
                    return JsonResponse({'error': f"Error serving converted file: {str(e)}"}, status=500)
            
            # If multiple files were converted, create a ZIP archive
            elif len(converted_files) > 1:
                logger.info(f"Creating ZIP archive for {len(converted_files)} converted files")
                try:
                    # Create a ZIP file
                    zip_filename = f"webp_to_png_{int(time.time())}.zip"
                    zip_path = os.path.join(temp_dir, zip_filename)
                    
                    with zipfile.ZipFile(zip_path, 'w') as zip_file:
                        for file_info in converted_files:
                            zip_file.write(file_info['path'], file_info['converted_name'])
                    
                    # Read the zip file into memory
                    with open(zip_path, 'rb') as f:
                        zip_content = f.read()
                    
                    # Create the response with the zip content from memory
                    response = HttpResponse(zip_content, content_type='application/zip')
                    response['Content-Disposition'] = f'attachment; filename="{zip_filename}"'
                    
                    # Skip cleanup for the same reason as above
                    return response
                except Exception as e:
                    logger.error(f"Error creating or serving ZIP file: {str(e)}")
                    logger.error(traceback.format_exc())
                    return JsonResponse({'error': f"Error creating ZIP file: {str(e)}"}, status=500)
            
            # If no files were converted
            else:
                logger.warning("No valid WebP files were uploaded or converted")
                return JsonResponse({'error': 'No valid WebP files were uploaded'}, status=400)
                
        except Exception as e:
            logger.error(f"General error during conversion: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({'error': f"Conversion error: {str(e)}"}, status=500)
    
    logger.warning("Invalid request method or no files uploaded")
    return JsonResponse({'error': 'Invalid request. Please upload WebP files.'}, status=400)

# Version for the regular view

def webp_to_png(request):
    """View for WebP to PNG conversion tool page"""
    return render(request, 'core/webp_to_png.html')

def png_to_webp(request):
    """View for PNG to WebP conversion tool page"""
    return render(request, 'core/png_to_webp.html')

@csrf_exempt
def png_to_webp_convert(request):
    """API endpoint for PNG to WebP conversion with improved error handling for Windows"""
    if request.method == 'POST' and request.FILES.getlist('files'):
        files = request.FILES.getlist('files')
        temp_dir = None
        
        try:
            # Create a temporary directory for processing files
            temp_dir = tempfile.mkdtemp()
            output_dir = os.path.join(temp_dir, 'output')
            os.makedirs(output_dir, exist_ok=True)
            
            # Process each file
            converted_files = []
            
            logger.info(f"Received {len(files)} files for conversion")
            
            # Debug: Print file details
            for i, file in enumerate(files):
                logger.info(f"File {i+1}: {file.name}, Size: {file.size}, Content Type: {file.content_type}")
            
            for file in files:
                # Check if the file is a PNG image
                if not file.name.lower().endswith('.png') or not file.content_type.startswith('image/png'):
                    logger.warning(f"Skipping non-PNG file: {file.name} (Content Type: {file.content_type})")
                    continue
                
                # Generate a unique filename for the output WebP
                original_name = os.path.splitext(file.name)[0]
                output_filename = f"{original_name}.webp"
                output_path = os.path.join(output_dir, output_filename)
                
                logger.info(f"Converting {file.name} to {output_filename}")
                
                try:
                    # Save the uploaded file to a temporary location
                    temp_file_path = os.path.join(temp_dir, file.name)
                    with open(temp_file_path, 'wb+') as destination:
                        for chunk in file.chunks():
                            destination.write(chunk)
                    
                    # Use PIL to convert PNG to WebP
                    from PIL import Image
                    img = Image.open(temp_file_path)
                    
                    # Convert to WebP with quality setting (0-100)
                    # 80 is a good default for balance of quality and size
                    img.save(output_path, 'WEBP', quality=85) 
                    img.close()  # Explicitly close the image
                    
                    converted_files.append({
                        'original_name': file.name,
                        'converted_name': output_filename,
                        'path': output_path
                    })
                    
                    logger.info(f"Successfully converted {file.name} to WebP")
                except Exception as e:
                    logger.error(f"Error converting file {file.name}: {str(e)}")
                    logger.error(traceback.format_exc())
                    return JsonResponse({'error': f"Error converting {file.name}: {str(e)}"}, status=500)
            
            # If only one file was converted, return it directly
            if len(converted_files) == 1:
                logger.info(f"Returning single converted file: {converted_files[0]['converted_name']}")
                try:
                    # Read the file content into memory first, then close it
                    with open(converted_files[0]['path'], 'rb') as f:
                        file_content = f.read()
                    
                    # Create the response with the file content from memory
                    response = HttpResponse(file_content, content_type='image/webp')
                    response['Content-Disposition'] = f'attachment; filename="{converted_files[0]["converted_name"]}"'
                    
                    # We'll skip cleanup to avoid the Windows file lock issue
                    return response
                except Exception as e:
                    logger.error(f"Error serving single converted file: {str(e)}")
                    logger.error(traceback.format_exc())
                    return JsonResponse({'error': f"Error serving converted file: {str(e)}"}, status=500)
            
            # If multiple files were converted, create a ZIP archive
            elif len(converted_files) > 1:
                logger.info(f"Creating ZIP archive for {len(converted_files)} converted files")
                try:
                    # Create a ZIP file
                    zip_filename = f"png_to_webp_{int(time.time())}.zip"
                    zip_path = os.path.join(temp_dir, zip_filename)
                    
                    with zipfile.ZipFile(zip_path, 'w') as zip_file:
                        for file_info in converted_files:
                            zip_file.write(file_info['path'], file_info['converted_name'])
                    
                    # Read the zip file into memory
                    with open(zip_path, 'rb') as f:
                        zip_content = f.read()
                    
                    # Create the response with the zip content from memory
                    response = HttpResponse(zip_content, content_type='application/zip')
                    response['Content-Disposition'] = f'attachment; filename="{zip_filename}"'
                    
                    # Skip cleanup
                    return response
                except Exception as e:
                    logger.error(f"Error creating or serving ZIP file: {str(e)}")
                    logger.error(traceback.format_exc())
                    return JsonResponse({'error': f"Error creating ZIP file: {str(e)}"}, status=500)
            
            # If no files were converted
            else:
                logger.warning("No valid PNG files were uploaded or converted")
                return JsonResponse({'error': 'No valid PNG files were uploaded'}, status=400)
                
        except Exception as e:
            logger.error(f"General error during conversion: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({'error': f"Conversion error: {str(e)}"}, status=500)
    
    logger.warning("Invalid request method or no files uploaded")
    return JsonResponse({'error': 'Invalid request. Please upload PNG files.'}, status=400)


def pdf_to_png(request):
    """View for PDF to PNG conversion tool page"""
    return render(request, 'core/pdf_to_png.html')

def is_valid_pdf(file):
    """
    Validate if a file is truly a PDF by checking its magic bytes.
    PDF files always start with "%PDF-"
    """
    try:
        # Save the first few bytes of the file to check the signature
        file_start = file.read(5)
        file.seek(0)  # Reset file pointer to the beginning
        
        # Check against PDF signature bytes
        pdf_signature = b'%PDF-'
        return file_start == pdf_signature
    except Exception as e:
        logger.error(f"Error validating PDF file: {str(e)}")
        return False

@csrf_exempt
def pdf_to_png_convert(request):
    """API endpoint for PDF to PNG conversion"""
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES.get('file')
        temp_dir = None
        
        # Validate file type
        if not file.name.lower().endswith('.pdf') or not file.content_type == 'application/pdf':
            return JsonResponse({'error': 'Only PDF files are allowed.'}, status=400)
        
        # Validate PDF content
        if not is_valid_pdf(file):
            return JsonResponse({'error': 'The uploaded file is not a valid PDF.'}, status=400)
        
        # Reset file pointer after validation
        file.seek(0)
        
        dpi = request.POST.get('dpi', '300')  # Default to 300 DPI if not specified
        try:
            dpi = int(dpi)
            if dpi < 72 or dpi > 600:
                dpi = 300  # Reset to default if outside reasonable range
        except ValueError:
            dpi = 300  # Reset to default if not a valid integer
        
        try:
            # Create a temporary directory for processing
            temp_dir = tempfile.mkdtemp()
            output_dir = os.path.join(temp_dir, 'output')
            os.makedirs(output_dir, exist_ok=True)
            
            # Save the uploaded PDF file
            pdf_path = os.path.join(temp_dir, file.name)
            with open(pdf_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            
            # Open the PDF file with PyMuPDF
            pdf_document = fitz.open(pdf_path)
            total_pages = pdf_document.page_count
            
            # Sanitize filename to avoid path issues
            base_filename = os.path.splitext(os.path.basename(file.name))[0]
            base_filename = re.sub(r'[^\w\-_.]', '_', base_filename)
            
            # Convert each page to PNG
            png_files = []
            for page_num in range(total_pages):
                page = pdf_document.load_page(page_num)
                
                # Calculate zoom factor based on DPI (PyMuPDF uses 72 DPI as base)
                zoom_factor = dpi / 72
                
                # Create PNG image with specified DPI
                pix = page.get_pixmap(matrix=fitz.Matrix(zoom_factor, zoom_factor))
                
                # Save PNG
                output_filename = f"{base_filename}_page_{page_num + 1}.png"
                output_path = os.path.join(output_dir, output_filename)
                pix.save(output_path)
                
                png_files.append({
                    'page': page_num + 1,
                    'path': output_path,
                    'filename': output_filename,
                    'size': os.path.getsize(output_path)
                })
            
            # Close the PDF document
            pdf_document.close()
            
            # Create a ZIP file if there are multiple pages
            if len(png_files) > 1:
                zip_filename = f"{base_filename}_png_{int(time.time())}.zip"
                zip_path = os.path.join(temp_dir, zip_filename)
                
                with zipfile.ZipFile(zip_path, 'w') as zip_file:
                    for png_file in png_files:
                        zip_file.write(png_file['path'], png_file['filename'])
                
                # Read ZIP file into memory
                with open(zip_path, 'rb') as f:
                    zip_content = f.read()
                
                # Send ZIP file
                response = HttpResponse(zip_content, content_type='application/zip')
                response['Content-Disposition'] = f'attachment; filename="{zip_filename}"'
                
                return response
            
            # If only one page, return the PNG directly
            elif len(png_files) == 1:
                with open(png_files[0]['path'], 'rb') as f:
                    image_content = f.read()
                
                response = HttpResponse(image_content, content_type='image/png')
                response['Content-Disposition'] = f'attachment; filename="{png_files[0]["filename"]}"'
                
                return response
            
            # No pages were processed
            else:
                return JsonResponse({'error': 'The PDF file contains no pages to convert.'}, status=400)
            
        except Exception as e:
            logger.error(f"Error converting PDF to PNG: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({'error': f"Error converting PDF to PNG: {str(e)}"}, status=500)
            
        finally:
            # Clean up temporary directory
            if temp_dir and os.path.exists(temp_dir):
                try:
                    # On Windows, there might be file lock issues, so we'll just try our best
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except:
                    pass
    
    # Return error for invalid requests
    return JsonResponse({'error': 'Invalid request. Please upload a PDF file.'}, status=400)

def png_to_pdf(request):
    """View for PNG to PDF conversion tool page"""
    return render(request, 'core/png_to_pdf.html')

def is_valid_png(file):
    """
    Validate if a file is truly a PNG image by checking its magic bytes.
    PNG files always start with the signature bytes: 89 50 4E 47 0D 0A 1A 0A
    """
    try:
        # Save the first few bytes of the file to check the signature
        file_start = file.read(8)
        file.seek(0)  # Reset file pointer to the beginning
        
        # Check against PNG signature bytes: 89 50 4E 47 0D 0A 1A 0A
        png_signature = b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'
        return file_start == png_signature
    except Exception as e:
        logger.error(f"Error validating PNG file: {str(e)}")
        return False

@csrf_exempt
def png_to_pdf_convert(request):
    """API endpoint for PNG to PDF conversion"""
    if request.method == 'POST' and request.FILES.getlist('files'):
        files = request.FILES.getlist('files')
        temp_dir = None
        
        try:
            # Create a temporary directory for processing files
            temp_dir = tempfile.mkdtemp()
            
            # Validate and save PNG files
            png_files = []
            
            logger.info(f"Received {len(files)} files for conversion")
            
            for i, file in enumerate(files):
                logger.info(f"File {i+1}: {file.name}, Size: {file.size}, Content Type: {file.content_type}")
                
                # Check if the file is a PNG image by extension and content type
                if not file.name.lower().endswith('.png') or not file.content_type.startswith('image/png'):
                    logger.warning(f"Skipping non-PNG file: {file.name} (Content Type: {file.content_type})")
                    continue
                
                # Validate that this is actually a PNG file by checking its magic bytes
                if not is_valid_png(file):
                    logger.warning(f"File {file.name} has a PNG extension but isn't a valid PNG file")
                    continue
                
                # Reset file pointer after validation
                file.seek(0)
                
                # Generate a unique filename for the temporary PNG file
                temp_png_path = os.path.join(temp_dir, file.name)
                
                # Save the PNG file
                with open(temp_png_path, 'wb+') as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)
                
                # Add to list of valid PNG files
                png_files.append({
                    'name': file.name,
                    'path': temp_png_path
                })
                
                logger.info(f"Saved PNG file: {file.name}")
            
            if not png_files:
                logger.warning("No valid PNG files were uploaded for conversion")
                return JsonResponse({'error': 'No valid PNG files were uploaded'}, status=400)
            
            # Get PDF settings from request
            page_size = request.POST.get('pageSize', 'A4')
            page_orientation = request.POST.get('pageOrientation', 'portrait')
            margin = request.POST.get('margin', '10')
            try:
                margin = int(margin)
                if margin < 0 or margin > 100:
                    margin = 10
            except ValueError:
                margin = 10
            
            # Set page size
            if page_size == 'letter':
                pdf_page_size = letter
            else:
                pdf_page_size = A4
            
            # Handle orientation
            if page_orientation == 'landscape':
                pdf_page_size = pdf_page_size[1], pdf_page_size[0]  # Swap width and height
            
            # Create a PDF file
            sanitized_name = re.sub(r'[^\w\-_.]', '_', os.path.splitext(png_files[0]['name'])[0])
            if len(png_files) > 1:
                pdf_filename = f"{sanitized_name}_and_more.pdf"
            else:
                pdf_filename = f"{sanitized_name}.pdf"
            
            pdf_path = os.path.join(temp_dir, pdf_filename)
            
            # Create PDF from PNG images
            c = canvas.Canvas(pdf_path, pagesize=pdf_page_size)
            width, height = pdf_page_size
            
            for png_file in png_files:
                # Open PNG with Pillow
                img = Image.open(png_file['path'])
                img_width, img_height = img.size
                
                # Calculate scaling to fit within page margins
                available_width = width - (2 * margin)
                available_height = height - (2 * margin)
                
                # Calculate scale factor to fit image proportionally
                width_ratio = available_width / img_width
                height_ratio = available_height / img_height
                scale = min(width_ratio, height_ratio)
                
                # Calculate dimensions of scaled image
                scaled_width = img_width * scale
                scaled_height = img_height * scale
                
                # Calculate position to center image on page
                x_position = (width - scaled_width) / 2
                y_position = (height - scaled_height) / 2
                
                # Add image to PDF
                c.drawImage(png_file['path'], x_position, height - y_position - scaled_height, 
                           width=scaled_width, height=scaled_height, preserveAspectRatio=True)
                
                # Add a new page for the next image (if any)
                c.showPage()
            
            # Save the PDF
            c.save()
            
            # Read the PDF file into memory
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()
            
            # Create response with PDF content
            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
            
            # Clean up temporary directory (excluding error handling for brevity)
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
            
            return response
            
        except Exception as e:
            logger.error(f"Error converting PNG to PDF: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Clean up temporary directory if it exists
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass
                    
            return JsonResponse({'error': f"Error converting PNG to PDF: {str(e)}"}, status=500)
    
    return JsonResponse({'error': 'Invalid request. Please upload PNG files.'}, status=400)

def jpg_to_png(request):
    """View for JPG to PNG conversion tool page"""
    return render(request, 'core/jpg_to_png.html')

def is_valid_jpg(file):
    """
    Validate if a file is truly a JPG/JPEG image by checking its magic bytes.
    JPEG files start with FF D8 FF
    """
    try:
        # Save the first few bytes of the file to check the signature
        file_start = file.read(3)
        file.seek(0)  # Reset file pointer to the beginning
        
        # Check against JPEG signature bytes: FF D8 FF
        jpg_signature = b'\xFF\xD8\xFF'
        return file_start == jpg_signature
    except Exception as e:
        logger.error(f"Error validating JPG file: {str(e)}")
        return False

@csrf_exempt
def jpg_to_png_convert(request):
    """API endpoint for JPG to PNG conversion with improved error handling"""
    if request.method == 'POST' and request.FILES.getlist('files'):
        files = request.FILES.getlist('files')
        temp_dir = None
        
        try:
            # Create a temporary directory for processing files
            temp_dir = tempfile.mkdtemp()
            output_dir = os.path.join(temp_dir, 'output')
            os.makedirs(output_dir, exist_ok=True)
            
            # Process each file
            converted_files = []
            
            logger.info(f"Received {len(files)} files for conversion")
            
            # Debug: Print file details
            for i, file in enumerate(files):
                logger.info(f"File {i+1}: {file.name}, Size: {file.size}, Content Type: {file.content_type}")
            
            for file in files:
                # Check if the file is a JPG image by extension and content type
                if not (file.name.lower().endswith('.jpg') or file.name.lower().endswith('.jpeg')) or not file.content_type.startswith('image/jpeg'):
                    logger.warning(f"Skipping non-JPG file: {file.name} (Content Type: {file.content_type})")
                    continue
                
                # Validate that this is actually a JPG file by checking its magic bytes
                if not is_valid_jpg(file):
                    logger.warning(f"File {file.name} has a JPG extension but isn't a valid JPG file")
                    continue
                
                # Reset file pointer after validation
                file.seek(0)
                
                # Generate a unique filename for the output PNG
                original_name = os.path.splitext(file.name)[0]
                output_filename = f"{original_name}.png"
                output_path = os.path.join(output_dir, output_filename)
                
                logger.info(f"Converting {file.name} to {output_filename}")
                
                try:
                    # Save the uploaded file to a temporary location
                    temp_file_path = os.path.join(temp_dir, file.name)
                    with open(temp_file_path, 'wb+') as destination:
                        for chunk in file.chunks():
                            destination.write(chunk)
                    
                    # Use PIL to convert JPG to PNG
                    img = Image.open(temp_file_path)
                    
                    # Convert to PNG with full quality
                    img.save(output_path, 'PNG')
                    img.close()  # Explicitly close the image
                    
                    converted_files.append({
                        'original_name': file.name,
                        'converted_name': output_filename,
                        'path': output_path,
                        'original_size': os.path.getsize(temp_file_path),
                        'converted_size': os.path.getsize(output_path)
                    })
                    
                    logger.info(f"Successfully converted {file.name} to PNG")
                except Exception as e:
                    logger.error(f"Error converting file {file.name}: {str(e)}")
                    logger.error(traceback.format_exc())
                    return JsonResponse({'error': f"Error converting {file.name}: {str(e)}"}, status=500)
            
            # If only one file was converted, return it directly
            if len(converted_files) == 1:
                logger.info(f"Returning single converted file: {converted_files[0]['converted_name']}")
                try:
                    # Read the file content into memory first, then close it
                    with open(converted_files[0]['path'], 'rb') as f:
                        file_content = f.read()
                    
                    # Create the response with the file content from memory
                    response = HttpResponse(file_content, content_type='image/png')
                    response['Content-Disposition'] = f'attachment; filename="{converted_files[0]["converted_name"]}"'
                    
                    # We'll skip cleanup to avoid the Windows file lock issue
                    return response
                except Exception as e:
                    logger.error(f"Error serving single converted file: {str(e)}")
                    logger.error(traceback.format_exc())
                    return JsonResponse({'error': f"Error serving converted file: {str(e)}"}, status=500)
            
            # If multiple files were converted, create a ZIP archive
            elif len(converted_files) > 1:
                logger.info(f"Creating ZIP archive for {len(converted_files)} converted files")
                try:
                    # Create a ZIP file
                    zip_filename = f"jpg_to_png_{int(time.time())}.zip"
                    zip_path = os.path.join(temp_dir, zip_filename)
                    
                    with zipfile.ZipFile(zip_path, 'w') as zip_file:
                        for file_info in converted_files:
                            zip_file.write(file_info['path'], file_info['converted_name'])
                    
                    # Read the zip file into memory
                    with open(zip_path, 'rb') as f:
                        zip_content = f.read()
                    
                    # Create the response with the zip content from memory
                    response = HttpResponse(zip_content, content_type='application/zip')
                    response['Content-Disposition'] = f'attachment; filename="{zip_filename}"'
                    
                    # Skip cleanup
                    return response
                except Exception as e:
                    logger.error(f"Error creating or serving ZIP file: {str(e)}")
                    logger.error(traceback.format_exc())
                    return JsonResponse({'error': f"Error creating ZIP file: {str(e)}"}, status=500)
            
            # If no files were converted
            else:
                logger.warning("No valid JPG files were uploaded or converted")
                return JsonResponse({'error': 'No valid JPG files were uploaded'}, status=400)
                
        except Exception as e:
            logger.error(f"General error during conversion: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({'error': f"Conversion error: {str(e)}"}, status=500)
    
    logger.warning("Invalid request method or no files uploaded")
    return JsonResponse({'error': 'Invalid request. Please upload JPG files.'}, status=400)

def png_to_jpg(request):
    """View for PNG to JPG conversion tool page"""
    return render(request, 'core/png_to_jpg.html')

def is_valid_png(file):
    """
    Validate if a file is truly a PNG image by checking its magic bytes.
    PNG files always start with the signature bytes: 89 50 4E 47 0D 0A 1A 0A
    """
    try:
        # Save the first few bytes of the file to check the signature
        file_start = file.read(8)
        file.seek(0)  # Reset file pointer to the beginning
        
        # Check against PNG signature bytes: 89 50 4E 47 0D 0A 1A 0A
        png_signature = b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'
        return file_start == png_signature
    except Exception as e:
        logger.error(f"Error validating PNG file: {str(e)}")
        return False

@csrf_exempt
def png_to_jpg_convert(request):
    """API endpoint for PNG to JPG conversion with improved error handling"""
    if request.method == 'POST' and request.FILES.getlist('files'):
        files = request.FILES.getlist('files')
        temp_dir = None
        
        try:
            # Get quality parameter (default to 90% if not specified)
            quality = int(request.POST.get('quality', 90))
            # Validate quality range
            if quality < 1 or quality > 100:
                quality = 90
                
            # Create a temporary directory for processing files
            temp_dir = tempfile.mkdtemp()
            output_dir = os.path.join(temp_dir, 'output')
            os.makedirs(output_dir, exist_ok=True)
            
            # Process each file
            converted_files = []
            
            logger.info(f"Received {len(files)} files for conversion")
            
            # Debug: Print file details
            for i, file in enumerate(files):
                logger.info(f"File {i+1}: {file.name}, Size: {file.size}, Content Type: {file.content_type}")
            
            for file in files:
                # Check if the file is a PNG image by extension and content type
                if not file.name.lower().endswith('.png') or not file.content_type.startswith('image/png'):
                    logger.warning(f"Skipping non-PNG file: {file.name} (Content Type: {file.content_type})")
                    continue
                
                # Validate that this is actually a PNG file by checking its magic bytes
                if not is_valid_png(file):
                    logger.warning(f"File {file.name} has a PNG extension but isn't a valid PNG file")
                    continue
                
                # Reset file pointer after validation
                file.seek(0)
                
                # Generate a unique filename for the output JPG
                original_name = os.path.splitext(file.name)[0]
                output_filename = f"{original_name}.jpg"
                output_path = os.path.join(output_dir, output_filename)
                
                logger.info(f"Converting {file.name} to {output_filename} with quality {quality}")
                
                try:
                    # Save the uploaded file to a temporary location
                    temp_file_path = os.path.join(temp_dir, file.name)
                    with open(temp_file_path, 'wb+') as destination:
                        for chunk in file.chunks():
                            destination.write(chunk)
                    
                    # Use PIL to convert PNG to JPG
                    img = Image.open(temp_file_path)
                    
                    # Convert to RGB mode if the image has an alpha channel
                    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                        # Create a white background
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        # Paste the image on the background, using the alpha channel as mask
                        if img.mode == 'RGBA':
                            background.paste(img, mask=img.split()[3])  # 3 is the alpha channel
                        elif img.mode == 'LA':
                            background.paste(img, mask=img.split()[1])  # 1 is the alpha channel
                        elif img.mode == 'P':
                            background.paste(img, mask=img.convert('RGBA').split()[3])
                        img = background
                    
                    # Convert to JPG with specified quality
                    img.save(output_path, 'JPEG', quality=quality, optimize=True)
                    img.close()  # Explicitly close the image
                    
                    converted_files.append({
                        'original_name': file.name,
                        'converted_name': output_filename,
                        'path': output_path,
                        'original_size': os.path.getsize(temp_file_path),
                        'converted_size': os.path.getsize(output_path)
                    })
                    
                    logger.info(f"Successfully converted {file.name} to JPG")
                except Exception as e:
                    logger.error(f"Error converting file {file.name}: {str(e)}")
                    logger.error(traceback.format_exc())
                    return JsonResponse({'error': f"Error converting {file.name}: {str(e)}"}, status=500)
            
            # If only one file was converted, return it directly
            if len(converted_files) == 1:
                logger.info(f"Returning single converted file: {converted_files[0]['converted_name']}")
                try:
                    # Read the file content into memory first, then close it
                    with open(converted_files[0]['path'], 'rb') as f:
                        file_content = f.read()
                    
                    # Create a response object with additional metadata for the client
                    response_data = {
                        'original_size': converted_files[0]['original_size'],
                        'converted_size': converted_files[0]['converted_size']
                    }
                    
                    # Create the response with the file content from memory
                    response = HttpResponse(file_content, content_type='image/jpeg')
                    response['Content-Disposition'] = f'attachment; filename="{converted_files[0]["converted_name"]}"'
                    response['X-Original-Size'] = str(converted_files[0]['original_size'])
                    response['X-Converted-Size'] = str(converted_files[0]['converted_size'])
                    
                    # We'll skip cleanup to avoid the Windows file lock issue
                    return response
                except Exception as e:
                    logger.error(f"Error serving single converted file: {str(e)}")
                    logger.error(traceback.format_exc())
                    return JsonResponse({'error': f"Error serving converted file: {str(e)}"}, status=500)
            
            # If multiple files were converted, create a ZIP archive
            elif len(converted_files) > 1:
                logger.info(f"Creating ZIP archive for {len(converted_files)} converted files")
                try:
                    # Create a ZIP file
                    zip_filename = f"png_to_jpg_{int(time.time())}.zip"
                    zip_path = os.path.join(temp_dir, zip_filename)
                    
                    with zipfile.ZipFile(zip_path, 'w') as zip_file:
                        for file_info in converted_files:
                            zip_file.write(file_info['path'], file_info['converted_name'])
                    
                    # Read the zip file into memory
                    with open(zip_path, 'rb') as f:
                        zip_content = f.read()
                    
                    # Create the response with the zip content from memory
                    response = HttpResponse(zip_content, content_type='application/zip')
                    response['Content-Disposition'] = f'attachment; filename="{zip_filename}"'
                    
                    # Skip cleanup
                    return response
                except Exception as e:
                    logger.error(f"Error creating or serving ZIP file: {str(e)}")
                    logger.error(traceback.format_exc())
                    return JsonResponse({'error': f"Error creating ZIP file: {str(e)}"}, status=500)
            
            # If no files were converted
            else:
                logger.warning("No valid PNG files were uploaded or converted")
                return JsonResponse({'error': 'No valid PNG files were uploaded'}, status=400)
                
        except Exception as e:
            logger.error(f"General error during conversion: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({'error': f"Conversion error: {str(e)}"}, status=500)
    
    logger.warning("Invalid request method or no files uploaded")
    return JsonResponse({'error': 'Invalid request. Please upload PNG files.'}, status=400)


def word_to_pdf(request):
    """View for Word to PDF conversion tool page"""
    return render(request, 'core/word_to_pdf.html')

def is_valid_word_file(file):
    """
    Validate if a file is truly a Word document by checking its magic bytes.
    Word files (.docx) start with "PK" signature as they are actually ZIP files
    Old Word files (.doc) start with D0 CF 11 E0 A1 B1 1A E1
    """
    try:
        # Save the first few bytes of the file to check the signature
        file_start = file.read(8)
        file.seek(0)  # Reset file pointer to the beginning
        
        # Check signatures
        docx_signature = b'PK\x03\x04'  # DOCX files (ZIP format)
        doc_signature = b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1'  # DOC files (Compound File Binary Format)
        
        return file_start.startswith(docx_signature) or file_start == doc_signature
    except Exception as e:
        logger.error(f"Error validating Word file: {str(e)}")
        return False

@csrf_exempt
def word_to_pdf_convert(request):
    """API endpoint for Word to PDF conversion with improved error handling"""
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES.get('file')
        temp_dir = None
        
        # Validate file type
        valid_extensions = ['.doc', '.docx', '.docm']
        file_ext = os.path.splitext(file.name)[1].lower()
        
        if file_ext not in valid_extensions:
            return JsonResponse({'error': 'Only Word files (.doc, .docx, .docm) are allowed.'}, status=400)
        
        if not file.content_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
                                     'application/vnd.ms-word.document.macroEnabled.12']:
            return JsonResponse({'error': 'File content type is not a valid Word document.'}, status=400)
        
        # Validate Word file content
        if not is_valid_word_file(file):
            return JsonResponse({'error': 'The uploaded file is not a valid Word document.'}, status=400)
        
        # Reset file pointer after validation
        file.seek(0)
        
        try:
            # Create a temporary directory for processing
            temp_dir = tempfile.mkdtemp()
            
            # Save the uploaded file
            word_path = os.path.join(temp_dir, file.name)
            with open(word_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            
            # Define output PDF path
            pdf_filename = os.path.splitext(file.name)[0] + '.pdf'
            pdf_path = os.path.join(temp_dir, pdf_filename)
            
            # Convert Word to PDF using appropriate library
            # For this implementation, we'll use python-docx2pdf or LibreOffice depending on what's available
            # This is a placeholder for the actual conversion code
            
            conversion_successful = False
            
            # Method 1: Try using docx2pdf (requires Microsoft Word on Windows or LibreOffice on Linux/Mac)
            try:
                from docx2pdf import convert
                convert(word_path, pdf_path)
                conversion_successful = os.path.exists(pdf_path)
            except Exception as e:
                logger.error(f"docx2pdf conversion failed: {str(e)}")
                conversion_successful = False
            
            # Method 2: If Method 1 fails, try using LibreOffice directly
            if not conversion_successful:
                try:
                    # Check if LibreOffice is available
                    libreoffice_path = "/usr/bin/libreoffice"  # Adjust for your system
                    if os.path.exists(libreoffice_path):
                        cmd = [
                            libreoffice_path,
                            '--headless',
                            '--convert-to', 'pdf',
                            '--outdir', temp_dir,
                            word_path
                        ]
                        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        output, error = process.communicate()
                        
                        if process.returncode != 0:
                            logger.error(f"LibreOffice conversion error: {error.decode('utf-8')}")
                        else:
                            conversion_successful = os.path.exists(pdf_path)
                except Exception as e:
                    logger.error(f"LibreOffice conversion failed: {str(e)}")
                    conversion_successful = False
            
            # Method 3: As a last resort, try using comtypes on Windows
            if not conversion_successful and os.name == 'nt':
                try:
                    import comtypes.client
                    
                    word = comtypes.client.CreateObject('Word.Application')
                    word.Visible = False
                    
                    doc = word.Documents.Open(word_path)
                    doc.SaveAs(pdf_path, FileFormat=17)  # 17 represents PDF format
                    doc.Close()
                    word.Quit()
                    
                    conversion_successful = os.path.exists(pdf_path)
                except Exception as e:
                    logger.error(f"COM conversion failed: {str(e)}")
                    conversion_successful = False
            
            if not conversion_successful:
                return JsonResponse({'error': 'Failed to convert Word to PDF. Please try again later.'}, status=500)
            
            # Return the PDF file
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()
            
            # Get file stats
            original_size = os.path.getsize(word_path)
            converted_size = os.path.getsize(pdf_path)
            
            # Clean up
            try:
                if temp_dir and os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            except Exception as e:
                logger.error(f"Error cleaning up: {str(e)}")
            
            # Create response
            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
            response['X-Original-Size'] = str(original_size)
            response['X-Converted-Size'] = str(converted_size)
            
            return response
            
        except Exception as e:
            logger.error(f"Error converting Word to PDF: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Clean up
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass
                    
            return JsonResponse({'error': f"Error converting Word to PDF: {str(e)}"}, status=500)
    
    return JsonResponse({'error': 'Invalid request. Please upload a Word file.'}, status=400)

def pdf_to_word(request):
    """View for PDF to Word conversion tool page"""
    return render(request, 'core/pdf_to_word.html')
@csrf_exempt
def convert_pdf_to_word(request):
    """API endpoint for PDF to Word conversion"""
    if request.method == 'POST':
        if 'file' not in request.FILES:
            return JsonResponse({'error': 'No file provided'}, status=400)
        
        uploaded_file = request.FILES['file']
        
        # Validate file type
        if not uploaded_file.name.lower().endswith('.pdf'):
            return JsonResponse({'error': 'Only PDF files are supported'}, status=400)
        
        # Get conversion options
        output_format = request.POST.get('format', 'docx')
        quality = request.POST.get('quality', 'balanced')
        use_ocr = request.POST.get('ocr', 'false').lower() == 'true'
        
        # Create temporary files
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, uploaded_file.name)
        base_name = os.path.splitext(uploaded_file.name)[0]
        output_path = os.path.join(temp_dir, f"{base_name}.{output_format}")
        
        # Save the uploaded file
        with open(input_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        
        try:
            # If OCR is enabled, process the PDF with OCR first
            if use_ocr:
                ocr_output_path = os.path.join(temp_dir, f"ocr_{uploaded_file.name}")
                try:
                    ocrmypdf.ocr(
                        input_path,
                        ocr_output_path,
                        force_ocr=True,
                        skip_text=False,
                        output_type='pdf',
                        optimize=0 if quality == 'highest' else 1,
                        language='eng',  # Can be expanded to support multiple languages
                        progress_bar=False
                    )
                    # If OCR successful, update input path to use the OCR'd file
                    if os.path.exists(ocr_output_path):
                        input_path = ocr_output_path
                except Exception as e:
                    logger.error(f"OCR processing failed: {str(e)}")
                    # Continue with conversion without OCR if it fails
            
            # Convert PDF to DOCX
            try:
                # Set conversion parameters based on quality setting
                if quality == 'highest':
                    cv = Converter(input_path)
                    cv.convert(output_path, start=0, end=None)
                    cv.close()
                else:
                    # Use different conversion settings for balanced and efficient
                    cv = Converter(input_path)
                    convert_options = {
                        'stream_table': quality != 'efficient',  # More accurate table detection
                        'adjust_bbox': quality == 'highest',     # Better layout preservation
                    }
                    cv.convert(output_path, start=0, end=None, **convert_options)
                    cv.close()
                
                logger.info(f"Successfully converted using pdf2docx")
            except Exception as e:
                logger.error(f"pdf2docx conversion failed: {str(e)}")
                
                # Try alternative conversion method using LibreOffice
                try:
                    logger.info("Attempting conversion with LibreOffice")
                    libreoffice_path = "soffice"  # or full path
                    cmd = [
                        libreoffice_path,
                        '--headless',
                        '--convert-to', output_format,
                        '--outdir', temp_dir,
                        input_path
                    ]
                    subprocess.run(cmd, check=True)
                    
                    # LibreOffice might change the output filename, find it
                    if not os.path.exists(output_path):
                        for file in os.listdir(temp_dir):
                            if file.startswith(base_name) and file.endswith(f".{output_format}"):
                                output_path = os.path.join(temp_dir, file)
                                break
                except Exception as e:
                    logger.error(f"LibreOffice conversion failed: {str(e)}")
                    return JsonResponse({'error': 'Conversion failed with all available methods'}, status=500)
            
            # Check if conversion was successful
            if not os.path.exists(output_path):
                return JsonResponse({'error': 'Conversion failed - output file not found'}, status=500)
            
            # Determine the correct content type
            content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            if output_format == 'doc':
                content_type = 'application/msword'
            
            # Return the Word file
            with open(output_path, 'rb') as docx_file:
                response = HttpResponse(docx_file.read(), content_type=content_type)
                response['Content-Disposition'] = f'attachment; filename="{os.path.basename(output_path)}"'
                response['X-Converted-Size'] = str(os.path.getsize(output_path))
                return response
                
        except Exception as e:
            logger.error(f"Unexpected error during conversion: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({'error': str(e)}, status=500)
        finally:
            # Clean up temporary files
            try:
                if os.path.exists(input_path):
                    os.remove(input_path)
                if os.path.exists(output_path):
                    os.remove(output_path)
                # Remove OCR'd file if it exists
                ocr_output_path = os.path.join(temp_dir, f"ocr_{uploaded_file.name}")
                if os.path.exists(ocr_output_path):
                    os.remove(ocr_output_path)
                os.rmdir(temp_dir)
            except Exception as e:
                logger.error(f"Error during cleanup: {str(e)}")
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

def jpg_to_pdf(request):
    """View for JPG to PDF conversion tool page"""
    return render(request, 'core/jpg_to_pdf.html')

def is_valid_jpg(file):
    """
    Validate if a file is truly a JPG/JPEG image by checking its magic bytes.
    JPEG files start with FF D8 FF
    """
    try:
        # Save the first few bytes of the file to check the signature
        file_start = file.read(3)
        file.seek(0)  # Reset file pointer to the beginning
        
        # Check against JPEG signature bytes: FF D8 FF
        jpg_signature = b'\xFF\xD8\xFF'
        return file_start == jpg_signature
    except Exception as e:
        logger.error(f"Error validating JPG file: {str(e)}")
        return False

@csrf_exempt
def jpg_to_pdf_convert(request):
    """API endpoint for JPG to PDF conversion"""
    if request.method == 'POST' and request.FILES.getlist('files'):
        files = request.FILES.getlist('files')
        temp_dir = None
        
        try:
            # Create a temporary directory for processing files
            temp_dir = tempfile.mkdtemp()
            
            # Validate and save JPG files
            jpg_files = []
            
            logger.info(f"Received {len(files)} files for conversion")
            
            for i, file in enumerate(files):
                logger.info(f"File {i+1}: {file.name}, Size: {file.size}, Content Type: {file.content_type}")
                
                # Check if the file is a JPG image by extension and content type
                if not (file.name.lower().endswith('.jpg') or file.name.lower().endswith('.jpeg')) or not file.content_type.startswith('image/jpeg'):
                    logger.warning(f"Skipping non-JPG file: {file.name} (Content Type: {file.content_type})")
                    continue
                
                # Validate that this is actually a JPG file by checking its magic bytes
                if not is_valid_jpg(file):
                    logger.warning(f"File {file.name} has a JPG extension but isn't a valid JPG file")
                    continue
                
                # Reset file pointer after validation
                file.seek(0)
                
                # Generate a unique filename for the temporary JPG file
                temp_jpg_path = os.path.join(temp_dir, file.name)
                
                # Save the JPG file
                with open(temp_jpg_path, 'wb+') as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)
                
                # Add to list of valid JPG files
                jpg_files.append({
                    'name': file.name,
                    'path': temp_jpg_path
                })
                
                logger.info(f"Saved JPG file: {file.name}")
            
            if not jpg_files:
                logger.warning("No valid JPG files were uploaded for conversion")
                return JsonResponse({'error': 'No valid JPG files were uploaded'}, status=400)
            
            # Get PDF settings from request
            page_size = request.POST.get('pageSize', 'A4')
            page_orientation = request.POST.get('pageOrientation', 'portrait')
            margin = request.POST.get('margin', '10')
            fit_to_page = request.POST.get('fitToPage', 'true') == 'true'
            one_image_per_page = request.POST.get('oneImagePerPage', 'true') == 'true'
            
            try:
                margin = int(margin)
                if margin < 0 or margin > 50:
                    margin = 10
            except ValueError:
                margin = 10
            
            # Set page size
            if page_size == 'letter':
                pdf_page_size = letter
            elif page_size == 'legal':
                pdf_page_size = (8.5*72, 14*72)  # Legal size in points
            elif page_size == 'A3':
                pdf_page_size = (841.89, 1190.55)  # A3 in points
            elif page_size == 'A5':
                pdf_page_size = (419.53, 595.28)  # A5 in points
            else:
                pdf_page_size = A4  # Default to A4
            
            # Handle orientation
            if page_orientation == 'landscape':
                pdf_page_size = pdf_page_size[1], pdf_page_size[0]  # Swap width and height
            
            # Convert margin from mm to points (1 point = 0.352778 mm)
            margin_points = margin * 2.83465  # Convert mm to points
            
            # Create a PDF file
            sanitized_name = re.sub(r'[^\w\-_.]', '_', os.path.splitext(jpg_files[0]['name'])[0])
            if len(jpg_files) > 1:
                pdf_filename = f"{sanitized_name}_and_more.pdf"
            else:
                pdf_filename = f"{sanitized_name}.pdf"
            
            pdf_path = os.path.join(temp_dir, pdf_filename)
            
            # Create PDF from JPG images
            c = canvas.Canvas(pdf_path, pagesize=pdf_page_size)
            width, height = pdf_page_size
            
            for jpg_file in jpg_files:
                # Open JPG with Pillow
                img = Image.open(jpg_file['path'])
                img_width, img_height = img.size
                
                if fit_to_page:
                    # Calculate scaling to fit within page margins
                    available_width = width - (2 * margin_points)
                    available_height = height - (2 * margin_points)
                    
                    # Calculate scale factor to fit image proportionally
                    width_ratio = available_width / img_width
                    height_ratio = available_height / img_height
                    scale = min(width_ratio, height_ratio)
                    
                    # Calculate dimensions of scaled image
                    scaled_width = img_width * scale
                    scaled_height = img_height * scale
                    
                    # Calculate position to center image on page
                    x_position = (width - scaled_width) / 2
                    y_position = (height - scaled_height) / 2
                    
                    # Add image to PDF
                    c.drawImage(jpg_file['path'], x_position, height - y_position - scaled_height, 
                               width=scaled_width, height=scaled_height, preserveAspectRatio=True)
                else:
                    # Use original size (up to page boundaries)
                    # This might crop the image if it's larger than the page
                    max_width = width - (2 * margin_points)
                    max_height = height - (2 * margin_points)
                    
                    use_width = min(img_width, max_width)
                    use_height = min(img_height, max_height)
                    
                    # Center the image on the page
                    x_position = (width - use_width) / 2
                    y_position = (height - use_height) / 2
                    
                    c.drawImage(jpg_file['path'], x_position, height - y_position - use_height, 
                               width=use_width, height=use_height)
                
                # Add a new page for the next image if multiple images
                if one_image_per_page and len(jpg_files) > 1:
                    c.showPage()
            
            # Save the PDF
            c.save()
            
            # Read the PDF file into memory
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()
            
            # Create response with PDF content
            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
            
            # Clean up temporary directory (excluding error handling for brevity)
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.error(f"Error cleaning up: {str(e)}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error converting JPG to PDF: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Clean up temporary directory if it exists
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception as clean_e:
                    logger.error(f"Error during cleanup: {str(clean_e)}")
                    
            return JsonResponse({'error': f"Error converting JPG to PDF: {str(e)}"}, status=500)
    
    return JsonResponse({'error': 'Invalid request. Please upload JPG files.'}, status=400)





from django.http import HttpResponse
from django.conf import settings
import os

def sitemap_view(request):
    """Serve the static sitemap.xml file directly."""
    # Path to your static sitemap.xml file
    sitemap_path = os.path.join(settings.BASE_DIR, 'pdf_tools', 'static', 'sitemap.xml')
    
    try:
        with open(sitemap_path, 'r') as f:
            sitemap_content = f.read()
        return HttpResponse(sitemap_content, content_type='application/xml')
    except FileNotFoundError:
        # Generate a basic sitemap if the file is not found
        base_url = request.build_absolute_uri('/').rstrip('/')
        
        sitemap_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{base_url}/</loc>
    <lastmod>2025-03-14</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>{base_url}/pdf-to-png/</loc>
    <lastmod>2025-03-14</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>{base_url}/pdf-to-jpg/</loc>
    <lastmod>2025-03-14</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>{base_url}/pdf-to-word/</loc>
    <lastmod>2025-03-14</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>{base_url}/jpg-to-pdf/</loc>
    <lastmod>2025-03-14</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>{base_url}/jpg-to-png/</loc>
    <lastmod>2025-03-14</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>{base_url}/png-to-jpg/</loc>
    <lastmod>2025-03-14</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>{base_url}/png-to-pdf/</loc>
    <lastmod>2025-03-14</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>{base_url}/png-to-webp/</loc>
    <lastmod>2025-03-14</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>{base_url}/webp-to-png/</loc>
    <lastmod>2025-03-14</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>{base_url}/word-to-pdf/</loc>
    <lastmod>2025-03-14</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>{base_url}/about-us/</loc>
    <lastmod>2025-03-14</lastmod>
    <changefreq>yearly</changefreq>
    <priority>0.5</priority>
  </url>
  <url>
    <loc>{base_url}/contact/</loc>
    <lastmod>2025-03-14</lastmod>
    <changefreq>yearly</changefreq>
    <priority>0.5</priority>
  </url>
  <url>
    <loc>{base_url}/privacy-policy/</loc>
    <lastmod>2025-03-14</lastmod>
    <changefreq>yearly</changefreq>
    <priority>0.4</priority>
  </url>
  <url>
    <loc>{base_url}/terms-of-service/</loc>
    <lastmod>2025-03-14</lastmod>
    <changefreq>yearly</changefreq>
    <priority>0.4</priority>
  </url>
</urlset>"""
        return HttpResponse(sitemap_content, content_type='application/xml')
    
def robots_txt_view(request):
    """Serve robots.txt content"""
    # Option 1: Try to read from static file first
    robots_path = os.path.join(settings.BASE_DIR, 'pdf_tools', 'static', 'robots.txt')
    
    try:
        with open(robots_path, 'r') as f:
            robots_content = f.read()
        return HttpResponse(robots_content, content_type='text/plain')
    except FileNotFoundError:
        # Option 2: Generate content dynamically
        base_url = request.build_absolute_uri('/').rstrip('/')
        
        robots_content = f"""User-agent: *
Allow: /
Disallow: /admin/
Disallow: /_pycache_/
Disallow: /media/_pycache_/

# Allow all files in static directory
Allow: /static/

# Sitemap location
Sitemap: {base_url}/sitemap.xml
"""
        return HttpResponse(robots_content, content_type='text/plain')

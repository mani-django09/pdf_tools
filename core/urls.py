from django.urls import path
from . import views
from django.contrib.sitemaps.views import sitemap
from .sitemaps import StaticViewSitemap, ToolSitemap, ImageToolSitemap, InfoPageSitemap

sitemaps = {
    'static': StaticViewSitemap,
    'tools': ToolSitemap,
    'image_tools': ImageToolSitemap,
    'info': InfoPageSitemap,
}

urlpatterns = [
    path('', views.index, name='index'),
    path('webp-to-png/', views.webp_to_png, name='webp_to_png'),
    path('api/webp-to-png/convert/', views.webp_to_png_convert, name='webp_to_png_convert'),
    path('png-to-webp/', views.png_to_webp, name='png_to_webp'),
    path('api/png-to-webp/convert/', views.png_to_webp_convert, name='png_to_webp_convert'),
    path('pdf-to-png/', views.pdf_to_png, name='pdf_to_png'),
    path('api/pdf-to-png/convert/', views.pdf_to_png_convert, name='pdf_to_png_convert'),
    path('png-to-pdf/', views.png_to_pdf, name='png_to_pdf'),
    path('api/png-to-pdf/convert/', views.png_to_pdf_convert, name='png_to_pdf_convert'),
    path('jpg-to-png/', views.jpg_to_png, name='jpg_to_png'),
    path('api/jpg-to-png/convert/', views.jpg_to_png_convert, name='jpg_to_png_convert'),
    path('png-to-jpg/', views.png_to_jpg, name='png_to_jpg'),
    path('api/png-to-jpg/convert/', views.png_to_jpg_convert, name='png_to_jpg_convert'),
    path('word-to-pdf/', views.word_to_pdf, name='word_to_pdf'),
    path('api/word-to-pdf/convert/', views.word_to_pdf_convert, name='word_to_pdf_convert'),
    path('pdf-to-word/', views.pdf_to_word, name='pdf_to_word'),
    path('api/pdf-to-word/convert/', views.convert_pdf_to_word, name='pdf_to_word_convert'),
    path('jpg-to-pdf/', views.jpg_to_pdf, name='jpg_to_pdf'),
    path('api/jpg-to-pdf/convert/', views.jpg_to_pdf_convert, name='jpg_to_pdf_convert'),
    path('pdf-to-jpg/', views.pdf_to_jpg, name='pdf_to_jpg'),
    path('api/pdf-to-jpg/convert/', views.pdf_to_jpg_convert, name='pdf_to_jpg_convert'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
    path('contact/', views.contact, name='contact'),
    path('about-us/', views.about_us, name='about_us'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, 
         name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', views.robots_txt_view, name='robots_txt'),

]

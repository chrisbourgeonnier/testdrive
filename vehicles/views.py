from django.views.generic import ListView, DetailView
from .models import Vehicle
from django.http import HttpResponse
from django.views import View
import requests
import base64
from urllib.parse import unquote

class VehicleListView(ListView):
    model = Vehicle
    queryset = Vehicle.objects.filter(is_active=True).order_by('make', 'model', 'year')
    template_name = 'vehicles/vehicle_list.html'
    context_object_name = 'vehicles'

class VehicleDetailView(DetailView):
    model = Vehicle
    template_name = 'vehicles/vehicle_detail.html'
    context_object_name = 'vehicle'


class ImageProxyView(View):
    """
    Temporary proxy view to serve external images and bypass CORS restrictions.

    Usage in templates:
    <img src="{% url 'image_proxy' %}?url={{ vehicle.photo_link|urlencode }}" />
    """

    def get(self, request):
        image_url = request.GET.get('url')
        if not image_url:
            return HttpResponse('No URL provided', status=400)

        # Decode URL if it's encoded
        image_url = unquote(image_url)

        # Security check - only allow richmonds.com.au images
        if 'richmonds.com.au' not in image_url:
            return HttpResponse('Forbidden', status=403)

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://richmonds.com.au/',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }

            response = requests.get(image_url, headers=headers, timeout=10)
            if response.status_code == 200:
                # Determine content type
                content_type = response.headers.get('content-type', 'image/jpeg')

                return HttpResponse(
                    response.content,
                    content_type=content_type,
                    headers={
                        'Cache-Control': 'public, max-age=3600',  # Cache for 1 hour
                        'Access-Control-Allow-Origin': '*',
                    }
                )
            else:
                return HttpResponse('Image not found', status=404)

        except requests.RequestException:
            return HttpResponse('Failed to fetch image', status=500)
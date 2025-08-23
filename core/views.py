from django.http import HttpResponseRedirect, HttpResponseBadRequest, StreamingHttpResponse
from django.shortcuts import render
import requests
from .forms import VideoForm
from .utils import extract_info, pick_best_formats
from .forms import ContactForm


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}


def home(request):
    context = {}
    if request.method == "POST":
        form = VideoForm(request.POST)
        if form.is_valid():
            video_url = form.cleaned_data["video_url"]

            try:
                info = extract_info(video_url)
                picks = pick_best_formats(info)
                best = picks['best'] or picks['fallback']

                context.update({
                    "form": form,
                    "video_url": video_url,
                    "info": {
                        "title": info.get("title"),
                        "uploader": info.get("uploader"),
                        "duration": info.get("duration"),
                    },
                    "thumbnail": info.get("thumbnail"),
                    "best": {
                        "url": best.get("url") if best else None,
                        "format_id": best.get("format_id") if best else None,
                        "height": best.get("height") if best else None,
                    } if best else None,
                })
            except Exception as e:
                context["error"] = f"Failed to fetch video: {str(e)}"
        else:
            context["form"] = form
            context["error"] = "Invalid Facebook video URL!"
    else:
        context["form"] = VideoForm()

    return render(request, "core/home.html", context)


import requests
from django.http import StreamingHttpResponse, HttpResponseBadRequest

# তোমার HEADERS এখানে define করতে হবে
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def _stream_external(url: str, filename: str = 'video.mp4'):
    """Stream remote file to client with headers and download attachment."""
    try:
        r = requests.get(url, headers=HEADERS, stream=True, timeout=25)
        r.raise_for_status()

        # fallback content type
        content_type = r.headers.get('Content-Type', 'application/octet-stream')

        # Streaming response wrapper
        def file_iterator(chunk_size=8192):
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    yield chunk

        resp = StreamingHttpResponse(file_iterator(), content_type=content_type)

        # ✅ গুরুত্বপূর্ণ: Content-Length দিলে ব্রাউজার ফাইল সাইজ বুঝতে পারবে
        if 'Content-Length' in r.headers:
            resp['Content-Length'] = r.headers['Content-Length']

        resp['Content-Disposition'] = f'attachment; filename="{filename}"'
        return resp

    except requests.RequestException as e:
        return HttpResponseBadRequest(f"Download failed: {e}")


def download_proxy(request):
    video_url = request.GET.get('video_url')
    format_id = request.GET.get('format_id')

    if not video_url or not format_id:
        return HttpResponseBadRequest('Missing parameters.')

    try:
        # extract_info তুমি আগে define করেছো ধরে নিচ্ছি
        info = extract_info(video_url)
        fmt = next((f for f in info.get('formats', []) if str(f.get('format_id')) == str(format_id)), None)

        if not fmt or not fmt.get('url'):
            return HttpResponseBadRequest('Selected format not available.')

        title = info.get('title') or 'facebook_video'
        filename = f"{title}.mp4".replace('/', '-').replace('\\', '-')

        # ফাইনালি stream করে client-এ পাঠানো হবে
        return _stream_external(fmt['url'], filename)

    except Exception as e:
        return HttpResponseBadRequest(f"Error: {e}")


def play_proxy(request):
    video_url = request.GET.get('video_url')
    if not video_url:
        return HttpResponseBadRequest('Missing video_url.')

    try:
        info = extract_info(video_url)
        picks = pick_best_formats(info)
        best = picks['best'] or picks['fallback']

        if not best or not best.get('url'):
            return HttpResponseBadRequest('Playable URL not found.')

        return HttpResponseRedirect(best['url'])
    except Exception as e:
        return HttpResponseBadRequest(f"Error: {e}")


def about(request):
    """
    Render the About page for AJYRA FB Downloader
    """
    return render(request, 'core/about.html')

def contact(request):
    """Render and process the Contact page form"""
    form = ContactForm()
    success = False

    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            message = form.cleaned_data['message']

            # Optional: send an email to site admin
            try:
                send_mail(
                    subject=f"Contact Form: {name}",
                    message=message,
                    from_email=email,
                    recipient_list=[settings.DEFAULT_FROM_EMAIL],
                )
                success = True
            except Exception as e:
                print(f"Email sending failed: {e}")

    context = {'form': form, 'success': success}
    return render(request, 'core/contact.html', context)
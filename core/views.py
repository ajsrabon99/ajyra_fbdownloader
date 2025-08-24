import os
import tempfile
import threading
from django.http import FileResponse, HttpResponseRedirect, HttpResponseBadRequest, StreamingHttpResponse, HttpResponse
from django.shortcuts import render
from django.utils.encoding import smart_str
from yt_dlp import YoutubeDL
from .forms import VideoForm, ContactForm
from .utils import extract_info, pick_best_formats
# from django.core.mail import send_mail  # uncomment if using email
# from django.conf import settings          # uncomment if using email

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
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

def _stream_file(path, filename="video.mp4"):
    """
    Stream local file as Django FileResponse
    """
    try:
        response = FileResponse(open(path, "rb"), as_attachment=True, filename=filename)
        return response
    except Exception as e:
        raise e

def download_proxy(request):
    video_url = request.GET.get('video_url')
    if not video_url:
        return HttpResponseBadRequest("Missing video_url parameter.")

    try:
        # Temp directory path
        tmp_dir = tempfile.gettempdir()
        output_path = os.path.join(tmp_dir, "temp_video.%(ext)s")

        # yt-dlp options (optimized for slow WiFi)
        ydl_opts = {
            "format": "best[height<=480]/best",  # ছোট resolution নেবে, fallback best
            "outtmpl": output_path,
            "merge_output_format": "mp4",
            "quiet": True,
            "http_headers": HEADERS,
            "noplaylist": True,
            "socket_timeout": 120,       # slow net এর জন্য বেশি সময়
            "retries": 10,               # বারবার চেষ্টা করবে
            "fragment_retries": 10,      # ফ্রাগমেন্ট fail হলে আবার চেষ্টা
            "continuedl": True,          # resume support
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            final_file = ydl.prepare_filename(info)

        if not os.path.exists(final_file):
            return HttpResponseBadRequest("Failed to download video.")

        response = _stream_file(final_file, filename=info.get("title", "video") + ".mp4")

        # ফাইল ডিলিট safe way
        def cleanup(path):
            try:
                os.remove(path)
            except PermissionError:
                print(f"⚠️ Could not delete {path}, file still in use.")

        threading.Thread(target=cleanup, args=(final_file,)).start()

        return response

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return HttpResponseBadRequest(f"Error downloading video: {e}")


def play_proxy(request):
    video_url = request.GET.get('video_url')
    if not video_url:
        return HttpResponseBadRequest('Missing video_url.')

    try:
        info = extract_info(video_url)

        # Find format with both audio+video
        best = next(
            (f for f in reversed(info.get('formats', []))
             if f.get('vcodec') != 'none' and f.get('acodec') != 'none'),
            None
        )

        if not best or not best.get('url'):
            return HttpResponseBadRequest('Playable URL with audio not found.')

        return HttpResponseRedirect(best['url'])

    except Exception as e:
        return HttpResponseBadRequest(f"Error: {e}")


def about(request):
    """Render the About page"""
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
            # try:
            #     send_mail(
            #         subject=f"Contact Form: {name}",
            #         message=message,
            #         from_email=email,
            #         recipient_list=[settings.DEFAULT_FROM_EMAIL],
            #     )
            #     success = True
            # except Exception as e:
            #     print(f"Email sending failed: {e}")

    context = {'form': form, 'success': success}
    return render(request, 'core/contact.html', context)

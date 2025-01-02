from rest_framework import viewsets
import os, requests

from re import search, sub
from base.tasks import (
    send_email_task,
    send_password_reset_email,
)  # Import your email sending task
import json

from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage, EmailMultiAlternatives, send_mail
from django.db.models.functions import Now
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from django.http import HttpResponsePermanentRedirect, HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.template.loader import get_template, render_to_string
from django.utils.encoding import DjangoUnicodeDecodeError, smart_bytes, smart_str
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import generics, status
from rest_framework.decorators import (
    api_view,
    action,
    parser_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.core.files.storage import default_storage
from django.shortcuts import render, get_object_or_404
from datetime import datetime
from django.views import View
from django.core.files.storage import default_storage
import json
from django.views.decorators.csrf import csrf_exempt
from base.models import *
from base.serializers import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser


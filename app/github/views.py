# -*- coding: utf-8 -*-
"""Handle github views.

Copyright (C) 2018 Gitcoin Core

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.

"""

from __future__ import print_function, unicode_literals

import logging

from django.conf import settings
from django.http import Http404
from django.shortcuts import redirect
from django.views.decorators.http import require_GET

from dashboard.models import Profile
from github.utils import get_auth_url, get_github_primary_email, get_github_user_data, get_github_user_token


@require_GET
def github_callback(request):
    """Handle the Github authentication callback."""
    # Get request parameters to handle authentication and the redirect.
    code = request.GET.get('code', None)
    redirect_uri = request.GET.get('redirect_uri')

    if not code or not redirect_uri:
        raise Http404

    # Get OAuth token and github user data.
    access_token = get_github_user_token(code)
    github_user_data = get_github_user_data(access_token)
    handle = github_user_data.get('login')

    if handle:
        # Create or update the Profile with the github user data.
        user_profile, _ = Profile.objects.update_or_create(
            handle=handle,
            defaults={
                'data': github_user_data or {},
                'email': get_github_primary_email(access_token),
                'github_access_token': access_token
            })

        # Update the user's session with handle and email info.
        session_data = {
            'handle': user_profile.handle,
            'email': user_profile.email,
            'access_token': user_profile.github_access_token,
            'profile_id': user_profile.pk
        }
        for k, v in session_data.items():
            request.session[k] = v

    return redirect(redirect_uri)


@require_GET
def github_authentication(request):
    """Handle Github authentication."""
    redirect_uri = request.GET.get('redirect_uri', '/')
    if settings.DEBUG and (not settings.GITHUB_CLIENT_ID or settings.GITHUB_CLIENT_ID == 'TODO'):
        logging.info('GITHUB_CLIENT_ID is not set. Github integration is disabled!')
        return redirect(redirect_uri)
    return redirect(get_auth_url(redirect_uri))

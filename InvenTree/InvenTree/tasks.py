# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
import json
import requests
import logging

from datetime import timedelta
from django.utils import timezone

from django.core.exceptions import AppRegistryNotReady
from django.db.utils import OperationalError, ProgrammingError
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _


logger = logging.getLogger("inventree")


def schedule_task(taskname, **kwargs):
    """
    Create a scheduled task.
    If the task has already been scheduled, ignore!
    """

    # If unspecified, repeat indefinitely
    repeats = kwargs.pop('repeats', -1)
    kwargs['repeats'] = repeats

    try:
        from django_q.models import Schedule
    except (AppRegistryNotReady):
        logger.info("Could not start background tasks - App registry not ready")
        return

    try:
        # If this task is already scheduled, don't schedule it again
        # Instead, update the scheduling parameters
        if Schedule.objects.filter(func=taskname).exists():
            logger.debug(f"Scheduled task '{taskname}' already exists - updating!")

            Schedule.objects.filter(func=taskname).update(**kwargs)
        else:
            logger.info(f"Creating scheduled task '{taskname}'")

            Schedule.objects.create(
                name=taskname,
                func=taskname,
                **kwargs
            )
    except (OperationalError, ProgrammingError):
        # Required if the DB is not ready yet
        pass


def offload_task(taskname, *args, force_sync=False, **kwargs):
    """
        Create an AsyncTask if workers are running.
        This is different to a 'scheduled' task,
        in that it only runs once!

        If workers are not running or force_sync flag
        is set then the task is ran synchronously.
    """

    try:
        from django_q.tasks import AsyncTask
    except (AppRegistryNotReady):
        logger.warning("Could not offload task - app registry not ready")
        return
    import importlib
    from InvenTree.status import is_worker_running

    if is_worker_running() and not force_sync:
        # Running as asynchronous task
        try:
            task = AsyncTask(taskname, *args, **kwargs)
            task.run()
        except ImportError:
            logger.warning(f"WARNING: '{taskname}' not started - Function not found")
    else:
        # Split path
        try:
            app, mod, func = taskname.split('.')
            app_mod = app + '.' + mod
        except ValueError:
            logger.warning(f"WARNING: '{taskname}' not started - Malformed function path")
            return

        # Import module from app
        try:
            _mod = importlib.import_module(app_mod)
        except ModuleNotFoundError:
            logger.warning(f"WARNING: '{taskname}' not started - No module named '{app_mod}'")
            return

        # Retrieve function
        try:
            _func = getattr(_mod, func)
        except AttributeError:
            # getattr does not work for local import
            _func = None

        try:
            if not _func:
                _func = eval(func)
        except NameError:
            logger.warning(f"WARNING: '{taskname}' not started - No function named '{func}'")
            return
        
        # Workers are not running: run it as synchronous task
        _func()


def heartbeat():
    """
    Simple task which runs at 5 minute intervals,
    so we can determine that the background worker
    is actually running.

    (There is probably a less "hacky" way of achieving this)?
    """

    try:
        from django_q.models import Success
        logger.info("Could not perform heartbeat task - App registry not ready")
    except AppRegistryNotReady:
        return

    threshold = timezone.now() - timedelta(minutes=30)

    # Delete heartbeat results more than half an hour old,
    # otherwise they just create extra noise
    heartbeats = Success.objects.filter(
        func='InvenTree.tasks.heartbeat',
        started__lte=threshold
    )

    heartbeats.delete()


def delete_successful_tasks():
    """
    Delete successful task logs
    which are more than a month old.
    """

    try:
        from django_q.models import Success
    except AppRegistryNotReady:
        logger.info("Could not perform 'delete_successful_tasks' - App registry not ready")
        return

    threshold = timezone.now() - timedelta(days=30)

    results = Success.objects.filter(
        started__lte=threshold
    )

    if results.count() > 0:
        logger.info(f"Deleting {results.count()} successful task records")
        results.delete()


def delete_old_error_logs():
    """
    Delete old error logs from the server
    """

    try:
        from error_report.models import Error

        # Delete any error logs more than 30 days old
        threshold = timezone.now() - timedelta(days=30)

        errors = Error.objects.filter(
            when__lte=threshold,
        )

        if errors.count() > 0:
            logger.info(f"Deleting {errors.count()} old error logs")
            errors.delete()

    except AppRegistryNotReady:
        # Apps not yet loaded
        logger.info("Could not perform 'delete_old_error_logs' - App registry not ready")
        return


def check_for_updates():
    """
    Check if there is an update for InvenTree
    """

    try:
        import common.models
    except AppRegistryNotReady:
        # Apps not yet loaded!
        logger.info("Could not perform 'check_for_updates' - App registry not ready")
        return

    response = requests.get('https://api.github.com/repos/inventree/inventree/releases/latest')

    if not response.status_code == 200:
        raise ValueError(f'Unexpected status code from GitHub API: {response.status_code}')

    data = json.loads(response.text)

    tag = data.get('tag_name', None)

    if not tag:
        raise ValueError("'tag_name' missing from GitHub response")

    match = re.match(r"^.*(\d+)\.(\d+)\.(\d+).*$", tag)

    if not len(match.groups()) == 3:
        logger.warning(f"Version '{tag}' did not match expected pattern")
        return

    latest_version = [int(x) for x in match.groups()]

    if not len(latest_version) == 3:
        raise ValueError(f"Version '{tag}' is not correct format")

    logger.info(f"Latest InvenTree version: '{tag}'")

    # Save the version to the database
    common.models.InvenTreeSetting.set_setting(
        'INVENTREE_LATEST_VERSION',
        tag,
        None
    )


def delete_expired_sessions():
    """
    Remove any expired user sessions from the database
    """

    try:
        from django.contrib.sessions.models import Session

        # Delete any sessions that expired more than a day ago
        expired = Session.objects.filter(expire_date__lt=timezone.now() - timedelta(days=1))

        if expired.count() > 0:
            logger.info(f"Deleting {expired.count()} expired sessions.")
            expired.delete()

    except AppRegistryNotReady:
        logger.info("Could not perform 'delete_expired_sessions' - App registry not ready")


def update_exchange_rates():
    """
    Update currency exchange rates
    """

    try:
        from InvenTree.exchange import InvenTreeExchange
        from djmoney.contrib.exchange.models import ExchangeBackend, Rate
        from common.settings import currency_code_default, currency_codes
    except AppRegistryNotReady:
        # Apps not yet loaded!
        logger.info("Could not perform 'update_exchange_rates' - App registry not ready")
        return
    except:
        # Other error?
        return

    # Test to see if the database is ready yet
    try:
        backend = ExchangeBackend.objects.get(name='InvenTreeExchange')
    except ExchangeBackend.DoesNotExist:
        pass
    except:
        # Some other error
        logger.warning("update_exchange_rates: Database not ready")
        return

    backend = InvenTreeExchange()
    logger.info(f"Updating exchange rates from {backend.url}")

    base = currency_code_default()

    logger.info(f"Using base currency '{base}'")

    backend.update_rates(base_currency=base)

    # Remove any exchange rates which are not in the provided currencies
    Rate.objects.filter(backend="InvenTreeExchange").exclude(currency__in=currency_codes()).delete()


def send_email(subject, body, recipients, from_email=None, html_message=None):
    """
    Send an email with the specified subject and body,
    to the specified recipients list.
    """

    if type(recipients) == str:
        recipients = [recipients]

    offload_task(
        'django.core.mail.send_mail',
        subject,
        body,
        from_email,
        recipients,
        fail_silently=False,
        html_message=html_message
    )


def notify_low_stock(stock_item):
    """
    Notify users who have starred a part when its stock quantity falls below the minimum threshold
    """

    from allauth.account.models import EmailAddress
    starred_users = EmailAddress.objects.filter(user__starred_parts__part=stock_item.part)

    if len(starred_users) > 0:
        logger.info(f"Notify users regarding low stock of {stock_item.part.name}")
        context = {
            'part_name': stock_item.part.name,
            # Part url can be used to open the page of part in application from the email.
            # It can be facilitated when the application base url is accessible programmatically.
            # 'part_url': f'{application_base_url}/part/{stock_item.part.id}',

            # quantity is in decimal field datatype. Since the same datatype is used in models,
            # it is not converted to number/integer,
            'part_quantity': stock_item.quantity,
            'minimum_quantity': stock_item.part.minimum_stock
        }
        subject = _(f'Attention! {stock_item.part.name} is low on stock')
        html_message = render_to_string('stock/low_stock_notification.html', context)
        recipients = starred_users.values_list('email', flat=True)
        send_email(subject, '', recipients, html_message=html_message)

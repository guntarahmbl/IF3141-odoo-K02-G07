import json
import logging
import time

import requests

from odoo import models, fields, api


_logger = logging.getLogger(__name__)
MAX_MESSAGE_LENGTH = 1000


class APIHealth(models.Model):
    _name = 'manajemen_piutang.api_health'
    _description = 'API Health Check Log'
    _order = 'last_check desc, id desc'
    _rec_name = 'service'

    service = fields.Selection([
        ('xendit', 'Xendit'),
        ('xendit_callback', 'Xendit Callback'),
        ('fonnte', 'Fonnte'),
    ], string='Service', required=True)
    last_check = fields.Datetime(string='Last Check', default=fields.Datetime.now)
    status = fields.Selection([
        ('ok', 'OK'),
        ('failed', 'Failed'),
    ], string='Status', required=True)
    http_status = fields.Integer(string='HTTP Status')
    response_time_ms = fields.Integer(string='Response Time (ms)')
    message = fields.Text(string='Message')

    @api.model
    def record_check(self, service, ok, http_status=None, response_time_ms=None, message=''):
        return self.sudo().create({
            'service': service,
            'last_check': fields.Datetime.now(),
            'status': 'ok' if ok else 'failed',
            'http_status': int(http_status) if http_status is not None else False,
            'response_time_ms': int(response_time_ms) if response_time_ms is not None else False,
            'message': (message or '')[:MAX_MESSAGE_LENGTH],
        })

    @api.model
    def run_xendit_check(self):
        params = self.env['ir.config_parameter'].sudo()
        secret_key = (params.get_param('manajemen_piutang.xendit_secret_api_key') or '').strip()

        if not secret_key:
            record = self.record_check(
                'xendit',
                False,
                message='Xendit Secret API Key belum dikonfigurasi.',
            )
            return self._result_from_record(record)

        return self._run_http_check(
            method='GET',
            service='xendit',
            url='https://api.xendit.co/v2/invoices?limit=1',
            request_kwargs={'auth': (secret_key, ''), 'timeout': 10},
        )

    @api.model
    def run_callback_check(self):
        params = self.env['ir.config_parameter'].sudo()
        callback_token = (params.get_param('manajemen_piutang.xendit_webhook_token') or '').strip()

        if not callback_token:
            record = self.record_check(
                'xendit_callback',
                False,
                message='Xendit Callback Token belum dikonfigurasi.',
            )
            return self._result_from_record(record)

        base_url = (params.get_param('web.base.url') or '').rstrip('/')
        if not base_url:
            record = self.record_check(
                'xendit_callback',
                False,
                message='web.base.url belum dikonfigurasi.',
            )
            return self._result_from_record(record)

        return self._run_http_check(
            method='GET',
            service='xendit_callback',
            url=f'{base_url}/xendit/webhook/health',
            request_kwargs={
                'headers': {'x-callback-token': callback_token},
                'timeout': 10,
            },
        )

    @api.model
    def run_fonnte_check(self):
        params = self.env['ir.config_parameter'].sudo()
        token = (params.get_param('manajemen_piutang.wa_fonnte_token') or '').strip()

        if not token:
            record = self.record_check(
                'fonnte',
                False,
                message='Fonnte API Token belum dikonfigurasi.',
            )
            return self._result_from_record(record)

        return self._run_http_check(
            method='POST',
            service='fonnte',
            url='https://api.fonnte.com/device',
            request_kwargs={'headers': {'Authorization': token}, 'timeout': 10},
        )

    @api.model
    def run_all_checks(self):
        return [
            self.run_xendit_check(),
            self.run_callback_check(),
            self.run_fonnte_check(),
        ]

    def action_check_xendit(self):
        result = self.env['manajemen_piutang.api_health'].run_xendit_check()
        return self._notification_action([result])

    def action_check_callback(self):
        result = self.env['manajemen_piutang.api_health'].run_callback_check()
        return self._notification_action([result])

    def action_check_fonnte(self):
        result = self.env['manajemen_piutang.api_health'].run_fonnte_check()
        return self._notification_action([result])

    def action_check_all(self):
        results = self.env['manajemen_piutang.api_health'].run_all_checks()
        return self._notification_action(results)

    @api.model
    def _run_http_check(self, method, service, url, request_kwargs):
        start = time.time()
        try:
            response = requests.request(method, url, **request_kwargs)
            elapsed_ms = int((time.time() - start) * 1000)
            payload = self._safe_json(response)
            ok = response.ok and not self._payload_is_failure(payload)
            record = self.record_check(
                service,
                ok,
                http_status=response.status_code,
                response_time_ms=elapsed_ms,
                message=self._response_message(response, payload, ok),
            )
            return self._result_from_record(record)
        except requests.RequestException as exc:
            elapsed_ms = int((time.time() - start) * 1000)
            _logger.exception('%s health check failed', service)
            record = self.record_check(
                service,
                False,
                response_time_ms=elapsed_ms,
                message=str(exc),
            )
            return self._result_from_record(record)

    @api.model
    def _safe_json(self, response):
        try:
            return response.json()
        except ValueError:
            return None

    @api.model
    def _payload_is_failure(self, payload):
        if not isinstance(payload, dict):
            return False

        status = payload.get('status')
        if status is False:
            return True
        if isinstance(status, str) and status.lower() in ('failed', 'failure', 'error'):
            return True
        return False

    @api.model
    def _response_message(self, response, payload, ok):
        if ok:
            return 'HTTP %s %s' % (response.status_code, response.reason or 'OK')

        if isinstance(payload, dict):
            for key in ('message', 'error_code', 'error', 'reason'):
                if payload.get(key):
                    return str(payload[key])[:MAX_MESSAGE_LENGTH]

            if payload:
                return json.dumps(payload, ensure_ascii=True)[:MAX_MESSAGE_LENGTH]

        text = (response.text or response.reason or '').strip()
        return text[:MAX_MESSAGE_LENGTH]

    @api.model
    def _result_from_record(self, record):
        return {
            'success': record.status == 'ok',
            'service': record.service,
            'status': record.status,
            'http_status': record.http_status,
            'response_time_ms': record.response_time_ms,
            'message': record.message or '',
            'last_check': fields.Datetime.to_string(record.last_check),
        }

    def _notification_action(self, results):
        failed_services = [
            result['service'].title()
            for result in results
            if not result.get('success')
        ]

        if failed_services:
            title = 'API Health Check Failed'
            message = 'Service bermasalah: %s' % ', '.join(failed_services)
            notification_type = 'danger'
            sticky = True
        else:
            title = 'API Health Check OK'
            message = 'Semua service berhasil dicek.'
            notification_type = 'success'
            sticky = False

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': message,
                'type': notification_type,
                'sticky': sticky,
                'next': {
                    'type': 'ir.actions.client',
                    'tag': 'soft_reload',
                },
            },
        }

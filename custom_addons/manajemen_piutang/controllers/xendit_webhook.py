import json
import logging

from odoo import fields, http
from odoo.http import request

_logger = logging.getLogger(__name__)


class XenditWebhookController(http.Controller):

    @http.route('/xendit/webhook', type='http', auth='public', methods=['POST'], csrf=False)
    def xendit_webhook(self, **kwargs):
        payload_raw = request.httprequest.data.decode('utf-8') if request.httprequest.data else '{}'

        try:
            payload = json.loads(payload_raw)
        except json.JSONDecodeError:
            _logger.warning('Xendit webhook payload is not valid JSON: %s', payload_raw)
            return request.make_json_response({'success': False, 'message': 'invalid json'}, status=400)

        params = request.env['ir.config_parameter'].sudo()
        expected_token = params.get_param('manajemen_piutang.xendit_webhook_token')
        callback_token = request.httprequest.headers.get('x-callback-token')

        if expected_token and callback_token != expected_token:
            _logger.warning('Xendit webhook rejected because callback token is invalid')
            return request.make_json_response({'success': False, 'message': 'unauthorized'}, status=401)

        data = payload.get('data') if isinstance(payload, dict) else {}
        if not isinstance(data, dict):
            data = {}

        invoice_id = data.get('id') or payload.get('id')
        external_id = data.get('external_id') or payload.get('external_id')
        status = (data.get('status') or payload.get('status') or '').upper()
        paid_amount = data.get('paid_amount') or data.get('amount') or payload.get('paid_amount') or payload.get('amount') or 0

        is_paid_event = status in ('PAID', 'SETTLED') or bool(payload.get('payment_id'))
        is_expired_event = status in ('EXPIRED', 'VOIDED') or bool(payload.get('expired_at'))

        tagihan = request.env['manajemen_piutang.tagihan'].sudo().search([
            '|',
            ('xendit_invoice_id', '=', invoice_id),
            ('xendit_external_id', '=', external_id),
        ], limit=1)

        if not tagihan:
            _logger.info('Xendit webhook received but no matching tagihan: invoice_id=%s external_id=%s', invoice_id, external_id)
            return request.make_json_response({'success': True, 'message': 'no matching invoice'}, status=200)

        if is_paid_event:
            pembayaran_model = request.env['manajemen_piutang.pembayaran'].sudo()
            existing_payment = pembayaran_model.search([
                '|',
                ('id_transaksi', '=', invoice_id),
                ('id_transaksi', '=', external_id),
            ], limit=1)

            if not existing_payment:
                pembayaran_model.create({
                    'id_transaksi': invoice_id or external_id or f'TRX-XENDIT-{tagihan.id}',
                    'nominal_masuk': paid_amount,
                    'waktu_bayar': fields.Datetime.now(),
                    'status_settlement': status.lower() or 'paid',
                    'tagihan_id': tagihan.id,
                })

            tagihan.write({'status_lunas': 'lunas'})
            _logger.info('Xendit webhook marked tagihan %s as paid', tagihan.id)

        if is_expired_event and not is_paid_event:
            tagihan.write({'status_lunas': 'belum_lunas'})
            _logger.info('Xendit webhook marked tagihan %s as expired', tagihan.id)

        return request.make_json_response({'success': True}, status=200)

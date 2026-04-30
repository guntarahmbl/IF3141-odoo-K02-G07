from uuid import uuid4
import requests
from datetime import date, timedelta
from odoo import models, fields, api
from odoo.exceptions import UserError

class Tagihan(models.Model):
    _name = 'manajemen_piutang.tagihan'
    _description = 'Data Tagihan & Piutang'

    _rec_name = 'xendit_external_id'

    konsumen_id = fields.Many2one('manajemen_piutang.konsumen', string='Pelanggan', required=True, ondelete='restrict')
    pembayaran_ids = fields.One2many('manajemen_piutang.pembayaran', 'tagihan_id', string='Riwayat Pembayaran')
    
    total_tagihan = fields.Integer(string='Total Tagihan (Rp)', required=True)
    rincian_item = fields.Text(string='Rincian Item Pesanan')
    tgl_terbit = fields.Date(string='Tanggal Terbit', default=fields.Date.context_today)
    tgl_jatuh_tempo = fields.Date(string='Tanggal Jatuh Tempo', required=True)
    
    status_lunas = fields.Selection([
        ('belum_lunas', 'Belum Lunas'),
        ('lunas', 'Lunas')
    ], string='Status Pembayaran', default='belum_lunas')
    
    link_payment = fields.Char(string='Link Pembayaran (Gateway)')
    xendit_invoice_id = fields.Char(string='Xendit Invoice ID', readonly=True, copy=False)
    xendit_external_id = fields.Char(string='Xendit External ID', readonly=True, copy=False)

    is_eskalasi = fields.Boolean(string='Perlu Eskalasi', compute='_compute_eskalasi', store=True)

    @api.depends('tgl_jatuh_tempo', 'status_lunas')
    def _compute_eskalasi(self):
        limit_hari = self.env['ir.config_parameter'].sudo().get_param('manajemen_piutang.hari_toleransi_eskalasi', 0)
        today = date.today()
        for rec in self:
            if rec.status_lunas == 'belum_lunas' and rec.tgl_jatuh_tempo:
                deadline = rec.tgl_jatuh_tempo + timedelta(days=int(limit_hari))
                rec.is_eskalasi = today > deadline
            else:
                rec.is_eskalasi = False

    def generateInvoice(self):
        params = self.env['ir.config_parameter'].sudo()
        secret_key = params.get_param('manajemen_piutang.xendit_secret_api_key')

        if not secret_key:
            raise UserError('Xendit Secret API Key belum diisi. Buka Settings > Manajemen Piutang untuk mengisi kredensial Xendit.')

        callback_base_url = params.get_param('web.base.url')

        for record in self:
            external_id = f"INV-{record.id}-{uuid4().hex[:8]}"
            payload = {
                'external_id': external_id,
                'amount': float(record.total_tagihan),
                'description': f'Tagihan #{record.id} - {record.konsumen_id.nama_pelanggan}',
                'currency': 'IDR',
                'invoice_duration': 86400,
                'success_redirect_url': f'{callback_base_url}/web',
            }

            try:
                response = requests.post(
                    'https://api.xendit.co/v2/invoices',
                    json=payload,
                    auth=(secret_key, ''),
                    timeout=15,
                )
                response.raise_for_status()
                result = response.json()
            except requests.RequestException as exc:
                raise UserError(f'Gagal membuat invoice Xendit: {exc}') from exc

            record.link_payment = result.get('invoice_url')
            record.xendit_invoice_id = result.get('id')
            record.xendit_external_id = external_id
            
    def reconcilePayment(self):
        for record in self:
            record.status_lunas = 'lunas'
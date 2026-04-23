from odoo import models, fields, api

class Tagihan(models.Model):
    _name = 'manajemen_piutang.tagihan'
    _description = 'Data Tagihan & Piutang'


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

    def generateInvoice(self):
        """Dipanggil saat tombol 'Kirim E-Invoice' di klik pada layar UI"""
        for record in self:
            record.link_payment = f"https://app.midtrans.com/pay/{record.id}-INV"
            

            
    def reconcilePayment(self):
        """Dipanggil oleh WebhookPaymentAPI saat konsumen selesai membayar"""
        for record in self:
            record.status_lunas = 'lunas'
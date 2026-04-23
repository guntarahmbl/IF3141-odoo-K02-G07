from odoo import models, fields

class Pembayaran(models.Model):
    _name = 'manajemen_piutang.pembayaran'
    _description = 'Data Riwayat Pembayaran'

    id_transaksi = fields.Char(string='ID Transaksi (Gateway)', required=True)
    nominal_masuk = fields.Float(string='Nominal Masuk', required=True)
    waktu_bayar = fields.Datetime(string='Waktu Bayar', default=fields.Datetime.now)
    status_settlement = fields.Char(string='Status Settlement', default='settlement')
    
    foto_bukti = fields.Binary(string='Foto Bukti (Manual)') 
    
    tagihan_id = fields.Many2one('manajemen_piutang.tagihan', string='Tagihan Terkait', required=True, ondelete='cascade')
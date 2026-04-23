from odoo import models, fields

class Kunjungan(models.Model):
    _name = 'manajemen_piutang.kunjungan'
    _description = 'Laporan Kunjungan Fisik'

    tagihan_id = fields.Many2one('manajemen_piutang.tagihan', string='Tagihan Terkait', required=True, ondelete='cascade')
    nama_staf = fields.Char(string='Nama Staf Penagihan', required=True)
    tgl_kunjungan = fields.Date(string='Tanggal Kunjungan', default=fields.Date.context_today)
    
    status_kunjungan = fields.Selection([
        ('berhasil', 'Berhasil Bertemu Konsumen'),
        ('gagal', 'Gagal / Rumah Kosong')
    ], string='Status Kunjungan', default='berhasil')
    
    hasil_kunjungan = fields.Char(string='Kesimpulan (Hasil)')
    catatan = fields.Text(string='Catatan Detail')
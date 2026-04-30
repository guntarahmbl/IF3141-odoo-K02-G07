from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Kunjungan(models.Model):
    _name = 'manajemen_piutang.kunjungan'
    _description = 'Laporan Kunjungan Fisik'

    tagihan_id = fields.Many2one('manajemen_piutang.tagihan', string='Tagihan Terkait', required=True, ondelete='cascade')
    
    nama_pelanggan = fields.Char(related='tagihan_id.konsumen_id.nama_pelanggan', string='Nama Pelanggan', readonly=True)
    total_tagihan = fields.Integer(related='tagihan_id.total_tagihan', string='Total Tagihan', readonly=True)
    
    nama_staf = fields.Char(string='Nama Staf Penagihan', required=True)
    tgl_kunjungan = fields.Date(string='Tanggal Kunjungan', default=fields.Date.context_today)
    
    status_kunjungan = fields.Selection([
        ('berhasil', 'Berhasil Bertemu Konsumen'),
        ('gagal', 'Gagal / Rumah Kosong')
    ], string='Status Kunjungan', default='berhasil')
    
    hasil_kunjungan = fields.Char(string='Kesimpulan (Hasil)')
    catatan = fields.Text(string='Catatan Detail')

    @api.constrains('tagihan_id')
    def _check_tagihan_status(self):
        for rec in self:
            if rec.tagihan_id.status_lunas == 'lunas':
                raise ValidationError("Kunjungan lapangan tidak dapat dibuat untuk tagihan yang sudah lunas.")
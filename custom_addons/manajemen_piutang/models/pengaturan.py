from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    hari_toleransi_eskalasi = fields.Integer(
        string='Batas Toleransi Eskalasi (Hari)',
        config_parameter='manajemen_piutang.hari_toleransi_eskalasi',
        default=3
    )
    
    template_pesan_wa = fields.Char(
        string='Template Pesan WhatsApp',
        config_parameter='manajemen_piutang.template_pesan_wa',
        default='Halo {nama}, tagihan Anda sebesar Rp {nominal} telah jatuh tempo. Mohon segera melakukan pelunasan.'
    )
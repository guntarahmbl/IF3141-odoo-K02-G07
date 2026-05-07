from odoo import models, fields, api
from odoo.exceptions import ValidationError


SETTING_KEYS = {
    'hari_toleransi_eskalasi': 'manajemen_piutang.hari_toleransi_eskalasi',
    'template_pesan_wa': 'manajemen_piutang.template_pesan_wa',
    'hari_reminder': 'manajemen_piutang.hari_reminder',
    'xendit_secret_api_key': 'manajemen_piutang.xendit_secret_api_key',
    'xendit_webhook_token': 'manajemen_piutang.xendit_webhook_token',
    'wa_fonnte_token': 'manajemen_piutang.wa_fonnte_token',
}

SECRET_FIELDS = {
    'xendit_secret_api_key',
    'xendit_webhook_token',
    'wa_fonnte_token',
}


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
        default='Halo {nama}, tagihan Anda sebesar Rp {nominal} akan jatuh tempo pada tanggal {jatuh_tempo}. Mohon segera melakukan pelunasan.'
    )

    hari_reminder = fields.Char(
        string='Jadwal Reminder (Hari Sebelum Jatuh Tempo)',
        config_parameter='manajemen_piutang.hari_reminder',
        default='3,0',
        help='Pisahkan dengan koma. Contoh: 3,0 berarti reminder H-3 dan H-0.'
    )

    xendit_secret_api_key = fields.Char(
        string='Xendit Secret API Key',
        config_parameter='manajemen_piutang.xendit_secret_api_key'
    )

    xendit_webhook_token = fields.Char(
        string='Xendit Callback Token',
        config_parameter='manajemen_piutang.xendit_webhook_token'
    )

    wa_fonnte_token = fields.Char(
        string='Fonnte API Token',
        config_parameter='manajemen_piutang.wa_fonnte_token'
    )

    @api.constrains('hari_reminder')
    def _check_hari_reminder(self):
        for rec in self:
            rec._parse_hari_reminder(rec.hari_reminder)

    def _parse_hari_reminder(self, value):
        days = []
        for raw_day in (value or '').split(','):
            raw_day = raw_day.strip()
            if not raw_day:
                continue
            if not raw_day.isdigit():
                raise ValidationError('Jadwal reminder hanya boleh berisi angka non-negatif yang dipisahkan koma.')
            days.append(int(raw_day))

        if not days:
            raise ValidationError('Jadwal reminder wajib diisi minimal satu angka, misalnya 3,0.')

        return sorted(set(days), reverse=True)

    def _mask_value(self, field_name, value):
        if field_name in SECRET_FIELDS and value:
            return '***'
        return str(value or '')

    def set_values(self):
        params = self.env['ir.config_parameter'].sudo()
        old_values = {
            field_name: params.get_param(param_key, '')
            for field_name, param_key in SETTING_KEYS.items()
        }

        super().set_values()

        log_model = self.env['manajemen_piutang.pengaturan_log'].sudo()
        for field_name, param_key in SETTING_KEYS.items():
            old_value = old_values.get(field_name, '')
            new_value = params.get_param(param_key, '')
            if old_value == new_value:
                continue

            log_model.create({
                'user_id': self.env.user.id,
                'field_name': field_name,
                'old_value': self._mask_value(field_name, old_value),
                'new_value': self._mask_value(field_name, new_value),
            })


class PengaturanLog(models.Model):
    _name = 'manajemen_piutang.pengaturan_log'
    _description = 'Log Audit Pengaturan Sistem'
    _order = 'waktu_perubahan desc'

    waktu_perubahan = fields.Datetime(
        string='Waktu Perubahan',
        required=True,
        default=fields.Datetime.now,
    )
    user_id = fields.Many2one(
        'res.users',
        string='Diubah Oleh',
        required=True,
        default=lambda self: self.env.user,
        readonly=True,
    )
    field_name = fields.Char(string='Field Pengaturan', required=True, readonly=True)
    old_value = fields.Text(string='Nilai Lama', readonly=True)
    new_value = fields.Text(string='Nilai Baru', readonly=True)

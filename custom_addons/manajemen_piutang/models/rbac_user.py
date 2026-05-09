from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    role_piutang = fields.Selection([
        ('none', 'Tidak Ada'),
        ('spesialis', 'Spesialis Pendapatan'),
        ('manajer', 'Manajer Keuangan'),
        ('staff', 'Staff Penagihan Piutang'),
        ('direktur', 'Direktur Utama'),
        ('admin', 'Administrator Sistem'),
    ], string='Role Manajemen Piutang', compute='_compute_role_piutang', inverse='_inverse_role_piutang')

    def _piutang_role_groups(self):
        return {
            'spesialis': self.env.ref('manajemen_piutang.group_spesialis_pendapatan'),
            'manajer': self.env.ref('manajemen_piutang.group_manajer_keuangan'),
            'staff': self.env.ref('manajemen_piutang.group_staff_penagihan'),
            'direktur': self.env.ref('manajemen_piutang.group_direktur_utama'),
            'admin': self.env.ref('manajemen_piutang.group_administrator_sistem'),
        }

    @api.depends('groups_id')
    def _compute_role_piutang(self):
        role_groups = self._piutang_role_groups()
        priority = ['admin', 'manajer', 'staff', 'direktur', 'spesialis']
        for user in self:
            user.role_piutang = 'none'
            for role in priority:
                if role_groups[role] in user.groups_id:
                    user.role_piutang = role
                    break

    def _inverse_role_piutang(self):
        role_groups = self._piutang_role_groups()
        base_user_group = self.env.ref('base.group_user')
        group_commands = [(3, group.id) for group in role_groups.values()]

        for user in self:
            commands = list(group_commands)
            if user.role_piutang and user.role_piutang != 'none':
                commands.append((4, base_user_group.id))
                commands.append((4, role_groups[user.role_piutang].id))
            user.groups_id = commands

    @api.model
    def action_open_piutang_rbac_groups(self):
        action = self.env.ref(
            'manajemen_piutang.action_piutang_rbac_groups',
            raise_if_not_found=False,
        )
        if action:
            return action.read()[0]

        category = self.env.ref('manajemen_piutang.module_category_manajemen_piutang')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Role & Hak Akses',
            'res_model': 'res.groups',
            'view_mode': 'tree,form',
            'domain': [('category_id', '=', category.id)],
            'context': {'default_category_id': category.id},
        }


class ResGroups(models.Model):
    _inherit = 'res.groups'

    piutang_menu_candidate_ids = fields.Many2many(
        'ir.ui.menu',
        string='Menu Manajemen Piutang',
        compute='_compute_piutang_menu_candidate_ids',
    )

    def _compute_piutang_menu_candidate_ids(self):
        root_menu = self.env.ref(
            'manajemen_piutang.menu_manajemen_piutang_root',
            raise_if_not_found=False,
        )
        menus = self.env['ir.ui.menu']
        if root_menu:
            menus = self.env['ir.ui.menu'].search([
                '|',
                ('id', '=', root_menu.id),
                ('parent_path', '=like', '%s/%%' % root_menu.id),
            ])

        for group in self:
            group.piutang_menu_candidate_ids = menus

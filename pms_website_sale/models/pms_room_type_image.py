# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later
#
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError

from odoo.addons.website.tools import get_video_embed_code


class PmsRoomTypeImage(models.Model):
    _name = 'pms.room.type.image'
    _description = "Room Type Image"
    _inherit = ['image.mixin']
    _order = 'sequence, id'

    name = fields.Char("Name", required=True)
    sequence = fields.Integer(default=10, index=True)

    image_1920 = fields.Image(required=True)

    room_type_id = fields.Many2one(comodel_name="pms.room.type", string="Room Type", index=True, ondelete="cascade")

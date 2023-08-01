# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import fields, models


class PmsRoomType(models.Model):
    _inherit = ["pms.room.type", "website.published.multi.mixin", "image.mixin"]
    _name = "pms.room.type"

    short_description = fields.Text(string="Short Description", translate=True)
    long_description = fields.Html(
        string="Long Description",
        sanitize_style=True,
        translate=True,
    )

    image_ids = fields.One2many(
        comodel_name="pms.room.type.image",
        inverse_name="room_type_id",
        string="Extra Room Type Media",
        copy=True,
    )

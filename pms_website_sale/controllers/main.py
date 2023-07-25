# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import http
from odoo.http import request


class WebsiteSale(http.Controller):
    @http.route(
        ["/room"],
        type="http",
        auth="public",
        website=True,
        # Do we need a sitemap?
        # sitemap=?,
    )
    def room(
        self,
        # The commented out arguments are used by website_sale. We may want to
        # also use some of them.
        #page=0,
        #category=None,
        #search="",
        #ppg=False,
        **post,
    ):
        domain = self._get_search_domain()
        room_types = request.env["pms.room.type"].search(domain)
        values = {
            "company_currency": request.env.company.currency_id,
            "room_types": room_types,
        }

        return request.render("pms_website_sale.rooms", values)

    def _get_search_domain(self):
        # TODO: Improve this.
        return []

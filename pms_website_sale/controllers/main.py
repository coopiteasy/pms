# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import http
from odoo.http import request

from odoo.addons.website.controllers.main import QueryURL


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
        # page=0,
        # category=None,
        # search="",
        # ppg=False,
        **post,
    ):
        keep = QueryURL(
            "/room",
            # category=category and int(category),
            # search=search,
            order=post.get("order"),
        )
        room_types = self._search_room_types(post)
        values = {
            "company_currency": request.env.company.currency_id,
            "room_types": room_types,
            "keep": keep,
        }

        return request.render("pms_website_sale.rooms", values)

    def _search_room_types(self, post):
        domain = self._get_search_domain()
        order = self._get_search_order(post)
        return request.env["pms.room.type"].search(domain, order=order)

    def _get_search_domain(self):
        # TODO: Improve this.
        return [
            # Unlike website_sale, we completely filter out non-published items,
            # meaning that even admin users cannot see greyed out unpublished
            # items. If you want this feature, it shouldn't be too difficult to
            # write.
            ("is_published", "=", True),
        ]

    def _get_search_order(self, post):
        # TODO: Get a better fallback than 'name ASC'. website_sale uses
        # 'website_sequence ASC'
        order = post.get("order") or "name ASC"
        return "%s, id desc" % order

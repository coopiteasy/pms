# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
from datetime import timedelta

from werkzeug.exceptions import NotFound

from odoo import http
from odoo.fields import Date
from odoo.http import request

from odoo.addons.payment.controllers.portal import PaymentProcessing

from .booking_engine_parser import BookingEngineParser, ParserError

logger = logging.getLogger(__name__)


def _dummy_request():  # todo remove
    # dummy data
    from random import randint

    today = Date.today()
    future = randint(100, 100000)
    single = request.env.ref("pms.pms_room_type_single").sudo()
    double = request.env.ref("pms.pms_room_type_double").sudo()
    return {
        "partner_id": False,
        "start_date": Date.to_string(today + timedelta(future)),
        "end_date": Date.to_string(today + timedelta(days=future + 2)),
        "channel_type_id": False,
        "rooms_requests": [
            {"room_type_id": single.id, "room_name": single.name, "quantity": 1},
            {"room_type_id": double.id, "room_name": double.name, "quantity": 2},
        ],
    }


class BookingEngineController(http.Controller):
    @http.route(
        ["/booking"],
        type="http",
        auth="public",
        website=True,
        methods=["GET", "POST"],
    )
    def booking(self, **post):
        errors = []
        be_parser = BookingEngineParser(request.env, request.session)

        if request.httprequest.method == "POST":
            if "delete" in post:
                try:
                    be_parser.del_room_request(post.get("delete"))
                except ParserError as e:
                    logger.error(e)
                    errors.append(e.usr_msg)
            else:
                try:
                    # Set daterange if it has not been set previously
                    be_parser.set_daterange(
                        post.get("start_date"), post.get("end_date"), overwrite=False
                    )
                    be_parser.add_room_request(
                        post.get("room_type_id"),
                        post.get("quantity"),
                        post.get("start_date"),
                        post.get("end_date"),
                    )
                except ParserError as e:
                    logger.error(e)
                    errors.append(e.usr_msg)
            be_parser.save()
        try:
            booking_engine = be_parser.parse()
        except KeyError as e:
            # todo return a nicer error
            # FIXME: why this type of error occurs ?
            raise e
        except ParserError as e:
            logger.error(e)
            errors.append(e.usr_msg)

        values = {
            "booking_engine": booking_engine,
            "errors": errors,
        }
        return request.render("pms_website_sale.pms_booking_engine_page", values)

    @http.route(
        ["/booking/extra_info"],
        type="http",
        auth="public",
        website=True,
        methods=["GET", "POST"],
    )
    def booking_extra_info(self, **post):
        errors = []

        parser = BookingEngineParser(request.env, request.session)

        values = {
            "internal_comment": parser.data.get("internal_comment", ""),
            "errors": errors,
        }

        if request.httprequest.method == "POST":
            try:
                parser.set_internal_comment(
                    internal_comment=post.get("internal_comment")
                )
            except ParserError as e:
                logger.error(e)
                errors.append(e.usr_msg)
            else:
                parser.save()
                return request.redirect("/booking/address")
            values["internal_comment"] = post.get("internal_comment", "")

        # FIXME: Is the booking engine really needed ?
        booking_engine = parser.parse()
        values["booking_engine"] = booking_engine

        return request.render("pms_website_sale.pms_booking_extra_info_page", values)

    @http.route(
        ["/booking/address"],
        type="http",
        auth="public",
        website=True,
        methods=["GET", "POST"],
    )
    def booking_address(self, **post):
        errors = []

        countries = request.env["res.country"].sudo().search([])
        default_country = request.env.company.country_id

        parser = BookingEngineParser(request.env, request.session)

        values = {
            "countries": countries,
            "default_country_id": default_country.id,
            "partner": parser.data.get("partner", {}),
            "errors": errors,
        }

        if request.httprequest.method == "POST":
            try:
                parser.set_partner(
                    name=post.get("name"),
                    email=post.get("email"),
                    phone=post.get("phone"),
                    address=post.get("address"),
                    city=post.get("city"),
                    postal_code=post.get("postal_code"),
                    country_id=post.get("country_id"),
                )
            except ParserError as e:
                logger.error(e)
                errors.append(e.usr_msg)
            else:
                parser.save()
                return request.redirect("/booking/payment")
            values["partner"] = post

        # FIXME: Is the booking engine really needed ?
        booking_engine = parser.parse()
        values["booking_engine"] = booking_engine

        return request.render("pms_website_sale.pms_booking_address_page", values)

    def _booking_payment(self):
        """
        processes the request on `/booking/payment`
        :return: dictionary to pass onto the template renderer
        """
        errors = []
        be_parser = BookingEngineParser(request.env, request.session)
        booking_engine = be_parser.parse()

        # todo check if need to filter on other acquirer fields (currency ?)
        acquirers = request.env["payment.acquirer"].search(
            [
                ("state", "in", ["enabled", "test"]),
                ("company_id", "=", request.env.company.id),
            ]
        )
        return {
            "booking_engine": booking_engine,
            "acquirers": acquirers,
            "error_message": errors,
            "bootstrap_formatting": True,
        }

    @http.route(
        ["/booking/payment"],
        type="http",
        auth="public",
        website=True,
        methods=["GET"],
    )
    def booking_payment(self):
        values = self._booking_payment()
        return request.render("pms_website_sale.pms_booking_payment_page", values)

    def _booking_payment_transaction(self, acquirer_id, **kwargs):
        """
        Processes requests on /booking/payment/transaction
        :param acquirer_id: the payment acquirer selected by the user
        :param kwargs:
        :return: the transaction tp pass onto the acquirer renderer
        """
        acquirer = request.env["payment.acquirer"].browse(acquirer_id)
        be_parser = BookingEngineParser(request.env, request.session)
        be_parser.parse()
        sudo_folio = be_parser.create_folio().sudo()
        tx = sudo_folio._create_payment_transaction(
            {
                "acquirer_id": acquirer.id,
                "type": "form",
                "return_url": f"/booking/success/{sudo_folio.id}",
            }
        )
        PaymentProcessing.add_payment_transaction(tx)
        return tx

    @http.route(
        ["/booking/payment/transaction"],
        type="json",
        auth="public",
        method=["POST"],
    )
    def booking_payment_transaction(self, acquirer_id, **kwargs):
        tx = self._booking_payment_transaction(acquirer_id, **kwargs)
        acquirer = request.env["payment.acquirer"].browse(acquirer_id)
        return acquirer.sudo().render(tx.reference, tx.amount, tx.currency_id.id)

    def _booking_success(self, folio_id):
        """
        Processes /booking/success for given folio id
        :return: dictionary to pass onto the template renderer
        """
        # todo Check for a token - otherwise anyone can validate any folio
        sudo_folio = request.env["pms.folio"].browse(folio_id).sudo()
        sudo_folio.action_confirm()
        moves = sudo_folio._create_invoices(grouped=True, final=True)
        moves.sudo().action_post()
        # TODO: move the cleanup of request.session to a BookingEnginerParser method
        request.session[BookingEngineParser.SESSION_KEY] = {}
        return {}

    @http.route(
        ["/booking/success/<int:folio_id>"],
        type="http",
        auth="public",
        website=True,
        methods=["GET"],
    )
    def booking_success(self, folio_id):
        folio = request.env["pms.folio"].sudo().browse(folio_id).exists()
        if not folio:
            raise NotFound("The requesting folio does not exists")
        values = self._booking_success(folio)
        return request.render("pms_website_sale.pms_booking_success_page", values)

    @http.route(
        ["/booking/failure"],
        type="http",
        auth="public",
        website=True,
        # methods=["GET"],
    )
    def booking_failure(self, **post):
        # todo notify property
        # todo cancel folio
        return request.render("pms_website_sale.pms_booking_failure_page")

from lxml.html import fromstring

from odoo.tests.common import HttpCase


class RoomControllerCase(HttpCase):
    def test_room_route(self):
        url = "/rooms"
        response = self.url_open(url=url)
        self.assertEqual(response.status_code, 200)
        page = fromstring(response.content)
        availability_divs = page.xpath("//div[@name='room_type_availability']")

        self.assertEqual(
            len(availability_divs), self.env["pms.room.type"].search([], count=True)
        )

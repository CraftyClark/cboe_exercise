import unittest
from app import PitchData


class TestPitchData(unittest.TestCase):

    def setUp(self):
        self.c = PitchData()


    def test_trade_order(self):
        trade_messages = [
                        "28807528PCK27GA000016B000177ZVZZT 0020000000000I000HV1PJ",
                        "28807529PCK27GA000016B000100ZVZZT 0020000000000I000HV1PK",
                        "28807529PCK27GA000016B000100ZVZZT 0020000000000I000HV1PL",
                        "28820482PCK27GA00001NB000100ZVZZT 0020000000000I000HV1Z0",
                        "28820483PCK27GA00001NB000100ZVZZT 0020002500000I000HV1Z1",
                        "28803240P4K27GA00004PB000200DXA   0000499600000N4AQ00003",
                        "28803240P4K27GA00004PB000300DXB   0000499600000N4AQ00003",
                        "28803240P4K27GA00004PB000400DXC   0000499600000N4AQ00003",
                        "28803240P4K27GA00004PB000500DXD   0000499600000N4AQ00003",
                        "28803240P4K27GA00004PB000600DXE   0000499600000N4AQ00003",
                        "28803240P4K27GA00004PB000700DXF   0000499600000N4AQ00003",
                        "28803240P4K27GA00004PB000800DXG   0000499600000N4AQ00003",
                        "28803240P4K27GA00004PB000900DXH   0000499600000N4AQ00003",
                        "28803240P4K27GA00004PB001000DXI   0000499600000N4AQ00003",
                        "28803240P4K27GA00004PB001700DXJ   0000499600000N4AQ00003",
                        "28803240P4K27GA00004PB001300DXB   0000499600000N4AQ00003"]

        for message in trade_messages:
            self.c.trade_order(message)
            
        self.assertEqual(self.c.executed_orders, {'ZVZZT': 577, 'DXA': 200, 'DXB': 1600, 'DXC': 400, 'DXD': 500, 'DXE': 600, 'DXF': 700, 'DXG': 800, 'DXH': 900, 'DXI': 1000, 'DXJ': 1700})


    def test_add_order(self):
        addorder_messages = [
            "28800011AAK27GA0000DTS000100SH    0000619200Y",
            "28800012ABK27GA00000KB001000SSO   0000763800Y",
            "28800161A4K27GA00002YS002100DIG   0001244400Y",
        ]
        for message in addorder_messages:
            self.c.add_order(message)
        
        self.assertEqual(self.c.existing_orders, {'AK27GA0000DT': {'stock_symbol': 'SH', 'shares': 100}, 'BK27GA00000K': {'stock_symbol': 'SSO', 'shares': 1000}, '4K27GA00002Y': {'stock_symbol': 'DIG', 'shares': 2100}})


    def test_cancel_order(self):
        self.c.add_order("28803228A4K27GA00003PB000100DXD   0000499700Y")
        self.assertEqual(self.c.existing_orders, {'4K27GA00003P': {'stock_symbol': 'DXD', 'shares': 100}})

        self.c.cancel_order("28803234X4K27GA00003P000100")
        self.assertEqual(self.c.existing_orders, {})


    def test_execute_order(self):
        self.c.add_order("28800161A4K27GA00002YS002100DIG   0001244400Y")
        self.c.execute_order("28843493E4K27GA00002Y00110000004AQ00005")

        self.assertEqual(self.c.existing_orders, {'4K27GA00002Y': {'stock_symbol': 'DIG', 'shares': 1000}})
        self.assertEqual(self.c.executed_orders, {'DIG': 1100})

        self.c.execute_order("28843493E4K27GA00002Y00100000004AQ00005")

        self.assertEqual(self.c.existing_orders, {})
        self.assertEqual(self.c.executed_orders, {'DIG': 2100})


if __name__ == '__main__':
    unittest.main()
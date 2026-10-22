import unittest
from unittest.mock import Mock, patch

from sama_lcd import app
from sama_lcd.transport import NoHelloResponse, ProtocolMismatch, probe_serial


class StartupTest(unittest.TestCase):
    @patch("sama_lcd.transport.inspect")
    def test_empty_hello_is_distinct_from_invalid_reply(self, _inspect):
        port = Mock()
        port.write.return_value = 250
        port.read.return_value = b""
        with self.assertRaises(NoHelloResponse):
            probe_serial(port)
        port.read.return_value = b"unexpected"
        with self.assertRaises(ProtocolMismatch) as error:
            probe_serial(port)
        self.assertNotIsInstance(error.exception, NoHelloResponse)

    @patch("sama_lcd.app.time.sleep")
    @patch("sama_lcd.app.ScreenSession")
    def test_startup_retries_only_empty_hello(self, session, sleep):
        session.return_value.__enter__.side_effect = [
            NoHelloResponse("empty"),
            ProtocolMismatch("invalid reply"),
        ]
        with self.assertRaisesRegex(ProtocolMismatch, "invalid reply"):
            app.run()
        self.assertEqual(session.call_count, 2)
        sleep.assert_called_once_with(2)

    @patch("sama_lcd.app.time.sleep")
    @patch("sama_lcd.app.ScreenSession")
    def test_repeated_empty_hello_stops_after_limit(self, session, sleep):
        session.return_value.__enter__.side_effect = NoHelloResponse("empty")
        with self.assertRaisesRegex(ProtocolMismatch, "连续 10 次"):
            app.run()
        self.assertEqual(session.call_count, app.HELLO_ATTEMPTS)
        self.assertEqual(sleep.call_count, app.HELLO_ATTEMPTS - 1)


if __name__ == "__main__":
    unittest.main()

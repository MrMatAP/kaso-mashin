import typing
from http.server import HTTPServer, BaseHTTPRequestHandler

from kaso_mashin.controllers import AbstractController
from kaso_mashin.model import InstanceModel


class PhoneHomeServer(HTTPServer):
    """
    A small server waiting for an instance to call home. We override this to pass it a function to be called
    with the actual IP address the instance has. We can't do this in the handler because it is statically
    referred to by the PhoneHomeServer
    """

    def __init__(self,
                 server_address: tuple[str, int],
                 RequestHandlerClass: typing.Callable,
                 callback: typing.Callable,
                 bind_and_activate: bool = ...) -> None:
        super().__init__(server_address, RequestHandlerClass, bind_and_activate)
        self._callback = callback

    @property
    def callback(self):
        return self._callback


class PhoneHomeHandler(BaseHTTPRequestHandler):
    """
    A handler for instances calling their mum
    """

    # It is actually required to be called do_POST, despite pylint complaining about it
    def do_POST(self):              # pylint: disable=invalid-name
        self.server.callback(self.client_address[0])
        self.send_response(code=200, message='Well, hello there!')
        self.end_headers()


class PhoneHomeController(AbstractController):
    """
    A controller for instances to call home when they're ready
    """

    def wait_for_instance(self, model: InstanceModel):
        httpd = PhoneHomeServer(server_address=(model.network.host_ip4, model.network.host_phone_home_port),
                                callback=self.instance_phoned_home,
                                RequestHandlerClass=PhoneHomeHandler)
        httpd.timeout = 120
        httpd.handle_request()

    def instance_phoned_home(self, actual_ip: str):
        pass

import vinc


class Module(vinc.BaseModule, mode=vinc.RunMode.FrameworkLoop):
    def on_name(self, args):
        return "receiver"

    def on_start(self, args):
        self.received = 0
        self.subscriber = self.context.subscribe(
            vinc.messages.CounterSample, "tutorial/counter", self.on_message
        )
        self.context.register_rpc(
            vinc.messages.GetCountRequest, vinc.messages.GetCountResponse,
            "get_count", self.get_count
        )
        print("ready receiver")

    def get_count(self, request, response):
        response.data().received = self.received
        return vinc.rpc.RpcStatus.success()

    def module_interface(self, args):
        if not args or args == ["status"]:
            print(f"received={self.received}")
            return 0
        if args == ["reset"]:
            self.received = 0
            print("counter reset")
            return 0

        print("Usage: receiver [status|reset]")
        return 1

    def on_message(self, message):
        self.received += 1
        print(
            f"received sequence={message.data().sequence} "
            f"publisher={message.publisher_name()}"
        )

    def on_stop(self):
        self.subscriber.close()
        print("stopped receiver")

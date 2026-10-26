import vinc


class Module(vinc.BaseModule, mode=vinc.RunMode.FrameworkLoop):
    def on_name(self, args):
        return "sender"

    def on_start(self, args):
        self.publisher = self.context.advertise(
            vinc.messages.CounterSample, "tutorial/counter"
        )
        self.next_sequence = 1
        print("ready sender")

    def module_interface(self, args):
        if args == ["send"]:
            return self.send_message()
        if args == ["count"]:
            return self.request_count()

        print("Usage: sender [send|count]")
        return 1

    def request_count(self):
        request = vinc.make_message(vinc.messages.GetCountRequest)
        try:
            self.context.call_rpc(
                vinc.messages.GetCountRequest, vinc.messages.GetCountResponse,
                "receiver", "get_count", request, self.on_count_reply
            )
        except vinc.VincError as error:
            print(f"RPC failed: {error}")
            return 1

        return 0

    def on_count_reply(self, reply, error):
        if error is not None:
            print(f"RPC failed: {error}")
            return

        status, response = reply
        if status.code != 0:
            print(f"RPC rejected: {status.reason}")
            return

        print(f"RPC received={response.data().received}")

    def send_message(self):
        try:
            message = vinc.make_message(vinc.messages.CounterSample)
            message.data().sequence = self.next_sequence
            self.publisher.push(message)
        except vinc.VincError as error:
            print(error)
            return 1

        self.next_sequence += 1
        return 0

    def on_stop(self):
        self.publisher.close()
        print("stopped sender")

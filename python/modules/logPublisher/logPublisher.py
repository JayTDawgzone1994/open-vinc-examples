import vinc


class Module(vinc.BaseModule, mode=vinc.RunMode.FrameworkLoop):
    def on_name(self, args):
        return "sender"

    def on_start(self, args):
        self.publisher = self.context.advertise(
            vinc.messages.CounterSample, "tutorial/counter"
        )
        self.next_sequence = 1
        self.write_log(vinc.log.Level.Info, "sender started")
        print("ready sender")

    def module_interface(self, args):
        if args == ["send"]:
            return self.send_message()
        if args == ["count"]:
            return self.request_count("receiver")
        if len(args) == 2 and args[0] == "count":
            return self.request_count(args[1])
        if args == ["trace"]:
            enabled = self.context.log.enabled(vinc.log.Level.Debug)
            self.write_log(vinc.log.Level.Debug, "trace detail")
            print(f"trace debug_enabled={int(enabled)}")
            return 0

        self.write_log(vinc.log.Level.Warn, "unknown sender command")
        print("Usage: sender [send|count [target]|trace]")
        return 1

    def write_log(self, level, text):
        try:
            self.context.log.write(level, text)
        except vinc.VincError as error:
            print(f"Log rejected: {error}")

    def request_count(self, target):
        request = vinc.make_message(vinc.messages.GetCountRequest)
        try:
            self.context.call_rpc(
                vinc.messages.GetCountRequest, vinc.messages.GetCountResponse,
                target, "get_count", request, self.on_count_reply
            )
        except vinc.VincError as error:
            self.write_log(vinc.log.Level.Error, f"RPC request failed: {error}")
            print(f"RPC failed: {error}")
            return 1

        return 0

    def on_count_reply(self, reply, error):
        if error is not None:
            self.write_log(vinc.log.Level.Error, f"RPC request failed: {error}")
            print(f"RPC failed: {error}")
            return

        status, response = reply
        if status.code != 0:
            self.write_log(vinc.log.Level.Error, f"RPC rejected: {status.reason}")
            print(f"RPC rejected: {status.reason}")
            return

        self.write_log(vinc.log.Level.Info, f"RPC count={response.data().received}")
        print(f"RPC received={response.data().received}")

    def send_message(self):
        self.write_log(vinc.log.Level.Debug, f"sending sequence={self.next_sequence}")
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
        self.write_log(vinc.log.Level.Info, "sender stopped")
        print("stopped sender")

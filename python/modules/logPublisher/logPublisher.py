import vinc


class Module(vinc.BaseModule, mode=vinc.RunMode.FrameworkLoop):
    def on_name(self, args):
        # Naming hook: return the instance name used to address this module in Shell.
        # Create publishers and subscriptions later, in on_start.
        return "sender"

    def on_start(self, args):
        # Startup hook: the framework calls this after the instance name is approved.
        # Set up this module here; returning None means initialization succeeded.
        self.publisher = self.context.advertise(
            vinc.messages.CounterSample, "tutorial/counter"
        )
        self.next_sequence = 1
        self.write_log(vinc.log.Level.Info, "sender started")
        print("ready sender")

    def module_interface(self, args):
        # Command hook: called when Shell addresses this instance.
        # Return 0 for success or 1 to report a command error.
        # args contains command arguments; the instance name is already removed.
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
        # Write one log entry; report rejected logs without stopping the module.
        try:
            self.context.log.write(level, text)
        except vinc.VincError as error:
            print(f"Log rejected: {error}")

    def request_count(self, target):
        # Submit an asynchronous RPC; on_count_reply handles the result later.
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
        # RPC completion callback: called later when the request finishes.
        # Check framework errors and the service status before using the response.
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
        # Publish one counter sample; advance the sequence after a successful push.
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
        # Shutdown hook: called during normal shutdown to clean up this module.
        self.publisher.close()
        self.write_log(vinc.log.Level.Info, "sender stopped")
        print("stopped sender")

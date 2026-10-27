import vinc


class Module(vinc.BaseModule, mode=vinc.RunMode.FrameworkLoop):
    def on_name(self, args):
        # Naming hook: return the instance name used to address this module in Shell.
        # Create publishers and subscriptions later, in on_start.
        return "receiver"

    def on_start(self, args):
        # Startup hook: the framework calls this after the instance name is approved.
        # Set up this module here; returning None means initialization succeeded.
        self.received = 0
        self.subscriber = self.context.subscribe(
            vinc.messages.CounterSample, "tutorial/counter", self.on_message
        )
        self.context.register_rpc(
            vinc.messages.GetCountRequest, vinc.messages.GetCountResponse,
            "get_count", self.get_count
        )
        self.write_log(vinc.log.Level.Info, "receiver started")
        print("ready receiver")

    def write_log(self, level, text):
        # Write one log entry; report rejected logs without stopping the module.
        try:
            self.context.log.write(level, text)
        except vinc.VincError as error:
            print(f"Log rejected: {error}")

    def get_count(self, request, response):
        # RPC handler: called when another module requests this receiver's count.
        # Fill response and return success; the framework sends the reply.
        response.data().received = self.received
        return vinc.rpc.RpcStatus.success()

    def module_interface(self, args):
        # Command hook: called when Shell addresses this instance.
        # Return 0 for success or 1 to report a command error.
        # args contains command arguments; the instance name is already removed.
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
        # Subscription callback: called when a counter message is delivered.
        self.received += 1
        self.write_log(vinc.log.Level.Info, f"counter received sequence={message.data().sequence}")
        print(
            f"received sequence={message.data().sequence} "
            f"publisher={message.publisher_name()}"
        )

    def on_stop(self):
        # Shutdown hook: called during normal shutdown to clean up this module.
        self.subscriber.close()
        self.write_log(vinc.log.Level.Info, "receiver stopped")
        print("stopped receiver")

import vinc


class Module(vinc.BaseModule, mode=vinc.RunMode.FrameworkLoop):
    def on_name(self, args):
        # Naming hook: return the instance name used to address this module in Shell.
        # Create publishers and subscriptions later, in on_start.
        return "sender"

    def on_start(self, args):
        # Startup hook: the framework calls this after the instance name is approved.
        # Set up this module here; returning None means initialization succeeded.
        self.sequence = 0
        self.step = 1
        self.context.param.register_param("step", vinc.param.Type.UInt64, 1)
        self.context.param.on_change(self.on_parameters_changed)
        self.publisher = self.context.advertise(
            vinc.messages.CounterSample, "tutorial/counter"
        )
        print("ready sender")

    def on_parameters_changed(self, values):
        # Parameter callback: read the latest step from the framework's local cache.
        try:
            self.step = self.context.param.update("step", vinc.param.Type.UInt64)
        except vinc.VincError as error:
            print(error)
            return

        print(f"step={self.step}")

    def module_interface(self, args):
        # Command hook: called when Shell addresses this instance.
        # Return 0 for success or 1 to report a command error.
        # args contains command arguments; the instance name is already removed.
        if args != ["send"]:
            print("Usage: sender send")
            return 1

        next_sequence = self.sequence + self.step
        if next_sequence > 2**64 - 1:
            print("sequence limit reached")
            return 1

        try:
            message = vinc.make_message(vinc.messages.CounterSample)
            message.data().sequence = next_sequence
            self.publisher.push(message)
        except vinc.VincError as error:
            print(error)
            return 1

        self.sequence = next_sequence
        return 0

    def on_stop(self):
        # Shutdown hook: called during normal shutdown to clean up this module.
        self.publisher.close()
        print("stopped sender")

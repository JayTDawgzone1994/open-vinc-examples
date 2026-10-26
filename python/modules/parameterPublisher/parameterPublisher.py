import vinc


class Module(vinc.BaseModule, mode=vinc.RunMode.FrameworkLoop):
    def on_name(self, args):
        return "sender"

    def on_start(self, args):
        self.sequence = 0
        self.step = 1
        self.context.param.register_param("step", vinc.param.Type.UInt64, 1)
        self.context.param.on_change(self.on_parameters_changed)
        self.publisher = self.context.advertise(
            vinc.messages.CounterSample, "tutorial/counter"
        )
        print("ready sender")

    def on_parameters_changed(self, values):
        try:
            self.step = self.context.param.update("step", vinc.param.Type.UInt64)
        except vinc.VincError as error:
            print(error)
            return

        print(f"step={self.step}")

    def module_interface(self, args):
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
        self.publisher.close()
        print("stopped sender")

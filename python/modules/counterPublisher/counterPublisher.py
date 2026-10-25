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
        if args != ["send"]:
            print("Usage: sender send")
            return 1

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

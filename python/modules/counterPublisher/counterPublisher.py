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
        print("ready sender")

    def module_interface(self, args):
        # Command hook: called when Shell addresses this instance.
        # Return 0 for success or 1 to report a command error.
        # args contains command arguments; the instance name is already removed.
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
        # Shutdown hook: called during normal shutdown to clean up this module.
        self.publisher.close()
        print("stopped sender")

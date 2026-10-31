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
            vinc.messages.SensorReading, "tutorial/sensor"
        )
        print("ready sender")

    def module_interface(self, args):
        # Command hook: called when Shell addresses this instance.
        # Return 0 for success or 1 to report a command error.
        if args == ["send"]:
            return self.send_message()
        print("Usage: sender send")
        return 1

    def send_message(self):
        # Fill both fields, then publish only if the string assignment succeeded.
        try:
            message = vinc.make_message(vinc.messages.SensorReading)
            message.data().temperature = 23.5
            message.data().sensor.assign("room")
            self.publisher.push(message)
        except vinc.VincError as error:
            print(error)
            return 1
        return 0

    def on_stop(self):
        # Shutdown hook: called during normal shutdown to clean up this module.
        self.publisher.close()
        print("stopped sender")

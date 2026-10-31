import vinc


class Module(vinc.BaseModule, mode=vinc.RunMode.FrameworkLoop):
    def on_name(self, args):
        # Naming hook: return the instance name used to address this module in Shell.
        # Create publishers and subscriptions later, in on_start.
        return "receiver"

    def on_start(self, args):
        # Startup hook: the framework calls this after the instance name is approved.
        # Set up this module here; returning None means initialization succeeded.
        self.subscriber = self.context.subscribe(
            vinc.messages.SensorReading, "tutorial/sensor", self.on_message
        )
        print("ready receiver")

    def module_interface(self, args):
        # This example only receives messages; it has no receiver commands.
        print("This receiver has no commands")
        return 1

    def on_message(self, message):
        # Subscription callback: read the numeric field and copy the sensor text.
        print(
            f"received sensor={message.data().sensor.decode()} "
            f"temperature={message.data().temperature} "
            f"publisher={message.publisher_name()}"
        )

    def on_stop(self):
        # Shutdown hook: called during normal shutdown to clean up this module.
        self.subscriber.close()
        print("stopped receiver")

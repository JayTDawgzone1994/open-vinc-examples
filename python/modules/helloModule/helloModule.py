import vinc


class Module(vinc.BaseModule, mode=vinc.RunMode.FrameworkLoop):
    def on_name(self, args):
        return "hello"

    def on_start(self, args):
        print("hello started")

    def on_stop(self):
        print("hello stopped")

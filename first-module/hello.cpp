#include <vinc/vinc.hpp>

#include <cstdint>
#include <iostream>
#include <string>
#include <vector>

class HelloModule final
    : public vinc::BaseModule<vinc::RunMode::FrameworkLoop> {
public:
    HelloModule() : BaseModule("hello") {
        // Set the instance name used by Shell commands.
    }

    vinc::Result<void> on_start(const std::vector<std::string>&) override {
        // Startup hook: the framework calls this after the instance name is approved.
        // Set up this module here; returning {} means initialization succeeded.
        std::cout << "hello started" << std::endl;
        return {};
    }

    vinc::Result<std::int32_t> module_interface(std::vector<std::string>) override {
        // Command hook: called when Shell addresses this instance.
        // Return 0 for success or 1 to report a command error.
        // This first example does not provide application commands.
        return 1;
    }

    vinc::Result<void> on_stop() override {
        // Shutdown hook: called during normal shutdown to clean up this module.
        std::cout << "hello stopped" << std::endl;
        return {};
    }
};

// Register the type name Shell uses to create this module.
REGISTER_MODULE(HelloModule, "helloModule")

#include <vinc/vinc.hpp>

#include <cstdint>
#include <iostream>
#include <string>
#include <vector>

class HelloModule final
    : public vinc::BaseModule<vinc::RunMode::FrameworkLoop> {
public:
    HelloModule() : BaseModule("hello") {
    }

    vinc::Result<void> on_start(const std::vector<std::string>&) override {
        std::cout << "hello started" << std::endl;
        return {};
    }

    vinc::Result<std::int32_t> module_interface(std::vector<std::string>) override {
        // This first example does not provide application commands.
        return 1;
    }

    vinc::Result<void> on_stop() override {
        std::cout << "hello stopped" << std::endl;
        return {};
    }
};

REGISTER_MODULE(HelloModule, "helloModule")

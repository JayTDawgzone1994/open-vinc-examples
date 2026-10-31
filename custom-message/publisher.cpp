#include <vinc/vinc.hpp>
#include <vinc_messages/SensorReading.hpp>

#include <cstdint>
#include <iostream>
#include <optional>
#include <string>
#include <utility>
#include <vector>

class SensorPublisher final
    : public vinc::BaseModule<vinc::RunMode::FrameworkLoop> {
public:
    SensorPublisher() : BaseModule("sender") {
        // Set the instance name used by Shell commands.
    }

    vinc::Result<void> on_start(const std::vector<std::string>&) override {
        // Startup hook: the framework calls this after the instance name is approved.
        // Set up this module here; returning {} means initialization succeeded.
        auto publisher = context.advertise<vinc::SensorReading>("tutorial/sensor");
        if (!publisher) {
            return std::unexpected(publisher.error());
        }

        publisher_.emplace(std::move(*publisher));
        std::cout << "ready sender" << std::endl;
        return {};
    }

    vinc::Result<std::int32_t> module_interface(std::vector<std::string> args) override {
        // Command hook: called when Shell addresses this instance.
        // Return 0 for success or 1 to report a command error.
        if (!args.empty() && args.front() == get_module_name()) {
            args.erase(args.begin());
        }
        if (args.size() == 1 && args.front() == "send") {
            return send_message();
        }

        std::cout << "Usage: sender send" << std::endl;
        return 1;
    }

    vinc::Result<void> on_stop() override {
        // Shutdown hook: called during normal shutdown to clean up this module.
        publisher_.reset();
        std::cout << "stopped sender" << std::endl;
        return {};
    }

private:
    std::int32_t send_message() {
        // Fill both fields, then publish only if the string assignment succeeded.
        auto message = vinc::make_message<vinc::SensorReading>();
        message->data().temperature = 23.5;
        auto assigned = message->data().sensor.assign("room");
        if (!assigned) {
            std::cerr << vinc::error_to_string(assigned.error()) << std::endl;
            return 1;
        }

        auto published = publisher_->push(*message);
        if (!published) {
            std::cerr << vinc::error_to_string(published.error()) << std::endl;
            return 1;
        }
        return 0;
    }

    std::optional<vinc::message_bus::Publisher<vinc::SensorReading>> publisher_;
};

// Register the type name Shell uses to create this module.
REGISTER_MODULE(SensorPublisher, "sensorPublisher")

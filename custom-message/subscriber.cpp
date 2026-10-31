#include <vinc/vinc.hpp>
#include <vinc_messages/SensorReading.hpp>

#include <cstdint>
#include <iostream>
#include <memory>
#include <optional>
#include <string>
#include <utility>
#include <vector>

class SensorSubscriber final
    : public vinc::BaseModule<vinc::RunMode::FrameworkLoop> {
public:
    SensorSubscriber() : BaseModule("receiver") {
        // Set the instance name used by Shell commands.
    }

    vinc::Result<void> on_start(const std::vector<std::string>&) override {
        // Startup hook: the framework calls this after the instance name is approved.
        // Set up this module here; returning {} means initialization succeeded.
        auto subscriber = context.subscribe<vinc::SensorReading>(
            "tutorial/sensor",
            [this](std::unique_ptr<vinc::SensorReading> message) {
                on_message(std::move(message));
            });
        if (!subscriber) {
            return std::unexpected(subscriber.error());
        }

        subscriber_.emplace(std::move(*subscriber));
        std::cout << "ready receiver" << std::endl;
        return {};
    }

    vinc::Result<std::int32_t> module_interface(std::vector<std::string>) override {
        // This example only receives messages; it has no receiver commands.
        std::cout << "This receiver has no commands" << std::endl;
        return 1;
    }

    vinc::Result<void> on_stop() override {
        // Shutdown hook: called during normal shutdown to clean up this module.
        subscriber_.reset();
        std::cout << "stopped receiver" << std::endl;
        return {};
    }

private:
    void on_message(std::unique_ptr<vinc::SensorReading> message) {
        // Subscription callback: read the numeric field and copy the sensor text.
        std::cout
            << "received sensor=" << message->data().sensor.str()
            << " temperature=" << message->data().temperature.get()
            << " publisher=" << message->publisher_name()
            << std::endl;
    }

    std::optional<vinc::message_bus::Subscriber<vinc::SensorReading>> subscriber_;
};

// Register the type name Shell uses to create this module.
REGISTER_MODULE(SensorSubscriber, "sensorSubscriber")

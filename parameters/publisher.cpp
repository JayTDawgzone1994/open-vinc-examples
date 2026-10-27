#include <vinc/vinc.hpp>
#include <vinc_messages/CounterSample.hpp>

#include <cstdint>
#include <iostream>
#include <limits>
#include <optional>
#include <string>
#include <utility>
#include <vector>

class ParameterPublisher final
    : public vinc::BaseModule<vinc::RunMode::FrameworkLoop> {
public:
    ParameterPublisher() : BaseModule("sender") {
        // Set the instance name used by Shell commands.
    }

    vinc::Result<void> on_start(const std::vector<std::string>&) override {
        // Startup hook: the framework calls this after the instance name is approved.
        // Set up this module here; returning {} means initialization succeeded.
        auto registered = context.param.register_param<std::uint64_t>("step", 1);
        if (!registered) {
            return std::unexpected(registered.error());
        }

        auto watching = context.param.on_change([this](const vinc::param::ParamMap&) {
            on_parameters_changed();
        });
        if (!watching) {
            return std::unexpected(watching.error());
        }

        auto publisher = context.advertise<vinc::CounterSample>("tutorial/counter");
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

        if (args.size() != 1 || args.front() != "send") {
            std::cout << "Usage: sender send" << std::endl;
            return 1;
        }

        if (step_ > std::numeric_limits<std::uint64_t>::max() - sequence_) {
            std::cout << "sequence limit reached" << std::endl;
            return 1;
        }

        const auto next_sequence = sequence_ + step_;
        auto message = vinc::make_message<vinc::CounterSample>();
        message->data().sequence = next_sequence;

        auto published = publisher_->push(*message);
        if (!published) {
            std::cerr << vinc::error_to_string(published.error()) << std::endl;
            return 1;
        }

        sequence_ = next_sequence;
        return 0;
    }

    vinc::Result<void> on_stop() override {
        // Shutdown hook: called during normal shutdown to clean up this module.
        publisher_.reset();
        std::cout << "stopped sender" << std::endl;
        return {};
    }

private:
    void on_parameters_changed() {
        // Parameter callback: read the latest step from the framework's local cache.
        auto updated = context.param.update("step", step_);
        if (!updated) {
            std::cerr << vinc::error_to_string(updated.error()) << std::endl;
            return;
        }

        std::cout << "step=" << step_ << std::endl;
    }

    std::optional<vinc::message_bus::Publisher<vinc::CounterSample>> publisher_;
    std::uint64_t sequence_ = 0;
    std::uint64_t step_ = 1;
};

// Register the type name Shell uses to create this module.
REGISTER_MODULE(ParameterPublisher, "parameterPublisher")

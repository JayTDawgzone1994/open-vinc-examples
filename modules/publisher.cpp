#include <vinc/vinc.hpp>
#include <vinc_messages/CounterSample.hpp>

#include <cstdint>
#include <iostream>
#include <optional>
#include <string>
#include <utility>
#include <vector>

class CounterPublisher final
    : public vinc::BaseModule<vinc::RunMode::FrameworkLoop> {
public:
    CounterPublisher() : BaseModule("sender") {
    }

    vinc::Result<void> on_start(const std::vector<std::string>&) override {
        auto publisher = context.advertise<vinc::CounterSample>(
            "tutorial/counter");
        if (!publisher) {
            return std::unexpected(publisher.error());
        }

        publisher_.emplace(std::move(*publisher));
        std::cout << "ready sender" << std::endl;
        return {};
    }

    vinc::Result<std::int32_t> module_interface(std::vector<std::string> args) override {
        // Native Shell includes the target. Direct Manager callers may omit it.
        if (!args.empty() && args.front() == get_module_name()) {
            args.erase(args.begin());
        }

        if (args.size() != 1 || args.front() != "send") {
            std::cout << "Usage: sender send" << std::endl;
            return 1;
        }

        auto message = vinc::make_message<vinc::CounterSample>();
        message->data().sequence = next_sequence_;

        auto published = publisher_->push(*message);
        if (!published) {
            std::cerr << vinc::error_to_string(published.error()) << std::endl;
            return 1;
        }

        ++next_sequence_;
        return 0;
    }

    vinc::Result<void> on_stop() override {
        publisher_.reset();
        std::cout << "stopped sender" << std::endl;
        return {};
    }

private:
    std::optional<vinc::message_bus::Publisher<vinc::CounterSample>> publisher_;
    std::uint64_t next_sequence_ = 1;
};

REGISTER_MODULE(CounterPublisher, "counterPublisher")

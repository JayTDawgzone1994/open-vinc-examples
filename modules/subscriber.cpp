#include <vinc/vinc.hpp>
#include <vinc_messages/CounterSample.hpp>

#include <cstdint>
#include <iostream>
#include <memory>
#include <optional>
#include <string>
#include <utility>
#include <vector>

class CounterSubscriber final
    : public vinc::BaseModule<vinc::RunMode::FrameworkLoop> {
public:
    CounterSubscriber() : BaseModule("receiver") {
    }

    vinc::Result<void> on_start(const std::vector<std::string>&) override {
        auto subscriber = context.subscribe<vinc::CounterSample>(
            "tutorial/counter",
            [this](std::unique_ptr<vinc::CounterSample> message) {
                on_message(std::move(message));
            });
        if (!subscriber) {
            return std::unexpected(subscriber.error());
        }

        subscriber_.emplace(std::move(*subscriber));
        std::cout << "ready receiver" << std::endl;
        return {};
    }

    vinc::Result<std::int32_t> module_interface(std::vector<std::string> args) override {
        if (!args.empty() && args.front() == get_module_name()) {
            args.erase(args.begin());
        }

        if (!args.empty() && (args.size() != 1 || args.front() != "status")) {
            std::cout << "Usage: receiver [status]" << std::endl;
            return 1;
        }

        std::cout << "received=" << received_ << std::endl;
        return 0;
    }

    vinc::Result<void> on_stop() override {
        subscriber_.reset();
        std::cout << "stopped receiver" << std::endl;
        return {};
    }

private:
    void on_message(std::unique_ptr<vinc::CounterSample> message) {
        ++received_;

        // Flush this small interactive example so captured output is visible promptly.
        std::cout
            << "received sequence=" << message->data().sequence.get()
            << " publisher=" << message->publisher_name()
            << std::endl;
    }

    std::optional<vinc::message_bus::Subscriber<vinc::CounterSample>> subscriber_;
    std::uint64_t received_ = 0;
};

REGISTER_MODULE(CounterSubscriber, "counterSubscriber")

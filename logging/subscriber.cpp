#include <vinc/vinc.hpp>
#include <vinc_messages/CounterSample.hpp>
#include <vinc_messages/GetCountRequest.hpp>
#include <vinc_messages/GetCountResponse.hpp>

#include <cstdint>
#include <iostream>
#include <memory>
#include <optional>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

class LogSubscriber final
    : public vinc::BaseModule<vinc::RunMode::FrameworkLoop> {
public:
    LogSubscriber() : BaseModule("receiver") {
        // Set the instance name used by Shell commands.
    }

    vinc::Result<void> on_start(const std::vector<std::string>&) override {
        // Startup hook: the framework calls this after the instance name is approved.
        // Set up this module here; returning {} means initialization succeeded.
        auto subscriber = context.subscribe<vinc::CounterSample>(
            "tutorial/counter", [this](std::unique_ptr<vinc::CounterSample> message) {
                on_message(std::move(message));
            });
        if (!subscriber) {
            return std::unexpected(subscriber.error());
        }
        subscriber_.emplace(std::move(*subscriber));

        auto registered = context.register_rpc<vinc::GetCountRequest, vinc::GetCountResponse>(
            "get_count", {},
            [this](const vinc::GetCountRequest& request, vinc::GetCountResponse& response) {
                return get_count(request, response);
            });
        if (!registered) {
            return std::unexpected(registered.error());
        }

        write_log(vinc::log::Level::Info, "receiver started");
        std::cout << "ready receiver" << std::endl;
        return {};
    }

    vinc::Result<std::int32_t> module_interface(std::vector<std::string> args) override {
        // Command hook: called when Shell addresses this instance.
        // Return 0 for success or 1 to report a command error.
        if (!args.empty() && args.front() == get_module_name()) {
            args.erase(args.begin());
        }
        if (args.empty()) {
            args.push_back("status");
        }
        if (args.size() == 1 && args.front() == "status") {
            std::cout << "received=" << received_ << std::endl;
            return 0;
        }
        if (args.size() == 1 && args.front() == "reset") {
            received_ = 0;
            std::cout << "counter reset" << std::endl;
            return 0;
        }

        std::cout << "Usage: receiver [status|reset]" << std::endl;
        return 1;
    }

    vinc::Result<void> on_stop() override {
        // Shutdown hook: called during normal shutdown to clean up this module.
        subscriber_.reset();
        write_log(vinc::log::Level::Info, "receiver stopped");
        std::cout << "stopped receiver" << std::endl;
        return {};
    }

private:
    void write_log(vinc::log::Level level, std::string_view text) {
        // Write one log entry; report rejected logs without stopping the module.
        auto logged = context.log.write(level, text);
        if (!logged) {
            std::cerr << "Log rejected: " << vinc::error_to_string(logged.error()) << std::endl;
        }
    }

    vinc::rpc::RpcStatus get_count(const vinc::GetCountRequest&, vinc::GetCountResponse& response) {
        // RPC handler: called when another module requests this receiver's count.
        // Fill response and return success; the framework sends the reply.
        response.data().received = received_;
        return vinc::rpc::RpcStatus::success();
    }

    void on_message(std::unique_ptr<vinc::CounterSample> message) {
        // Subscription callback: called when a counter message is delivered.
        ++received_;
        write_log(vinc::log::Level::Info,
                  "counter received sequence=" + std::to_string(message->data().sequence.get()));
        std::cout << "received sequence=" << message->data().sequence.get()
                  << " publisher=" << message->publisher_name() << std::endl;
    }

    std::optional<vinc::message_bus::Subscriber<vinc::CounterSample>> subscriber_;
    std::uint64_t received_ = 0;
};

// Register the type name Shell uses to create this module.
REGISTER_MODULE(LogSubscriber, "logSubscriber")

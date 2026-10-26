#include <vinc/vinc.hpp>
#include <vinc_messages/CounterSample.hpp>
#include <vinc_messages/GetCountRequest.hpp>
#include <vinc_messages/GetCountResponse.hpp>

#include <cstdint>
#include <iostream>
#include <memory>
#include <optional>
#include <string>
#include <utility>
#include <vector>

class RpcSubscriber final
    : public vinc::BaseModule<vinc::RunMode::FrameworkLoop> {
public:
    RpcSubscriber() : BaseModule("receiver") {
    }

    vinc::Result<void> on_start(const std::vector<std::string>&) override {
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

        std::cout << "ready receiver" << std::endl;
        return {};
    }

    vinc::Result<std::int32_t> module_interface(std::vector<std::string> args) override {
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
        subscriber_.reset();
        std::cout << "stopped receiver" << std::endl;
        return {};
    }

private:
    vinc::rpc::RpcStatus get_count(const vinc::GetCountRequest&, vinc::GetCountResponse& response) {
        response.data().received = received_;
        return vinc::rpc::RpcStatus::success();
    }

    void on_message(std::unique_ptr<vinc::CounterSample> message) {
        ++received_;
        std::cout << "received sequence=" << message->data().sequence.get()
                  << " publisher=" << message->publisher_name() << std::endl;
    }

    std::optional<vinc::message_bus::Subscriber<vinc::CounterSample>> subscriber_;
    std::uint64_t received_ = 0;
};

REGISTER_MODULE(RpcSubscriber, "rpcSubscriber")
